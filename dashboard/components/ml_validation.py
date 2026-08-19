from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


DATA_ROOT = Path(__file__).resolve().parents[1] / "data" / "ml_validation"
VOICE_DATA_ROOT = Path(__file__).resolve().parents[1] / "data" / "금융감독원 데이터셋"
BLUE, NAVY, TEAL, ORANGE, RED, GRAY = "#2563eb", "#173f73", "#0f9d8a", "#f59e0b", "#dc5a5a", "#94a3b8"
MODEL_KO = {
    "LogisticRegression": "Logistic Regression",
    "DecisionTree": "Decision Tree",
    "RandomForest": "Random Forest",
    "XGBoost": "XGBoost",
    "LightGBM": "LightGBM",
}


@st.cache_data(show_spinner=False)
def _csv(name: str) -> pd.DataFrame:
    return pd.read_csv(DATA_ROOT / name, encoding="utf-8-sig")


@st.cache_data(show_spinner=False)
def _config() -> dict:
    return json.loads((DATA_ROOT / "risk_score_config_07.json").read_text(encoding="utf-8"))


@st.cache_data(show_spinner=False)
def _dataset_shape(name: str, fallback: tuple[int, int]) -> tuple[int, int]:
    path = VOICE_DATA_ROOT / name
    if not path.exists():
        return fallback
    frame = pd.read_csv(path, encoding="utf-8-sig", low_memory=False)
    return frame.shape


def _layout(fig: go.Figure, height: int = 340) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=dict(l=10, r=12, t=18, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Arial, Apple SD Gothic Neo, Malgun Gothic, sans-serif", size=13, color="#273449"),
        hoverlabel=dict(font_size=13),
        legend=dict(orientation="h", y=1.02, x=1, xanchor="right"),
    )
    fig.update_xaxes(showgrid=True, gridcolor="#e9eef5", zeroline=False)
    fig.update_yaxes(showgrid=False, zeroline=False)
    return fig


def _section(title: str, note: str) -> None:
    st.markdown(f"<div class='mlv-title'>{title}</div><div class='mlv-note'>{note}</div>", unsafe_allow_html=True)


def _metric(label: str, value: str, note: str = "") -> None:
    st.markdown(
        f"<div class='mlv-metric'><div class='mlv-metric-label'>{label}</div>"
        f"<div class='mlv-metric-value'>{value}</div><div class='mlv-metric-note'>{note}</div></div>",
        unsafe_allow_html=True,
    )


def render_ml_validation() -> None:
    """ML 제작 과정, 비교 검증, 확률 보정과 경고 기준을 설명한다."""
    with st.container(key="analysis_container"):
        st.markdown(
            """
            <style>
            .mlv-hero{padding:1.15rem 1.3rem;border:1px solid #dce4ee;border-radius:.85rem;background:linear-gradient(120deg,#fff,#edf5ff)}
            .mlv-hero h1{margin:0;color:#172033;font-size:1.82rem}.mlv-hero p{margin:.45rem 0 0;color:#315a87;font-size:.95rem;line-height:1.55}
            .mlv-flow{display:grid;grid-template-columns:repeat(8,minmax(0,1fr));gap:.42rem;margin-top:1rem}
            .mlv-step{position:relative;padding:.66rem .35rem;border:1px solid #dce4ee;border-radius:.55rem;background:#fff;text-align:center;color:#315a87;font-size:.73rem;font-weight:750}
            .mlv-step:not(:last-child):after{content:'›';position:absolute;right:-.35rem;top:50%;transform:translateY(-52%);z-index:2;color:#2563eb;font-size:1.1rem}
            .mlv-title{margin:1.65rem 0 .18rem;color:#172033;font-size:1.15rem;font-weight:800}.mlv-note{margin-bottom:.65rem;color:#657187;font-size:.82rem;line-height:1.5}
            .mlv-card{height:100%;padding:1rem 1.1rem;border:1px solid #dce4ee;border-radius:.75rem;background:#fff}.mlv-card h3{margin:0 0 .35rem;color:#173f73;font-size:1rem}.mlv-card .big{font-size:1.6rem;font-weight:800;color:#172033}.mlv-card p{margin:.35rem 0 0;color:#657187;font-size:.78rem;line-height:1.55}
            .mlv-badge{display:inline-block;margin-bottom:.45rem;padding:.2rem .5rem;border-radius:999px;background:#edf5ff;color:#2563eb;font-size:.68rem;font-weight:800}
            .mlv-architecture{display:grid;grid-template-columns:1fr 4rem 1fr;align-items:stretch;gap:.7rem}.mlv-plus{display:flex;align-items:center;justify-content:center;color:#2563eb;font-size:1.8rem;font-weight:800}
            .mlv-model{padding:1rem;border:1px solid #dce4ee;border-top:4px solid var(--tone);border-radius:.75rem;background:#fff;text-align:center}.mlv-model h3{margin:.3rem 0;color:#172033;font-size:1.05rem}.mlv-model p{margin:.25rem 0;color:#657187;font-size:.78rem;line-height:1.5}
            .mlv-risk-join{box-sizing:border-box;width:100%;margin:.65rem 0 0;padding:.7rem 1rem;border-radius:.6rem;background:#173f73;color:#fff;text-align:center;font-size:.84rem;font-weight:800}
            .mlv-metric{min-height:105px;padding:.85rem 1rem;border:1px solid #dce4ee;border-radius:.7rem;background:#fff}.mlv-metric-label{color:#657187;font-size:.75rem;font-weight:700}.mlv-metric-value{margin:.15rem 0;color:#172033;font-size:1.42rem;font-weight:800}.mlv-metric-note{color:#657187;font-size:.7rem;line-height:1.4}
            .mlv-score-flow{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:.55rem}.mlv-score-step{padding:.8rem .5rem;border:1px solid #bfd6f5;border-radius:.65rem;background:#f4f8ff;text-align:center;color:#173f73;font-size:.76rem;font-weight:800}
            .mlv-formula{margin:.75rem 0;padding:.75rem;border-radius:.6rem;background:#172033;color:#fff;text-align:center;font-size:.9rem;font-weight:800}
            .mlv-limit{margin-top:1.3rem;padding:.9rem 1rem;border-left:4px solid #f59e0b;border-radius:.45rem;background:#fff7e8;color:#6b4b0d;font-size:.76rem;line-height:1.6}
            [data-testid='stPlotlyChart']{border:1px solid #e1e7ef;border-radius:.75rem;background:#fff;padding:.25rem}
            @media(max-width:900px){.mlv-flow{grid-template-columns:repeat(4,1fr)}.mlv-architecture{grid-template-columns:1fr}.mlv-plus{min-height:2rem}.mlv-score-flow{grid-template-columns:1fr}}
            </style>
            <header class="mlv-hero"><h1>ML 위험 탐지 및 검증</h1><p>의미 있는 위험신호를 동일 기준으로 수치화하고, Case·Window 데이터 구축부터 모델 비교·확률 보정·경고 기준 설정까지 하나의 파이프라인으로 검증했음.</p></header>
            <div class="mlv-flow">
              <div class="mlv-step">원천 통화</div><div class="mlv-step">전사·화자분리</div><div class="mlv-step">EDA</div><div class="mlv-step">Feature 추출</div>
              <div class="mlv-step">Semantic QC</div><div class="mlv-step">ML Dataset</div><div class="mlv-step">5개 모델 비교</div><div class="mlv-step">Risk Score</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        _section("학습 데이터셋", "정상과 피싱에 같은 12개 위험신호 추출 기준을 적용했고, 출처·길이 Proxy는 모델 입력에서 제외했음")
        case_shape = _dataset_shape("case_ml_dataset_v1.csv", (1148, 15))
        window_shape = _dataset_shape("window_ml_dataset_v1.csv", (7406, 18))
        left, right = st.columns(2, gap="medium")
        with left:
            st.markdown(f"<div class='mlv-card'><span class='mlv-badge'>CASE DATASET</span><h3>통화 전체 판별</h3><div class='big'>{case_shape[0]:,} Calls</div><p><b>1 Call = 1 Row</b> · 기본 위험 Feature 12개<br>Target: y_phishing · 전체 문맥의 종합판단에 사용했음</p></div>", unsafe_allow_html=True)
        with right:
            st.markdown(f"<div class='mlv-card'><span class='mlv-badge'>WINDOW DATASET</span><h3>통화 중 조기탐지</h3><div class='big'>{window_shape[0]:,} Windows</div><p><b>10 Turn / Stride 5</b> · Window 위험 Feature 12개<br>통화 source_id 단위로 Split해 같은 통화의 Train/Test 누수를 차단했음</p></div>", unsafe_allow_html=True)

        _section("Case + Window 이중 모델", "두 모델의 역할이 달라 PR-AUC 수치를 직접적인 우열로 비교하지 않았음")
        st.markdown(
            """
            <div class="mlv-architecture">
              <div class="mlv-model" style="--tone:#0f9d8a"><span class="mlv-badge">조기경보</span><h3>Window Random Forest</h3><p>최근 10 Turn을 반복 분석해 통화가 끝나기 전 위험 변화를 갱신했음.</p></div>
              <div class="mlv-plus">＋</div>
              <div class="mlv-model" style="--tone:#2563eb"><span class="mlv-badge">종합판단</span><h3>Case Random Forest</h3><p>전체 문맥과 Window 위험확률의 흐름을 결합해 최종 위험도를 판단했음.</p></div>
            </div>
            <div class="mlv-risk-join">Window 조기탐지 + Case 종합판단 → Calibration → Risk Score</div>
            """,
            unsafe_allow_html=True,
        )
        st.caption("STACKED_SAFE = Case 기본 Feature 12개 + Window 확률 요약 8개(평균·최대·P90·변동·처음·마지막·증감·추세). 통화 길이 Proxy가 될 수 있는 Window 개수·가용 여부는 제외했음.")

        _section("5개 알고리즘 비교", "Validation PR-AUC를 1차 선정 기준으로 사용했으며 Random Forest를 처음부터 정답으로 가정하지 않았음")
        left, right = st.columns(2, gap="medium")
        window_cmp = _csv("window_model_comparison.csv").copy()
        window_cmp["모델"] = window_cmp.model.map(MODEL_KO)
        window_cmp["선택"] = window_cmp.model.eq("RandomForest")
        with left:
            st.markdown("#### Window 모델")
            ordered = window_cmp.sort_values("selection_pr_auc_case_equal")
            fig = px.bar(ordered, x="selection_pr_auc_case_equal", y="모델", orientation="h", text="selection_pr_auc_case_equal", color="선택", color_discrete_map={True: BLUE, False: GRAY})
            fig.update_traces(texttemplate="%{text:.4f}", textposition="outside", hovertemplate="%{y}<br>Validation PR-AUC %{x:.4f}<extra></extra>")
            fig.update_xaxes(title="Validation PR-AUC (case-equal)", range=[.78,.83]); fig.update_yaxes(title=None); fig.update_layout(showlegend=False)
            st.plotly_chart(_layout(fig), width="stretch", config={"displayModeBar": False})
        case_cmp = _csv("case_model_comparison.csv").copy()
        case_cmp["모델"] = case_cmp.model.map(MODEL_KO)
        case_cmp["조합"] = case_cmp.feature_set + " / " + case_cmp["모델"]
        case_cmp["선택"] = case_cmp.model.eq("RandomForest") & case_cmp.feature_set.eq("STACKED_SAFE")
        with right:
            st.markdown("#### Case 모델 · 상위 6개")
            top = case_cmp.nlargest(6, "selection_pr_auc").sort_values("selection_pr_auc")
            fig = px.bar(top, x="selection_pr_auc", y="조합", orientation="h", text="selection_pr_auc", color="선택", color_discrete_map={True: BLUE, False: GRAY})
            fig.update_traces(texttemplate="%{text:.4f}", textposition="outside", hovertemplate="%{y}<br>Validation PR-AUC %{x:.4f}<extra></extra>")
            fig.update_xaxes(title="Validation PR-AUC", range=[.89,.97]); fig.update_yaxes(title=None); fig.update_layout(showlegend=False)
            st.plotly_chart(_layout(fig), width="stretch", config={"displayModeBar": False})

        config = _config()
        window_best = window_cmp.loc[window_cmp.selection_pr_auc_case_equal.idxmax()]
        case_best = case_cmp.loc[case_cmp.selection_pr_auc.idxmax()]
        _section("최종 선택과 내부 Test 성능", "Window는 제한된 최근 구간, Case는 전체 통화와 Window 확률 흐름을 사용하므로 서로 다른 역할의 성능임")
        cols = st.columns(4, gap="small")
        with cols[0]: _metric("WINDOW · 모델", "Random Forest", f"VAL PR-AUC {window_best.selection_pr_auc_case_equal:.4f}")
        with cols[1]: _metric("WINDOW · TEST", f"{config['window']['test_calibration_metrics']['pr_auc']:.4f}", "PR-AUC · Platt 보정")
        with cols[2]: _metric("CASE · 모델", "RF + STACKED", f"VAL PR-AUC {case_best.selection_pr_auc:.4f}")
        with cols[3]: _metric("CASE · TEST", f"{config['case']['test_calibration_metrics']['pr_auc']:.4f}", f"ROC-AUC {config['case']['test_calibration_metrics']['roc_auc']:.4f}")

        _section("확률 보정 → Risk Score → 경고", "Feature별 수동 점수를 더하지 않고 모델의 보정 확률을 0~100 점수로 변환했음")
        st.markdown("<div class='mlv-score-flow'><div class='mlv-score-step'>Model Probability</div><div class='mlv-score-step'>Calibration</div><div class='mlv-score-step'>× 100</div><div class='mlv-score-step'>Risk Score</div><div class='mlv-score-step'>Threshold 경고</div></div><div class='mlv-formula'>Risk Score = Calibrated P(PHISHING) × 100</div>", unsafe_allow_html=True)
        cal_left, cal_right = st.columns(2, gap="medium")
        with cal_left:
            st.markdown("#### Calibration 선택")
            methods = pd.concat([
                _csv("window_calibration_comparison.csv").assign(모델="Window"),
                _csv("case_calibration_comparison.csv").assign(모델="Case"),
            ], ignore_index=True)
            methods["선택"] = ((methods.모델.eq("Window") & methods.method.eq("PLATT")) | (methods.모델.eq("Case") & methods.method.eq("IDENTITY")))
            methods["방법"] = methods.method.map({"IDENTITY":"Identity", "PLATT":"Platt", "ISOTONIC":"Isotonic"})
            fig = px.bar(methods, x="모델", y="brier", color="방법", barmode="group", opacity=.88, text_auto=".3f")
            fig.update_traces(hovertemplate="%{x} · %{fullData.name}<br>Brier %{y:.4f}<extra></extra>")
            fig.update_yaxes(title="Validation Brier Score (낮을수록 좋음)"); fig.update_xaxes(title=None)
            st.plotly_chart(_layout(fig, 315), width="stretch", config={"displayModeBar": False})
            st.caption("Window는 Platt, Case는 Identity가 내부 검증에서 선택됐음.")
        with cal_right:
            st.markdown("#### Prototype Alert 기준")
            for key, label, tone in [("window", "WINDOW", TEAL), ("case", "CASE", BLUE)]:
                item = config[key]
                tm = item["test_threshold_metrics"]
                st.markdown(
                    f"<div class='mlv-card' style='margin-bottom:.55rem;border-left:4px solid {tone}'><h3>{label} · Risk Score ≥ {item['alert_risk_score_threshold']:.0f}</h3>"
                    f"<p>Test 기준 Recall <b>{tm['recall']:.3f}</b> · Precision <b>{tm['precision']:.3f}</b> · FPR <b>{tm['fpr']:.3f}</b><br>"
                    f"내부 Prototype 임계값이며 실제 운영 확정값이 아님</p></div>",
                    unsafe_allow_html=True,
                )

        st.markdown(
            """
            <div class="mlv-limit"><b>검증 범위와 적용 한계</b><br>
            현재 성능은 내부 데이터 분할 기준의 결과이며 완전히 독립된 외부 Test가 아니었음. Feature 선정에도 동일 출처 데이터가 사용됐고 Source Confounding이 완전히 해소됐다고 볼 수 없었음. 또한 높은 Recall을 위한 Prototype Threshold는 오탐을 크게 만들 수 있으므로, 실제 서비스 적용 전 외부 데이터 검증·재Calibration·오탐/미탐 비용을 반영한 Threshold 재설정이 필요함.</div>
            """,
            unsafe_allow_html=True,
        )
        st.caption("결과 파일: 06 머신러닝 모델링/결과_v1 및 07 Calibration_RiskScore_Threshold/결과_v1 · 최종 Pipeline: final_voice_phishing_risk_pipeline.pkl")
