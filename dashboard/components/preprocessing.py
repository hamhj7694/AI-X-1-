from pathlib import Path

import pandas as pd
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[2]
POSTAL_DATA_RELATIVE_PATH = Path("c_이종열/데이터/df_postal.csv")
POSTAL_DATA_PATH = PROJECT_ROOT / POSTAL_DATA_RELATIVE_PATH
POSTAL_REQUIRED_COLUMNS = (
    "피해액",
    "사기유형",
    "전화_보이스피싱",
    "중복후보",
)
WON_PER_MANWON = 10_000


def calculate_postal_outlier_metrics() -> dict[str, float | int]:
    """우체국 최종 분석표본에서 IQR 이상치 검토 지표를 재현합니다."""
    raw_data = pd.read_csv(POSTAL_DATA_PATH, encoding="utf-8-sig")
    raw_data.columns = raw_data.columns.str.strip()

    for column in raw_data.select_dtypes(include=["object", "string"]).columns:
        raw_data[column] = raw_data[column].str.strip()

    missing_columns = [
        column for column in POSTAL_REQUIRED_COLUMNS if column not in raw_data.columns
    ]
    if missing_columns:
        raise ValueError(f"필수 컬럼이 없습니다: {', '.join(missing_columns)}")

    raw_data["피해액"] = pd.to_numeric(
        raw_data["피해액"].astype("string").str.replace(",", "", regex=False),
        errors="coerce",
    )
    if raw_data["피해액"].isna().any():
        raise ValueError("피해액을 숫자로 변환할 수 없는 행이 있습니다.")

    phone_mask = (
        raw_data["전화_보이스피싱"].astype("string").str.lower().eq("true")
    )
    investment_mask = raw_data["사기유형"].eq("투자사기")
    duplicate_mask = raw_data["중복후보"].astype("string").str.lower().eq("true")
    damage_amounts = raw_data.loc[
        phone_mask & ~investment_mask & ~duplicate_mask,
        "피해액",
    ]

    if damage_amounts.empty:
        raise ValueError("우체국 피해금액 분석대상이 없습니다.")
    if damage_amounts.le(0).any():
        raise ValueError("피해액이 0원 이하인 행이 있습니다.")

    q1 = float(damage_amounts.quantile(0.25))
    median = float(damage_amounts.median())
    q3 = float(damage_amounts.quantile(0.75))
    upper_bound = q3 + 1.5 * (q3 - q1)
    outlier_mask = damage_amounts.gt(upper_bound)
    outlier_count = int(outlier_mask.sum())
    sample_size = int(damage_amounts.size)
    mean_amount = float(damage_amounts.mean())
    without_outlier_mean = float(damage_amounts.loc[~outlier_mask].mean())

    # 평균 비교는 이상치 후보의 영향만 확인하며, 실제 분석표본에서는 행을 삭제하지 않습니다.
    reduction_rate = (1 - without_outlier_mean / mean_amount) * 100
    return {
        "sample_size": sample_size,
        "q1": q1,
        "median": median,
        "q3": q3,
        "upper_bound": upper_bound,
        "outlier_count": outlier_count,
        "outlier_ratio": outlier_count / sample_size * 100,
        "mean_amount": mean_amount,
        "without_outlier_mean": without_outlier_mean,
        "reduction_rate": reduction_rate,
    }


def _format_manwon(amount_won: float, decimal_places: int = 0) -> str:
    """원 단위 금액을 발표 화면용 만원 단위로 표시합니다."""
    return f"{amount_won / WON_PER_MANWON:,.{decimal_places}f}만원"


def _render_process_strip() -> None:
    """페이지 상단에 전체 전처리 흐름을 낮은 높이로 표시합니다."""
    st.markdown(
        """
        <section class="preprocess-overview" aria-label="전체 전처리 흐름">
            <div class="preprocess-process-track">
                <div class="preprocess-process-step"><strong>원본 데이터</strong><span>경찰청 · 우체국</span></div>
                <span class="preprocess-process-arrow" aria-hidden="true">→</span>
                <div class="preprocess-process-step"><strong>품질 점검</strong><span>결측 · 중복 · 형식</span></div>
                <span class="preprocess-process-arrow" aria-hidden="true">→</span>
                <div class="preprocess-process-step"><strong>분석대상 선정</strong><span>전화 사례 선별</span></div>
                <span class="preprocess-process-arrow" aria-hidden="true">→</span>
                <div class="preprocess-process-step"><strong>형식·변수 정리</strong><span>수치형 · 파생변수</span></div>
                <span class="preprocess-process-arrow" aria-hidden="true">→</span>
                <div class="preprocess-process-step"><strong>이상치 검토</strong><span>IQR 기준 확인</span></div>
                <span class="preprocess-process-arrow" aria-hidden="true">→</span>
                <div class="preprocess-process-step"><strong>최종 분석 데이터</strong><span>후속 분석 활용</span></div>
            </div>
            <p class="preprocess-overview-note">
                원본 데이터는 보존하고, 품질 점검과 분석대상 선정을 거쳐 후속 분석에 사용할 데이터를 구성했습니다.
            </p>
        </section>
        """,
        unsafe_allow_html=True,
    )


def _render_police_preprocessing() -> None:
    """경찰청 집계데이터의 정리 과정과 처리 결과를 표시합니다."""
    st.markdown(
        """
        <section class="preprocess-panel">
            <header class="preprocess-panel-header">
                <p class="preprocess-kicker">데이터별 전처리</p>
                <h2>경찰청 집계데이터</h2>
                <p>전국 단위 집계통계를 분석 가능한 형식으로 정리했습니다.</p>
            </header>
            <div class="preprocess-flow" aria-label="경찰청 데이터 전처리 과정">
                <div class="preprocess-flow-step"><span>01</span><strong>원본 집계자료</strong></div>
                <div class="preprocess-flow-step"><span>02</span><div><strong>결측·중복·공백 점검</strong><small>컬럼명·문자열 공백과 형식 확인</small></div></div>
                <div class="preprocess-flow-step"><span>03</span><div><strong>연도·수치형 형식 확인</strong><small>연도 · 발생건수 · 피해금액 숫자형 정리</small></div></div>
                <div class="preprocess-flow-step"><span>04</span><div><strong>2016~2025 분석기간 확인</strong><small>연도가 연속적으로 존재하는지 점검</small></div></div>
                <div class="preprocess-flow-step"><span>05</span><div><strong>사기유형 합산 및 전체 지표 생성</strong><small>기관사칭형·대출사기형을 합산해 전체 건수·피해금액 구성</small></div></div>
            </div>
            <div class="preprocess-formulas" aria-label="경찰청 파생변수">
                <div><span>기관사칭형 + 대출사기형 발생건수</span><strong>전체 발생건수</strong></div>
                <div><span>기관사칭형 + 대출사기형 피해금액</span><strong>전체 피해금액</strong></div>
            </div>
            <div class="preprocess-result-block">
                <p class="preprocess-result-title">처리 결과</p>
                <div class="preprocess-result-grid">
                    <div><strong>0</strong><span>결측</span></div>
                    <div><strong>0</strong><span>완전중복</span></div>
                    <div><strong>2016~2025</strong><span>기간 확인</span></div>
                    <div><strong>2개</strong><span>파생변수</span></div>
                </div>
            </div>
            <p class="preprocess-principle">경찰청 자료는 집계 기준이 서로 다르기 때문에 각각의 집계 단위를 유지합니다.</p>
        </section>
        """,
        unsafe_allow_html=True,
    )


def _render_postal_preprocessing() -> None:
    """우체국 피해사례의 분석대상 선정 과정과 최종 변수 구성을 표시합니다."""
    st.markdown(
        """
        <section class="preprocess-panel">
            <header class="preprocess-panel-header">
                <p class="preprocess-kicker">데이터별 전처리</p>
                <h2>우체국 피해사례</h2>
                <p>원본 피해사례에서 전화 보이스피싱 분석에 사용할 사례를 선정했습니다.</p>
            </header>
            <div class="preprocess-selection" aria-label="우체국 분석표본 선정 과정">
                <div class="preprocess-selection-step"><span>원본 피해사례</span><strong>184건</strong></div>
                <div class="preprocess-selection-step"><span>전화 보이스피싱 선정</span><strong>141건</strong><small>전화_보이스피싱 == True</small></div>
                <div class="preprocess-selection-step"><span>투자사기 제외</span><strong>141건</strong><small>추가 제외 0건 · 전화 사례 선정 단계에서 이미 제외</small></div>
                <div class="preprocess-selection-step"><span>중복후보 35건 제외</span><strong>106건</strong><small>중복후보 == False</small></div>
            </div>
            <p class="preprocess-principle preprocess-postal-principle">원본은 그대로 보존하고 분석용 데이터에 선정 조건을 적용했습니다.</p>
            <div class="preprocess-variable-block">
                <div class="preprocess-variable-heading"><span>최종 분석 데이터</span><strong>106건 × 13개 변수</strong></div>
                <div class="preprocess-variable-grid">
                    <div><span>피해자 특성</span><strong>2개</strong></div>
                    <div><span>피해·접수 정보</span><strong>4개</strong></div>
                    <div><span>사기 특성</span><strong>3개</strong></div>
                    <div><span>분석·출처 관리</span><strong>4개</strong></div>
                </div>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def _render_outlier_review(metrics: dict[str, float | int]) -> None:
    """피해금액 IQR 지표와 이상치 유지 결정을 표시합니다."""
    st.markdown(
        f"""
        <section class="preprocess-outlier-section">
            <header class="preprocess-outlier-header">
                <p class="preprocess-kicker">피해금액 분포 점검 · 최종 표본 {metrics['sample_size']:,}건</p>
                <h2>피해금액 이상치 검토</h2>
                <p>
                    일부 고액 피해사례가 전체 피해금액 분포에 미치는 영향을 확인하기 위해
                    IQR 기준으로 이상치 후보를 검토했습니다.
                </p>
                <small>IQR은 데이터 가운데 50%의 범위를 기준으로 크게 벗어난 값을 확인하는 방법입니다.</small>
            </header>
            <div class="preprocess-iqr-strip">
                <div><span>Q1</span><strong>{_format_manwon(float(metrics['q1']))}</strong></div>
                <div><span>중앙값</span><strong>{_format_manwon(float(metrics['median']))}</strong></div>
                <div><span>Q3</span><strong>{_format_manwon(float(metrics['q3']))}</strong></div>
                <div><span>IQR 상한</span><strong>약 {_format_manwon(float(metrics['upper_bound']), 1)}</strong></div>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    decision_column, impact_column = st.columns(2, gap="medium")
    with decision_column:
        st.markdown(
            f"""
            <section class="preprocess-outlier-card">
                <p class="preprocess-outlier-card-title">이상치 검토</p>
                <div class="preprocess-outlier-number">
                    <strong>{metrics['outlier_count']:,}건</strong>
                    <span>전체의 약 {metrics['outlier_ratio']:.2f}%</span>
                </div>
                <p class="preprocess-outlier-decision">분석에서 유지</p>
                <p class="preprocess-outlier-copy">
                    이상치 후보라고 해서 제거하지 않았습니다. 실제 보이스피싱의 고액 피해일
                    가능성이 있고, 단순 입력 오류라고 판단할 근거가 없기 때문입니다.
                </p>
            </section>
            """,
            unsafe_allow_html=True,
        )

    with impact_column:
        st.markdown(
            f"""
            <section class="preprocess-outlier-card">
                <p class="preprocess-outlier-card-title">평균에 미치는 영향</p>
                <div class="preprocess-average-flow">
                    <div><span>전체 평균</span><strong>약 {_format_manwon(float(metrics['mean_amount']))}</strong></div>
                    <b aria-hidden="true">↓</b>
                    <div><span>후보 제외 평균</span><strong>약 {_format_manwon(float(metrics['without_outlier_mean']))}</strong></div>
                    <p>약 {metrics['reduction_rate']:.2f}% 감소</p>
                </div>
                <p class="preprocess-outlier-copy">
                    일부 고액 피해사례가 평균에 큰 영향을 주어, 이후 피해금액 분석에서는
                    평균만 단독으로 사용하지 않고 중앙값과 사분위수를 함께 확인했습니다.
                </p>
            </section>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <aside class="preprocess-completion-note">
            <strong>전처리 완료</strong>
            <span>→ 정리된 분석 데이터를 📊 피해 현황 및 특성 분석에 활용했습니다.</span>
        </aside>
        """,
        unsafe_allow_html=True,
    )


def render_preprocessing() -> None:
    """경찰청·우체국 데이터의 분석용 전처리 과정을 표시합니다."""
    with st.container(key="analysis_container"):
        _render_process_strip()

        police_column, postal_column = st.columns(2, gap="medium")
        with police_column:
            _render_police_preprocessing()
        with postal_column:
            _render_postal_preprocessing()

        try:
            outlier_metrics = calculate_postal_outlier_metrics()
        except FileNotFoundError:
            st.error(
                "우체국 데이터 파일을 찾을 수 없습니다. "
                f"확인 파일: `{POSTAL_DATA_RELATIVE_PATH.as_posix()}`"
            )
            return
        except (UnicodeDecodeError, pd.errors.ParserError, ValueError) as error:
            st.error(f"피해금액 이상치 검토 데이터를 계산할 수 없습니다: {error}")
            return

        _render_outlier_review(outlier_metrics)
