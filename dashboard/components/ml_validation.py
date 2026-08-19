import streamlit as st


def render_ml_validation() -> None:
    """ML 위험 탐지 및 검증 페이지의 현재 placeholder를 표시합니다."""
    with st.container(key="analysis_container"):
        st.markdown(
            """
            <section class="page-placeholder">
                <h2>콘텐츠 준비 중</h2>
                <p>향후 ML 위험 탐지 과정, 성능지표, 검증 결과와 모델 한계가 이 영역에 추가됩니다.</p>
            </section>
            """,
            unsafe_allow_html=True,
        )
