import streamlit as st


OVERVIEW_CARDS = (
    {
        "id": "contest-info",
        "icon": "🏆",
        "chapter": "CHAPTER 01",
        "title": "2026 금융 AI Challenge",
        "content": """
            <p>
                <strong>금융 AI Challenge</strong>는 AI를 활용해 금융 문제를 해결하고,
                실제로 작동하는 웹서비스까지 구현하는 공모전입니다.
            </p>
            <p style="margin-top: 0.85rem;">
                <strong>공모전 배경</strong><br>
                참가자는 금융 분야의 문제를 정의하고 데이터를 통해 현안을 이해한 뒤,
                AI 기반 해결 방안과 서비스 기획을 MVP 형태의 프로토타입으로 개발합니다.
                단순한 아이디어 제안을 넘어 실제 서비스로 구현할 수 있는 가능성을
                검증하는 것이 대회의 목표입니다.
            </p>
            <p style="margin-top: 0.85rem;">
                <strong>핵심 방향</strong><br>
                “금융 문제를 발견하는 것에서 끝나지 않고, 데이터를 통해 문제를 이해하고
                AI를 활용한 해결방안을 실제 서비스로 구현한다.”
            </p>
            <p style="margin-top: 0.85rem;">
                <strong>공모전 주제</strong><br>
                AI 기반의 금융 현안 해결 아이디어 및 웹서비스 개발
            </p>
            <p style="margin-top: 0.85rem;">
                <a href="https://daker.ai/public/hackathons/2026-finance-ai-challenge?utm_source=chatgpt.com"
                   target="_blank" rel="noopener noreferrer">공모전 안내 페이지 바로가기 ↗</a>
            </p>
        """,
    },
    {
        "id": "service-direction",
        "icon": "🛡️",
        "chapter": "CHAPTER 02",
        "title": "AI 독립검증형 송금 방지턱",
        "content": """
            <p>
                보이스피싱 고위험 송금이 감지되면 거래를 일시 보류하고,
                사전에 지정된 신뢰인의 추가 승인과 실제 당사자·기관의 독립검증을 거쳐야
                송금이 완료되는 <strong>AI 기반 다중검증 금융사기 방지 서비스</strong>입니다.
            </p>
            <p style="margin-top: 0.85rem;">
                <strong>핵심 키워드</strong><br>
                <strong>AI 위험탐지 → 송금 보류 → 독립검증 → 신뢰인 승인 → 송금</strong>
            </p>
            <p style="margin-top: 0.85rem;">
                <strong>핵심 차별점</strong><br>
                고위험 거래가 감지되면 사용자의 송금 실행 권한을 일시적으로 제한하고,
                사전에 등록된 신뢰인에게 해당 거래의 승인 권한을 임시로 전환합니다.
                피해자에게 단순히 “한 번 더 생각하세요”라고 알리는 것을 넘어,
                위험한 순간에는 혼자 송금을 완료할 수 없도록 금융 권한 자체에
                방지턱을 만드는 것이 핵심 차별점입니다.
            </p>
        """,
    },
    {
        "id": "team-info",
        "icon": "👥",
        "chapter": "CHAPTER 03",
        "title": "팀원 정보",
        "content": """
            <p><strong>조장</strong> · 함형준</p>
            <p style="margin-top: 0.55rem;"><strong>팀원</strong> · 이종열, 엄정희</p>
        """,
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
                    위험 신호를 분석하고, AI 기반 송금 방지 서비스로 연결하는 프로젝트입니다.
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
                        <div class="page-eyebrow">{card['chapter']}</div>
                        <h2>{card['title']}</h2>
                        {card['content']}
                    </div>
                </section>
                """,
                unsafe_allow_html=True,
            )
