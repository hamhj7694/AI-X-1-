import streamlit as st


def apply_styles() -> None:
    """대시보드에서 공통으로 사용하는 CSS를 한 곳에 적용합니다."""
    st.markdown(
        """
        <style>
            :root {
                --primary: #1f5fae;
                --primary-dark: #174a88;
                --primary-soft: #edf5ff;
                --text-main: #172033;
                --text-muted: #657187;
                --border: #dce4ee;
                --surface: #ffffff;
                --background: #f6f8fb;
            }

            .stApp {
                background: var(--background);
                color: var(--text-main);
            }

            [data-testid="stHeader"] {
                background: transparent;
            }

            [data-testid="stSidebar"] {
                background: var(--surface);
                border-right: 1px solid var(--border);
            }

            [data-testid="stSidebar"] > div:first-child {
                padding-top: 0;
            }

            .sidebar-brand {
                display: flex;
                align-items: flex-start;
                gap: 0.65rem;
                padding: 0.25rem 0.25rem 1.5rem;
                color: var(--text-main);
                font-size: 1.05rem;
                font-weight: 750;
                line-height: 1.45;
            }

            .sidebar-brand-icon {
                font-size: 1.35rem;
                line-height: 1.35;
            }

            .st-key-selected_page {
                padding-top: 0.9rem;
                border-top: 1px solid var(--border);
            }

            .st-key-selected_page [role="radiogroup"] {
                gap: 0.2rem;
            }

            .st-key-selected_page label {
                width: 100%;
                min-height: 2.65rem;
                margin: 0;
                padding: 0.65rem 0.7rem;
                border-left: 3px solid transparent;
                border-radius: 0.55rem;
                color: var(--text-main);
                font-size: 0.92rem;
                line-height: 1.4;
            }

            /* Streamlit이 생성한 원형 indicator만 숨기고 radio 동작은 유지합니다. */
            .st-key-selected_page label > div > div > div:first-child {
                display: none;
            }

            .st-key-selected_page label [data-testid="stMarkdownContainer"] p {
                color: var(--text-main) !important;
            }

            .st-key-selected_page label:hover {
                background: #f4f8fd;
            }

            .st-key-selected_page label:hover [data-testid="stMarkdownContainer"] p {
                color: var(--text-main) !important;
            }

            .st-key-selected_page label[data-selected] {
                border-left-color: var(--primary);
                background: var(--primary-soft);
                color: var(--primary-dark);
                font-weight: 700;
            }

            .st-key-selected_page label[data-selected]
            [data-testid="stMarkdownContainer"] p {
                color: var(--primary-dark) !important;
                font-weight: 700;
            }

            .block-container {
                max-width: 1500px;
                padding-top: 3.5rem;
                padding-bottom: 4rem;
            }

            /* 페이지별 컨테이너 key를 사용해 너비 값을 쉽게 구분합니다. */
            .st-key-overview_container {
                width: 100%;
                max-width: 1120px;
                margin: 0 auto;
            }

            .st-key-analysis_container {
                width: 100%;
                max-width: 1500px;
                margin: 0 auto;
            }

            .page-header {
                margin-bottom: 2rem;
            }

            .page-eyebrow {
                margin: 0 0 0.5rem;
                color: var(--primary);
                font-size: 0.76rem;
                font-weight: 750;
                letter-spacing: 0.1em;
            }

            .page-header h1 {
                margin: 0;
                color: var(--text-main);
                font-size: 2.25rem;
                line-height: 1.25;
            }

            .page-description {
                max-width: 760px;
                margin: 0.85rem 0 0;
                color: var(--text-muted);
                font-size: 1rem;
                line-height: 1.75;
            }

            .overview-card {
                display: flex;
                gap: 1.15rem;
                align-items: flex-start;
                margin-bottom: 1.15rem;
                padding: 1.65rem 1.75rem;
                scroll-margin-top: 1.5rem;
                border: 1px solid var(--border);
                border-radius: 0.9rem;
                background: var(--surface);
                box-shadow: 0 4px 16px rgba(31, 70, 120, 0.045);
            }

            .card-icon {
                display: flex;
                flex: 0 0 2.7rem;
                align-items: center;
                justify-content: center;
                width: 2.7rem;
                height: 2.7rem;
                border-radius: 0.7rem;
                background: var(--primary-soft);
                font-size: 1.25rem;
            }

            .card-content h2 {
                margin: 0 0 0.5rem;
                color: var(--text-main);
                font-size: 1.2rem;
                line-height: 1.4;
            }

            .card-content p {
                margin: 0;
                color: var(--text-muted);
                font-size: 0.95rem;
                line-height: 1.7;
            }

            .page-placeholder {
                padding: 1.65rem 1.75rem;
                border: 1px solid var(--border);
                border-radius: 0.9rem;
                background: var(--surface);
                box-shadow: 0 4px 16px rgba(31, 70, 120, 0.045);
            }

            .page-placeholder h2 {
                margin: 0 0 0.65rem;
                color: var(--text-main);
                font-size: 1.2rem;
            }

            .page-placeholder p {
                margin: 0;
                color: var(--text-muted);
                font-size: 0.95rem;
                line-height: 1.7;
            }

            @media (max-width: 640px) {
                .block-container {
                    padding-top: 2rem;
                }

                .overview-card {
                    padding: 1.25rem;
                }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )
