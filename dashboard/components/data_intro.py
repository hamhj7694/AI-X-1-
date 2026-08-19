import streamlit as st


def render_data_intro() -> None:
    """데이터 소개 페이지의 현재 placeholder를 표시합니다."""
    with st.container(key="analysis_container"):
        st.markdown(
            """
            <section class="page-placeholder">
                <h2>콘텐츠 준비 중</h2>
                <p>향후 데이터 출처, 기간, 규모, 주요 변수와 프로젝트 내 역할이 이 영역에 추가됩니다.</p>
            </section>
            """,
            unsafe_allow_html=True,
        )
