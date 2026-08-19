import streamlit as st


def render_call_insights() -> None:
    """통화 패턴 및 핵심 인사이트 페이지의 현재 placeholder를 표시합니다."""
    with st.container(key="analysis_container"):
        st.markdown(
            """
            <section class="page-placeholder">
                <h2>콘텐츠 준비 중</h2>
                <p>향후 보이스피싱 통화 패턴과 핵심 분석 인사이트가 이 영역에 추가됩니다.</p>
            </section>
            """,
            unsafe_allow_html=True,
        )
