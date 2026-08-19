import streamlit as st


def render_preprocessing() -> None:
    """데이터 전처리 및 한계 페이지의 현재 placeholder를 표시합니다."""
    with st.container(key="analysis_container"):
        st.markdown(
            """
            <section class="page-placeholder">
                <h2>콘텐츠 준비 중</h2>
                <p>향후 데이터 정제 과정과 분석 데이터가 가진 품질 한계가 이 영역에 추가됩니다.</p>
            </section>
            """,
            unsafe_allow_html=True,
        )
