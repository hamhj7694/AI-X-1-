import streamlit as st


PAGE_OPTIONS = {
    "overview": "🏠 개요",
    "dataset": "🗂️ 데이터셋 정보",
    "preprocessing": "🧹 데이터 전처리 및 한계",
    "data_insights": "📊 보이스피싱 현황 인사이트",
    "ml_insights": "🤖 ML 기반 위험 인사이트",
}


def render_sidebar() -> str:
    """대시보드 이름과 페이지 메뉴를 표시하고 선택값을 반환합니다."""
    with st.sidebar:
        st.markdown(
            """
            <div class="sidebar-brand">
                <span class="sidebar-brand-icon">🛡️</span>
                <span>보이스피싱 현황 및 위험 분석</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # radio가 선택 상태를 관리하므로 별도의 Session State가 필요하지 않습니다.
        return st.radio(
            "페이지 선택",
            options=tuple(PAGE_OPTIONS),
            format_func=PAGE_OPTIONS.get,
            key="selected_page",
            label_visibility="collapsed",
        )
