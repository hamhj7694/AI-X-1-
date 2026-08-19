from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from services.feature_extractor import (
    CASE_FEATURES,
    EXTRACTOR_MATCHES_TRAINING_PIPELINE,
    EXTRACTOR_NAME,
    FEATURE_META,
    extract_evidence,
    extract_features,
    make_windows,
    parse_turns,
)
from services.model_loader import load_model_bundle


STATE_KO = {"MONITORING": "모니터링", "SUSPICIOUS": "의심", "HIGH_RISK": "고위험"}
DECISION_MESSAGES = {
    "HIGH_RISK": "보이스피싱 고위험 신호가 감지되었습니다. 송금·개인정보 제공을 중단하고 공식 채널로 사실을 확인하세요.",
    "SUSPICIOUS": "보이스피싱 의심 신호가 감지되었습니다. 상대방 요구를 즉시 이행하지 말고 공식 기관을 통해 다시 확인하세요.",
    "MONITORING": "현재 고위험 기준을 넘지 않았습니다. 이는 정상 통화 확정을 의미하지 않으며 계속 주의가 필요합니다.",
}


def _positive_probability(model: Any, frame: pd.DataFrame) -> np.ndarray:
    probabilities = np.asarray(model.predict_proba(frame), dtype=float)
    classes = list(getattr(model, "classes_", [0, 1]))
    positive_index = classes.index(1) if 1 in classes else probabilities.shape[1] - 1
    return probabilities[:, positive_index]


def _calibrate(method: str, calibrator: Any, raw_probability: np.ndarray) -> np.ndarray:
    """Apply the exact 07 calibration contract (PLATT was fitted on logit(raw p))."""
    probability = np.clip(np.asarray(raw_probability, dtype=float), 1e-6, 1 - 1e-6)
    method = str(method or "IDENTITY").upper()
    if method == "IDENTITY":
        return probability
    if calibrator is None:
        raise ValueError(f"{method} 보정기가 bundle에 없습니다.")
    if method == "PLATT":
        model_input = np.log(probability / (1 - probability)).reshape(-1, 1)
        return np.asarray(calibrator.predict_proba(model_input)[:, 1], dtype=float)
    if method == "ISOTONIC":
        return np.asarray(calibrator.predict(probability), dtype=float)
    if hasattr(calibrator, "predict_proba"):
        return np.asarray(calibrator.predict_proba(probability.reshape(-1, 1))[:, 1], dtype=float)
    if hasattr(calibrator, "predict"):
        return np.asarray(calibrator.predict(probability), dtype=float)
    raise ValueError(f"지원하지 않는 보정 방식입니다: {method}")


def _ordered_frame(values: dict[str, float], declared: list[str]) -> pd.DataFrame:
    missing = [feature for feature in declared if feature not in values]
    if missing:
        raise ValueError(f"생성할 수 없는 모델 특징: {', '.join(missing)}")
    return pd.DataFrame([{feature: values[feature] for feature in declared}], columns=declared, dtype=float)


def _threshold(section: dict[str, Any], level: str) -> float:
    score_key = f"{level}_risk_score_threshold"
    probability_key = f"{level}_probability_threshold"
    if section.get(score_key) is not None:
        return float(section[score_key])
    if section.get(probability_key) is not None:
        return float(section[probability_key]) * 100
    raise ValueError(f"bundle에 {level} 임계값이 없습니다.")


def _state(score: float, suspicious_threshold: float, high_threshold: float) -> str:
    if score >= high_threshold:
        return "HIGH_RISK"
    if score >= suspicious_threshold:
        return "SUSPICIOUS"
    return "MONITORING"


def _window_summary(raw_probabilities: list[float], declared_features: list[str]) -> dict[str, float]:
    if not raw_probabilities:
        return {feature: np.nan for feature in declared_features}

    values = np.asarray(raw_probabilities, dtype=float)
    trend = float(np.polyfit(np.linspace(0, 1, len(values)), values, 1)[0]) if len(values) > 1 else 0.0
    summary = {
        "window_prob_mean": float(values.mean()),
        "window_prob_max": float(values.max()),
        "window_prob_p90": float(np.percentile(values, 90)),
        "window_prob_std": float(values.std(ddof=0)) if len(values) > 1 else 0.0,
        "window_prob_first": float(values[0]),
        "window_prob_last": float(values[-1]),
        "window_prob_delta_last_first": float(values[-1] - values[0]),
        "window_prob_trend": trend,
    }
    unsupported = [feature for feature in declared_features if feature not in summary]
    if unsupported:
        raise ValueError(f"지원하지 않는 Window 요약 특징: {', '.join(unsupported)}")
    return {feature: summary[feature] for feature in declared_features}


def _service_state(window_results: list[dict[str, Any]], case_state: str) -> str:
    window_states = {item["state"] for item in window_results}
    if "HIGH_RISK" in window_states or case_state == "HIGH_RISK":
        return "HIGH_RISK"
    if "SUSPICIOUS" in window_states or case_state == "SUSPICIOUS":
        return "SUSPICIOUS"
    return "MONITORING"


def analyze_text(raw_text: str) -> dict[str, Any]:
    turns = parse_turns(raw_text)
    case_features = extract_features(" ".join(turn["text"] for turn in turns))
    evidence = extract_evidence(turns)
    bundle, model_error = load_model_bundle()

    result: dict[str, Any] = {
        "model_ready": bundle is not None,
        "model_error": model_error,
        "bundle_version": None,
        "window_model_name": None,
        "case_model_name": None,
        "feature_extractor": EXTRACTOR_NAME,
        "feature_extractor_matches_training": EXTRACTOR_MATCHES_TRAINING_PIPELINE,
        "turns": turns,
        "windows": [],
        "window_results": [],
        "window_max_score": None,
        "case_score": None,
        "case_raw_probability": None,
        "case_calibrated_probability": None,
        "window_suspicious_threshold": None,
        "window_high_threshold": None,
        "case_suspicious_threshold": None,
        "case_high_threshold": None,
        "window_threshold": None,
        "case_threshold": None,
        "window_calibration_method": None,
        "case_calibration_method": None,
        "policy_selection_status": None,
        "policy_validation": None,
        "decision": "분석 대기",
        "decision_state": None,
        "decision_message": "모델 파일이 준비되면 실제 위험점수를 계산합니다.",
        "case_features": case_features,
        "evidence": evidence,
    }
    if bundle is None:
        return result

    try:
        window_bundle, case_bundle = bundle["window"], bundle["case"]
        window_suspicious = _threshold(window_bundle, "suspicious")
        window_high = _threshold(window_bundle, "high")
        case_suspicious = _threshold(case_bundle, "suspicious")
        case_high = _threshold(case_bundle, "high")
        window_turns = int(window_bundle.get("window_turns", 10))
        window_stride = int(window_bundle.get("window_stride", 5))
        windows = make_windows(turns, window_turns=window_turns, stride=window_stride)

        result.update(
            {
                "bundle_version": bundle.get("bundle_version"),
                "window_model_name": window_bundle.get("model_name", type(window_bundle["model"]).__name__),
                "case_model_name": case_bundle.get("model_name", type(case_bundle["model"]).__name__),
                "windows": windows,
                "window_turns": window_turns,
                "window_stride": window_stride,
                "window_suspicious_threshold": window_suspicious,
                "window_high_threshold": window_high,
                "case_suspicious_threshold": case_suspicious,
                "case_high_threshold": case_high,
                "window_threshold": window_high,
                "case_threshold": case_high,
                "window_calibration_method": str(window_bundle.get("calibration_method", "IDENTITY")).upper(),
                "case_calibration_method": str(case_bundle.get("calibration_method", "IDENTITY")).upper(),
                "policy_selection_status": bundle.get("service_policy", {}).get("soft_selection_status"),
                "policy_validation": bundle.get("service_policy", {}).get("aggressive_suspicious_policy"),
            }
        )

        previous_signal_count = 0.0
        window_raw_probabilities: list[float] = []
        window_features = list(window_bundle["features"])
        for window in windows:
            values = extract_features(window["text"])
            current_signal_count = float(values["signal_family_count_sem"])
            values["signal_family_count_delta_sem"] = current_signal_count - previous_signal_count
            previous_signal_count = current_signal_count
            frame = _ordered_frame(values, window_features)
            raw = _positive_probability(window_bundle["model"], frame)
            calibrated = _calibrate(window_bundle.get("calibration_method", "IDENTITY"), window_bundle.get("calibrator"), raw)
            raw_value, calibrated_value = float(raw[0]), float(calibrated[0])
            score = calibrated_value * 100
            state = _state(score, window_suspicious, window_high)
            window_raw_probabilities.append(raw_value)  # STACKED_SAFE was trained on raw Window probability.
            result["window_results"].append(
                {
                    "window_index": window["window_index"],
                    "start_turn": window["start_turn"],
                    "end_turn": window["end_turn"],
                    "raw_probability": raw_value,
                    "calibrated_probability": calibrated_value,
                    "risk_score": score,
                    "state": state,
                    "suspicious": state in {"SUSPICIOUS", "HIGH_RISK"},
                    "high_risk": state == "HIGH_RISK",
                    "alert": state == "HIGH_RISK",  # legacy alias
                }
            )

        stack_features = list(bundle["stacking"].get("features", []))
        case_values = {**case_features, **_window_summary(window_raw_probabilities, stack_features)}
        case_features_order = list(case_bundle["features"])
        case_frame = _ordered_frame(case_values, case_features_order)
        case_raw = _positive_probability(case_bundle["model"], case_frame)
        case_calibrated = _calibrate(case_bundle.get("calibration_method", "IDENTITY"), case_bundle.get("calibrator"), case_raw)
        case_raw_value, case_calibrated_value = float(case_raw[0]), float(case_calibrated[0])
        case_score = case_calibrated_value * 100
        case_state = _state(case_score, case_suspicious, case_high)
        final_state = _service_state(result["window_results"], case_state)

        result.update(
            {
                "window_max_score": max((item["risk_score"] for item in result["window_results"]), default=None),
                "case_raw_probability": case_raw_value,
                "case_calibrated_probability": case_calibrated_value,
                "case_score": case_score,
                "case_state": case_state,
                "decision_state": final_state,
                "decision": STATE_KO[final_state],
                "decision_message": DECISION_MESSAGES[final_state],
            }
        )
    except Exception as exc:
        result["model_ready"] = False
        result["model_error"] = f"추론 입력을 구성하지 못했습니다: {type(exc).__name__}: {exc}"
    return result


def feature_table(result: dict[str, Any]) -> pd.DataFrame:
    rows = []
    for feature in CASE_FEATURES:
        category, label = FEATURE_META.get(feature, ("기타", feature))
        value = result.get("case_features", {}).get(feature, 0)
        rows.append(
            {
                "위험범주": category,
                "탐지변수": label,
                "모델변수": feature,
                "추출값": value,
                "해석": "신호 확인" if pd.notna(value) and value > 0 else "미탐지",
            }
        )
    return pd.DataFrame(rows)
