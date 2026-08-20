import math
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots


PROJECT_ROOT = Path(__file__).resolve().parents[2]
POLICE_DATA_RELATIVE_PATH = Path(
    "c_이종열/데이터/경찰청_보이스피싱 현황_20251231.csv"
)
POLICE_DATA_PATH = PROJECT_ROOT / POLICE_DATA_RELATIVE_PATH
POLICE_AGE_DATA_RELATIVE_PATH = Path(
    "c_이종열/데이터/경찰청_전화금융사기 피해자 연령별 현황_20251231.csv"
)
POLICE_AGE_DATA_PATH = PROJECT_ROOT / POLICE_AGE_DATA_RELATIVE_PATH
POSTAL_DATA_RELATIVE_PATH = Path("c_이종열/데이터/df_postal.csv")
POSTAL_DATA_PATH = PROJECT_ROOT / POSTAL_DATA_RELATIVE_PATH

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
POLICE_AGE_SOURCE_COLUMNS = (
    "20대이하",
    "30대",
    "40대",
    "50대",
    "60대",
    "70대이상",
)
POLICE_AGE_LABELS = {
    "20대이하": "20대 이하",
    "30대": "30대",
    "40대": "40대",
    "50대": "50대",
    "60대": "60대",
    "70대이상": "70대 이상",
}
POLICE_AGE_PERIODS = ("2016년", "2025년", "2016~2025년 누적")
POLICE_AGE_COLORS = {
    "20대 이하": "#4778a7",
    "30대": "#2f6497",
    "40대": "#173f73",
    "50대": "#2f7d78",
    "60대": "#3f6f55",
    "70대 이상": "#626b3f",
}
POSTAL_AGE_ORDER = ("20대", "30대", "40대", "50대", "60대", "70대")
POSTAL_REQUIRED_COLUMNS = (
    "연령대",
    "피해액",
    "사기유형",
    "사칭기관",
    "전화_보이스피싱",
    "중복후보",
)
WON_PER_MANWON = 10_000
WON_PER_EOK = 100_000_000


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


def load_police_age_data() -> pd.DataFrame:
    """경찰청 원본에서 연도별·누적 연령대 피해자 구성비를 계산합니다."""
    raw_data = pd.read_csv(POLICE_AGE_DATA_PATH, encoding="cp949")
    raw_data.columns = raw_data.columns.str.strip()

    required_columns = (SOURCE_YEAR_COLUMN, *POLICE_AGE_SOURCE_COLUMNS)
    missing_columns = [
        column for column in required_columns if column not in raw_data.columns
    ]
    if missing_columns:
        raise ValueError(f"필수 컬럼이 없습니다: {', '.join(missing_columns)}")

    age_data = raw_data[list(required_columns)].rename(
        columns={SOURCE_YEAR_COLUMN: "연도"}
    )
    for column in age_data.columns:
        age_data[column] = pd.to_numeric(age_data[column], errors="coerce")

    invalid_columns = age_data.columns[age_data.isna().any()].tolist()
    if invalid_columns:
        raise ValueError(
            "숫자로 변환할 수 없는 값이 있습니다: " + ", ".join(invalid_columns)
        )

    age_data["연도"] = age_data["연도"].astype(int)
    age_data = age_data.sort_values("연도", ignore_index=True)
    expected_years = list(range(2016, 2026))
    if age_data["연도"].tolist() != expected_years:
        raise ValueError("연령 데이터의 분석기간이 2016~2025년인지 확인해주세요.")
    if age_data[list(POLICE_AGE_SOURCE_COLUMNS)].le(0).any().any():
        raise ValueError("연령대별 피해자 수에 0 이하인 값이 있습니다.")

    annual_long = age_data.melt(
        id_vars="연도",
        value_vars=list(POLICE_AGE_SOURCE_COLUMNS),
        var_name="원본_연령대",
        value_name="피해자수",
    )
    annual_totals = age_data.set_index("연도")[
        list(POLICE_AGE_SOURCE_COLUMNS)
    ].sum(axis=1)
    annual_long["전체_피해자수"] = annual_long["연도"].map(annual_totals)
    annual_long["구성비"] = (
        annual_long["피해자수"] / annual_long["전체_피해자수"] * 100
    )
    annual_long["기간"] = annual_long["연도"].astype(str) + "년"

    cumulative_counts = age_data[list(POLICE_AGE_SOURCE_COLUMNS)].sum()
    cumulative_total = cumulative_counts.sum()
    cumulative_long = pd.DataFrame(
        {
            "연도": pd.NA,
            "원본_연령대": cumulative_counts.index,
            "피해자수": cumulative_counts.to_numpy(),
            "전체_피해자수": cumulative_total,
            "구성비": cumulative_counts.to_numpy() / cumulative_total * 100,
            "기간": POLICE_AGE_PERIODS[-1],
        }
    )

    result = pd.concat([annual_long, cumulative_long], ignore_index=True)
    result["연령대"] = result["원본_연령대"].map(POLICE_AGE_LABELS)
    return result[
        ["연도", "기간", "연령대", "피해자수", "전체_피해자수", "구성비"]
    ]


def _format_amount(amount_eok: float) -> str:
    """억원 단위 값을 조·억 원 단위의 읽기 쉬운 문자열로 바꿉니다."""
    rounded_amount = int(round(amount_eok))
    if rounded_amount < 10_000:
        return f"{rounded_amount:,}억 원"

    trillion, eok = divmod(rounded_amount, 10_000)
    if eok == 0:
        return f"{trillion:,}조 원"
    return f"{trillion:,}조 {eok:,}억 원"


def _format_won_as_manwon(amount_won: float) -> str:
    """원 단위 피해액을 대시보드용 억·만원 문자열로 변환합니다."""
    rounded_manwon = int(round(amount_won / WON_PER_MANWON))
    if rounded_manwon < 10_000:
        return f"{rounded_manwon:,}만원"

    eok, manwon = divmod(rounded_manwon, 10_000)
    if manwon == 0:
        return f"{eok:,}억 원"
    return f"{eok:,}억 {manwon:,}만원"


def _create_damage_trend_figure(trend_data: pd.DataFrame) -> go.Figure:
    """발생건수와 피해금액 추세를 공통 연도축의 상하 그래프로 구성합니다."""
    amount_tick_step = 5_000
    max_amount = trend_data["전체_피해액_억원"].max()
    # 최대값이 경계와 같아도 막대 위에 한 눈금의 여유가 생기도록 올립니다.
    amount_axis_max = (
        math.floor(max_amount / amount_tick_step) + 1
    ) * amount_tick_step
    amount_tick_values = list(
        range(0, amount_axis_max + amount_tick_step, amount_tick_step)
    )

    figure = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.14,
        subplot_titles=("발생건수", "피해금액"),
    )
    figure.add_trace(
        go.Scatter(
            x=trend_data["연도"],
            y=trend_data["전체_발생건수"],
            mode="lines+markers",
            line={"color": "#1f5fae", "width": 3},
            marker={"color": "#1f5fae", "size": 7},
            hovertemplate=(
                "<b>%{x}년</b><br>"
                "발생건수: %{y:,.0f}건<extra></extra>"
            ),
        ),
        row=1,
        col=1,
    )
    figure.add_trace(
        go.Bar(
            x=trend_data["연도"],
            y=trend_data["전체_피해액_억원"],
            marker={"color": "#1f5fae"},
            opacity=0.78,
            hovertemplate=(
                "<b>%{x}년</b><br>"
                "피해금액: %{y:,.0f}억 원<extra></extra>"
            ),
        ),
        row=2,
        col=1,
    )
    figure.update_layout(
        title={
            "text": "연도별 보이스피싱 피해 추세",
            "x": 0.01,
            "xanchor": "left",
            "font": {"color": "#172033", "size": 16},
        },
        height=415,
        margin={"l": 22, "r": 10, "t": 58, "b": 32},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#172033", "family": "Arial, sans-serif", "size": 12},
        hoverlabel={"bgcolor": "#ffffff", "font_color": "#172033"},
        showlegend=False,
        bargap=0.3,
    )
    figure.update_annotations(font={"color": "#172033", "size": 12})
    figure.update_xaxes(
        tickmode="array",
        tickvals=trend_data["연도"],
        ticktext=[str(year) for year in trend_data["연도"]],
        tickfont={"color": "#172033", "size": 11},
        automargin=True,
        showgrid=False,
        linecolor="#dce4ee",
        showticklabels=False,
        row=1,
        col=1,
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
        row=2,
        col=1,
    )
    for row, y_axis_title in ((1, "발생건수(건)"), (2, "피해금액(억원)")):
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
            row=row,
            col=1,
        )
    figure.update_yaxes(
        range=[0, amount_axis_max],
        tickmode="array",
        tickvals=amount_tick_values,
        row=2,
        col=1,
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


def _create_type_structure_figure(type_data: pd.DataFrame) -> go.Figure:
    """발생건수와 피해금액의 사기유형 비중을 한 Figure로 구성합니다."""
    metric_specs = (
        ("발생건수 비중", "발생건수", "발생건수_비중", "건"),
        ("피해금액 비중", "피해금액_억원", "피해금액_비중", "억 원"),
    )
    figure = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.16,
        subplot_titles=tuple(spec[0] for spec in metric_specs),
    )

    for row, (_, value_column, share_column, value_unit) in enumerate(
        metric_specs, start=1
    ):
        for fraud_type, _, _ in FRAUD_TYPE_COLUMNS:
            type_rows = (
                type_data[type_data["사기유형"] == fraud_type]
                .set_index("기간")
                .loc[list(TYPE_PERIOD_LABELS)]
                .reset_index()
            )
            share_labels = [
                f"{fraud_type}<br>{share:.1f}%"
                for share in type_rows[share_column]
            ]
            figure.add_trace(
                go.Bar(
                    name=fraud_type,
                    y=[
                        TYPE_PERIOD_Y_POSITIONS[period]
                        for period in type_rows["기간"]
                    ],
                    x=type_rows[share_column],
                    orientation="h",
                    marker={"color": FRAUD_TYPE_COLORS[fraud_type]},
                    text=share_labels,
                    textposition="inside",
                    insidetextanchor="middle",
                    textfont={"color": "#ffffff", "size": 10},
                    hovertext=type_rows["기간"],
                    customdata=type_rows[
                        [value_column, share_column]
                    ].to_numpy(),
                    hovertemplate=(
                        "<b>%{hovertext}</b><br>"
                        f"{fraud_type}<br>"
                        f"%{{customdata[0]:,.0f}}{value_unit}<br>"
                        "%{customdata[1]:.2f}%<extra></extra>"
                    ),
                ),
                row=row,
                col=1,
            )

    figure.update_layout(
        height=390,
        margin={"l": 20, "r": 10, "t": 34, "b": 34},
        barmode="stack",
        bargap=0.35,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#172033", "family": "Arial, sans-serif", "size": 12},
        hoverlabel={"bgcolor": "#ffffff", "font_color": "#172033"},
        showlegend=False,
        uniformtext={"minsize": 9, "mode": "show"},
    )
    figure.update_annotations(font={"color": "#172033", "size": 12})
    figure.update_xaxes(
        range=[0, 100],
        tickmode="array",
        tickvals=[0, 25, 50, 75, 100],
        ticksuffix="%",
        tickfont={"color": "#172033", "size": 11},
        automargin=True,
        showgrid=True,
        gridcolor="rgba(101,113,135,0.20)",
        zeroline=False,
    )
    figure.update_xaxes(showticklabels=False, row=1, col=1)
    figure.update_xaxes(
        title="비중",
        showticklabels=True,
        title_font={"color": "#172033", "size": 12},
        row=2,
        col=1,
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


def _create_police_age_comparison_figure(age_data: pd.DataFrame) -> go.Figure:
    """2016년·2025년·누적 피해자 연령 구성을 100% 누적 막대로 비교합니다."""
    figure = go.Figure()
    for age_group in POLICE_AGE_LABELS.values():
        age_group_data = (
            age_data[age_data["연령대"].eq(age_group)]
            .set_index("기간")
            .loc[list(POLICE_AGE_PERIODS)]
            .reset_index()
        )
        segment_labels = []
        for share in age_group_data["구성비"]:
            if share >= 10:
                segment_labels.append(f"{age_group}<br>{share:.1f}%")
            elif share >= 5:
                segment_labels.append(f"{share:.1f}%")
            else:
                segment_labels.append("")

        figure.add_trace(
            go.Bar(
                name=age_group,
                x=age_group_data["구성비"],
                y=age_group_data["기간"],
                customdata=age_group_data[["피해자수", "구성비"]].to_numpy(),
                orientation="h",
                marker={
                    "color": POLICE_AGE_COLORS[age_group],
                    "line": {"color": "#ffffff", "width": 1},
                },
                text=segment_labels,
                textposition="inside",
                insidetextanchor="middle",
                textfont={"color": "#ffffff", "size": 10},
                hovertemplate=(
                    "<b>%{y}</b><br>"
                    f"연령대: {age_group}<br><br>"
                    "피해자 수: %{customdata[0]:,.0f}명<br>"
                    "전체 피해자 중 구성비: %{customdata[1]:.2f}%"
                    "<extra></extra>"
                ),
            )
        )

    figure.update_layout(
        title={
            "text": "연령대별 피해자 구성 비교",
            "x": 0.01,
            "xanchor": "left",
            "font": {"color": "#172033", "size": 16},
        },
        height=285,
        margin={"l": 12, "r": 8, "t": 88, "b": 42},
        barmode="stack",
        bargap=0.34,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#172033", "family": "Arial, sans-serif", "size": 11},
        hoverlabel={"bgcolor": "#ffffff", "font_color": "#172033"},
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.14,
            "xanchor": "left",
            "x": 0,
            "font": {"size": 10},
            "traceorder": "normal",
        },
        uniformtext={"minsize": 9, "mode": "hide"},
    )
    figure.update_xaxes(
        title="피해자 구성비",
        range=[0, 100],
        tickmode="array",
        tickvals=[0, 25, 50, 75, 100],
        ticksuffix="%",
        title_font={"color": "#172033", "size": 11},
        tickfont={"color": "#172033", "size": 10},
        automargin=True,
        showgrid=True,
        gridcolor="rgba(101,113,135,0.20)",
        zeroline=False,
    )
    # Plotly의 범주형 y축은 첫 범주가 아래에 오므로 축을 뒤집어 과거→최근→누적으로 표시합니다.
    figure.update_yaxes(
        categoryorder="array",
        categoryarray=list(POLICE_AGE_PERIODS),
        autorange="reversed",
        tickfont={"color": "#172033", "size": 10},
        automargin=True,
        showgrid=False,
        zeroline=False,
        title=None,
    )
    return figure


def _build_police_age_insight(age_data: pd.DataFrame) -> str:
    cumulative = age_data[age_data["기간"].eq(POLICE_AGE_PERIODS[-1])]
    largest_group = cumulative.loc[cumulative["구성비"].idxmax()]
    return (
        f"2016~2025년 누적에서는 {largest_group['연령대']}가 전체 피해자 중 "
        f"{largest_group['구성비']:.2f}%로 가장 큰 비중을 차지했습니다. "
        "2016년과 2025년의 구성을 비교하면 일부 연령대의 비중이 달라져, "
        "피해자 연령 구성이 고정되어 있지 않음을 확인할 수 있습니다."
    )


def load_postal_damage_data() -> pd.DataFrame:
    """Notebook과 동일한 조건으로 우체국 피해금액 분석표본을 만듭니다."""
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

    # Notebook의 분석대상과 같이 전화 보이스피싱에서 투자사기·중복후보를 제외합니다.
    phone_mask = (
        raw_data["전화_보이스피싱"]
        .astype("string")
        .str.lower()
        .eq("true")
    )
    investment_mask = raw_data["사기유형"].eq("투자사기")
    duplicate_candidate_mask = (
        raw_data["중복후보"].astype("string").str.lower().eq("true")
    )
    damage_data = raw_data.loc[
        phone_mask & ~investment_mask & ~duplicate_candidate_mask,
        ["연령대", "피해액", "사기유형", "사칭기관"],
    ].copy()

    if damage_data.empty:
        raise ValueError("우체국 피해금액 분석대상이 없습니다.")
    if damage_data["피해액"].le(0).any():
        raise ValueError("피해액이 0원 이하인 행이 있습니다.")

    age_numbers = pd.to_numeric(damage_data["연령대"], errors="coerce")
    if age_numbers.isna().any():
        raise ValueError("연령대를 숫자로 변환할 수 없는 행이 있습니다.")
    damage_data["연령대"] = age_numbers.astype(int).astype(str) + "대"
    unexpected_ages = sorted(set(damage_data["연령대"]) - set(POSTAL_AGE_ORDER))
    if unexpected_ages:
        raise ValueError(f"예상하지 못한 연령대가 있습니다: {', '.join(unexpected_ages)}")

    damage_data["피해액_억원"] = damage_data["피해액"] / WON_PER_EOK
    return damage_data.reset_index(drop=True)


def _create_postal_damage_distribution_figure(
    damage_data: pd.DataFrame,
) -> go.Figure:
    """우체국 분석표본의 피해금액 분포를 가로형 boxplot으로 표시합니다."""
    max_amount_eok = damage_data["피해액_억원"].max()
    axis_max_eok = math.floor(max_amount_eok) + 1
    tick_values = list(range(0, axis_max_eok + 1))
    tick_labels = ["0", *[f"{value}억" for value in tick_values[1:]]]

    figure = go.Figure(
        go.Box(
            x=damage_data["피해액_억원"],
            customdata=damage_data["피해액"],
            orientation="h",
            quartilemethod="linear",
            boxpoints="outliers",
            jitter=0,
            line={"color": "#1f5fae", "width": 2},
            fillcolor="rgba(31,95,174,0.20)",
            marker={"color": "#1f5fae", "size": 6},
            hovertemplate=(
                "피해금액: %{customdata:,.0f}원<extra></extra>"
            ),
        )
    )
    figure.update_layout(
        height=250,
        margin={"l": 8, "r": 8, "t": 18, "b": 42},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#172033", "family": "Arial, sans-serif", "size": 12},
        hoverlabel={"bgcolor": "#ffffff", "font_color": "#172033"},
        showlegend=False,
    )
    figure.update_xaxes(
        title="피해금액",
        range=[0, axis_max_eok],
        tickmode="array",
        tickvals=tick_values,
        ticktext=tick_labels,
        title_font={"color": "#172033", "size": 12},
        tickfont={"color": "#172033", "size": 10},
        automargin=True,
        showgrid=True,
        gridcolor="rgba(101,113,135,0.20)",
        zeroline=False,
    )
    figure.update_yaxes(showticklabels=False, showgrid=False, zeroline=False)
    return figure


def _build_postal_damage_insight(damage_data: pd.DataFrame) -> str:
    median_amount = damage_data["피해액"].median()
    mean_amount = damage_data["피해액"].mean()
    return (
        f"중앙값은 {_format_won_as_manwon(median_amount)}이지만 평균은 약 "
        f"{_format_won_as_manwon(mean_amount)}으로 더 높아, 일부 고액 피해사례가 "
        "전체 평균을 크게 끌어올리는 오른쪽으로 치우친 분포가 나타났습니다."
    )


def _create_postal_age_median_figure(damage_data: pd.DataFrame) -> go.Figure:
    """우체국 표본의 연령대별 중앙 피해금액을 발표용 막대로 표시합니다."""
    age_summary = (
        damage_data.groupby("연령대", observed=False)["피해액"]
        .agg(표본수="size", 중앙값="median", 평균="mean")
        .reindex(POSTAL_AGE_ORDER)
    )
    if age_summary.isna().any().any():
        raise ValueError("연령대별 피해금액 요약에 필요한 표본이 없습니다.")

    age_summary = age_summary.reset_index()
    age_summary["중앙값_억원"] = age_summary["중앙값"] / WON_PER_EOK
    age_summary["표시값"] = age_summary["중앙값"].map(_format_won_as_manwon)

    figure = go.Figure(
        go.Bar(
            x=age_summary["연령대"],
            y=age_summary["중앙값_억원"],
            customdata=age_summary[["표본수", "중앙값", "평균"]].to_numpy(),
            marker={"color": "#1f5fae"},
            text=age_summary["표시값"],
            textposition="outside",
            cliponaxis=False,
            hovertemplate=(
                "<b>%{x}</b><br>"
                "표본 수: %{customdata[0]:,.0f}건<br>"
                "중앙값: %{customdata[1]:,.0f}원<br>"
                "평균: %{customdata[2]:,.0f}원<extra></extra>"
            ),
        )
    )
    figure.update_layout(
        title={
            "text": "연령대별 중앙 피해금액",
            "x": 0.01,
            "xanchor": "left",
            "font": {"color": "#172033", "size": 16},
        },
        height=285,
        margin={"l": 12, "r": 8, "t": 56, "b": 28},
        bargap=0.32,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#172033", "family": "Arial, sans-serif", "size": 11},
        hoverlabel={"bgcolor": "#ffffff", "font_color": "#172033"},
        showlegend=False,
    )
    figure.update_xaxes(
        title="연령대",
        categoryorder="array",
        categoryarray=list(POSTAL_AGE_ORDER),
        title_font={"color": "#172033", "size": 11},
        tickfont={"color": "#172033", "size": 10},
        automargin=True,
        showgrid=False,
        linecolor="#dce4ee",
    )
    figure.update_yaxes(
        title="중앙 피해금액",
        tickformat=".1f",
        ticksuffix="억",
        rangemode="tozero",
        title_font={"color": "#172033", "size": 11},
        tickfont={"color": "#172033", "size": 10},
        automargin=True,
        showgrid=True,
        gridcolor="rgba(101,113,135,0.20)",
        zeroline=False,
    )
    return figure


def _build_age_section_insight(
    police_age_data: pd.DataFrame,
    postal_damage_data: pd.DataFrame,
) -> str:
    """두 데이터의 역할과 U1 확정 결론을 구분해 연령 영역을 요약합니다."""
    police_insight = _build_police_age_insight(police_age_data)
    return (
        f"{police_insight} 우체국 실제 피해사례 {len(postal_damage_data):,}건에서도 "
        "연령대별 피해금액 분포 차이가 BH 보정 후 확인되었고 효과크기도 크게 "
        "나타났습니다. 다만 이는 특정 연령이 보이스피싱 위험이나 피해금액의 "
        "원인이라는 의미가 아니며, 연령을 단독 차단 기준으로 사용하지 않습니다."
    )


def _create_postal_category_damage_figure(
    damage_data: pd.DataFrame,
    category_column: str,
) -> go.Figure:
    """Notebook 순서대로 범주별 피해금액 분포와 표본 수를 표시합니다."""
    category_order = (
        damage_data.dropna(subset=[category_column, "피해액"])
        .groupby(category_column, observed=False)["피해액"]
        .median()
        .sort_values(ascending=False)
        .index.tolist()
    )
    category_counts = damage_data[category_column].value_counts()
    category_labels = {
        category: f"{category} (n={int(category_counts[category])})"
        for category in category_order
    }

    max_amount_eok = damage_data["피해액_억원"].max()
    axis_max_eok = math.floor(max_amount_eok) + 1
    tick_values = list(range(0, axis_max_eok + 1))
    tick_labels = ["0", *[f"{value}억" for value in tick_values[1:]]]
    figure_height = max(360, 46 * len(category_order) + 100)

    figure = go.Figure()
    for category in category_order:
        category_data = damage_data[damage_data[category_column].eq(category)]
        figure.add_trace(
            go.Box(
                name=category_labels[category],
                x=category_data["피해액_억원"],
                y=[category_labels[category]] * len(category_data),
                customdata=category_data[[category_column, "피해액"]].to_numpy(),
                orientation="h",
                quartilemethod="linear",
                boxpoints="outliers",
                jitter=0,
                line={"color": "#1f5fae", "width": 2},
                fillcolor="rgba(31,95,174,0.18)",
                marker={"color": "#1f5fae", "size": 5},
                hovertemplate=(
                    "<b>%{customdata[0]}</b><br>"
                    "피해금액: %{customdata[1]:,.0f}원<extra></extra>"
                ),
            )
        )

    figure.update_layout(
        height=figure_height,
        margin={"l": 8, "r": 8, "t": 18, "b": 42},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#172033", "family": "Arial, sans-serif", "size": 12},
        hoverlabel={"bgcolor": "#ffffff", "font_color": "#172033"},
        showlegend=False,
        boxgap=0.35,
    )
    figure.update_xaxes(
        title="피해금액",
        range=[0, axis_max_eok],
        tickmode="array",
        tickvals=tick_values,
        ticktext=tick_labels,
        title_font={"color": "#172033", "size": 12},
        tickfont={"color": "#172033", "size": 10},
        automargin=True,
        showgrid=True,
        gridcolor="rgba(101,113,135,0.20)",
        zeroline=False,
    )
    # Plotly 범주축은 아래에서 위로 배치되므로 Notebook 순서가 위에서 시작되도록 뒤집습니다.
    figure.update_yaxes(
        categoryorder="array",
        categoryarray=list(reversed([category_labels[item] for item in category_order])),
        tickfont={"color": "#172033", "size": 11},
        automargin=True,
        showgrid=False,
        zeroline=False,
    )
    return figure


def _build_postal_fraud_type_insight() -> str:
    return (
        "BH 다중검정 보정 후에도 사기유형별 피해금액 분포 차이가 확인되었으며 "
        "효과크기도 크게 나타났습니다. 다만 1~2건인 유형이 포함되어 있어 "
        "확정적인 피해위험 순위나 인과관계로 해석하지 않습니다."
    )


def _build_postal_institution_insight() -> str:
    return (
        "BH 다중검정 보정 후에도 사칭기관별 피해금액 분포 차이가 확인되었으며 "
        "효과크기도 크게 나타났습니다. 다만 일부 기관은 2~4건으로 표본이 작아 "
        "확정적인 피해위험 순위로 해석하지 않습니다."
    )


def _render_deep_analysis_summary_strip() -> None:
    """피해 특성 심층분석의 기존 검정 결과를 발표용으로 요약합니다."""
    st.markdown(
        """
        <section class="deep-summary-strip">
            <div class="deep-summary-grid">
                <div class="deep-summary-item">
                    <p class="deep-summary-label">사기유형별 피해금액</p>
                    <p class="deep-summary-value">통계적으로 차이 확인</p>
                    <p class="deep-summary-meta">
                        BH 보정 후에도 유의 · 일부 유형 표본 1~2건
                    </p>
                </div>
                <div class="deep-summary-item">
                    <p class="deep-summary-label">차이의 크기</p>
                    <p class="deep-summary-value">큰 차이</p>
                    <p class="deep-summary-meta">효과크기 ε² = 0.257</p>
                </div>
                <div class="deep-summary-item">
                    <p class="deep-summary-label">사칭기관별 피해금액</p>
                    <p class="deep-summary-value">통계적으로 차이 확인</p>
                    <p class="deep-summary-meta">
                        BH 보정 후에도 유의 · 일부 기관 표본 2~4건
                    </p>
                </div>
                <div class="deep-summary-item">
                    <p class="deep-summary-label">차이의 크기</p>
                    <p class="deep-summary-value">큰 차이</p>
                    <p class="deep-summary-meta">효과크기 ε² = 0.308</p>
                </div>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_damage_insights() -> None:
    """경찰청 피해 추세·유형 구조와 우체국 피해금액 분포를 표시합니다."""
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

        try:
            police_age_data = load_police_age_data()
        except FileNotFoundError:
            st.error(
                "경찰청 연령 데이터 파일을 찾을 수 없습니다. "
                f"확인 파일: `{POLICE_AGE_DATA_RELATIVE_PATH.as_posix()}`"
            )
            return
        except (UnicodeDecodeError, pd.errors.ParserError, ValueError) as error:
            st.error(f"연령 구성 계산에 필요한 경찰청 데이터를 확인할 수 없습니다: {error}")
            return

        try:
            postal_damage_data = load_postal_damage_data()
        except FileNotFoundError:
            st.error(
                "우체국 데이터 파일을 찾을 수 없습니다. "
                f"확인 파일: `{POSTAL_DATA_RELATIVE_PATH.as_posix()}`"
            )
            return
        except (UnicodeDecodeError, pd.errors.ParserError, ValueError) as error:
            st.error(
                "피해금액 분포에 필요한 우체국 데이터를 확인할 수 없습니다: "
                f"{error}"
            )
            return

        latest = trend_data.iloc[-1]
        latest_type_data = type_data[type_data["기간"] == TYPE_LATEST_PERIOD]
        latest_type_data = latest_type_data.set_index("사기유형")
        latest_impersonation = latest_type_data.loc["기관사칭형"]
        cumulative_age_data = police_age_data[
            police_age_data["기간"].eq(POLICE_AGE_PERIODS[-1])
        ]
        largest_age_group = cumulative_age_data.loc[
            cumulative_age_data["구성비"].idxmax()
        ]
        postal_sample_size = len(postal_damage_data)
        postal_median = postal_damage_data["피해액"].median()
        postal_mean = postal_damage_data["피해액"].mean()

        st.markdown(
            f"""
            <section class="damage-summary-strip">
                <div class="damage-summary-grid">
                    <div class="damage-summary-item">
                        <p class="damage-summary-label">2025 전체 피해 규모</p>
                        <p class="damage-summary-value">{int(latest['전체_발생건수']):,}건</p>
                        <p class="damage-summary-meta">
                            <span class="damage-summary-secondary">
                                피해금액 {_format_amount(latest['전체_피해액_억원'])}
                            </span>
                            <span class="damage-summary-source">경찰청 · 2025</span>
                        </p>
                    </div>
                    <div class="damage-summary-item">
                        <p class="damage-summary-label">피해자 구성 최다 연령대</p>
                        <p class="damage-summary-value">
                            {largest_age_group['연령대']} · {largest_age_group['구성비']:.1f}%
                        </p>
                        <p class="damage-summary-meta">
                            <span class="damage-summary-secondary">
                                전체 피해자 중 구성비
                            </span>
                            <span class="damage-summary-source">경찰청 · 2016~2025</span>
                        </p>
                    </div>
                    <div class="damage-summary-item">
                        <p class="damage-summary-label">기관사칭형 피해비중</p>
                        <p class="damage-summary-value">{latest_impersonation['피해금액_비중']:.1f}%</p>
                        <p class="damage-summary-meta">
                            <span class="damage-summary-secondary">
                                발생비중 {latest_impersonation['발생건수_비중']:.1f}%
                            </span>
                            <span class="damage-summary-source">경찰청 · 2025</span>
                        </p>
                    </div>
                    <div class="damage-summary-item">
                        <p class="damage-summary-label">실제 피해금액 중앙값</p>
                        <p class="damage-summary-value">{_format_won_as_manwon(postal_median)}</p>
                        <p class="damage-summary-meta">
                            <span class="damage-summary-secondary">
                                평균 약 {_format_won_as_manwon(postal_mean)}
                            </span>
                            <span class="damage-summary-source">
                                우체국 · n={postal_sample_size:,}
                            </span>
                        </p>
                    </div>
                </div>
            </section>
            """,
            unsafe_allow_html=True,
        )

        chart_config = {"displayModeBar": False, "responsive": True}
        row1_left, row1_right = st.columns(2, gap="medium")
        row2_left, row2_right = st.columns(2, gap="medium")

        with row1_left:
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

            trend_figure = _create_damage_trend_figure(trend_data)

            with st.container(key="police_trend_chart", gap="small"):
                st.plotly_chart(
                    trend_figure,
                    width="stretch",
                    theme=None,
                    config=chart_config,
                )
                st.caption(_build_count_insight(trend_data))
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

        with row1_right:
            st.markdown(
                """
                <header class="analysis-section-header">
                    <p class="analysis-source">경찰청 집계통계 + 우체국 피해사례</p>
                    <h2>연령대별 피해 특성</h2>
                    <p>
                        피해자 연령 구성의 변화와 실제 피해사례의 연령대별
                        피해금액을 함께 확인합니다.
                    </p>
                </header>
                """,
                unsafe_allow_html=True,
            )

            police_age_figure = _create_police_age_comparison_figure(
                police_age_data
            )
            st.plotly_chart(
                police_age_figure,
                width="stretch",
                theme=None,
                config=chart_config,
                key="police_age_comparison_chart",
            )

            postal_age_figure = _create_postal_age_median_figure(
                postal_damage_data
            )
            st.plotly_chart(
                postal_age_figure,
                width="stretch",
                theme=None,
                config=chart_config,
                key="postal_age_median_chart",
            )

            st.markdown(
                f"""
                <aside class="analysis-insight">
                    <strong>연령대별 통합 인사이트</strong>
                    <p>{_build_age_section_insight(police_age_data, postal_damage_data)}</p>
                </aside>
                """,
                unsafe_allow_html=True,
            )

        with row2_left:
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

            type_structure_figure = _create_type_structure_figure(type_data)

            st.plotly_chart(
                type_structure_figure,
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

        with row2_right:
            st.markdown(
                f"""
                <header class="analysis-section-header">
                    <p class="analysis-source">
                        우체국 피해사례 · n={postal_sample_size:,}
                    </p>
                    <h2>실제 피해금액 분포</h2>
                    <p>
                        실제 보이스피싱 피해사례에서 피해금액의 분포와
                        고액 피해 사례를 확인합니다.
                    </p>
                </header>
                """,
                unsafe_allow_html=True,
            )

            postal_damage_figure = _create_postal_damage_distribution_figure(
                postal_damage_data
            )
            st.plotly_chart(
                postal_damage_figure,
                width="stretch",
                theme=None,
                config=chart_config,
            )

            st.markdown(
                f"""
                <aside class="analysis-insight">
                    <strong>피해금액 인사이트</strong>
                    <p>{_build_postal_damage_insight(postal_damage_data)}</p>
                </aside>
                """,
                unsafe_allow_html=True,
            )

        st.markdown(
            '<div class="analysis-section-divider"></div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f"""
            <header class="analysis-section-header">
                <p class="analysis-source">우체국 피해사례 · n={postal_sample_size:,}</p>
                <h2>피해 특성 심층 분석</h2>
                <p>
                    사기유형과 사칭기관에 따라 실제 피해금액 분포가
                    어떻게 나타나는지 확인합니다.
                </p>
            </header>
            """,
            unsafe_allow_html=True,
        )

        _render_deep_analysis_summary_strip()

        fraud_type_column, institution_column = st.columns(2, gap="medium")

        with fraud_type_column:
            st.markdown(
                """
                <header class="analysis-section-header analysis-subsection-header">
                    <p class="analysis-source">우체국 피해사례 · 사기유형별 비교</p>
                    <h2>사기유형별 피해금액</h2>
                    <p>
                        사기유형에 따라 실제 피해금액 분포가 어떻게 다른지 비교합니다.
                    </p>
                </header>
                """,
                unsafe_allow_html=True,
            )
            fraud_type_figure = _create_postal_category_damage_figure(
                postal_damage_data,
                "사기유형",
            )
            st.plotly_chart(
                fraud_type_figure,
                width="stretch",
                theme=None,
                config=chart_config,
                key="postal_fraud_type_damage_chart",
            )
            st.markdown(
                f"""
                <aside class="analysis-insight">
                    <strong>사기유형별 피해금액 차이</strong>
                    <p>{_build_postal_fraud_type_insight()}</p>
                </aside>
                """,
                unsafe_allow_html=True,
            )

        with institution_column:
            st.markdown(
                """
                <header class="analysis-section-header analysis-subsection-header">
                    <p class="analysis-source">우체국 피해사례 · 사칭기관별 비교</p>
                    <h2>사칭기관별 피해금액</h2>
                    <p>
                        사칭기관에 따라 실제 피해금액 분포가 어떻게 다른지 비교합니다.
                    </p>
                </header>
                """,
                unsafe_allow_html=True,
            )
            institution_figure = _create_postal_category_damage_figure(
                postal_damage_data,
                "사칭기관",
            )
            st.plotly_chart(
                institution_figure,
                width="stretch",
                theme=None,
                config=chart_config,
                key="postal_institution_damage_chart",
            )
            st.markdown(
                f"""
                <aside class="analysis-insight">
                    <strong>사칭기관별 피해금액 차이</strong>
                    <p>{_build_postal_institution_insight()}</p>
                </aside>
                """,
                unsafe_allow_html=True,
            )

        st.markdown(
            f"""
            <aside class="analysis-caution">
                <strong>해석 주의</strong>
                <p>
                    우체국 데이터는 실제 피해사례 {postal_sample_size:,}건 표본입니다.
                    일부 사기유형·사칭기관의 표본 수가 작으며, 확인된 분포 차이는
                    인과관계나 자동 차단 기준, 위험 가중치 확정을 의미하지 않습니다.
                </p>
            </aside>
            """,
            unsafe_allow_html=True,
        )
