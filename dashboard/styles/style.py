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
                width: 100%;
                max-width: none;
                padding-top: 3.5rem;
                padding-right: 2rem;
                padding-bottom: 4rem;
                padding-left: 2rem;
            }

            /* 페이지별 컨테이너 key를 사용해 너비 값을 쉽게 구분합니다. */
            .st-key-overview_container {
                width: 100%;
                max-width: 1120px;
                margin: 0 auto;
            }

            .st-key-analysis_container {
                width: 100%;
                max-width: none;
                margin-top: -1.5rem;
                margin-right: auto;
                margin-left: auto;
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

            .card-content {
                flex: 1 1 auto;
                min-width: 0;
            }

            .card-content p {
                margin: 0;
                color: var(--text-muted);
                font-size: 0.95rem;
                line-height: 1.7;
            }

            .card-content .card-lead {
                max-width: 760px;
                color: var(--text-main);
                font-size: 0.97rem;
            }

            .overview-points {
                display: grid;
                gap: 0.55rem;
                margin: 1rem 0 0;
                padding: 0;
                list-style: none;
            }

            .overview-points li {
                display: grid;
                grid-template-columns: 6.25rem minmax(0, 1fr);
                gap: 0.75rem;
                color: var(--text-muted);
                font-size: 0.92rem;
                line-height: 1.55;
            }

            .overview-points strong {
                color: var(--text-main);
            }

            .contest-link {
                margin-top: 1rem !important;
            }

            .service-flow {
                margin-top: 1rem;
                padding: 0.75rem 0.9rem;
                border-radius: 0.65rem;
                background: var(--primary-soft);
                color: var(--primary);
                font-size: 0.9rem;
                font-weight: 700;
                line-height: 1.55;
            }

            .contest-poster-wrap {
                flex: 0 0 220px;
                align-self: stretch;
                overflow: hidden;
                border: 1px solid var(--border);
                border-radius: 0.75rem;
                background: var(--primary-soft);
            }

            .contest-poster-trigger {
                position: relative;
                display: block;
                width: 100%;
                height: 100%;
                cursor: zoom-in;
            }

            .contest-poster {
                display: block;
                width: 100%;
                height: 100%;
                min-height: 285px;
                object-fit: contain;
                object-position: top center;
            }

            .poster-zoom-label {
                position: absolute;
                right: 0.55rem;
                bottom: 0.55rem;
                padding: 0.32rem 0.55rem;
                border-radius: 999px;
                background: rgba(15, 23, 42, 0.78);
                color: #ffffff;
                font-size: 0.72rem;
                font-weight: 700;
                opacity: 0;
                transform: translateY(0.25rem);
                transition: opacity 0.18s ease, transform 0.18s ease;
            }

            .contest-poster-trigger:hover .poster-zoom-label,
            .contest-poster-trigger:focus-visible .poster-zoom-label {
                opacity: 1;
                transform: translateY(0);
            }

            .poster-lightbox {
                position: fixed;
                z-index: 99999;
                inset: 0;
                display: none;
                align-items: center;
                justify-content: center;
                padding: 2rem;
            }

            .poster-lightbox:target {
                display: flex;
            }

            .poster-lightbox-backdrop {
                position: absolute;
                inset: 0;
                background: rgba(8, 15, 29, 0.88);
                backdrop-filter: blur(4px);
            }

            .poster-lightbox-dialog {
                position: relative;
                z-index: 1;
                display: flex;
                max-width: min(92vw, 900px);
                max-height: 92vh;
                padding: 0.7rem;
                border-radius: 0.9rem;
                background: #ffffff;
                box-shadow: 0 24px 70px rgba(0, 0, 0, 0.4);
            }

            .poster-lightbox-dialog img {
                display: block;
                max-width: 100%;
                max-height: calc(92vh - 1.4rem);
                border-radius: 0.45rem;
                object-fit: contain;
            }

            .poster-lightbox-close {
                position: absolute;
                z-index: 2;
                top: -0.9rem;
                right: -0.9rem;
                display: flex;
                align-items: center;
                justify-content: center;
                width: 2.35rem;
                height: 2.35rem;
                border: 2px solid #ffffff;
                border-radius: 50%;
                background: #0f172a;
                color: #ffffff !important;
                font-size: 1.55rem;
                line-height: 1;
                text-decoration: none !important;
                box-shadow: 0 6px 18px rgba(0, 0, 0, 0.3);
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

            .analysis-section-header {
                margin-bottom: 1.25rem;
            }

            .analysis-section-header .analysis-source {
                margin: 0 0 0.35rem;
                color: var(--primary);
                font-size: 0.78rem;
                font-weight: 700;
                letter-spacing: 0.04em;
            }

            .analysis-section-header h2 {
                margin: 0;
                color: var(--text-main);
                font-size: 1.65rem;
                line-height: 1.4;
            }

            .analysis-section-header > p:last-child {
                margin: 0.5rem 0 0;
                color: var(--text-muted);
                font-size: 0.95rem;
                line-height: 1.7;
            }

            .police-trend-header {
                margin-bottom: 0.9rem;
            }

            .police-trend-header .analysis-source {
                margin-bottom: 0.25rem;
            }

            .police-trend-header > p:last-child {
                margin-top: 0.4rem;
            }

            .police-summary-strip {
                margin-bottom: 1.25rem;
                padding: 0.85rem 1rem;
                border: 1px solid var(--border);
                border-radius: 0.75rem;
                background: var(--surface);
            }

            .police-summary-title {
                margin: 0 0 0.65rem;
                color: var(--primary-dark);
                font-size: 0.9rem;
                font-weight: 750;
            }

            .police-summary-grid {
                display: grid;
                grid-template-columns: repeat(4, minmax(0, 1fr));
            }

            .police-summary-item {
                min-width: 0;
                padding: 0.1rem 1rem;
            }

            .police-summary-item + .police-summary-item {
                border-left: 1px solid var(--border);
            }

            .police-summary-label {
                margin: 0 0 0.2rem;
                color: var(--text-muted);
                font-size: 0.82rem;
                font-weight: 600;
                line-height: 1.35;
            }

            .police-summary-value {
                margin: 0;
                color: var(--text-main);
                font-size: 1.35rem;
                font-weight: 750;
                line-height: 1.25;
            }

            .police-summary-secondary {
                margin: 0.25rem 0 0;
                color: var(--text-muted);
                font-size: 0.78rem;
                line-height: 1.35;
            }

            /* 출처 문구는 본문보다 약하게 유지하되 기본 caption보다 선명하게 표시합니다. */
            .st-key-police_count_chart [data-testid="stCaptionContainer"],
            .st-key-police_count_chart [data-testid="stCaptionContainer"] p,
            .st-key-police_amount_chart [data-testid="stCaptionContainer"],
            .st-key-police_amount_chart [data-testid="stCaptionContainer"] p {
                color: #526078 !important;
            }

            .analysis-insight {
                margin-top: 1.15rem;
                padding: 1rem 1.15rem;
                border-left: 4px solid var(--primary);
                border-radius: 0.35rem;
                background: var(--primary-soft);
                color: var(--text-main);
            }

            .police-trend-insight {
                margin-top: 0.75rem;
            }

            .analysis-section-divider {
                margin: 2.25rem 0 1.75rem;
                border-top: 1px solid var(--border);
            }

            .analysis-insight strong {
                color: var(--primary-dark);
            }

            .analysis-insight p {
                margin: 0.35rem 0 0;
                font-size: 0.94rem;
                line-height: 1.65;
            }

            @media (max-width: 900px) {
                .police-summary-grid {
                    grid-template-columns: repeat(2, minmax(0, 1fr));
                }

                .police-summary-item {
                    padding: 0.5rem 1rem;
                }

                .police-summary-item + .police-summary-item {
                    border-left: 0;
                }

                .police-summary-item:nth-child(even) {
                    border-left: 1px solid var(--border);
                }

                .police-summary-item:nth-child(n + 3) {
                    border-top: 1px solid var(--border);
                }
            }

            @media (max-width: 640px) {
                .block-container {
                    padding-top: 2rem;
                    padding-right: 1rem;
                    padding-left: 1rem;
                }

                .st-key-analysis_container {
                    margin-top: 0;
                }

                .police-summary-grid {
                    grid-template-columns: 1fr;
                }

                .police-summary-item:nth-child(even) {
                    border-left: 0;
                }

                .police-summary-item:nth-child(n + 2) {
                    border-top: 1px solid var(--border);
                }

                .overview-card {
                    padding: 1.25rem;
                }

                .overview-card--with-poster {
                    flex-wrap: wrap;
                }

                .overview-card--with-poster .card-content {
                    flex-basis: calc(100% - 4rem);
                }

                .contest-poster-wrap {
                    flex: 1 1 100%;
                    height: auto;
                    margin-left: 3.85rem;
                }

                .contest-poster {
                    height: auto;
                    max-height: 520px;
                    object-fit: contain;
                }

                .poster-lightbox {
                    padding: 1rem;
                }

                .poster-lightbox-dialog {
                    max-width: 96vw;
                    max-height: 94vh;
                    padding: 0.45rem;
                }

                .poster-lightbox-dialog img {
                    max-height: calc(94vh - 0.9rem);
                }

                .poster-lightbox-close {
                    top: 0.4rem;
                    right: 0.4rem;
                }

                .overview-points li {
                    grid-template-columns: 1fr;
                    gap: 0.1rem;
                }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )
