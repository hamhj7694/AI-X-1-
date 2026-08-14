import streamlit as st


OVERVIEW_CARDS = (
    {
        "id": "contest-info",
        "icon": "🏆",
        "title": "공모전 정보",
        "description": "공모전의 목적과 주요 내용을 소개하는 영역입니다.",
    },
    {
        "id": "service-direction",
        "icon": "💡",
        "title": "서비스 방향 설명",
        "description": (
            "보이스피싱 송금 방지턱 AI 서비스의 문제 정의와 "
            "핵심 방향을 설명하는 영역입니다."
        ),
    },
    {
        "id": "team-info",
        "icon": "👥",
        "title": "팀원 정보",
        "description": "프로젝트 참여 팀원과 역할을 소개하는 영역입니다.",
    },
)


def render_overview() -> None:
    """개요 제목과 세 개의 안내 카드를 표시합니다."""
    # 개요는 읽기 편한 기존 폭을 유지하고, 분석 페이지와 너비를 분리합니다.
    with st.container(key="overview_container"):
        st.markdown(
            """
            <header class="page-header">
                <p class="page-eyebrow">VOICE PHISHING DATA DASHBOARD</p>
                <h1>개요</h1>
                <p class="page-description">
                    경찰청·우체국 등에서 확보한 데이터를 기반으로 보이스피싱 피해 현황과
                    위험 요인을 분석한 결과를 소개합니다.
                </p>
            </header>
            """,
            unsafe_allow_html=True,
        )

        for card in OVERVIEW_CARDS:
            st.markdown(
                f"""
                <section id="{card['id']}" class="overview-card">
                    <div class="card-icon" aria-hidden="true">{card['icon']}</div>
                    <div class="card-content">
                        <h2>{card['title']}</h2>
                        <p>{card['description']}</p>
                    </div>
                </section>
                """,
                unsafe_allow_html=True,
            )
