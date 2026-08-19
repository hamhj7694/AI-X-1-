from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[2]
FSS_VOICE_SOURCE_URL = "https://www.fss.or.kr/fss/bbs/B0000203/list.do?menuNo=200686"
AIHUB_FINANCE_URL = (
    "https://www.aihub.or.kr/aihubdata/data/view.do?"
    "aihubDataSe=data&currMenu=115&dataSetSn=71926&topMenu=100"
)

POLICE_FILES = (
    {
        "name": "경찰청_보이스피싱_현황_20251231.csv",
        "period": "2016년 부터 2025년",
        "unit": "연도 × 사기유형 × 지표",
        "content": "기관사칭형·대출사기형의 발생건수, 피해액, 검거인원",
    },
    {
        "name": "경찰청_전화금융사기_보이스피싱_시도청별_피해금액_현황_20251231.csv",
        "period": "2023년 부터 2025년",
        "unit": "시도청 × 연도",
        "content": "시도청별 보이스피싱 피해금액",
    },
    {
        "name": "경찰청_전화금융사기_시도경찰청별_피해_현황_20251231.csv",
        "period": "2016년 부터 2025년",
        "unit": "시도경찰청 × 연도",
        "content": "시도경찰청별 피해 현황",
    },
    {
        "name": "경찰청_전화금융사기_피해자_연령별_현황_20251231.csv",
        "period": "2016년 부터 2025년",
        "unit": "연도 × 연령대",
        "content": "20대 이하부터 70대 이상까지의 피해자 구성",
    },
)

POSTAL_RAW_FILE = "우체국금융개발원_우체국_금융_사기계좌_정보_20251231.csv"
POSTAL_FINAL_FILE = "df_postal.csv"
VP_CASES_FILE = "vp_cases.csv"
NORMAL_REPRESENTATIVE_FILE = "normal_finance_calls_representative.csv"
CASE_ML_FILE = "case_ml_dataset_v1.csv"
WINDOW_ML_FILE = "window_ml_dataset_v1.csv"


def _candidate_data_directories() -> list[Path]:
    """환경변수·프로젝트 폴더·사용자 Downloads 순으로 데이터 폴더를 찾습니다."""
    candidates: list[Path] = []
    configured = os.getenv("AIX_DATASET_DIR")
    if configured:
        candidates.append(Path(configured).expanduser())

    candidates.extend(
        [
            PROJECT_ROOT / "dashboard" / "data" / "금융감독원 데이터셋",
            PROJECT_ROOT / "dashboard" / "data" / "original",
            PROJECT_ROOT / "2. 우체국, 경찰 공개 데이터 전처리",
            PROJECT_ROOT
            / "2. 우체국, 경찰 공개 데이터 전처리"
            / "voice_phishing_outputs_filtered",
            Path.home() / "Downloads" / "데이터셋",
        ]
    )
    return candidates


def _find_data_file(filename: str) -> Path | None:
    """후보 폴더에서 파일을 찾되 사용자 이름이 포함된 절대경로는 사용하지 않습니다."""
    for directory in _candidate_data_directories():
        path = directory / filename
        if path.is_file():
            return path
    return None


@st.cache_data(show_spinner=False)
def _read_table(path_text: str) -> pd.DataFrame:
    """CSV 인코딩 차이와 Excel 검수표를 공통 방식으로 읽습니다."""
    path = Path(path_text)
    if path.suffix.lower() in {".xlsx", ".xls"}:
        workbook = pd.ExcelFile(path)
        sheet_name = "review_sample" if "review_sample" in workbook.sheet_names else workbook.sheet_names[0]
        return pd.read_excel(workbook, sheet_name=sheet_name)

    last_error: Exception | None = None
    for encoding in ("utf-8-sig", "cp949", "utf-8"):
        try:
            return pd.read_csv(path, encoding=encoding, low_memory=False)
        except UnicodeDecodeError as error:
            last_error = error
    if last_error:
        raise last_error
    raise ValueError(f"지원하지 않는 파일 형식입니다: {path.name}")


def _load_optional(filename: str) -> tuple[pd.DataFrame | None, Path | None, str | None]:
    path = _find_data_file(filename)
    if path is None:
        return None, None, "파일을 찾지 못했습니다. AIX_DATASET_DIR 또는 데이터 폴더를 확인해주세요."
    try:
        return _read_table(str(path)), path, None
    except Exception as error:  # 화면 전체가 중단되지 않게 파일별 오류를 표시합니다.
        return None, path, str(error)


def _render_page_header() -> None:
    st.markdown(
        """
        <header class="page-header">
            <p class="page-eyebrow">DATA SOURCES</p>
            <h1>사용 데이터 소개</h1>
            <p class="page-description">
                프로젝트에 사용한 경찰청·우체국·금융감독원·AI허브 자료의 출처와 범위를 확인하고,
                최초 원본과 전처리·가공된 최종 데이터의 구조 및 상위 5행을 비교했음.
            </p>
        </header>
        """,
        unsafe_allow_html=True,
    )


def _render_compact_styles() -> None:
    """데이터 소개 페이지 안에서만 사용하는 조밀한 레이아웃을 적용합니다."""
    st.markdown(
        """
        <style>
            /* Streamlit이 제목에 자동으로 붙이는 앵커 링크 아이콘 제거 */
            .st-key-data_intro_content [data-testid="stHeaderActionElements"],
            .st-key-data_intro_content a.anchor-link,
            .st-key-data_intro_content h1 > a,
            .st-key-data_intro_content h2 > a,
            .st-key-data_intro_content h3 > a,
            .st-key-data_intro_content h4 > a,
            .st-key-data_intro_content h5 > a,
            .st-key-data_intro_content h6 > a {
                display: none !important;
            }

            .st-key-data_intro_content .page-header {
                margin-bottom: 1rem;
            }

            .st-key-data_intro_content .page-eyebrow {
                margin-bottom: 0.25rem;
                font-size: 0.78rem;
            }

            .st-key-data_intro_content .page-header h1 {
                font-size: 1.75rem;
            }

            .st-key-data_intro_content .page-description {
                max-width: 900px;
                margin-top: 0.45rem;
                font-size: 0.92rem;
                line-height: 1.5;
            }

            .st-key-data_intro_content .analysis-section-header {
                margin-top: 0.15rem;
                margin-bottom: 0.65rem;
            }

            .st-key-data_intro_content .analysis-section-header h2 {
                margin-top: 0;
                font-size: 1.18rem;
            }

            .st-key-data_intro_content .analysis-section-header .analysis-source {
                margin-bottom: 0.15rem;
                font-size: 0.78rem;
            }

            .st-key-data_intro_content [data-testid="stVerticalBlock"] {
                gap: 0.55rem;
            }

            .st-key-data_intro_content [data-testid="stVerticalBlockBorderWrapper"] {
                border-radius: 0.65rem;
            }

            .st-key-data_intro_content [data-testid="stVerticalBlockBorderWrapper"]
            > div {
                padding: 0.7rem 0.8rem;
            }

            .st-key-data_intro_content [data-testid="stMetric"] {
                padding: 0;
            }

            .st-key-data_intro_content [data-testid="stMetricLabel"] {
                font-size: 0.78rem;
            }

            .st-key-data_intro_content [data-testid="stMetricValue"] {
                font-size: 1.18rem;
            }

            .st-key-data_intro_content [data-testid="stCaptionContainer"] {
                font-size: 0.78rem;
                line-height: 1.45;
            }

            .st-key-data_intro_content [data-testid="stAlert"] {
                padding: 0.55rem 0.75rem;
                font-size: 0.84rem;
            }

            .st-key-data_intro_content [data-testid="stExpander"] details summary {
                min-height: 2.25rem;
                padding-top: 0.35rem;
                padding-bottom: 0.35rem;
                font-size: 0.86rem;
            }

            .st-key-data_intro_content [data-testid="stExpanderDetails"] {
                padding-top: 0.4rem;
                padding-bottom: 0.55rem;
            }

            .st-key-data_intro_content [data-testid="stTabs"] button {
                min-height: 2.45rem;
                padding: 0.35rem 0.8rem;
                font-size: 0.86rem;
            }

            .st-key-data_intro_content h4 {
                margin: 0;
                font-size: 0.98rem;
            }

            .st-key-data_intro_content h5 {
                margin: 0.1rem 0 0;
                font-size: 0.9rem;
            }

            .st-key-data_intro_content hr {
                margin: 0.55rem 0;
            }

            .st-key-data_intro_content .compact-column-list {
                margin: 0.15rem 0 0.35rem;
                padding: 0.45rem 0.55rem;
                border: 1px solid #e4eaf1;
                border-radius: 0.45rem;
                background: #f8fafc;
                color: #526078;
                font-size: 0.78rem;
                line-height: 1.55;
                word-break: break-word;
            }

            .st-key-data_intro_content .comparison-label {
                margin: 0.2rem 0 0.35rem;
                color: #657187;
                font-size: 0.78rem;
                font-weight: 700;
                letter-spacing: 0.04em;
                text-align: center;
            }

            .st-key-data_intro_content [data-testid="stMarkdownContainer"] p,
            .st-key-data_intro_content [data-testid="stMarkdownContainer"] li {
                font-size: 0.84rem;
                line-height: 1.5;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_source_summary() -> None:
    police_shapes = []
    for spec in POLICE_FILES:
        dataframe, _, _ = _load_optional(spec["name"])
        if dataframe is not None:
            police_shapes.append(dataframe.shape)
    police_rows = [shape[0] for shape in police_shapes]
    police_cols = [shape[1] for shape in police_shapes]
    police_original = (
        f"4 CSV · {min(police_rows)}–{max(police_rows)}행 / {min(police_cols)}–{max(police_cols)}열"
        if len(police_shapes) == 4
        else "4 CSV · 일부 파일 확인 필요"
    )

    postal_raw, _, _ = _load_optional(POSTAL_RAW_FILE)
    postal_final, _, _ = _load_optional(POSTAL_FINAL_FILE)
    postal_original = (
        f"1 CSV · {len(postal_raw):,}행 × {postal_raw.shape[1]}열"
        if postal_raw is not None
        else "1 CSV · 파일 확인 필요"
    )
    postal_result = (
        f"1 CSV · {len(postal_final):,}행 × {postal_final.shape[1]}열"
        if postal_final is not None
        else "1 CSV · 파일 확인 필요"
    )
    vp_cases, _, _ = _load_optional(VP_CASES_FILE)
    normal_sample, _, _ = _load_optional(NORMAL_REPRESENTATIVE_FILE)
    case_ml, _, _ = _load_optional(CASE_ML_FILE)
    window_ml, _, _ = _load_optional(WINDOW_ML_FILE)

    def shape_text(dataframe: pd.DataFrame | None) -> str:
        if dataframe is None:
            return "파일 확인 필요"
        return f"{len(dataframe):,}×{dataframe.shape[1]}"

    def summary_card(title: str, role: str, original: str, result: str, status: str) -> None:
        with st.container(border=True):
            source_column, original_column, result_column = st.columns(
                [0.9, 1, 1.25], gap="small", vertical_alignment="top"
            )
            with source_column:
                st.markdown(f"#### {title}")
                st.caption(role)
                st.markdown(f"`{status}`")
            with original_column:
                st.markdown("**초기·원본**")
                st.markdown(original)
            with result_column:
                st.markdown("**분석·최종 상태**")
                st.markdown(result)

    first_left, first_right = st.columns(2, gap="small")
    with first_left:
        summary_card(
            "🏛️ 경찰청",
            "전체 보이스피싱 현황",
            police_original,
            "원본 4개 그대로 사용했음",
            "원본 사용",
        )
    with first_right:
        summary_card(
            "📮 우체국",
            "피해자 특성·피해 형태",
            postal_original,
            postal_result,
            "전처리 완료",
        )

    second_left, second_right = st.columns(2, gap="small")
    with second_left:
        summary_card(
            "📞 금융감독원",
            "보이스피싱 통화 수법",
            f"미디어 513 → vp_cases {shape_text(vp_cases)}",
            f"case {shape_text(case_ml)} · window {shape_text(window_ml)}",
            "학습셋 2개 구성했음",
        )
    with second_right:
        summary_card(
            "🆚 AI허브 정상 금융상담",
            "정상 통화 비교군",
            f"12 ZIP → 대표 {shape_text(normal_sample)}",
            "case·window 학습셋에 비교군을 통합했음",
            "공통 입력 12개로 정렬했음",
        )

    st.caption(
        "읽는 법 · 경찰청=전체 현황 · 우체국=피해 사례 · 금융감독원=사기 통화 수법 · "
        "AI허브=정상 상담 비교군 후보"
    )


def _render_common_limitations() -> None:
    """서로 다른 네 자료를 함께 해석할 때의 공통 범위와 한계를 설명합니다."""
    limitations = pd.DataFrame(
        {
            "점검 항목": [
                "① 구조·분석 단위",
                "② 기간·표본 규모",
                "③ 결측치·범주·이상값",
                "④ 데이터 간 연결",
            ],
            "확인 내용": [
                "경찰청은 집계 통계, 우체국은 피해구제 사례, 금감원은 발췌 음원·영상, AI허브는 정상 상담 텍스트",
                "수집 기간과 표본 규모가 다르고 전국 통계와 개별 사례가 함께 존재",
                "결측값·자료형, 연령·사기유형·사칭기관의 범주 차이, 피해액 고액값 점검 필요",
                "경찰청·우체국·통화 자료는 동일 사건이 아니며 공통 사건 식별자가 없음",
            ],
            "분석 원칙": [
                "각 데이터의 목적과 행 단위에 맞춰 개별 전처리",
                "절대 수치를 직접 비교하지 않고 각 자료의 모집단과 범위 안에서 해석",
                "일괄 삭제·대체하지 않고 실제 의미를 확인한 뒤 처리하며 처리 이력을 보존",
                "사건별 1:1 결합을 하지 않고 공통 범주의 그룹 수준 비교만 수행",
            ],
        }
    )
    with st.expander("공통 전처리 한계와 해석 원칙", expanded=True):
        st.success(
            "전처리를 통해 데이터를 정리하는 동시에, 데이터마다 다른 구조·범위·한계를 "
            "파악하고 분석 가능한 범위를 설정했음."
        )
        st.dataframe(limitations, hide_index=True, width="stretch")


def _render_dataset_snapshot(
    title: str,
    dataframe: pd.DataFrame | None,
    path: Path | None,
    error: str | None,
    *,
    note: str | None = None,
) -> None:
    st.markdown(f"##### {title}")
    if error or dataframe is None:
        st.warning(error or "표시할 데이터가 없습니다.")
        return

    metric_rows, metric_cols = st.columns(2)
    metric_rows.metric("행 수", f"{len(dataframe):,}")
    metric_cols.metric("컬럼 수", f"{dataframe.shape[1]:,}")
    if path:
        st.caption(f"파일: `{path.name}`")
    if note:
        st.caption(note)

    columns_text = " · ".join(map(str, dataframe.columns))
    st.markdown(
        f'<div class="compact-column-list"><strong>컬럼</strong> · {columns_text}</div>',
        unsafe_allow_html=True,
    )
    st.markdown("**Top 5**")
    preview = dataframe.head(5).copy()
    for column in preview.select_dtypes(include=["object"]).columns:
        if preview[column].dropna().map(type).nunique() > 1:
            preview[column] = preview[column].astype("string")
    st.dataframe(preview, hide_index=True, width="stretch", height=205)


def _render_two_column_comparison(
    *,
    raw_data: pd.DataFrame | None,
    raw_path: Path | None,
    raw_error: str | None,
    final_data: pd.DataFrame | None,
    final_path: Path | None,
    final_error: str | None,
    raw_note: str,
    final_note: str,
) -> None:
    """원본과 최종본을 동일한 구조의 두 카드로 나란히 표시합니다."""
    st.markdown('<div class="comparison-label">원본 ↔ 최종본 구조 비교</div>', unsafe_allow_html=True)
    original_column, final_column = st.columns([1, 1], gap="small", vertical_alignment="top")
    with original_column:
        with st.container(border=True):
            _render_dataset_snapshot(
                "① 최초 원본 데이터셋",
                raw_data,
                raw_path,
                raw_error,
                note=raw_note,
            )
    with final_column:
        with st.container(border=True):
            _render_dataset_snapshot(
                "② 전처리·가공 최종 데이터셋",
                final_data,
                final_path,
                final_error,
                note=final_note,
            )


def _render_police_tab() -> None:
    st.markdown(
        """
        <div class="analysis-section-header">
            <p class="analysis-source">경찰청 공개데이터</p>
            <h2>전국 보이스피싱 피해 규모와 장기 변화</h2>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.info(
        "2016–2025년 현황·지역·연령 자료와 2023–2025년 시도청별 피해금액 자료를 확인했음. "
        "4개 원본을 그대로 사용했으며 개인·통화 단위 예측에서는 제외했음."
    )

    for spec in POLICE_FILES:
        with st.expander(f"{spec['name']} · {spec['period']}", expanded=True):
            st.caption(f"원본 단위: {spec['unit']} · 포함 내용: {spec['content']}")
            raw_data, raw_path, raw_error = _load_optional(spec["name"])
            _render_dataset_snapshot(
                "원본 데이터셋 (최종 분석에 그대로 사용)",
                raw_data,
                raw_path,
                raw_error,
                note="별도의 전처리·가공 데이터셋 없음",
            )


def _render_postal_tab(*, compact_column: bool = False) -> None:
    st.markdown(
        """
        <div class="analysis-section-header">
            <p class="analysis-source">우체국금융개발원 공개데이터</p>
            <h2>금융사기 피해구제 사례의 피해 특성</h2>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.info(
        "최초 접수월 기준 2025년 7–12월 자료를 분석했음. "
        "전화 기반·개인 피해를 남기고 일반 대출을 제외하되 피해구제 요청 사례는 유지한 "
        "최종본을 df_postal.csv로 구성했음."
    )

    raw_data, raw_path, raw_error = _load_optional(POSTAL_RAW_FILE)
    final_data, final_path, final_error = _load_optional(POSTAL_FINAL_FILE)
    if compact_column:
        st.markdown(
            '<div class="comparison-label">원본 ↔ 최종본 구조 비교</div>',
            unsafe_allow_html=True,
        )
        raw_shape = f"{len(raw_data):,}행 × {raw_data.shape[1]}열" if raw_data is not None else "확인 필요"
        final_shape = f"{len(final_data):,}행 × {final_data.shape[1]}열" if final_data is not None else "확인 필요"
        raw_metric, final_metric = st.columns(2)
        raw_metric.metric("원본", raw_shape)
        final_metric.metric("최종", final_shape)
        with st.expander("원본 컬럼과 Top 5 보기", expanded=True):
            _render_dataset_snapshot(
                "① 최초 원본 데이터셋",
                raw_data,
                raw_path,
                raw_error,
                note="우체국 금융 사기계좌 공개 원자료",
            )
        with st.expander("최종본 컬럼과 Top 5 보기", expanded=True):
            _render_dataset_snapshot(
                "② 전처리·가공 최종 데이터셋",
                final_data,
                final_path,
                final_error,
                note="전화_보이스피싱·중복후보·원본파일 등 검증 컬럼 포함",
            )
    else:
        _render_two_column_comparison(
            raw_data=raw_data,
            raw_path=raw_path,
            raw_error=raw_error,
            final_data=final_data,
            final_path=final_path,
            final_error=final_error,
            raw_note="우체국 금융 사기계좌 공개 원자료",
            final_note="전화_보이스피싱·중복후보·원본파일 등 검증 컬럼 포함",
        )

def _render_voice_tab() -> None:
    st.markdown(
        """
        <div class="analysis-section-header">
            <p class="analysis-source">금융감독원 × AI허브</p>
            <h2>보이스피싱 통화와 정상 금융상담 비교 데이터</h2>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.info(
        "서로 다른 목적으로 수집된 두 코퍼스의 차이를 확인했음. 공통 스키마와 동일 전처리만으로 "
        "출처 편향이 제거되지 않음을 한계로 설정했음."
    )

    source_comparison = pd.DataFrame(
        {
            "비교 항목": ["출처", "원자료 성격", "제작 목적", "분석 단위", "프로젝트 내 용도"],
            "보이스피싱": [
                "금융감독원 ‘그놈 목소리’",
                "보이스피싱 주요 발화를 담은 발췌 음원·영상",
                "범죄 수법 공개와 피해 예방",
                "전사 후 분리한 사건 또는 발화",
                "위험 표현 탐색·사칭 유형 분류·사기 양성 표본",
            ],
            "정상 금융상담": [
                "AI허브 ‘금융분야 고객상담 데이터’",
                "은행·보험·증권의 실제 상담 기반 텍스트",
                "금융 상담 언어 데이터 구축",
                "상담 대화 1건",
                "보이스피싱 여부 분류의 비교군 후보",
            ],
        }
    )
    st.dataframe(source_comparison, hide_index=True, width="stretch")

    with st.expander(
        "금융감독원 통화 수집·전사·데이터셋 구축 과정 자세히 보기",
        expanded=True,
    ):
        stored_media, processed_media, case_candidates = st.columns(3)
        stored_media.metric("보관 미디어", "513개", "MP3 412 · MP4 101", delta_color="off")
        processed_media.metric("처리 입력", "402개", "보고서 기준", delta_color="off")
        case_candidates.metric("사건 후보", "776건", "확정값 아님", delta_color="off")
        build_process = pd.DataFrame(
            {
                "단계": ["1. 자동 수집", "2. 전사·화자 분리", "3. 구조화", "4. 보조 라벨", "5. 검수"],
                "수행 내용": [
                    "공개 게시판을 자동 순회해 MP3·MP4를 지정 폴더에 저장",
                    "음성을 텍스트로 바꾸고 화자별 발화 구간을 자동 분리",
                    "파일·사건·발화 단위와 사칭·행동·전략·금액 근거표 구성",
                    "일부 분류·라벨 후보 생성에 GPT API를 보조적으로 사용",
                    "누락·빈 전사·역할 불명·근거 문장을 점검하고 일부 표본을 사람이 확인",
                ],
                "도구·산출물": [
                    "Python RPA 성격의 수집 코드 · 다운로드 목록",
                    "faster-whisper-large-v3-turbo · pyannote speaker-diarization-community-1",
                    "vp_files · vp_cases · vp_utterances · 이벤트 표",
                    "자동 생성 SILVER 라벨",
                    "검수 상태·제외 사유·사람 검수 표본",
                ],
            }
        )
        st.dataframe(build_process, hide_index=True, width="stretch")
        st.caption(
            "513개는 보관 미디어, 402개는 처리 보고서 입력, 776건은 자동 사건 후보로 확인했음. "
            "집계 기준이 달라 하나의 증감 흐름으로 해석하지 않았음."
        )

    st.warning(
        "자동 전사·화자 분리·사건 경계·역할 추정·GPT 보조 라벨을 SILVER로 구분했음. "
        "사람이 확인한 GOLD 표본만 최종 성능 판단에 사용하도록 기준을 설정했음."
    )

    st.markdown("#### 데이터셋 구성")
    vp_cases, vp_path, vp_error = _load_optional(VP_CASES_FILE)
    normal_sample, normal_path, normal_error = _load_optional(NORMAL_REPRESENTATIVE_FILE)
    case_ml, case_path, case_error = _load_optional(CASE_ML_FILE)
    window_ml, window_path, window_error = _load_optional(WINDOW_ML_FILE)

    def dataset_shape(dataframe: pd.DataFrame | None) -> str:
        if dataframe is None:
            return "파일 확인 필요"
        return f"{len(dataframe):,}행 × {dataframe.shape[1]}열"

    def class_balance(dataframe: pd.DataFrame | None) -> str:
        if dataframe is None or "y_phishing" not in dataframe.columns:
            return "라벨 분포 확인 필요"
        counts = dataframe["y_phishing"].value_counts().to_dict()
        return f"보이스피싱 {counts.get(1, 0):,}건 · 정상 {counts.get(0, 0):,}건"

    st.markdown("##### 컬럼 1 · 초기 데이터셋")
    initial_phishing, initial_normal = st.columns(2, gap="medium", vertical_alignment="top")
    with initial_phishing:
        with st.container(border=True):
            st.markdown("**1. 보이스피싱 통화 기반 초기 데이터셋**")
            st.markdown(f"`vp_cases.csv` · **{dataset_shape(vp_cases)}**")
            st.caption("보이스피싱 사건 1건이 한 행인 구조화 초기 데이터셋임")
            st.markdown(
                "음원·영상 전사문을 사건 단위로 구성했음. 원문, 정규화문, "
                "사칭·요구행동 후보와 검수 상태 등 분석 전 정보를 보존했음."
            )
            st.caption("한계 · 발췌 자료이므로 전체 시간·길이·실제 초중후반 흐름 분석에 사용하지 않음")
            with st.expander("vp_cases 컬럼과 Top 5 보기", expanded=True):
                _render_dataset_snapshot("vp_cases.csv", vp_cases, vp_path, vp_error)

    with initial_normal:
        with st.container(border=True):
            st.markdown("**2. AI허브 정상 금융상담 대표 데이터셋**")
            st.markdown(
                f"`normal_finance_calls_representative.csv` · **{dataset_shape(normal_sample)}**"
            )
            st.caption("은행·보험·증권 × 학습·검증 6개 층에서 각 100건을 고정 난수로 추출했음")
            st.markdown(
                "AI허브 원천 ZIP의 정상 상담을 대시보드 확인용 대표 CSV로 구성했음. "
                "원문·정규화문·기관·상담 주제·데이터 분할 정보를 보존했음."
            )
            st.caption("한계 · 판별용 정상 정답이 아니라 비교군 후보이며 보이스피싱 자료와 공통 사건 키가 없음")
            with st.expander("정상 금융상담 컬럼과 Top 5 보기", expanded=True):
                _render_dataset_snapshot(
                    "normal_finance_calls_representative.csv",
                    normal_sample,
                    normal_path,
                    normal_error,
                )

    st.markdown("##### 컬럼 2 · 모델 학습용 최종 데이터셋")
    st.caption("두 파일 모두 보이스피싱과 정상 금융상담을 함께 포함했음")
    final_case, final_window = st.columns(2, gap="medium", vertical_alignment="top")
    with final_case:
        with st.container(border=True):
            st.markdown("**1. 전체 단위 분석용**")
            st.markdown(f"`case_ml_dataset_v1.csv` · **{dataset_shape(case_ml)}**")
            st.caption(class_balance(case_ml))
            st.markdown(
                "사건 또는 정상 상담 전체를 한 행으로 구성했음. 공통 핵심 모델 입력 변수 12개에 "
                "source_id·정답 라벨·데이터 분할을 더해 총 15열로 저장했음."
            )
            with st.expander("전체 분석 데이터 컬럼과 Top 5 보기", expanded=True):
                _render_dataset_snapshot("case_ml_dataset_v1.csv", case_ml, case_path, case_error)

    with final_window:
        with st.container(border=True):
            st.markdown("**2. 구간 단위 분석용**")
            st.markdown(f"`window_ml_dataset_v1.csv` · **{dataset_shape(window_ml)}**")
            st.caption(class_balance(window_ml))
            st.markdown(
                "통화·상담을 일정 구간으로 나눠 한 행으로 구성했음. 공통 핵심 모델 입력 변수 12개에 "
                "구간 ID·사건 ID·정답·분할·구간 수·표본 가중치를 더해 총 18열로 저장했음."
            )
            with st.expander("구간 분석 데이터 컬럼과 Top 5 보기", expanded=True):
                _render_dataset_snapshot(
                    "window_ml_dataset_v1.csv", window_ml, window_path, window_error
                )

    st.markdown("#### 이 비교의 핵심 한계")
    st.warning(
        "높은 정확도만으로 실제 탐지 성능을 확정하지 않았음. 모델이 위험 표현보다 "
        "발췌 방식·전사 형식·기관명 같은 출처 차이를 학습했을 가능성을 확인했음."
    )
    limitations = pd.DataFrame(
        {
            "한계": [
                "출처·제작 목적 차이",
                "발췌 여부 차이",
                "형식·문체 차이",
                "라벨 의미 차이",
                "자동 전사·자동 라벨 오류",
                "높은 정확도의 오해 가능성",
            ],
            "분석에 미치는 영향": [
                "모델이 사기 언어가 아니라 기관·코퍼스의 흔적을 학습할 수 있음",
                "보이스피싱의 길이·시점·대화 흐름을 정상상담과 공정하게 비교할 수 없음",
                "화자 표기, 문장부호, 전사 방식, 상담 스크립트가 분류 단서가 될 수 있음",
                "사기 자료는 양성 사례지만 AI허브 자료는 판별 실험용 음성 라벨이 아님",
                "Whisper·화자 분리·규칙·GPT 결과에 오인식과 잘못된 사건·역할·범주가 포함될 수 있음",
                "지나치게 높은 성능이 실제 탐지력보다 데이터 출처 구분 능력을 반영할 수 있음",
            ],
            "대응 원칙": [
                "공통 스키마 적용 후 출처 식별 실험과 외부 검증 수행",
                "시간·길이·위치 변수 제외, 텍스트 단위를 유사하게 맞춤",
                "동일 전처리 적용 및 출처 전용 토큰·메타데이터 제거",
                "‘정상 비교군 후보’로 명시하고 오분류 표본을 수동 점검",
                "SILVER 상태와 생성 방법을 보존하고 GOLD 검수 표본에서만 성능을 확정",
                "무작위 분할 외에 출처 차단·교차 데이터셋 검증과 사기 단독 분석 병행",
            ],
        }
    )
    with st.expander("통화 데이터의 상세 한계와 대응 원칙", expanded=True):
        st.dataframe(limitations, hide_index=True, width="stretch")

    link_left, link_right, _ = st.columns([1, 1, 2])
    with link_left:
        st.link_button("금융감독원 원본 출처", FSS_VOICE_SOURCE_URL, width="stretch")
    with link_right:
        st.link_button("AI허브 데이터 출처", AIHUB_FINANCE_URL, width="stretch")


def render_data_intro() -> None:
    """사용 데이터의 출처·범위와 원본/최종 데이터 Top 5를 표시합니다."""
    with st.container(key="analysis_container"):
        with st.container(key="data_intro_content"):
            _render_compact_styles()
            _render_page_header()
            _render_source_summary()
            st.divider()
            public_tab, voice_tab = st.tabs(
                ["🏛️ 공개 통계·피해 사례", "📞 통화·텍스트 데이터"]
            )
            with public_tab:
                police_column, postal_column = st.columns(2, gap="medium", vertical_alignment="top")
                with police_column:
                    _render_police_tab()
                with postal_column:
                    _render_postal_tab(compact_column=True)
            with voice_tab:
                _render_voice_tab()
            st.divider()
            _render_common_limitations()
