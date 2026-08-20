from __future__ import annotations
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

DATA_ROOT = Path(__file__).resolve().parents[1] / "data" / "call_insights"
BLUE, NAVY, TEAL, ORANGE, RED = "#2563eb", "#173f73", "#0f9d8a", "#f59e0b", "#dc5a5a"

@st.cache_data(show_spinner=False)
def _load_csv(name: str) -> pd.DataFrame:
    return pd.read_csv(DATA_ROOT / name, encoding="utf-8-sig")

def _layout(fig: go.Figure, height: int = 330) -> go.Figure:
    text_color = "#172033"
    axis_style = dict(
        showline=True,
        linecolor="#8291a5",
        linewidth=1,
        ticks="outside",
        tickcolor="#526078",
        tickfont=dict(size=13, color=text_color),
        title_font=dict(size=14, color=text_color),
        title_standoff=12,
        automargin=True,
        zeroline=False,
    )
    fig.update_layout(
        height=height,
        margin=dict(l=20, r=20, t=32, b=22),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#ffffff",
        font=dict(
            family="Arial, Apple SD Gothic Neo, Malgun Gothic, sans-serif",
            size=13,
            color=text_color,
        ),
        hoverlabel=dict(
            bgcolor="#ffffff",
            bordercolor="#526078",
            font_size=13,
            font_color=text_color,
            namelength=0,
        ),
        legend=dict(
            orientation="h",
            y=1.04,
            x=1,
            xanchor="right",
            font=dict(size=13, color=text_color),
            bgcolor="rgba(255,255,255,0.96)",
            bordercolor="#d8e3f0",
            borderwidth=1,
        ),
        uniformtext=dict(minsize=12, mode="show"),
    )
    fig.update_xaxes(showgrid=True, gridcolor="#d8e1ec", gridwidth=1, **axis_style)
    fig.update_yaxes(showgrid=True, gridcolor="#e2e8f0", gridwidth=1, **axis_style)
    if "yaxis2" in fig.layout:
        fig.update_layout(yaxis2=dict(showgrid=False))

    # 막대·선 위 값 라벨도 발표 화면에서 흐려지지 않도록 공통 대비를 적용한다.
    for trace in fig.data:
        if hasattr(trace, "textfont"):
            trace.textfont = dict(size=13, color=text_color)
    fig.update_annotations(font=dict(size=13, color=text_color))
    return fig

def _section(title: str, note: str) -> None:
    st.markdown(f"<div class='ci-section-title'>{title}</div><div class='ci-section-note'>{note}</div>",unsafe_allow_html=True)

def _insight(text: str) -> None:
    st.markdown(f"<div class='ci-insight'><b>한 줄 해석</b> · {text}</div>",unsafe_allow_html=True)

def _caution(text: str, label: str = "해석상 주의") -> None:
    st.markdown(f"<div class='ci-caution'><b>{label}</b> · {text}</div>",unsafe_allow_html=True)

def _plot(fig: go.Figure, height: int = 330) -> None:
    st.plotly_chart(_layout(fig, height), width="stretch", config={"displayModeBar": False})

def _count_pct_labels(counts: pd.Series, percentages: pd.Series, unit: str = "건", decimals: int = 1) -> list[str]:
    """Plotly가 빈 템플릿 변수를 화면에 노출하지 않도록 라벨을 미리 완성한다."""
    return [f"{int(count):,}{unit} · {float(pct):.{decimals}f}%" for count, pct in zip(counts, percentages)]

def _kpi(label: str, value: float, count: int, total: int, tone: str) -> None:
    st.markdown(f"<div class='ci-kpi' style='--tone:{tone}'><div class='ci-kpi-label'>{label}</div><div class='ci-kpi-value'>{value:.1f}%</div><div class='ci-kpi-meta'>{count:,} / {total:,}건에서 1회 이상 탐지</div></div>",unsafe_allow_html=True)

def render_call_insights() -> None:
    """중복을 걷어낸 통화 EDA를 위험 신호에서 ML 후보까지 한 흐름으로 보여준다."""
    with st.container(key="analysis_container"):
        st.markdown("""
        <style>
        .ci-hero{padding:1.25rem 1.4rem;margin-bottom:1rem;border:1px solid #d8e3f0;border-radius:.85rem;background:linear-gradient(120deg,#fff,#edf5ff);box-shadow:0 2px 10px rgba(23,63,115,.05)}
        .ci-hero h1{margin:0;font-size:1.82rem;line-height:1.25;color:#172033}.ci-hero p{margin:.48rem 0 0;color:#315a87;font-size:1.02rem;font-weight:700;line-height:1.5}
        .ci-sample-info{display:inline-flex;margin:0 0 1rem;padding:.44rem .74rem;border:1px solid #bfd6f5;border-radius:999px;background:#edf5ff;color:#173f73;font-size:.82rem;font-weight:750;line-height:1.35}
        .ci-kpi{min-height:118px;padding:1rem 1.05rem;border:1px solid #d8e3f0;border-top:4px solid var(--tone);border-radius:.75rem;background:#fff;box-shadow:0 2px 8px rgba(23,63,115,.045)}
        .ci-kpi-label{font-size:.84rem;font-weight:750;color:#46566d}.ci-kpi-value{margin:.2rem 0;font-size:1.78rem;font-weight:800;line-height:1.15;color:#172033}.ci-kpi-meta{font-size:.74rem;font-weight:550;line-height:1.45;color:#5b6779}
        .ci-section-title{margin:2.05rem 0 .24rem;padding-bottom:.22rem;border-bottom:1px solid #edf1f6;font-size:1.2rem;font-weight:800;line-height:1.4;color:#172033}.ci-section-note{margin-bottom:.78rem;font-size:.83rem;font-weight:500;color:#5b6779;line-height:1.55}
        .ci-insight{margin:.55rem 0 .9rem;padding:.72rem .82rem;border:1px solid #d7e7fb;border-left:4px solid #2563eb;border-radius:.58rem;background:#edf5ff;color:#274f7c;font-size:.8rem;line-height:1.6}
        .ci-caution{margin:.55rem 0 .9rem;padding:.72rem .82rem;border:1px solid #d8e3f0;border-left:4px solid #64748b;border-radius:.58rem;background:#f8fafc;color:#46566d;font-size:.8rem;line-height:1.6}
        .ci-stat-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:.7rem;margin:.55rem 0 .9rem}.ci-stat{padding:.85rem .9rem;border:1px solid #d8e3f0;border-radius:.68rem;background:#fff;box-shadow:0 1px 5px rgba(23,63,115,.035)}.ci-stat b{display:block;color:#173f73;font-size:.88rem;line-height:1.4}.ci-stat span{display:block;margin-top:.3rem;color:#526078;font-size:.77rem;line-height:1.5}
        .ci-feature-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:.7rem;margin:.55rem 0 .9rem}.ci-feature-card{min-height:100%;padding:.9rem;border:1px solid #d8e3f0;border-radius:.72rem;background:#fff;box-shadow:0 2px 8px rgba(23,63,115,.045)}.ci-feature-card h4{margin:0 0 .55rem;color:#173f73;font-size:.89rem;line-height:1.4}.ci-feature-card code{display:block;margin:.25rem 0;padding:.28rem .42rem;border:1px solid #d8e3f0;border-radius:.35rem;background:#f1f5f9 !important;color:#173f73 !important;-webkit-text-fill-color:#173f73;font-size:.74rem;font-weight:650;line-height:1.35;overflow-wrap:anywhere}.ci-feature-card .candidate{margin-top:.45rem;color:#526078;font-size:.74rem;line-height:1.5}
        .ci-conclusion{margin-top:1.65rem;padding:1.25rem 1.35rem;border:1px solid #315f98;border-radius:.82rem;color:#fff;background:linear-gradient(120deg,#173f73,#2563eb);box-shadow:0 4px 14px rgba(23,63,115,.14)}.ci-conclusion .label{font-size:.76rem;font-weight:800;letter-spacing:.08em;opacity:.84}.ci-conclusion p{margin:.48rem 0 0;font-size:1.02rem;font-weight:700;line-height:1.68}
        [data-testid="stPlotlyChart"]{margin:.15rem 0 .35rem;border:1px solid #d8e3f0;border-radius:.75rem;background:#fff;padding:.35rem;box-shadow:0 2px 8px rgba(23,63,115,.04)}
        [data-testid="stExpander"]{border-color:#d8e3f0;border-radius:.68rem;background:#fff}
        @media(max-width:900px){.ci-feature-grid,.ci-stat-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
        @media(max-width:640px){.ci-feature-grid,.ci-stat-grid{grid-template-columns:1fr}.ci-section-title{margin-top:1.7rem}.ci-hero{padding:1.05rem 1.1rem}}
        </style><header class="ci-hero"><h1>통화 패턴 및 핵심 인사이트</h1><p>현재 확보된 발췌 통화 구간에서도 여러 위험 신호의 결합과 변화 양상이 관찰됐음</p></header>
        <div class="ci-sample-info">분석 대상 · 현재 확보된 보이스피싱 발췌 통화 사건 776건</div>
        """, unsafe_allow_html=True)

        with st.expander("분석 전제와 분모 먼저 보기"):
            st.markdown("""
            - 이벤트 현황은 **전체 추출 이벤트 기준**, 전략·행동 세부 분석과 순서 분석은 **가해자 역할 확인 이벤트 기준**입니다.
            - 피해자 반응은 피해자 발화가 있는 **359건**, 대표 사칭은 가해자 기준 대표값을 정할 수 있는 **494건**이 주 분모입니다.
            - 자동 추출·LLM 분류가 포함된 **SILVER 데이터**이며, `검토 필요` 표시는 사람 검수가 남았다는 뜻입니다.
            - 미탐지는 실제 통화에 해당 신호가 없었다는 뜻이 아닙니다. 심리전략 미탐지 121건도 16건은 분석 가능 구간에서 미탐지, 105건은 역할·원문 정보가 충분하지 않은 경우로 구분됩니다.
            - 통화는 발췌·편집 구간일 수 있으므로 Turn·순서·Window는 **현재 확보된 발췌 구간 기준**으로만 해석합니다.
            """)

        _section("① 위험 신호 현황", "전체 776건 중 각 이벤트가 1회 이상 탐지된 사건 기준")
        coverage = _load_csv("10_event_coverage_summary.csv")
        kpi_specs = [
            ("strategy", "심리전략", BLUE),
            ("impersonation", "사칭", NAVY),
            ("requested_action", "요구행동", ORANGE),
            ("amount", "금액", RED),
        ]
        for col, (code, label, tone) in zip(st.columns(4, gap="small"), kpi_specs):
            row = coverage.loc[coverage.event_type.eq(code)].iloc[0]
            with col:
                _kpi(label, row.coverage_rate * 100, int(row.covered_cases), int(row.total_cases), tone)

        coverage_detail = coverage.assign(
            구분=coverage.event_name_kr,
            총이벤트수=coverage.total_events.astype(int),
            탐지사건수=coverage.covered_cases.astype(int),
            탐지사건당평균=coverage.mean_per_covered_case.round(2),
            탐지사건당중앙값=coverage.median_per_covered_case.round(1),
        )[["구분", "총이벤트수", "탐지사건수", "탐지사건당평균", "탐지사건당중앙값"]]
        with st.expander("이벤트 수와 탐지 사건당 분포"):
            st.dataframe(coverage_detail, hide_index=True, width="stretch")
            st.caption("한 사건에 같은 유형의 이벤트가 여러 번 탐지될 수 있으므로 이벤트 수와 사건 수는 다름.")
        _caution("커버리지의 미탐지는 실제 전체 통화에서의 부재가 아니라 현재 확보·추출된 구간에서 탐지되지 않았음을 의미함.")

        _section("② 위험 신호 조합", "각 사건에서 심리전략·사칭·요구행동·금액의 탐지 여부를 조합한 전체 776건 기준")
        combinations = pd.DataFrame([
            ("심리전략 + 사칭", 236, 30.412371),
            ("심리전략 + 사칭 + 요구행동", 125, 16.108247),
            ("이벤트 미탐지", 110, 14.175258),
            ("심리전략 + 사칭 + 요구행동 + 금액", 108, 13.917526),
            ("심리전략 + 사칭 + 금액", 67, 8.634021),
            ("심리전략", 66, 8.505155),
            ("심리전략 + 요구행동", 21, 2.706186),
            ("심리전략 + 금액", 17, 2.190722),
            ("심리전략 + 요구행동 + 금액", 15, 1.932990),
            ("사칭", 8, 1.030928),
            ("금액", 2, 0.257732),
            ("요구행동 + 금액", 1, 0.128866),
        ], columns=["이벤트 조합", "사건수", "전체사건중_pct"]).sort_values("전체사건중_pct")
        fig = px.bar(combinations, x="전체사건중_pct", y="이벤트 조합", orientation="h", text=_count_pct_labels(combinations["사건수"], combinations["전체사건중_pct"]), color_discrete_sequence=[BLUE])
        fig.update_traces(textposition="outside", customdata=combinations[["사건수"]], hovertemplate="%{y}<br>%{customdata[0]}건 · %{x:.2f}%<extra></extra>")
        fig.update_xaxes(title="전체 776건 중 비율(%)", range=[0, 36]); fig.update_yaxes(title=None)
        _plot(fig, 500)
        st.markdown("""
        <div class="ci-stat-grid">
          <div class="ci-stat"><b>사칭 탐지 사건</b><span>544건 중 536건(98.5%)에서 심리전략도 탐지</span></div>
          <div class="ci-stat"><b>요구행동 탐지 사건</b><span>270건 중 269건(99.6%)에서 심리전략도 탐지</span></div>
          <div class="ci-stat"><b>금액 탐지 사건</b><span>210건 중 207건(98.6%)에서 심리전략도 탐지</span></div>
        </div>
        """, unsafe_allow_html=True)
        _insight("심리전략은 사칭·요구행동·금액 신호와 함께 탐지되는 경우가 많았음. 이는 사건 내 동반 관찰 결과이며 심리전략이 원인이라는 뜻은 아님.")

        _section("③ 위험 신호 등장 순서", "가해자 역할과 Turn을 확인할 수 있는 발췌 구간에서 두 이벤트가 함께 탐지된 사건 기준")
        order = _load_csv("11_event_order_pairwise.csv").sort_values("선행_또는_동시_pct")
        order_labels = [f"{value:.1f}%" for value in order["선행_또는_동시_pct"]]
        fig = px.bar(order, x="선행_또는_동시_pct", y="비교", orientation="h", text=order_labels, color_discrete_sequence=[NAVY])
        fig.update_traces(textposition="outside", hovertemplate="%{y}<br>먼저 또는 동일 Turn %{x:.1f}%<extra></extra>")
        fig.update_xaxes(title="왼쪽 이벤트가 먼저 또는 동일 Turn에 등장한 비율(%)", range=[0, 105]); fig.update_yaxes(title=None)
        _plot(fig, 350)
        _insight("순서 확인이 가능한 583건 중 최초 시점에 심리전략이 포함된 사건은 506건이었음. 요구행동과 금액은 요구행동 먼저 38.6%, 동일 Turn 7.9%, 금액 먼저 53.5%로 한 방향의 고정 순서가 관찰되지 않았음.")
        _caution("Pair마다 두 신호가 모두 존재하는 사건 수가 다르며, 순서는 실제 전체 통화의 절대적 시작·진행 단계가 아니라 발췌 구간 내 선후관계임.")

        _section("④ 대표 사칭과 전술 프로필", "가해자 기준 mention_count 합계로 대표 사칭을 정할 수 있었던 494건 기준")
        impersonation_group = _load_csv("01_사칭대상_그룹분포.csv")
        impersonation_group = impersonation_group[
            impersonation_group["표시명"].ne("대표 사칭 없음")
            & impersonation_group["사칭그룹"].ne("NO_IMPERSONATION")
        ].sort_values("사칭탐지사건중_pct")
        impersonation_subtype = _load_csv("02_사칭_세부유형분포.csv")
        impersonation_subtype = impersonation_subtype[
            impersonation_subtype["표시명"].ne("대표 사칭 없음")
            & impersonation_subtype["사칭세부유형"].ne("NO_IMPERSONATION")
        ].sort_values("사칭탐지사건중_pct")

        left, right = st.columns(2, gap="medium")
        with left:
            st.markdown("**사칭 대상 그룹**")
            group_labels = _count_pct_labels(impersonation_group["사건수"], impersonation_group["사칭탐지사건중_pct"])
            fig = px.bar(impersonation_group, x="사칭탐지사건중_pct", y="표시명", orientation="h", text=group_labels, color_discrete_sequence=[TEAL])
            fig.update_traces(textposition="outside", customdata=impersonation_group[["사건수"]], hovertemplate="%{y}<br>%{customdata[0]}건 · %{x:.2f}%<extra></extra>")
            fig.update_xaxes(title="대표 사칭 494건 중 비율(%)", range=[0, 80]); fig.update_yaxes(title=None)
            _plot(fig, 500)
        with right:
            st.markdown("**사칭 세부유형**")
            subtype_labels = _count_pct_labels(impersonation_subtype["사건수"], impersonation_subtype["사칭탐지사건중_pct"])
            fig = px.bar(impersonation_subtype, x="사칭탐지사건중_pct", y="표시명", orientation="h", text=subtype_labels, color_discrete_sequence=[NAVY])
            fig.update_traces(textposition="outside", customdata=impersonation_subtype[["사건수"]], hovertemplate="%{y}<br>%{customdata[0]}건 · %{x:.2f}%<extra></extra>")
            fig.update_xaxes(title="대표 사칭 494건 중 비율(%)", range=[0, 50]); fig.update_yaxes(title=None)
            _plot(fig, 500)
        _insight("대표 사칭 그룹은 금융기관 322건(65.2%), 공공기관 127건(25.7%)이었음. 세부유형은 은행 199건(40.3%), 검찰 84건(17.0%), 공동 1위 75건(15.2%), 카드사 44건(8.9%), 경찰 34건(6.9%) 순이었음.")

        strategy_profile = pd.DataFrame({
            "권위·신뢰":[100.0,94.0,92.0,63.6,97.1,52.6,25.0], "행동 통제":[2.5,2.4,1.3,6.8,0.0,5.3,0.0],
            "이익·혜택 약속":[12.6,0.0,17.3,31.8,5.9,26.3,50.0], "공포·위협":[60.3,81.0,50.7,34.1,41.2,57.9,6.2],
            "정보 추출":[31.2,14.3,26.7,31.8,11.8,15.8,18.8], "고립·비밀 유지":[4.5,4.8,8.0,11.4,0.0,10.5,6.2],
            "정당성 구축":[28.6,29.8,20.0,31.8,26.5,21.1,25.0], "금전 요구":[53.3,19.0,52.0,70.5,32.4,52.6,62.5],
            "저항 대응":[8.5,4.8,6.7,6.8,5.9,15.8,6.2], "긴급성·시간압박":[80.9,64.3,72.0,88.6,70.6,84.2,87.5],
        }, index=["은행 (199)","검찰 (84)","공동대표 (75)","카드사 (44)","경찰 (34)","대출업체 (19)","캐피탈사 (16)"])
        action_profile = pd.DataFrame({
            "현금 인출":[20.1,2.4,18.7,22.7,8.8,15.8,25.0], "송금·이체":[12.1,1.2,14.7,15.9,2.9,0.0,18.8],
            "계좌정보":[12.1,7.1,6.7,9.1,2.9,0.0,6.2], "신분번호":[7.5,0.0,5.3,11.4,5.9,0.0,18.8],
            "카드정보":[6.5,2.4,4.0,13.6,0.0,0.0,6.2], "외부연락 차단":[4.5,4.8,5.3,11.4,0.0,0.0,6.2],
            "대출 상환":[4.0,0.0,5.3,9.1,2.9,10.5,18.8], "비밀번호":[3.0,6.0,4.0,11.4,0.0,0.0,0.0],
            "은행 방문":[6.0,1.2,1.3,2.3,0.0,5.3,0.0], "수수료":[4.5,0.0,5.3,4.5,0.0,5.3,0.0],
            "OTP":[1.5,1.2,2.7,6.8,2.9,5.3,0.0], "통화 유지":[3.0,2.4,0.0,2.3,0.0,5.3,0.0],
        }, index=strategy_profile.index)

        with st.expander("대표 사칭별 심리전략·요구행동 전체 프로필"):
            for title, profile, height in [("심리전략 등장률(%)", strategy_profile, 430), ("요구행동 등장률(%)", action_profile, 430)]:
                st.markdown(f"**{title}**")
                fig = go.Figure(go.Heatmap(z=profile.values, x=profile.columns, y=profile.index, texttemplate="%{z:.1f}", colorscale=[[0,"#eff6ff"],[1,"#60a5fa"]], zmin=0, zmax=100, colorbar=dict(title="%"), hovertemplate="%{y}<br>%{x}: %{z:.1f}%<extra></extra>"))
                fig.update_xaxes(title=None, tickangle=-35); fig.update_yaxes(title=None)
                _plot(fig, height)
            _caution("각 셀은 해당 대표 사칭 사건에서 라벨이 1회 이상 탐지된 비율임. 캐피탈사·대출업체 등은 표본이 작아 유형 간 차이를 확정하지 않고 후속 검정 후보로만 사용함.")

        _section("⑤ 심리전략·요구행동과 등장률", "전체 776건 중 각 심리전략·요구행동이 1회 이상 관찰된 사건 비율")
        strategy_prevalence = pd.DataFrame([
            ("권위·신뢰",455,58.6),("긴급성·시간압박",448,57.7),("공포·위협",294,37.9),("금전요구",280,36.1),("정당성 구축",152,19.6),
            ("정보추출",128,16.5),("혜택·이익 제시",92,11.9),("저항 대응",44,5.7),("고립·비밀유지",29,3.7),("행동통제",14,1.8),
        ], columns=["유형","사건수","전체사건중_pct"]).sort_values("전체사건중_pct")
        action_prevalence = pd.DataFrame([
            ("현금 인출",92,11.9),("송금",58,7.5),("계좌정보 제공",44,5.7),("신분번호 제공",32,4.1),("대출 상환",31,4.0),
            ("카드정보 제공",25,3.2),("수수료 지급",24,3.1),("외부연락 차단",24,3.1),("비밀번호 제공",20,2.6),("은행 방문",16,2.1),
        ], columns=["유형","사건수","전체사건중_pct"]).sort_values("전체사건중_pct")
        left, right = st.columns(2, gap="medium")
        for container, frame, title, color, xmax in [(left,strategy_prevalence,"심리전략 TOP 10",BLUE,65),(right,action_prevalence,"요구행동 TOP 10",ORANGE,14)]:
            with container:
                prevalence_labels = _count_pct_labels(frame["사건수"], frame["전체사건중_pct"])
                fig = px.bar(frame, x="전체사건중_pct", y="유형", orientation="h", text=prevalence_labels, color_discrete_sequence=[color])
                fig.update_traces(textposition="outside", customdata=frame[["사건수"]], hovertemplate="%{y}<br>%{customdata[0]}건 · %{x:.1f}%<extra></extra>")
                fig.update_xaxes(title="전체 776건 중 비율(%)", range=[0,xmax]); fig.update_yaxes(title=None)
                fig.update_layout(title=dict(text=title, font=dict(size=15)))
                _plot(fig, 410)
        _caution("여러 전략·행동이 한 사건에 함께 존재할 수 있어 비율의 합은 100%를 넘을 수 있음. 이는 발화 빈도가 아니라 해당 유형이 1회 이상 관찰된 사건 비율임.")

        _section("보조 분석 · 4대 이벤트의 시작과 동반 구조", "최초 등장 사건 비율과 사건 단위 조건부 동반율을 함께 확인했음")
        event_order = ["심리전략", "사칭", "요구행동", "금액"]
        first_event = _load_csv("04_최초등장이벤트.csv")
        first_event["이벤트"] = pd.Categorical(first_event["이벤트"], categories=event_order, ordered=True)
        first_event = first_event.sort_values("전체사건대비_pct")

        conditional_event = _load_csv("05_4대이벤트_조건부등장률.csv").set_index("조건이벤트_A")
        conditional_event = conditional_event.reindex(index=event_order, columns=event_order)

        event_left, event_right = st.columns(2, gap="medium")
        with event_left:
            first_labels = _count_pct_labels(first_event["최초등장_사건수"], first_event["전체사건대비_pct"])
            fig = px.bar(
                first_event,
                x="전체사건대비_pct",
                y="이벤트",
                orientation="h",
                text=first_labels,
                color="이벤트",
                color_discrete_map={"심리전략": BLUE, "사칭": NAVY, "요구행동": ORANGE, "금액": RED},
            )
            fig.update_traces(
                textposition="outside",
                customdata=first_event[["최초등장_사건수"]],
                hovertemplate="%{y}<br>최초 등장 %{customdata[0]}건 · 전체의 %{x:.1f}%<extra></extra>",
            )
            fig.update_xaxes(title="전체 776건 중 최초 등장 사건 비율(%)", range=[0, 72])
            fig.update_yaxes(title=None)
            fig.update_layout(title=dict(text="사건에서 가장 먼저 등장한 이벤트", font=dict(size=15)), showlegend=False)
            _plot(fig, 350)
            _insight("심리전략이 최초로 등장한 사건은 498건(64.2%), 사칭은 243건(31.3%)이었으며 요구행동 43건(5.5%)보다 앞단에서 주로 관찰됐음.")

        with event_right:
            fig = go.Figure(
                go.Heatmap(
                    z=conditional_event.values,
                    x=conditional_event.columns,
                    y=conditional_event.index,
                    texttemplate="%{z:.1f}",
                    colorscale="Blues",
                    zmin=0,
                    zmax=100,
                    colorbar=dict(title="조건부<br>등장률(%)"),
                    hovertemplate="%{y} 등장 사건 중<br>%{x} 동반 %{z:.1f}%<extra></extra>",
                )
            )
            fig.update_xaxes(title="함께 등장한 이벤트", side="bottom")
            fig.update_yaxes(title="조건 이벤트", autorange="reversed")
            fig.update_layout(title=dict(text="4대 이벤트 조건부 동반율", font=dict(size=15)))
            _plot(fig, 350)
            _insight("요구행동 등장 사건의 99.2%에서 심리전략, 87.4%에서 사칭이 함께 관찰됐고 금액 등장 사건에서도 심리전략이 94.3% 동반됐음.")

        _caution("최초 등장 이벤트는 같은 첫 Turn에 여러 유형이 동시에 나타날 수 있어 비율 합이 100%를 넘음. 조건부 등장률은 P(열 이벤트 | 행 이벤트)이며 방향에 따라 값이 달라지고, 사건 내 동반관계이지 시간적 선후나 인과관계를 의미하지 않음.")

        rel = _load_csv("08_strategy_x_action_relationship.csv")
        main_pairs = [("INFORMATION_EXTRACTION","DISCLOSE_ACCOUNT"),("MONEY_REQUEST","TRANSFER_MONEY")]
        chosen = pd.concat([rel[(rel.심리전략.eq(strategy)) & (rel.요구행동.eq(action))] for strategy, action in main_pairs], ignore_index=True)
        labels = {"INFORMATION_EXTRACTION":"정보추출", "MONEY_REQUEST":"금전요구", "DISCLOSE_ACCOUNT":"계좌정보 제공", "TRANSFER_MONEY":"송금"}
        chosen["관계"] = chosen.apply(lambda row: f"{labels[row.심리전략]} → {labels[row.요구행동]}", axis=1)
        chosen = chosen.sort_values("Lift")
        lift_labels = [f"Lift {value:.2f}" for value in chosen["Lift"]]
        fig = px.bar(chosen, x="Lift", y="관계", orientation="h", text=lift_labels, color_discrete_sequence=[NAVY])
        fig.update_traces(marker_line_color="#0f2f57", marker_line_width=1, textposition="outside", customdata=chosen[["동반사건수","심리전략_사건수","P(행동|전략)_pct"]], hovertemplate="%{y}<br>Lift %{x:.2f}<br>동반사건수 %{customdata[0]}건<br>전략 사건수 %{customdata[1]}건<br>P(행동|전략) %{customdata[2]:.2f}%<extra></extra>")
        fig.update_xaxes(title="Lift (사건 내 동반 관찰의 상대적 정도)", range=[0, chosen.Lift.max() * 1.18]); fig.update_yaxes(title=None)
        _plot(fig, 280)
        info_row = chosen.loc[chosen.심리전략.eq("INFORMATION_EXTRACTION")].iloc[0]
        money_row = chosen.loc[chosen.심리전략.eq("MONEY_REQUEST")].iloc[0]
        _insight(f"정보추출 {int(info_row.심리전략_사건수)}건 중 계좌정보 제공 요구 동반 {int(info_row.동반사건수)}건({info_row['P(행동|전략)_pct']:.2f}%, Lift {info_row.Lift:.2f}), 금전요구 {int(money_row.심리전략_사건수)}건 중 송금 요구 동반 {int(money_row.동반사건수)}건({money_row['P(행동|전략)_pct']:.2f}%, Lift {money_row.Lift:.2f})이었음.")
        _caution("Lift는 사건 내 동반 관찰의 상대적 정도를 나타내며 인과관계를 의미하지 않음. 고립·비밀유지처럼 전략과 행동 라벨 의미가 겹치거나 표본이 작은 조합은 과해석하지 않음.")

        with st.expander("그 밖의 Lift 2 이상 탐색 후보"):
            strategy_kr = {"AUTHORITY_TRUST":"권위·신뢰","URGENCY_TIME_PRESSURE":"긴급성·시간압박","FEAR_THREAT":"공포·위협","MONEY_REQUEST":"금전요구","LEGITIMACY_BUILDING":"정당성 구축","INFORMATION_EXTRACTION":"정보추출","BENEFIT_PROMISE":"혜택·이익 제시","RESISTANCE_HANDLING":"저항 대응","ISOLATION_SECRECY":"고립·비밀유지","BEHAVIOR_CONTROL":"행동통제"}
            action_kr = {"WITHDRAW_CASH":"현금 인출","TRANSFER_MONEY":"송금","DISCLOSE_ACCOUNT":"계좌정보 제공","DISCLOSE_ID_NUMBER":"신분번호 제공","REPAY_LOAN":"대출 상환","DISCLOSE_CARD":"카드정보 제공","PAY_FEE":"수수료 지급","AVOID_OUTSIDE_CONTACT":"외부연락 차단","DISCLOSE_PASSWORD":"비밀번호 제공","VISIT_BANK":"은행 방문","KEEP_CALL_CONNECTED":"통화 유지","DISCLOSE_OTP":"OTP 제공"}
            candidates = rel[(rel.Lift.ge(2)) & (rel.동반사건수.ge(10))].copy()
            candidates["관계"] = candidates.apply(lambda row: f"{strategy_kr.get(row.심리전략,row.심리전략)} → {action_kr.get(row.요구행동,row.요구행동)}", axis=1)
            candidates = candidates.assign(조건부비율_pct=candidates["P(행동|전략)_pct"].round(2), Lift=candidates.Lift.round(2)).sort_values(["Lift","동반사건수"], ascending=False)
            st.dataframe(candidates[["관계","심리전략_사건수","동반사건수","조건부비율_pct","Lift"]], hide_index=True, width="stretch")

        partial = pd.DataFrame([
            ("사칭 횟수 ↔ 권위·신뢰",655,.7825,.7023),("사칭 이벤트 ↔ 권위·신뢰",655,.7403,.6265),("사칭 그룹 다양성 ↔ 권위·신뢰",655,.6428,.5499),
            ("사칭 횟수 ↔ 심리전략 다양성",776,.6981,.4475),("사칭 그룹 다양성 ↔ 심리전략 다양성",776,.6522,.4211),("심리전략 이벤트 ↔ 사칭 이벤트",776,.7577,.4097),
            ("사칭 이벤트 ↔ 심리전략 다양성",776,.6876,.3651),("금전요구 전략 ↔ 금액 이벤트",655,.5039,.3586),("금전요구 전략 ↔ 요구행동",655,.4252,.2610),("심리전략 이벤트 ↔ 요구행동",776,.5187,.1585),
        ], columns=["관계","n","Raw Spearman","통화길이 통제 Partial Spearman"])
        with st.expander("통화 길이를 통제한 관계 후보"):
            st.dataframe(partial, hide_index=True, width="stretch")
            _caution("Partial Spearman은 통화 길이 효과를 줄인 상관 후보일 뿐 인과관계가 아님. 특히 사칭과 권위·신뢰는 같은 문장·Turn에 두 라벨이 함께 부여된 구조적 상관인지 원문 QC가 필요함.")

        _section("⑥ 피해자 반응과 질문 기능", "피해자 발화가 존재하는 359건과 의미유형이 일관된 SILVER 질문 1,347개를 각각의 분모로 사용")
        responses = _load_csv("11_overall_victim_response_key_metrics.csv").sort_values("피해자발화사건중_pct")
        question_function = _load_csv("11_question_function_summary.csv")
        left, right = st.columns(2, gap="medium")
        with left:
            response_labels = _count_pct_labels(responses["사건수"], responses["피해자발화사건중_pct"])
            fig = px.bar(responses, x="피해자발화사건중_pct", y="반응", orientation="h", text=response_labels, color_discrete_sequence=[BLUE])
            fig.update_traces(textposition="outside", customdata=responses[["사건수"]], hovertemplate="%{y}<br>%{customdata[0]}건 · %{x:.1f}%<extra></extra>")
            fig.update_xaxes(title="피해자 발화 359건 중 비율(%)", range=[0,90]); fig.update_yaxes(title=None)
            _plot(fig, 380)
        with right:
            question_labels = _count_pct_labels(question_function["질문수"], question_function["비율_pct"], unit="개")
            fig = px.bar(question_function, x="질문기능", y="비율_pct", color="질문기능", text=question_labels, custom_data=["질문수"], color_discrete_map={"대화지속·수행":BLUE,"경계·의심":ORANGE,"기타":"#94a3b8"})
            fig.update_traces(textposition="outside", hovertemplate="%{x}<br>%{customdata[0]}개 · %{y:.2f}%<extra></extra>")
            fig.update_yaxes(title="질문 1,347개 중 비율(%)", range=[0,80]); fig.update_xaxes(title=None); fig.update_layout(showlegend=False)
            _plot(fig, 380)
        _insight("질문은 피해자 발화 사건의 80.2%에서 관찰됐지만, 질문 1,347개 중 대화지속·수행 기능이 71.0%, 경계·의심 기능이 27.3%였음. 질문을 곧바로 의심으로, 단순 긍정을 명확한 순응으로 해석하지 않음.")

        _section("⑦ 질문의 연결 구조와 변화", "피해자 질문의 기능과 인접 화자 구조를 심리상태가 아닌 대화 구조 proxy로 확인")
        bridge = pd.DataFrame([
            ("전체 피해자 발화",65.5,49.1),("대화지속·수행 질문",72.1,61.4),("경계·저항 질문",70.8,62.3),
        ], columns=["구분","직전 화자가 가해자_pct","가해자→피해자→가해자_pct"])
        bridge_long = bridge.melt(id_vars="구분", var_name="지표", value_name="비율_pct")
        bridge_labels = [f"{value:.1f}%" for value in bridge_long["비율_pct"]]
        fig = px.bar(bridge_long, x="구분", y="비율_pct", color="지표", barmode="group", text=bridge_labels, custom_data=["지표"], color_discrete_sequence=[BLUE,TEAL])
        fig.update_traces(textposition="outside", hovertemplate="%{x}<br>%{customdata[0]}: %{y:.1f}%<extra></extra>")
        fig.update_yaxes(title="발화 구조 비율(%)", range=[0,82]); fig.update_xaxes(title=None)
        _plot(fig, 350)
        proxy = pd.DataFrame([("가해자 Turn 비중",595,83.3),("가해자 발화시간 비중",359,84.1),("피해자 발화가 가해자 직후인 비율",352,80.0)], columns=["proxy","사건수","중앙값_pct"])
        proxy_labels = [f"중앙값 {value:.1f}%" for value in proxy["중앙값_pct"]]
        fig = px.bar(proxy, x="중앙값_pct", y="proxy", orientation="h", text=proxy_labels, color_discrete_sequence=[NAVY])
        fig.update_traces(textposition="outside", customdata=proxy[["사건수"]], hovertemplate="%{y}<br>중앙값 %{x:.1f}% · %{customdata[0]}건<extra></extra>")
        fig.update_xaxes(title="사건별 비율의 중앙값(%)", range=[0,92]); fig.update_yaxes(title=None)
        _plot(fig, 280)

        transition = _load_csv("18_question_transition_pct.csv").set_index("prev_group")
        fig = go.Figure(go.Heatmap(z=transition.values, x=transition.columns, y=transition.index, texttemplate="%{z:.1f}%", colorscale=[[0,"#eff6ff"],[1,"#60a5fa"]], zmin=0, zmax=100, colorbar=dict(title="%"), hovertemplate="%{y} → %{x}<br>%{z:.1f}%<extra></extra>"))
        fig.update_xaxes(title="다음 질문 기능"); fig.update_yaxes(title="직전 질문 기능")
        _plot(fig, 330)
        transition_cases = _load_csv("18_question_transition_case_summary.csv")
        to_alert = transition_cases.iloc[0]; back_continue = transition_cases.iloc[1]
        _insight(f"질문이 2개 이상인 211건 중 대화지속·수행 뒤 경계·의심이 나타난 사건은 {int(to_alert.사건수)}건({to_alert.비율_pct:.1f}%), 경계·의심 뒤 다시 대화지속·수행이 나타난 사건은 {int(back_continue.사건수)}건({back_continue.비율_pct:.1f}%)이었음.")
        _caution("가해자→피해자→가해자와 질문 Transition은 대화가 이어진 구조를 나타내는 proxy이며 심리적 통제, 재신뢰, 실제 순응의 직접 증거가 아님.")

        _section("⑧ 발췌 구간 상대 위치와 선행 Turn 차이", "최근 10개 역할 확인 Turn을 5 Turn씩 이동하고, 다음 10개 Turn의 고위험 행동요구 탐지 여부를 확인")
        phase = _load_csv("15_phase_future_risk_summary.csv")
        fig = go.Figure()
        future_risk_labels = [f"{value:.2f}%" for value in phase["이후_고위험행동률_pct"]]
        signal_mean_labels = [f"{value:.2f}" for value in phase["평균_신호수"]]
        fig.add_trace(go.Scatter(x=phase.phase, y=phase.이후_고위험행동률_pct, mode="lines+markers+text", name="이후 고위험 행동요구", line=dict(color=RED,width=3), text=future_risk_labels, textposition="top center", customdata=phase[["이후_고위험행동_window수","window수","사건수"]], hovertemplate="%{x}<br>%{y:.2f}% · %{customdata[0]}/%{customdata[1]}개 Window<br>포함 사건 %{customdata[2]}건<extra></extra>"))
        fig.add_trace(go.Scatter(x=phase.phase, y=phase.평균_신호수, mode="lines+markers+text", name="평균 신호 수", yaxis="y2", line=dict(color=BLUE,width=3,dash="dot"), text=signal_mean_labels, textposition="bottom center", hovertemplate="%{x}<br>평균 신호 %{y:.2f}개<extra></extra>"))
        fig.update_layout(yaxis=dict(title="이후 고위험 행동요구 Window 비율(%)",range=[0,12]), yaxis2=dict(title="평균 신호 수",overlaying="y",side="right",range=[0,3]))
        fig.update_xaxes(title="발췌 구간 내 상대 위치")
        _plot(fig, 360)
        _caution("초반·중반·후반 표시는 확보된 발췌 구간의 상대적 위치임. 실제 전체 통화 단계로 일반화하지 않으며, Window는 독립된 통화 사건이 아님.")

        lead = _load_csv("16_risk_signal_lead_time_summary.csv").sort_values("LeadTime_중앙값_turn")
        lead_labels = [f"중앙 {value:.1f}T" for value in lead["LeadTime_중앙값_turn"]]
        fig = go.Figure(go.Bar(x=lead.LeadTime_중앙값_turn, y=lead.신호, orientation="h", marker_color=BLUE, error_x=dict(type="data",symmetric=False,array=lead.LeadTime_Q3_turn-lead.LeadTime_중앙값_turn,arrayminus=lead.LeadTime_중앙값_turn-lead.LeadTime_Q1_turn), customdata=lead[["행동이전_신호사건수","고위험행동사건수","행동이전_등장률_pct","5Turn이상_pct"]], text=lead_labels, textposition="outside", hovertemplate="%{y}<br>중앙 Turn 차이 %{x:.1f}T<br>행동 이전 등장 %{customdata[0]}/%{customdata[1]}건 (%{customdata[2]:.1f}%)<br>선행 사건 중 5T 이상 %{customdata[3]:.1f}%<extra></extra>"))
        fig.update_xaxes(title="첫 고위험 행동요구 이전에 탐지된 신호의 Turn 차이(중앙값, 오차선=Q1~Q3)"); fig.update_yaxes(title=None)
        _plot(fig, 440)
        _insight("첫 고위험 행동요구가 탐지된 231건 중 사칭 132건, 긴급성 124건, 권위·신뢰 120건에서 해당 신호가 먼저 관찰됐으며, 선행 사건의 중앙 Turn 차이는 각각 14.5T, 16.0T, 14.0T였음.")
        _caution("Turn 차이는 실제 시간 여유나 최적 개입 시점을 뜻하지 않으며 발췌 구간 내 선후관계임. 먼저 등장했다는 사실도 인과관계를 의미하지 않음.")

        _section("⑨ 탐지 신호 개수와 이후 고위험 행동요구", "현재 고위험 행동요구가 없는 Window에서 신호 개수별 이후 탐지 비율을 비교")
        accumulation = _load_csv("17_signal_accumulation_future_risk.csv").sort_values("signal_count_group")
        accumulation_labels = [f"{value:.2f}%" for value in accumulation["이후_고위험행동률_pct"]]
        fig = go.Figure(go.Scatter(x=accumulation.signal_count_label, y=accumulation.이후_고위험행동률_pct, mode="lines+markers+text", line=dict(color=BLUE,width=3), marker=dict(size=10,color=NAVY,line=dict(color="#0f2f57",width=1)), text=accumulation_labels, textposition="top center", customdata=accumulation[["window수","사건수","이후_고위험행동_window수"]], hovertemplate="신호 %{x}개<br>Window 수 %{customdata[0]:,.0f}<br>사건 수 %{customdata[1]:,.0f}<br>이후 고위험행동 Window 수 %{customdata[2]:,.0f}<br>비율 %{y:.2f}%<extra></extra>"))
        fig.update_layout(showlegend=False); fig.update_xaxes(title="탐지 신호 개수"); fig.update_yaxes(title="이후 고위험 행동요구 Window 비율(%)", range=[0,accumulation.이후_고위험행동률_pct.max()*1.3])
        _plot(fig, 350)
        _insight("0개에서 3개까지는 5.76%→9.47%로 높아졌지만 4개 8.52%, 5개 이상 7.96%로 낮아져 단조 증가 관계는 관찰되지 않았음. 신호 종류·조합·맥락과 비선형 관계를 후속 검증할 필요가 있음.")
        _caution("future_risk는 실제 피해나 송금 성공이 아니라, 현재 Window 이후의 발췌 구간에서 송금·현금인출·민감정보 제공 등 고위험 행동요구가 탐지됐는지를 의미함.")

        _section("⑩ ML 위험 탐지 Feature 후보", "현재 Sliding Window 데이터에 존재하는 신호와 첨부 분석에서 제안된 검증 원칙")
        st.markdown("""
        <div class="ci-feature-grid">
          <div class="ci-feature-card"><h4>사칭·맥락 신호</h4><code>has_impersonation</code><code>has_authority</code><code>has_urgency</code><code>has_fear</code><code>has_legitimacy</code></div>
          <div class="ci-feature-card"><h4>요구·의도 신호</h4><code>has_money_request</code><code>has_info_extraction</code></div>
          <div class="ci-feature-card"><h4>피해자 반응 신호</h4><code>has_continue_question</code><code>has_alert_question</code></div>
          <div class="ci-feature-card"><h4>종합·상호작용 후보</h4><code>signal_count</code><div class="candidate">사칭×전략, 전략×행동, 질문 변화 등은 향후 검증 후보</div></div>
        </div>
        """, unsafe_allow_html=True)
        _caution("Feature는 현재 시점 이전 정보만 사용해야 하며 사건 전체 대표값처럼 미래를 포함한 값은 실시간 Feature로 직접 사용하지 않음. 같은 사건에서 여러 Window가 나오므로 case_id 단위 Group Split/CV가 필요하고, 정상 통화 데이터가 없어 오탐률은 아직 검증할 수 없음.", "모델링 원칙")

        st.markdown("<div class='ci-conclusion'><div class='label'>CORE CONCLUSION</div><p>발췌 통화 사건에서는 위험 신호가 단독보다 여러 형태로 함께 관찰됐고, 대표 사칭에 따라 전략·요구행동 프로필도 달라지는 후보가 확인됐음. 피해자의 질문 역시 경계만이 아니라 대화를 이어가는 기능이 많았으며, 단순 신호 개수와 이후 고위험 행동요구는 단조 관계가 아니었음. 따라서 단일 키워드보다 신호 종류·조합·질문 변화·대화 맥락을 함께 다루는 Feature를 검증하되, 다음 「🤖 ML 위험 탐지 및 검증」 단계에서 사람 검수, 정상 통화 비교, 사건 단위 검증을 거쳐야 함.</p></div>", unsafe_allow_html=True)
        st.caption("자료: 03_01_핵심데이터_선별본.ipynb, 데이터 정리 (1).pptx, dashboard/data/call_insights · 중복 결과는 한 번만 표시 · 자동 추출·LLM 분류가 포함된 SILVER 데이터이므로 사람 검수 GOLD 표본에서 추가 검증 필요")
