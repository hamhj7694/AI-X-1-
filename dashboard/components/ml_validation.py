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
def _json(name: str) -> dict:
    return json.loads((DATA_ROOT / name).read_text(encoding="utf-8"))


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
            .mlv-process-head{margin-top:2rem;padding-top:1.5rem;border-top:1px solid #dce4ee}.mlv-process-head h2{margin:0;color:#172033;font-size:1.35rem}.mlv-process-head p{margin:.35rem 0 0;color:#657187;font-size:.82rem}
            .mlv-funnel{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:.55rem}.mlv-funnel-card{position:relative;padding:.9rem;border:1px solid #dce4ee;border-radius:.7rem;background:#fff}.mlv-funnel-card:not(:last-child):after{content:'›';position:absolute;right:-.43rem;top:50%;z-index:2;color:#2563eb;font-size:1.4rem;font-weight:800}.mlv-funnel-card b{display:block;color:#173f73;font-size:.82rem}.mlv-funnel-card strong{display:block;margin:.22rem 0;color:#172033;font-size:1.15rem}.mlv-funnel-card span{color:#657187;font-size:.7rem;line-height:1.4}
            .mlv-feature-grid{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:.55rem}.mlv-feature-card{padding:.78rem;border:1px solid #dce4ee;border-radius:.65rem;background:#fff}.mlv-feature-card b{display:block;margin-bottom:.35rem;color:#173f73;font-size:.79rem}.mlv-feature-card span{display:block;color:#526078;font-size:.7rem;line-height:1.55}.mlv-feature-card code{font-size:.63rem;color:#2563eb}
            .mlv-safety-grid{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:.55rem}.mlv-safety{padding:.72rem;border-radius:.62rem;background:#f4f8ff;color:#315a87;font-size:.7rem;line-height:1.45}.mlv-safety b{display:block;margin-bottom:.18rem;color:#173f73;font-size:.75rem}
            .mlv-equation{padding:1rem 1.1rem;border-radius:.7rem;background:#172033;color:#e7f0ff;font-family:Consolas,monospace;font-size:.78rem;line-height:1.75;white-space:pre-wrap}.mlv-intent{padding:.85rem 1rem;border-left:4px solid #2563eb;border-radius:.45rem;background:#edf5ff;color:#315a87;font-size:.76rem;line-height:1.6}
            .mlv-stage-flow{display:grid;grid-template-columns:repeat(8,minmax(0,1fr));gap:.38rem}.mlv-stage{padding:.65rem .35rem;border:1px solid #dce4ee;border-radius:.55rem;background:#fff;text-align:center}.mlv-stage b{display:block;color:#2563eb;font-size:.68rem}.mlv-stage span{color:#526078;font-size:.66rem;line-height:1.35}
            .mlv-alert-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:.6rem}.mlv-alert{padding:.85rem 1rem;border:1px solid #dce4ee;border-top:4px solid var(--tone);border-radius:.7rem;background:#fff}.mlv-alert b{display:block;color:#172033;font-size:.86rem}.mlv-alert strong{display:block;margin:.22rem 0;color:var(--tone);font-size:1.25rem}.mlv-alert span{color:#657187;font-size:.71rem;line-height:1.5}
            [data-testid='stPlotlyChart']{border:1px solid #e1e7ef;border-radius:.75rem;background:#fff;padding:.25rem}
            @media(max-width:900px){.mlv-flow,.mlv-stage-flow{grid-template-columns:repeat(4,1fr)}.mlv-architecture{grid-template-columns:1fr}.mlv-plus{min-height:2rem}.mlv-score-flow{grid-template-columns:1fr}.mlv-funnel,.mlv-feature-grid,.mlv-safety-grid,.mlv-alert-grid{grid-template-columns:repeat(2,1fr)}}
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

        calibration = _json("calibration_manifest_07.json")
        threshold = _json("threshold_policy_config_08.json")
        policy09 = _json("integrated_alert_policy_config_09.json")
        policy092 = _json("integrated_alert_policy_config_09_02.json")
        window_best = window_cmp.loc[window_cmp.selection_pr_auc_case_equal.idxmax()]
        case_best = case_cmp.loc[case_cmp.selection_pr_auc.idxmax()]
        _section("최종 선택과 내부 Test 성능", "Window는 제한된 최근 구간, Case는 전체 통화와 Window 확률 흐름을 사용하므로 서로 다른 역할의 성능임")
        cols = st.columns(4, gap="small")
        with cols[0]: _metric("WINDOW · 모델", "Random Forest", f"VAL PR-AUC {window_best.selection_pr_auc_case_equal:.4f}")
        with cols[1]: _metric("WINDOW · TEST", f"{calibration['window']['test_calibration_metrics']['pr_auc']:.4f}", "PR-AUC · Platt 보정")
        with cols[2]: _metric("CASE · 모델", "RF + STACKED", f"VAL PR-AUC {case_best.selection_pr_auc:.4f}")
        with cols[3]: _metric("CASE · TEST", f"{calibration['case']['test_calibration_metrics']['pr_auc']:.4f}", f"ROC-AUC {calibration['case']['test_calibration_metrics']['roc_auc']:.4f}")

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
            st.markdown("#### 최종 09-2 다단계 기준")
            p2t = policy092["thresholds"]
            p2w = policy092["test_realtime_window_suspicious"]
            st.markdown(
                f"<div class='mlv-card' style='margin-bottom:.55rem;border-left:4px solid {TEAL}'><span class='mlv-badge'>FEASIBLE_AGGRESSIVE · 내부 정책</span><h3>WINDOW · 의심 {p2t['window_suspicious']:.0f} / 고위험 {p2t['window_high_risk']:.0f}</h3>"
                f"<p>10 Turn · Stride 5 실시간 분석<br>Test 의심 Recall <b>{p2w['recall']:.1%}</b> · 정상 FPR <b>{p2w['fpr']:.1%}</b></p></div>",
                unsafe_allow_html=True,
            )
            p2i = policy092["test_integrated_suspicious"]
            st.markdown(
                f"<div class='mlv-card' style='margin-bottom:.55rem;border-left:4px solid {BLUE}'><span class='mlv-badge'>통화 종료 후 보완</span><h3>CASE · 의심 {p2t['case_suspicious']:.0f} / 고위험 {p2t['case_high_risk']:.0f}</h3>"
                f"<p>Window OR Case 통합 의심 기준<br>Test Recall <b>{p2i['recall']:.1%}</b> · Precision <b>{p2i['precision']:.1%}</b> · 정상 FPR <b>{p2i['fpr']:.1%}</b></p></div>",
                unsafe_allow_html=True,
            )

        st.markdown(
            """
            <div class="mlv-limit"><b>검증 범위와 적용 한계</b><br>
            현재 성능은 내부 데이터 분할 기준의 결과이며 완전히 독립된 외부 Test가 아니었음. Feature 선정에도 동일 출처 데이터가 사용됐고 Source Confounding이 완전히 해소됐다고 볼 수 없었음. 또한 높은 Recall을 위한 Prototype Threshold는 오탐을 크게 만들 수 있으므로, 실제 서비스 적용 전 외부 데이터 검증·재Calibration·오탐/미탐 비용을 반영한 Threshold 재설정이 필요함.</div>
            """,
            unsafe_allow_html=True,
        )
        st.caption("결과 파일: 06 모델 비교 · 07 Calibration/Risk Score · 08 Threshold/실시간 경고정책 · 최종 Pipeline: final_voice_phishing_risk_pipeline.pkl")

        # ------------------------------------------------------------------
        # 구현 과정: EDA에서 서비스 경고정책까지 이어진 제작 근거
        # ------------------------------------------------------------------
        st.markdown("<div class='mlv-process-head'><h2>구현 과정</h2><p>EDA에서 찾은 위험신호를 어떻게 변수로 만들고, 검증·축소·점수화해 서비스 경고로 연결했는지 정리했음.</p></div>", unsafe_allow_html=True)

        _section("01 → 09-2 Colab 진행 흐름", "각 단계의 산출물을 다음 단계 입력으로 사용해 분석과 모델이 자연스럽게 연결되도록 구성했음")
        st.markdown(
            """
            <div class="mlv-stage-flow">
              <div class="mlv-stage"><b>01 전처리</b><span>전사·화자분리·Turn 구조화</span></div>
              <div class="mlv-stage"><b>02 EDA</b><span>사칭·전략·행동 패턴 탐색</span></div>
              <div class="mlv-stage"><b>03 핵심선별</b><span>Lead Time·전 구간 위험 확인</span></div>
              <div class="mlv-stage"><b>04 Feature</b><span>동일 추출·통계·CV·QC</span></div>
              <div class="mlv-stage"><b>05 Dataset</b><span>Case·Window 누수 차단 Split</span></div>
              <div class="mlv-stage"><b>06 모델비교</b><span>5개 알고리즘 중 RF 선택</span></div>
              <div class="mlv-stage"><b>07 점수화</b><span>Calibration·Risk Score</span></div>
              <div class="mlv-stage"><b>08 경고정책</b><span>Threshold·단일 Pipeline</span></div>
              <div class="mlv-stage"><b>09-1 다단계</b><span>절충 의심·고위험 정책</span></div>
              <div class="mlv-stage"><b>09-2 최종</b><span>공격적 의심기준 실험</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        _section("Feature 후보를 최종 12개로 축소", "후보 수를 많이 유지하는 대신 비교 가능성·안정성·의미 타당성을 순서대로 검증했음")
        st.markdown(
            """
            <div class="mlv-funnel">
              <div class="mlv-funnel-card"><b>1 · 후보 생성</b><strong>Window 51열<br>Case 117열</strong><span>EDA 패턴을 수치화하고 통화 단위 max·mean·sum 집계 후보를 만들었음</span></div>
              <div class="mlv-funnel-card"><b>2 · 공통화</b><strong>29개</strong><span>정상·피싱에 동일한 정의와 추출기를 적용할 수 있는 공통 후보로 재구성했음</span></div>
              <div class="mlv-funnel-card"><b>3 · 검증</b><strong>통계 + CV + QC</strong><span>효과크기·BH-FDR·Group CV·중복·Semantic QC를 확인했음</span></div>
              <div class="mlv-funnel-card"><b>4 · 최종 확정</b><strong>Case 12<br>Window 12</strong><span>출처·길이 Proxy와 약하거나 불안정한 변수를 제외했음</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.caption("51열과 117열은 같은 층위의 독립변수 수가 아니라 피싱 내부 Window 후보 테이블과 이를 통화 단위로 집계한 후보 테이블의 컬럼 수임. 실제 정상·피싱 공통 선별은 29개 후보에서 시작했음.")

        _section("최종 12개 위험 Feature", "사칭·심리전략·위험행동·복합성·상호작용을 함께 반영해 단일 키워드 의존을 줄였음")
        st.markdown(
            """
            <div class="mlv-feature-grid">
              <div class="mlv-feature-card"><b>사칭 · 2개</b><span>공공기관 <code>imp_public</code><br>금융기관 <code>imp_financial</code></span></div>
              <div class="mlv-feature-card"><b>심리전략 · 3개</b><span>권위 <code>strategy_authority</code><br>공포 <code>strategy_fear</code><br>정보추출 <code>strategy_info_extraction_sem</code></span></div>
              <div class="mlv-feature-card"><b>위험행동 · 2개</b><span>민감정보 요구 <code>sensitive_info_request_sem</code><br>인증정보 요구 <code>auth_info_request_sem</code></span></div>
              <div class="mlv-feature-card"><b>복합성 · 3개</b><span>전략 다양성 <code>strategy_diversity_sem</code><br>행동 다양성 <code>action_diversity_sem</code><br>신호계열 수 <code>signal_family_count_sem</code></span></div>
              <div class="mlv-feature-card"><b>상호작용 · 2개</b><span>신분주장×권위 <code>ix_identityclaim_authority_sem</code><br>정보추출×민감정보 <code>ix_info_sensitive_sem</code></span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.info("Case는 통화 전체 누적값 `signal_family_count_sem`을 사용했고, Window는 직전 구간 대비 증가량 `signal_family_count_delta_sem`으로 교체해 실시간 변화에 반응하도록 했음.")

        _section("Feature 선정 안전장치", "출처 형식이 아니라 통화 내용의 위험구조를 학습하도록 다섯 가지 검증 장치를 적용했음")
        st.markdown(
            """
            <div class="mlv-safety-grid">
              <div class="mlv-safety"><b>동일 추출기</b>정상·피싱에 같은 Rule·Semantic 계약을 적용했음</div>
              <div class="mlv-safety"><b>통계 검증</b>p-value뿐 아니라 효과크기와 BH-FDR을 확인했음</div>
              <div class="mlv-safety"><b>Group CV</b>같은 통화가 Train/Test에 섞이지 않게 source_id로 분리했음</div>
              <div class="mlv-safety"><b>Semantic QC</b>정상 금융안내·경고와 실제 위험요구 문맥을 구분했음</div>
              <div class="mlv-safety"><b>Proxy 제거</b>길이·파일명·출처·Window 개수 등 제작방식 단서를 제외했음</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        _section("머신러닝용 점수화 수식", "사람이 Feature별 점수를 임의로 더하지 않고 모델이 가중치와 비선형 조합을 학습하게 했음")
        eq_left, eq_right = st.columns([1.05, .95], gap="medium")
        with eq_left:
            st.markdown(
                """<div class="mlv-equation">p_raw = RandomForest.predict_proba(X)[:, 1]

Window: p_cal = sigmoid(a × logit(p_raw) + b)  # Platt
Case:   p_cal = p_raw                           # Identity

Risk Score = 100 × p_cal</div>""",
                unsafe_allow_html=True,
            )
        with eq_right:
            st.markdown(
                """<div class="mlv-intent"><b>왜 수동 가산점이 아닌가?</b><br>위험신호는 단순히 많을수록 항상 위험하지 않았고, 같은 신호도 다른 신호와 결합될 때 의미가 달라졌음. 따라서 `사칭 +20점`처럼 임의 배점하지 않고 Random Forest가 12개 신호의 조합을 학습하게 했음. 이후 Calibration으로 확률의 과신·과소신뢰를 조정하고 0~100 점수로 변환했음.</div>""",
                unsafe_allow_html=True,
            )

        _section("07 Calibration → 08 경고정책", "연속형 위험점수를 먼저 만든 뒤 Validation의 Recall·정상 FPR Trade-off로 경고기준을 별도 선택했음")
        st.markdown(
            f"""
            <div class="mlv-score-flow">
              <div class="mlv-score-step">07 Window<br><b>Platt</b></div>
              <div class="mlv-score-step">07 Case<br><b>Identity</b></div>
              <div class="mlv-score-step">Risk Score<br><b>0~100</b></div>
              <div class="mlv-score-step">08 Window<br><b>{threshold['window_realtime_alert']['risk_score_threshold']:.0f}점 SINGLE</b></div>
              <div class="mlv-score-step">08 Case<br><b>{threshold['case_secondary']['risk_score_threshold']:.0f}점 보조판정</b></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.warning("Window 69점과 Case 58점은 모두 `COMPROMISE · 내부 Prototype`임. Validation에서 목표 Recall 0.90과 정상 통화 FPR 0.20을 동시에 만족하는 정책이 없어 선택한 절충값이며, 외부 데이터 검증 전 확정 운영기준이나 절대적인 보이스피싱 확률로 해석하지 않음.")

        _section("08 한계 확인 → 09 다단계 경고 실험", "08의 고위험 기준은 유지하고, 놓친 피싱을 보완하기 위한 SUSPICIOUS 단계를 Validation에서 추가 탐색했음")
        p09w, p09c = policy09["window"], policy09["case"]
        p09i = policy09["integrated_service"]
        st.markdown(
            f"""
            <div class="mlv-alert-grid">
              <div class="mlv-alert" style="--tone:{GRAY}"><b>MONITORING</b><strong>Window 0~{p09w['suspicious_risk_score_threshold']-1:.0f}점</strong><span>경고가 없더라도 안전으로 확정하지 않고 통화 중 위험도를 계속 갱신했음.</span></div>
              <div class="mlv-alert" style="--tone:{ORANGE}"><b>SUSPICIOUS</b><strong>Window ≥ {p09w['suspicious_risk_score_threshold']:.0f} · Case ≥ {p09c['suspicious_risk_score_threshold']:.0f}</strong><span>Window 또는 통화 종료 후 Case 중 하나가 기준을 넘으면 의심 상태로 분류했음.</span></div>
              <div class="mlv-alert" style="--tone:{RED}"><b>HIGH_RISK</b><strong>Window ≥ {p09w['high_risk_score_threshold']:.0f} · Case ≥ {p09c['high_risk_score_threshold']:.0f}</strong><span>08에서 선택한 정밀 고위험 기준을 그대로 유지했음.</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.caption("09의 선택 상태는 COMPROMISE였음. 1,360개 Window×Case 의심 임계값 조합 중 Validation 목표(통합 Recall ≥ 90%, 정상 FPR ≤ 40%)를 동시에 만족한 조합은 없었음.")

        comparison09 = _csv("08_vs_09_improvement_comparison.csv")
        contrib09 = _csv("test_model_contribution.csv")
        left09, right09 = st.columns(2, gap="medium")
        with left09:
            st.markdown("#### 08 고위험 vs 09 의심 단계 · Test")
            chart09 = comparison09.melt(
                id_vars=["scope", "tier", "threshold"],
                value_vars=["recall", "precision", "fpr"],
                var_name="metric",
                value_name="value",
            )
            chart09["구분"] = chart09["scope"] + " · " + chart09["tier"]
            chart09["metric"] = chart09["metric"].map({"recall": "Recall", "precision": "Precision", "fpr": "정상 FPR"})
            fig = px.bar(chart09, x="value", y="구분", color="metric", barmode="group", text="value",
                         color_discrete_map={"Recall": BLUE, "Precision": TEAL, "정상 FPR": ORANGE})
            fig.update_traces(texttemplate="%{text:.1%}", textposition="outside", hovertemplate="%{y}<br>%{fullData.name} %{x:.1%}<extra></extra>")
            fig.update_xaxes(title="비율", tickformat=".0%", range=[0, 1.08]); fig.update_yaxes(title=None)
            st.plotly_chart(_layout(fig, 380), width="stretch", config={"displayModeBar": False})
            st.caption("Window 지표의 분모는 Window가 존재한 통화, Case·통합 지표의 분모는 전체 Test 통화였음. 따라서 통합 Recall을 실시간 Recall로 해석하지 않았음.")
        with right09:
            st.markdown("#### 09 의심 단계 · 피싱 115건 포착 기여")
            contrib09["구분"] = contrib09["category"].map({"Window only":"Window만", "Case only":"Case만", "Both":"둘 다", "Missed by both":"둘 다 놓침"})
            fig = px.bar(contrib09, x="n_phishing_calls", y="구분", orientation="h", text="n_phishing_calls",
                         color="구분", color_discrete_map={"Window만": TEAL, "Case만": BLUE, "둘 다": NAVY, "둘 다 놓침": RED})
            fig.update_traces(textposition="outside", hovertemplate="%{y}<br>%{x}건 · %{customdata[0]:.1%}<extra></extra>", customdata=contrib09[["ratio"]])
            fig.update_xaxes(title="피싱 통화 수", range=[0, 70]); fig.update_yaxes(title=None); fig.update_layout(showlegend=False)
            st.plotly_chart(_layout(fig, 380), width="stretch", config={"displayModeBar": False})
            st.caption("Window만 1건, Case만 62건, 둘 다 40건, 둘 다 놓침 12건이었음. 확대된 포착의 대부분은 통화 종료 후 Case가 보완했음.")

        soft09 = p09i["soft_test_metrics"]
        high09 = p09i["high_test_metrics"]
        cols09 = st.columns(4, gap="small")
        with cols09[0]: _metric("09 통합 의심 · Recall", f"{soft09['recall']:.1%}", "Test 전체 피싱 115건 기준")
        with cols09[1]: _metric("09 통합 의심 · Precision", f"{soft09['precision']:.1%}", f"정상 FPR {soft09['fpr']:.1%}")
        with cols09[2]: _metric("통합 고위험 · Recall", f"{high09['recall']:.1%}", "Window 69 OR Case 58")
        with cols09[3]: _metric("통합 고위험 · Precision", f"{high09['precision']:.1%}", f"정상 FPR {high09['fpr']:.1%}")

        st.markdown(
            """<div class="mlv-limit"><b>09에서 확인한 핵심 결론</b><br>
            의심 단계 통합 Recall은 89.6%까지 확대됐지만 정상 FPR도 36.2%로 증가했음. 더 중요한 점은 Window 의심 기준이 69점으로 08과 달라지지 않아 실시간 모델 자체의 포착력은 개선되지 않았고, 추가 포착 대부분이 통화 종료 후 Case에서 발생했다는 사실이었음. 따라서 09는 모델 성능 향상을 증명한 단계가 아니라 서비스 상태를 세분화한 정책 실험이었으며, 다음 개선 대상으로 Window Feature와 실시간 모델을 확정했음.</div>""",
            unsafe_allow_html=True,
        )
        st.caption("최종 정책 구조: Window 실시간 모니터링·고위험 경고 + 통화 종료 후 Case 보완 · Risk Score = 보정확률 × 100 · 외부 검증은 수행되지 않았음.")

        _section("09-2 · 놓침을 줄이기 위한 공격적 의심기준", "고위험 기준은 69/58점으로 유지하고 SUSPICIOUS만 Window 64점·Case 36점으로 낮춰 최종 정책을 다시 평가했음")
        p2t = policy092["thresholds"]
        st.markdown(
            f"""
            <div class="mlv-alert-grid">
              <div class="mlv-alert" style="--tone:{GRAY}"><b>MONITORING</b><strong>Window &lt; {p2t['window_suspicious']:.0f}점</strong><span>기준 미만은 안전 판정이 아니라 계속 관찰하는 상태였음.</span></div>
              <div class="mlv-alert" style="--tone:{ORANGE}"><b>SUSPICIOUS · 낮춘 기준</b><strong>Window ≥ {p2t['window_suspicious']:.0f} · Case ≥ {p2t['case_suspicious']:.0f}</strong><span>놓침을 줄이기 위해 09-1보다 민감한 내부 주의단계를 적용했음.</span></div>
              <div class="mlv-alert" style="--tone:{RED}"><b>HIGH_RISK · 유지</b><strong>Window ≥ {p2t['window_high_risk']:.0f} · Case ≥ {p2t['case_high_risk']:.0f}</strong><span>08에서 정한 강한 경고 기준은 낮추지 않았음.</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.caption("09-2 선택은 Validation에서만 수행했음. 목표는 통합 Recall ≥ 97%, 정상 FPR ≤ 50%였고 Validation에서 FEASIBLE_AGGRESSIVE로 선택된 뒤 Test를 1회 평가했음.")

        p2w = policy092["test_realtime_window_suspicious"]
        p2i = policy092["test_integrated_suspicious"]
        p2h = policy092["test_integrated_high_risk"]
        cols092 = st.columns(4, gap="small")
        with cols092[0]: _metric("실시간 Window 의심 · Recall", f"{p2w['recall']:.1%}", f"정상 FPR {p2w['fpr']:.1%}")
        with cols092[1]: _metric("통합 의심 · Recall", f"{p2i['recall']:.1%}", "Window OR 종료 후 Case")
        with cols092[2]: _metric("통합 의심 · Precision", f"{p2i['precision']:.1%}", f"정상 FPR {p2i['fpr']:.1%}")
        with cols092[3]: _metric("통합 고위험 · Precision", f"{p2h['precision']:.1%}", f"Recall {p2h['recall']:.1%} · FPR {p2h['fpr']:.1%}")

        compare092 = pd.DataFrame(
            [
                {"평가 범위": "실시간 Window 의심", "Recall": p2w["recall"], "정상 FPR": p2w["fpr"]},
                {"평가 범위": "통합 의심", "Recall": p2i["recall"], "정상 FPR": p2i["fpr"]},
                {"평가 범위": "통합 고위험", "Recall": p2h["recall"], "정상 FPR": p2h["fpr"]},
            ]
        ).melt(id_vars="평가 범위", var_name="지표", value_name="비율")
        fig = px.bar(compare092, x="평가 범위", y="비율", color="지표", barmode="group", text="비율",
                     color_discrete_map={"Recall": BLUE, "정상 FPR": ORANGE})
        fig.update_traces(texttemplate="%{text:.1%}", textposition="outside", hovertemplate="%{x}<br>%{fullData.name} %{y:.1%}<extra></extra>")
        fig.update_yaxes(title="비율", tickformat=".0%", range=[0, 1.08]); fig.update_xaxes(title=None)
        st.plotly_chart(_layout(fig, 330), width="stretch", config={"displayModeBar": False})

        st.markdown(
            """<div class="mlv-limit"><b>09-2 최종 해석</b><br>
            통합 의심 Recall 99.1%는 대부분의 피싱을 Window 또는 통화 종료 후 Case 중 하나로 포착했다는 뜻이었음. 그러나 정상 통화 FPR도 51.7%여서 정상의 절반 이상이 의심 알림 대상이 됐음. 실시간 Window 단독 Recall은 58.4%였으므로 99.1%를 실시간 탐지율로 표현하지 않았음. 64/36점은 강한 차단 기준이 아니라 놓침을 줄이기 위한 약한 내부 검증 안내 기준이었음.</div>""",
            unsafe_allow_html=True,
        )
