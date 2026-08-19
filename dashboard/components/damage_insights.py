from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[2]
POLICE_DATA_RELATIVE_PATH = Path(
    "c_이종열/데이터/경찰청_보이스피싱 현황_20251231.csv"
)
POLICE_DATA_PATH = PROJECT_ROOT / POLICE_DATA_RELATIVE_PATH

SOURCE_YEAR_COLUMN = "구분"
COUNT_COLUMNS = ("기관사칭형_발생건수", "대출사기형_발생건수")
AMOUNT_COLUMNS = ("기관사칭형_피해액_억원", "대출사기형_피해액_억원")
REQUIRED_COLUMNS = (SOURCE_YEAR_COLUMN, *COUNT_COLUMNS, *AMOUNT_COLUMNS)
FRAUD_TYPE_COLUMNS = (
    ("기관사칭형", COUNT_COLUMNS[0], AMOUNT_COLUMNS[0]),
    ("대출사기형", COUNT_COLUMNS[1], AMOUNT_COLUMNS[1]),
)
FRAUD_TYPE_COLORS = {
    "기관사칭형": "#1f5fae",
    "대출사기형": "#2f7d78",
}
TYPE_CUMULATIVE_PERIOD = "2016~2025년 누적"
TYPE_LATEST_PERIOD = "2025년"
TYPE_PERIOD_LABELS = (TYPE_CUMULATIVE_PERIOD, TYPE_LATEST_PERIOD)
TYPE_PERIOD_Y_POSITIONS = {TYPE_CUMULATIVE_PERIOD: 1, TYPE_LATEST_PERIOD: 0}


def load_police_trend_data() -> pd.DataFrame:
    """Notebook과 같은 계산으로 경찰청 P1·P2 연도별 데이터를 만듭니다."""
    raw_data = pd.read_csv(POLICE_DATA_PATH, encoding="cp949")
    raw_data.columns = raw_data.columns.str.strip()

    for column in raw_data.select_dtypes(include=["object", "string"]).columns:
        raw_data[column] = raw_data[column].str.strip()

    missing_columns = [
        column for column in REQUIRED_COLUMNS if column not in raw_data.columns
    ]
    if missing_columns:
        raise ValueError(f"필수 컬럼이 없습니다: {', '.join(missing_columns)}")

    trend_data = raw_data[list(REQUIRED_COLUMNS)].rename(
        columns={SOURCE_YEAR_COLUMN: "연도"}
    )
    for column in trend_data.columns:
        trend_data[column] = pd.to_numeric(trend_data[column], errors="coerce")

    invalid_columns = trend_data.columns[trend_data.isna().any()].tolist()
    if invalid_columns:
        raise ValueError(
            "숫자로 변환할 수 없는 값이 있습니다: " + ", ".join(invalid_columns)
        )

    # Notebook에서 확정한 대로 두 사기유형의 값을 더해 전체값을 생성합니다.
    trend_data["전체_발생건수"] = trend_data[list(COUNT_COLUMNS)].sum(axis=1)
    trend_data["전체_피해액_억원"] = trend_data[list(AMOUNT_COLUMNS)].sum(axis=1)
    trend_data["연도"] = trend_data["연도"].astype(int)
    trend_data = trend_data[
        ["연도", "전체_발생건수", "전체_피해액_억원"]
    ].sort_values("연도", ignore_index=True)

    expected_years = list(range(2016, 2026))
    if trend_data["연도"].tolist() != expected_years:
        raise ValueError("분석기간이 2016~2025년의 연속된 연도인지 확인해주세요.")

    return trend_data


def _format_amount(amount_eok: float) -> str:
    """억원 단위 값을 조·억 원 단위의 읽기 쉬운 문자열로 바꿉니다."""
    rounded_amount = int(round(amount_eok))
    if rounded_amount < 10_000:
        return f"{rounded_amount:,}억 원"

    trillion, eok = divmod(rounded_amount, 10_000)
    if eok == 0:
        return f"{trillion:,}조 원"
    return f"{trillion:,}조 {eok:,}억 원"


def _create_trend_figure(
    trend_data: pd.DataFrame,
    value_column: str,
    title: str,
    y_axis_title: str,
    hover_label: str,
    hover_unit: str,
) -> go.Figure:
    figure = go.Figure(
        go.Scatter(
            x=trend_data["연도"],
            y=trend_data[value_column],
            mode="lines+markers",
            line={"color": "#1f5fae", "width": 3},
            marker={"color": "#1f5fae", "size": 7},
            hovertemplate=(
                "<b>%{x}년</b><br>"
                f"{hover_label}: %{{y:,.0f}}{hover_unit}<extra></extra>"
            ),
        )
    )
    figure.update_layout(
        title={
            "text": title,
            "x": 0.01,
            "xanchor": "left",
            "font": {"color": "#172033", "size": 16},
        },
        height=260,
        margin={"l": 22, "r": 10, "t": 38, "b": 30},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#172033", "family": "Arial, sans-serif", "size": 12},
        hoverlabel={"bgcolor": "#ffffff", "font_color": "#172033"},
        showlegend=False,
    )
    figure.update_xaxes(
        title="연도",
        tickmode="array",
        tickvals=trend_data["연도"],
        ticktext=[str(year) for year in trend_data["연도"]],
        title_font={"color": "#172033", "size": 12},
        tickfont={"color": "#172033", "size": 11},
        automargin=True,
        showgrid=False,
        linecolor="#dce4ee",
    )
    figure.update_yaxes(
        title=y_axis_title,
        tickformat=",",
        rangemode="tozero",
        title_font={"color": "#172033", "size": 12},
        tickfont={"color": "#172033", "size": 11},
        automargin=True,
        showgrid=True,
        gridcolor="rgba(101,113,135,0.24)",
        zeroline=False,
    )
    return figure


def _build_count_insight(trend_data: pd.DataFrame) -> str:
    peak = trend_data.loc[trend_data["전체_발생건수"].idxmax()]
    recent = trend_data.tail(3).reset_index(drop=True)
    recent_is_increasing = recent["전체_발생건수"].is_monotonic_increasing

    if recent_is_increasing:
        return (
            f"{int(peak['연도'])}년 {int(peak['전체_발생건수']):,}건으로 "
            f"가장 많았으며, {int(recent.loc[0, '연도'])}년까지 감소한 뒤 "
            f"{int(recent.loc[1, '연도'])}~{int(recent.loc[2, '연도'])}년 "
            "다시 증가했습니다."
        )

    return (
        f"분석기간 중 발생건수는 {int(peak['연도'])}년 "
        f"{int(peak['전체_발생건수']):,}건으로 가장 많았습니다."
    )


def _build_amount_insight(trend_data: pd.DataFrame) -> str:
    peak = trend_data.loc[trend_data["전체_피해액_억원"].idxmax()]
    latest = trend_data.iloc[-1]

    if int(peak["연도"]) == int(latest["연도"]):
        return (
            f"{int(latest['연도'])}년 피해금액은 "
            f"{_format_amount(latest['전체_피해액_억원'])}으로 "
            "분석기간 중 가장 큰 규모를 기록했습니다."
        )

    return (
        f"분석기간 중 피해금액은 {int(peak['연도'])}년 "
        f"{_format_amount(peak['전체_피해액_억원'])}으로 가장 컸습니다."
    )


def load_police_type_data() -> pd.DataFrame:
    """원본 집계에서 누적·2025년 사기유형별 값과 비중을 계산합니다."""
    raw_data = pd.read_csv(POLICE_DATA_PATH, encoding="cp949")
    raw_data.columns = raw_data.columns.str.strip()

    for column in raw_data.select_dtypes(include=["object", "string"]).columns:
        raw_data[column] = raw_data[column].str.strip()

    missing_columns = [
        column for column in REQUIRED_COLUMNS if column not in raw_data.columns
    ]
    if missing_columns:
        raise ValueError(f"필수 컬럼이 없습니다: {', '.join(missing_columns)}")

    type_data = raw_data[list(REQUIRED_COLUMNS)].rename(
        columns={SOURCE_YEAR_COLUMN: "연도"}
    )
    for column in type_data.columns:
        type_data[column] = pd.to_numeric(type_data[column], errors="coerce")

    invalid_columns = type_data.columns[type_data.isna().any()].tolist()
    if invalid_columns:
        raise ValueError(
            "숫자로 변환할 수 없는 값이 있습니다: " + ", ".join(invalid_columns)
        )

    type_data["연도"] = type_data["연도"].astype(int)
    type_data = type_data.sort_values("연도", ignore_index=True)
    expected_years = list(range(2016, 2026))
    if type_data["연도"].tolist() != expected_years:
        raise ValueError("분석기간이 2016~2025년의 연속된 연도인지 확인해주세요.")

    period_data = (
        (TYPE_CUMULATIVE_PERIOD, type_data),
        (TYPE_LATEST_PERIOD, type_data[type_data["연도"] == 2025]),
    )
    records = []
    for period_label, period_rows in period_data:
        count_total = period_rows[list(COUNT_COLUMNS)].sum().sum()
        amount_total = period_rows[list(AMOUNT_COLUMNS)].sum().sum()
        if count_total <= 0 or amount_total <= 0:
            raise ValueError("사기유형 비중을 계산할 전체값이 0 이하입니다.")

        for fraud_type, count_column, amount_column in FRAUD_TYPE_COLUMNS:
            count_value = period_rows[count_column].sum()
            amount_value = period_rows[amount_column].sum()
            records.append(
                {
                    "기간": period_label,
                    "사기유형": fraud_type,
                    "발생건수": count_value,
                    "피해금액_억원": amount_value,
                    "발생건수_비중": count_value / count_total * 100,
                    "피해금액_비중": amount_value / amount_total * 100,
                }
            )

    return pd.DataFrame.from_records(records)


def _create_type_share_figure(
    type_data: pd.DataFrame,
    value_column: str,
    share_column: str,
    title: str,
    value_unit: str,
) -> go.Figure:
    figure = go.Figure()
    for fraud_type, _, _ in FRAUD_TYPE_COLUMNS:
        type_rows = (
            type_data[type_data["사기유형"] == fraud_type]
            .set_index("기간")
            .loc[list(TYPE_PERIOD_LABELS)]
            .reset_index()
        )
        share_labels = [
            f"{fraud_type}<br>{share:.1f}%" for share in type_rows[share_column]
        ]
        figure.add_bar(
            name=fraud_type,
            y=[TYPE_PERIOD_Y_POSITIONS[period] for period in type_rows["기간"]],
            x=type_rows[share_column],
            orientation="h",
            marker={"color": FRAUD_TYPE_COLORS[fraud_type]},
            text=share_labels,
            textposition="inside",
            insidetextanchor="middle",
            textfont={"color": "#ffffff", "size": 10},
            hovertext=type_rows["기간"],
            customdata=type_rows[[value_column, share_column]].to_numpy(),
            hovertemplate=(
                "<b>%{hovertext}</b><br>"
                f"{fraud_type}<br>"
                f"%{{customdata[0]:,.0f}}{value_unit}<br>"
                "%{customdata[1]:.2f}%<extra></extra>"
            ),
        )

    figure.update_layout(
        title={
            "text": title,
            "x": 0.01,
            "xanchor": "left",
            "font": {"color": "#172033", "size": 15},
        },
        height=235,
        margin={"l": 20, "r": 10, "t": 42, "b": 34},
        barmode="stack",
        bargap=0.35,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#172033", "family": "Arial, sans-serif", "size": 12},
        hoverlabel={"bgcolor": "#ffffff", "font_color": "#172033"},
        showlegend=False,
        uniformtext={"minsize": 9, "mode": "show"},
    )
    figure.update_xaxes(
        title="비중",
        range=[0, 100],
        tickmode="array",
        tickvals=[0, 25, 50, 75, 100],
        ticksuffix="%",
        title_font={"color": "#172033", "size": 12},
        tickfont={"color": "#172033", "size": 11},
        automargin=True,
        showgrid=True,
        gridcolor="rgba(101,113,135,0.20)",
        zeroline=False,
    )
    figure.update_yaxes(
        tickmode="array",
        tickvals=[0, 1],
        ticktext=list(reversed(TYPE_PERIOD_LABELS)),
        range=[-0.55, 1.55],
        tickfont={"color": "#172033", "size": 11},
        automargin=True,
        showgrid=False,
    )
    return figure


def _build_type_insight(type_data: pd.DataFrame) -> str:
    cumulative = type_data[type_data["기간"] == TYPE_CUMULATIVE_PERIOD]
    latest = type_data[type_data["기간"] == TYPE_LATEST_PERIOD]
    cumulative_loan = cumulative[cumulative["사기유형"] == "대출사기형"].iloc[0]
    latest_impersonation = latest[latest["사기유형"] == "기관사칭형"].iloc[0]

    return (
        "2016~2025년 누적에서는 대출사기형이 "
        f"발생건수 약 {cumulative_loan['발생건수_비중']:.1f}%, "
        f"피해금액 약 {cumulative_loan['피해금액_비중']:.1f}%로 "
        "더 큰 비중을 차지했습니다. 반면 2025년에는 기관사칭형이 "
        f"발생건수 약 {latest_impersonation['발생건수_비중']:.1f}%, "
        f"피해금액 약 {latest_impersonation['피해금액_비중']:.1f}%로 "
        "더 큰 비중을 보였습니다. 특히 피해금액에서 누적 구조와 "
        "2025년 구조의 차이가 크게 나타났습니다."
    )


def render_damage_insights() -> None:
    """피해 현황 페이지의 경찰청 P1·P2·P3 콘텐츠를 표시합니다."""
    with st.container(key="analysis_container"):
        try:
            trend_data = load_police_trend_data()
        except FileNotFoundError:
            st.error(
                "경찰청 데이터 파일을 찾을 수 없습니다. "
                f"확인 파일: `{POLICE_DATA_RELATIVE_PATH.as_posix()}`"
            )
            return
        except (UnicodeDecodeError, pd.errors.ParserError, ValueError) as error:
            st.error(f"P1·P2 계산에 필요한 경찰청 데이터를 확인할 수 없습니다: {error}")
            return

        try:
            type_data = load_police_type_data()
        except FileNotFoundError:
            st.error(
                "경찰청 데이터 파일을 찾을 수 없습니다. "
                f"확인 파일: `{POLICE_DATA_RELATIVE_PATH.as_posix()}`"
            )
            return
        except (UnicodeDecodeError, pd.errors.ParserError, ValueError) as error:
            st.error(f"P3 계산에 필요한 경찰청 데이터를 확인할 수 없습니다: {error}")
            return

        latest = trend_data.iloc[-1]
        latest_type_data = type_data[type_data["기간"] == TYPE_LATEST_PERIOD]
        latest_type_data = latest_type_data.set_index("사기유형")
        latest_impersonation = latest_type_data.loc["기관사칭형"]
        latest_loan = latest_type_data.loc["대출사기형"]

        st.markdown(
            f"""
            <section class="police-summary-strip">
                <div class="police-summary-grid">
                    <div class="police-summary-item">
                        <p class="police-summary-label">전체 발생건수</p>
                        <p class="police-summary-value">{int(latest['전체_발생건수']):,}건</p>
                    </div>
                    <div class="police-summary-item">
                        <p class="police-summary-label">전체 피해금액</p>
                        <p class="police-summary-value">{_format_amount(latest['전체_피해액_억원'])}</p>
                    </div>
                    <div class="police-summary-item">
                        <p class="police-summary-label">기관사칭형 발생비중</p>
                        <p class="police-summary-value">{latest_impersonation['발생건수_비중']:.1f}%</p>
                        <p class="police-summary-secondary">
                            대출사기형 {latest_loan['발생건수_비중']:.1f}%
                        </p>
                    </div>
                    <div class="police-summary-item">
                        <p class="police-summary-label">기관사칭형 피해비중</p>
                        <p class="police-summary-value">{latest_impersonation['피해금액_비중']:.1f}%</p>
                        <p class="police-summary-secondary">
                            대출사기형 {latest_loan['피해금액_비중']:.1f}%
                        </p>
                    </div>
                </div>
            </section>
            """,
            unsafe_allow_html=True,
        )

        chart_config = {"displayModeBar": False, "responsive": True}
        police_overview_column, police_type_column = st.columns(2, gap="medium")

        with police_overview_column:
            st.markdown(
                """
                <header class="analysis-section-header police-trend-header">
                    <p class="analysis-source">경찰청 집계통계 · 2016~2025</p>
                    <h2>대한민국 보이스피싱 피해 현황</h2>
                    <p>
                        경찰청 연도별 통계를 통해 보이스피싱 발생건수와 금전적 피해 규모의
                        변화를 함께 확인합니다.
                    </p>
                </header>
                """,
                unsafe_allow_html=True,
            )

            count_figure = _create_trend_figure(
                trend_data,
                "전체_발생건수",
                "연도별 보이스피싱 발생건수",
                "발생건수(건)",
                "발생건수",
                "건",
            )
            amount_figure = _create_trend_figure(
                trend_data,
                "전체_피해액_억원",
                "연도별 보이스피싱 피해금액",
                "피해금액(억원)",
                "피해금액",
                "억 원",
            )

            with st.container(key="police_count_chart", gap="small"):
                st.plotly_chart(
                    count_figure,
                    width="stretch",
                    theme=None,
                    config=chart_config,
                )
                st.caption(_build_count_insight(trend_data))

            with st.container(key="police_amount_chart", gap="small"):
                st.plotly_chart(
                    amount_figure,
                    width="stretch",
                    theme=None,
                    config=chart_config,
                )
                st.caption(_build_amount_insight(trend_data))

            st.markdown(
                """
                <aside class="analysis-insight police-trend-insight">
                    <strong>종합 인사이트</strong>
                    <p>
                        발생건수와 피해금액은 항상 같은 방향으로 움직이지 않습니다.
                        따라서 보이스피싱의 심각성을 파악할 때는 사건 수뿐 아니라
                        금전적 피해 규모도 함께 살펴볼 필요가 있습니다.
                    </p>
                </aside>
                """,
                unsafe_allow_html=True,
            )

        with police_type_column:
            st.markdown(
                """
                <header class="analysis-section-header">
                    <p class="analysis-source">경찰청 집계통계 · 사기유형 비교</p>
                    <h2>사기유형별 피해 구조</h2>
                    <p>
                        2016~2025년 누적 구조와 2025년의 기관사칭형·대출사기형
                        비중을 비교합니다.
                    </p>
                </header>
                """,
                unsafe_allow_html=True,
            )

            count_share_figure = _create_type_share_figure(
                type_data,
                "발생건수",
                "발생건수_비중",
                "사기유형별 발생건수 비중",
                "건",
            )
            amount_share_figure = _create_type_share_figure(
                type_data,
                "피해금액_억원",
                "피해금액_비중",
                "사기유형별 피해금액 비중",
                "억 원",
            )

            st.plotly_chart(
                count_share_figure,
                width="stretch",
                theme=None,
                config=chart_config,
            )

            st.plotly_chart(
                amount_share_figure,
                width="stretch",
                theme=None,
                config=chart_config,
            )

            st.markdown(
                f"""
                <aside class="analysis-insight">
                    <strong>핵심 인사이트</strong>
                    <p>{_build_type_insight(type_data)}</p>
                </aside>
                """,
                unsafe_allow_html=True,
            )
