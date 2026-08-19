import base64
from pathlib import Path
from textwrap import dedent

import streamlit as st


POSTER_PATH = Path(__file__).parents[1] / "styles" / "img" / "공모전포스터.jpg"


def _image_data_uri(image_path: Path) -> str:
    """로컬 이미지를 HTML에서 사용할 수 있는 데이터 URI로 변환합니다."""
    encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
    return f"data:image/jpeg;base64,{encoded}"


OVERVIEW_CARDS = (
    {
        "id": "contest-info",
        "icon": "🏆",
        "chapter": "CHAPTER 01",
        "title": "2026 금융 AI Challenge",
        "content": """
        <p class="card-lead">
            금융 현안을 데이터로 분석하고, AI 해결 방안을 실제 웹서비스로 구현하는 대회입니다.
        </p>
        <ul class="overview-points">
            <li><strong>공모전 주제</strong><span>AI 기반 금융 현안 해결 아이디어 및 웹서비스 개발</span></li>
            <li><strong>최종 목표</strong><span>서비스 기획을 넘어 작동 가능한 MVP 프로토타입 구현</span></li>
            <li><strong>우리의 접근</strong><span>보이스피싱 위험 신호를 분석하고 송금 차단 서비스로 연결</span></li>
        </ul>
        <p class="contest-link">
            <a href="https://daker.ai/public/hackathons/2026-finance-ai-challenge?utm_source=chatgpt.com"
               target="_blank" rel="noopener noreferrer">공모전 안내 페이지 바로가기</a>
        </p>
        """,
    },
    {
        "id": "service-direction",
        "icon": "🛡️",
        "chapter": "CHAPTER 02",
        "title": "AI 독립검증형 송금 방지턱",
        "content": """
        <p class="card-lead">
            고위험 보이스피싱 송금을 AI가 탐지하면 거래를 잠시 멈추고,
            독립적인 확인과 신뢰인의 승인을 거쳐 송금을 완료하는 금융사기 방지 서비스입니다.
        </p>
        <div class="service-flow">AI 위험탐지 <b>→</b> 송금 보류 <b>→</b> 독립검증 <b>→</b> 신뢰인 승인 <b>→</b> 송금</div>
        <ul class="overview-points">
            <li><strong>기존 방식</strong><span>사용자에게 위험을 알리고 판단을 요청</span></li>
            <li><strong>제안 방식</strong><span>고위험 순간에는 혼자 송금을 완료하지 못하도록 거래 권한을 일시 제한</span></li>
            <li><strong>핵심 가치</strong><span>주의 안내를 넘어 금융 권한 자체에 실질적인 방지턱 적용</span></li>
        </ul>
        """,
    },
)


def render_overview() -> None:
    """프로젝트 개요와 안내 카드를 표시합니다."""
    with st.container(key="overview_container"):
        st.markdown(
            dedent(
                """
                <header class="page-header">
                    <p class="page-eyebrow">VOICE PHISHING DATA DASHBOARD</p>
                    <h1>개요</h1>
                    <p class="page-description">
                        금융감독원 보이스피싱 사례와 공공 피해 데이터를 바탕으로 위험 신호를 분석하고,
                        고위험 송금을 실제로 멈추는 AI 금융사기 예방 서비스를 제안합니다.
                    </p>
                </header>
                """
            ),
            unsafe_allow_html=True,
        )

        poster_uri = _image_data_uri(POSTER_PATH) if POSTER_PATH.exists() else ""
        for card in OVERVIEW_CARDS:
            is_contest_card = card["id"] == "contest-info"
            card_class = "overview-card overview-card--with-poster" if is_contest_card else "overview-card"
            poster_html = (
                f'<div class="contest-poster-wrap">'
                f'<a class="contest-poster-trigger" href="#contest-poster-full" '
                f'aria-label="공모전 포스터 크게 보기">'
                f'<img class="contest-poster" src="{poster_uri}" alt="2026 금융 AI Challenge 공모전 포스터">'
                f'<span class="poster-zoom-label">크게 보기</span>'
                f'</a>'
                f'</div>'
                f'<div id="contest-poster-full" class="poster-lightbox">'
                f'<a class="poster-lightbox-backdrop" href="#contest-info" aria-label="포스터 닫기"></a>'
                f'<div class="poster-lightbox-dialog" role="dialog" aria-modal="true" aria-label="공모전 포스터 전체 보기">'
                f'<a class="poster-lightbox-close" href="#contest-info" aria-label="포스터 닫기">×</a>'
                f'<img src="{poster_uri}" alt="2026 금융 AI Challenge 공모전 포스터 전체 이미지">'
                f'</div>'
                f'</div>'
                if is_contest_card and poster_uri
                else ""
            )
            card_html = (
                f'<section id="{card["id"]}" class="{card_class}">'
                f'<div class="card-icon" aria-hidden="true">{card["icon"]}</div>'
                '<div class="card-content">'
                f'<div class="page-eyebrow">{card["chapter"]}</div>'
                f'<h2>{card["title"]}</h2>'
                f'{dedent(card["content"]).strip()}'
                '</div>'
                f'{poster_html}'
                '</section>'
            )
            st.markdown(card_html, unsafe_allow_html=True)
