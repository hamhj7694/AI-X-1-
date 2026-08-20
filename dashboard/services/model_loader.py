from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any


DASHBOARD_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = DASHBOARD_ROOT.parent
MODEL_PATH = PROJECT_ROOT / "a_함형준" / "MLmodel_v1" / "final_voice_phishing_risk_pipeline.pkl"


def _restore_missing_imputer_dtype(bundle: dict[str, Any]) -> list[str]:
    """Restore dtype metadata omitted from this trusted sklearn 1.8 bundle."""
    repaired: list[str] = []
    for section in ("window", "case"):
        pipeline = bundle.get(section, {}).get("model")
        steps = getattr(pipeline, "named_steps", {})
        imputer = steps.get("imputer") if hasattr(steps, "get") else None
        if imputer is not None and not hasattr(imputer, "_fill_dtype") and hasattr(imputer, "_fit_dtype"):
            imputer._fill_dtype = imputer._fit_dtype
            repaired.append(f"{section}.model.imputer._fill_dtype")
    return repaired


@lru_cache(maxsize=1)
def load_model_bundle() -> tuple[dict[str, Any] | None, str | None]:
    """Load only the trusted, project-owned bundle once per server process."""
    if not MODEL_PATH.is_file():
        return None, f"최종 모델 파일을 찾을 수 없습니다: {MODEL_PATH}"
    try:
        import joblib
    except ModuleNotFoundError:
        return None, "모델 실행에 필요한 joblib 또는 scikit-learn이 설치되지 않았습니다."

    try:
        bundle = joblib.load(MODEL_PATH)
        required = {"window", "stacking", "case", "service_policy", "risk_score"}
        missing = required - set(bundle)
        if missing:
            raise ValueError(f"bundle 필수 항목 누락: {', '.join(sorted(missing))}")
        for section in ("window", "case"):
            absent = {"model", "features"} - set(bundle[section])
            if absent:
                raise ValueError(f"bundle[{section!r}] 필수 항목 누락: {', '.join(sorted(absent))}")
        bundle["runtime_compatibility_repairs"] = _restore_missing_imputer_dtype(bundle)
        return bundle, None
    except Exception as exc:  # version mismatch/corruption must not crash Streamlit
        return None, f"모델 파일을 불러오지 못했습니다: {type(exc).__name__}: {exc}"
