import streamlit as st


def _render_placeholder(title: str, description: str) -> None:
    """아직 분석 결과가 연결되지 않은 페이지의 공통 골격을 표시합니다."""
    # 향후 표와 2열 그래프를 배치할 수 있도록 분석 페이지는 넓은 폭을 사용합니다.
    with st.container(key="analysis_container"):
        st.markdown(
            f"""
            <header class="page-header">
                <h1>{title}</h1>
            </header>
            <section class="page-placeholder">
                <h2>{title}</h2>
                <p>{description}</p>
            </section>
            """,
            unsafe_allow_html=True,
        )


def render_dataset_info() -> None:
    _render_placeholder(
        "데이터셋 정보",
        "분석에 사용한 데이터의 출처, 기간, 주요 컬럼 및 데이터 구성을 정리하는 영역입니다.",
    )


def render_preprocessing() -> None:
    _render_placeholder(
        "데이터 전처리 및 한계",
        "분석 전 수행한 데이터 정제·파생변수 생성 과정과 데이터가 가진 한계점을 설명하는 영역입니다.",
    )


def render_data_insights() -> None:
    _render_placeholder(
        "보이스피싱 현황 인사이트",
        "경찰청 및 우체국 데이터를 분석하여 확인한 피해 현황과 주요 통계적 인사이트를 보여주는 영역입니다.",
    )


def render_ml_insights() -> None:
    _render_placeholder(
        "ML 기반 위험 인사이트",
        "머신러닝 분석을 통해 확인한 주요 위험 요인과 모델 분석 결과를 보여주는 영역입니다.",
    )
