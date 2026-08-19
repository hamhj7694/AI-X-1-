import streamlit as st

import pandas as pd
import plotly.graph_objects as go

from services.detection_service import analyze_text, feature_table


def _render_demo_placeholder() -> None:
    """실제 적용 데모 페이지의 현재 placeholder를 표시합니다."""
    with st.container(key="analysis_container"):
        st.markdown(
            """
            <section class="page-placeholder">
                <h2>콘텐츠 준비 중</h2>
                <p>향후 가상 시나리오를 활용한 위험 탐지 및 송금 보류 흐름이 이 영역에 추가됩니다.</p>
            </section>
            """,
            unsafe_allow_html=True,
        )


EXAMPLES = {
    "수사기관 사칭 예시": """범인: 서울중앙지검 수사관입니다.
피해자: 무슨 일이시죠?
범인: 고객님 명의 계좌가 범죄에 연루됐습니다.
피해자: 저는 전혀 모르는 일입니다.
범인: 사건번호를 확인하려면 본인 확인이 필요합니다.
범인: 지금부터 누구에게도 말하지 마세요.
피해자: 가족에게 물어보면 안 되나요?
범인: 수사 중이라 외부에 알리면 처벌받을 수 있습니다.
범인: 계좌번호와 잔액을 말씀해 주세요.
피해자: 왜 필요한가요?
범인: 지금 바로 은행에 가서 현금을 인출하세요.
범인: 통화를 끊지 말고 제가 안내하는 대로 하세요.""",
    "대출사기 예시": """상담원: 저금리 대환대출 담당자입니다.
고객: 어떤 상품인가요?
상담원: 기존 대출을 오늘 상환하면 한도를 올려드릴 수 있습니다.
고객: 은행에 확인해 봐도 되나요?
상담원: 오늘 안에 처리해야 승인이 가능합니다.
상담원: 먼저 수수료를 입금하셔야 합니다.
고객: 수수료가 얼마인가요?
상담원: 300만 원을 지정 계좌로 이체하세요.
상담원: 앱을 설치하면 제가 원격으로 도와드리겠습니다.
고객: 조금 의심스러운데요.
상담원: 걱정하지 마시고 말씀드린 대로 진행하세요.
상담원: 처리될 때까지 통화를 끊지 마세요.""",
    "정상 금융상담 예시": """상담원: 고객센터 상담원입니다.
고객: 예금 만기일을 확인하고 싶습니다.
상담원: 본인 확인 후 안내해 드리겠습니다.
고객: 어떤 정보가 필요한가요?
상담원: 앱에서 본인인증을 완료해 주세요.
고객: 인증을 완료했습니다.
상담원: 만기일은 다음 달 15일입니다.
고객: 자동 재예치가 되나요?
상담원: 현재 자동 재예치로 설정되어 있습니다.
고객: 설정을 변경하고 싶습니다.
상담원: 앱의 상품관리 메뉴에서 변경할 수 있습니다.
고객: 감사합니다.""",
}


def _metric_value(value: float | None) -> str:
    return "분석 불가" if value is None else f"{value:.1f}점"


def _window_chart(
    window_results: list[dict], suspicious_threshold: float, high_threshold: float
) -> go.Figure:
    frame = pd.DataFrame(window_results)
    frame["구간"] = frame.apply(lambda row: f"{int(row.start_turn)}~{int(row.end_turn)}번", axis=1)
    state_colors = {"MONITORING": "#2563eb", "SUSPICIOUS": "#f59e0b", "HIGH_RISK": "#dc2626"}
    colors = frame["state"].map(state_colors).fillna("#2563eb")
    figure = go.Figure(
        go.Scatter(
            x=frame["구간"],
            y=frame["risk_score"],
            mode="lines+markers+text",
            text=frame["risk_score"].map(lambda value: f"{value:.1f}"),
            textposition="top center",
            line={"color": "#2563eb", "width": 3},
            marker={"color": colors, "size": 10},
            hovertemplate="발화 %{x}<br>위험점수 %{y:.1f}점<extra></extra>",
        )
    )
    figure.add_hline(
        y=suspicious_threshold,
        line_dash="dash",
        line_color="#f59e0b",
        annotation_text=f"의심 {suspicious_threshold:.0f}점",
        annotation_position="top left",
    )
    figure.add_hline(
        y=high_threshold,
        line_dash="dash",
        line_color="#dc2626",
        annotation_text=f"고위험 {high_threshold:.0f}점",
        annotation_position="bottom left",
    )
    figure.update_layout(
        height=380,
        margin={"l": 30, "r": 20, "t": 45, "b": 30},
        xaxis_title="10개 발화 Window",
        yaxis={"title": "위험점수", "range": [0, 105]},
        hovermode="x unified",
    )
    return figure


def _render_result(result: dict) -> None:
    st.markdown("### 분석 결과")
    if not result["model_ready"]:
        st.warning(
            "실제 추론 모델이 연결되지 않아 위험점수는 계산하지 않았습니다. "
            "현재 화면에서는 입력 구조와 탐지된 위험 특징까지만 확인할 수 있습니다."
        )
        st.caption(result["model_error"] or "모델 준비 상태를 확인하세요.")

    window_score = result["window_max_score"]
    case_score = result["case_score"]
    signal_count = int((feature_table(result)["추출값"] > 0).sum())
    metric_columns = st.columns(4, gap="medium")
    with metric_columns[0]:
        thresholds = (
            f"의심 {result['window_suspicious_threshold']:.0f} / 고위험 {result['window_high_threshold']:.0f}"
            if result.get("window_suspicious_threshold") is not None else "모델 기준 확인 불가"
        )
        st.metric("Window 최고 위험점수", _metric_value(window_score), thresholds)
    with metric_columns[1]:
        thresholds = (
            f"의심 {result['case_suspicious_threshold']:.0f} / 고위험 {result['case_high_threshold']:.0f}"
            if result.get("case_suspicious_threshold") is not None else "모델 기준 확인 불가"
        )
        st.metric("Case 종합 위험점수", _metric_value(case_score), thresholds)
    with metric_columns[2]:
        st.metric("최종 판정", result["decision"] if result["model_ready"] else "모델 미연결")
    with metric_columns[3]:
        st.metric("탐지된 특징", f"{signal_count}개", f"근거 발화 {len(result['evidence'])}건")

    if result["model_ready"]:
        if result["decision_state"] == "HIGH_RISK":
            st.error(result["decision_message"])
        elif result["decision_state"] == "SUSPICIOUS":
            st.warning(result["decision_message"])
        else:
            st.info(result["decision_message"])

    st.caption(
        f"입력 발화 {len(result['turns'])}개 · 생성 Window {len(result['windows'])}개 · "
        f"Window는 {result.get('window_turns', 10)}개 발화를 {result.get('window_stride', 5)}개씩 이동해 분석합니다."
    )

    if result["window_results"]:
        st.markdown("#### 구간별 위험점수")
        st.plotly_chart(
            _window_chart(
                result["window_results"],
                result["window_suspicious_threshold"],
                result["window_high_threshold"],
            ),
            width="stretch",
            config={"displayModeBar": False},
        )
    elif len(result["turns"]) < 10:
        st.info("Window 분석에는 최소 10개 발화가 필요합니다. 현재 입력에서는 구간 점수를 만들 수 없습니다.")

    st.markdown("#### 어떤 부분이 의심스러운가")
    if result["evidence"]:
        evidence_df = pd.DataFrame(result["evidence"])
        st.dataframe(evidence_df, hide_index=True, width="stretch")
        st.caption("위 표는 규칙으로 찾은 후보 근거입니다. 모델 기여도와 동일한 의미는 아닙니다.")
    else:
        st.success("현재 규칙에서 탐지된 위험 표현이 없습니다. 다만 이것만으로 정상임을 확정할 수는 없습니다.")

    with st.expander("입력 변수 상세보기", expanded=False):
        st.dataframe(feature_table(result), hide_index=True, width="stretch")

    with st.expander("모델 계산 방식과 제한사항", expanded=False):
        st.markdown(
            f"""
- Window는 최근 **{result.get('window_turns', 10)}개 발화**를 Stride **{result.get('window_stride', 5)}**로 분석했으며, 통화 중 위험 변화 탐지에 사용했음.
- Window Risk Score = `{result.get('window_calibration_method') or 'bundle 보정'} calibrated P(phishing) × 100`이었음.
- Case는 전체 통화 Feature 12개와 **Window raw probability 요약 8개**를 사용한 통화 종료 후 종합·보조 판정이었음.
- Case Risk Score = `{result.get('case_calibration_method') or 'bundle 보정'} calibrated P(phishing) × 100`이었음.
- Window와 Case를 단순 평균하거나 임의 가중합하지 않았으며, 최종 상태는 bundle의 **OR 정책**을 적용했음.
- `SUSPICIOUS`는 약한 주의 단계, `HIGH_RISK`는 강한 경고 단계였음. 낮은 점수는 안전 확정을 의미하지 않았음.
- 이 점수는 내부 데이터 분포의 상대적 위험도이며 실제 피해확률이나 금융기관의 확정 판정이 아닙니다.
            """
        )
        policy_validation = result.get("policy_validation") or {}
        operating_point = policy_validation.get("validation_operating_point") or {}
        if operating_point:
            st.warning(
                "현재 SUSPICIOUS 기준은 놓침을 줄이기 위해 선택한 공격적 내부 정책이었음. "
                f"Validation 기준 Recall {operating_point.get('recall', 0):.1%}, "
                f"Precision {operating_point.get('precision', 0):.1%}, "
                f"정상 FPR {operating_point.get('fpr', 0):.1%}였으며 외부 검증은 수행되지 않았음."
            )
        if not result.get("feature_extractor_matches_training", False):
            st.warning(
                f"현재 추출기 `{result.get('feature_extractor')}`는 저장소에 남아 있는 규칙 기반 대체 구현입니다. "
                "학습 Colab의 Semantic Feature 생성기와 완전히 같은 구현임을 검증하지 못했으므로 점수는 연동 테스트용으로 해석해야 합니다."
            )
        if result["model_ready"]:
            st.json(
                {
                    "bundle_version": result.get("bundle_version"),
                    "window_model": result.get("window_model_name"),
                    "case_model": result.get("case_model_name"),
                    "window_calibration": result.get("window_calibration_method"),
                    "case_calibration": result.get("case_calibration_method"),
                    "case_raw_probability": result["case_raw_probability"],
                    "case_calibrated_probability": result["case_calibrated_probability"],
                    "window_count": len(result["window_results"]),
                }
            )


def render_demo() -> None:
    """새 통화 텍스트의 위험 신호와 ML 점수를 확인하는 서비스 데모입니다."""
    with st.container(key="analysis_container"):
        st.markdown(
            """
            <header class="analysis-section-header demo-hero">
                <p class="analysis-source">SERVICE PROTOTYPE</p>
                <h2>보이스피싱 위험 탐지 데모</h2>
                <p>새로운 통화 텍스트에서 위험 특징을 찾고 Window·Case 모델의 판단 근거를 확인합니다.</p>
            </header>
            """,
            unsafe_allow_html=True,
        )

        choice_column, load_column, reset_column = st.columns([2.2, 1, 1], vertical_alignment="bottom")
        with choice_column:
            example_name = st.selectbox("테스트 예시", tuple(EXAMPLES), key="demo_example_name")
        with load_column:
            if st.button("예시 불러오기", width="stretch"):
                st.session_state["demo_input_text"] = EXAMPLES[example_name]
                st.session_state.pop("demo_result", None)
        with reset_column:
            if st.button("초기화", width="stretch"):
                st.session_state["demo_input_text"] = ""
                st.session_state.pop("demo_result", None)

        input_text = st.text_area(
            "분석할 통화 텍스트",
            key="demo_input_text",
            height=280,
            placeholder="화자 구분 없이 문장으로 입력하거나, 한 줄에 한 발화씩 입력할 수 있습니다.",
        )
        st.caption("입력 내용은 파일이나 분석 로그로 저장하지 않습니다. 실제 개인정보는 입력하지 마세요.")

        if st.button("위험도 분석하기", type="primary", width="stretch"):
            if not input_text.strip():
                st.error("분석할 텍스트를 입력해 주세요.")
            else:
                with st.spinner("통화 위험 신호를 분석하고 있습니다..."):
                    st.session_state["demo_result"] = analyze_text(input_text)

        result = st.session_state.get("demo_result")
        if result:
            st.divider()
            _render_result(result)
