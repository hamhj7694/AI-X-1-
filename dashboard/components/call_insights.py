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
    fig.update_layout(height=height, margin=dict(l=12,r=12,t=18,b=12), paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)", font=dict(family="Arial, Apple SD Gothic Neo, Malgun Gothic, sans-serif",size=13,color="#273449"),
        hoverlabel=dict(font_size=13), legend=dict(orientation="h",y=1.02,x=1,xanchor="right"))
    fig.update_xaxes(showgrid=True,gridcolor="#e9eef5",zeroline=False); fig.update_yaxes(showgrid=False,zeroline=False)
    return fig

def _section(title: str, note: str) -> None:
    st.markdown(f"<div class='ci-section-title'>{title}</div><div class='ci-section-note'>{note}</div>",unsafe_allow_html=True)

def _insight(text: str) -> None:
    st.markdown(f"<div class='ci-insight'><b>한 줄 해석</b> · {text}</div>",unsafe_allow_html=True)

def _kpi(label: str, value: float, count: int, total: int, tone: str) -> None:
    st.markdown(f"<div class='ci-kpi' style='--tone:{tone}'><div class='ci-kpi-label'>{label}</div><div class='ci-kpi-value'>{value:.1f}%</div><div class='ci-kpi-meta'>{count:,} / {total:,}건에서 1회 이상 탐지</div></div>",unsafe_allow_html=True)

def render_call_insights() -> None:
    """핵심 EDA 결과를 Lead Time 중심의 탐지 스토리로 보여준다."""
    with st.container(key="analysis_container"):
        st.markdown("""
        <style>
        .ci-hero{padding:1.15rem 1.3rem;margin-bottom:1rem;border:1px solid #dce4ee;border-radius:.85rem;background:linear-gradient(120deg,#fff,#edf5ff)}
        .ci-hero h1{margin:0;font-size:1.82rem;color:#172033}.ci-hero p{margin:.45rem 0 0;color:#315a87;font-size:1.02rem;font-weight:700}
        .ci-kpi{min-height:118px;padding:1rem;border:1px solid #dce4ee;border-top:4px solid var(--tone);border-radius:.75rem;background:#fff}
        .ci-kpi-label{font-size:.84rem;font-weight:750;color:#526078}.ci-kpi-value{margin:.18rem 0;font-size:1.75rem;font-weight:800;color:#172033}.ci-kpi-meta{font-size:.73rem;color:#6b7280}
        .ci-section-title{margin:1.7rem 0 .18rem;font-size:1.16rem;font-weight:800;color:#172033}.ci-section-note{margin-bottom:.65rem;font-size:.82rem;color:#657187;line-height:1.5}
        .ci-insight{margin:.45rem 0 .75rem;padding:.62rem .75rem;border-radius:.55rem;background:#edf5ff;color:#315a87;font-size:.79rem;line-height:1.5}
        .ci-lead{padding:1.05rem 1.2rem;border:1px solid #bfd6f5;border-left:5px solid #2563eb;border-radius:.75rem;background:#f4f8ff}.ci-lead h3{margin:0 0 .3rem;color:#173f73;font-size:1.08rem}.ci-lead p{margin:0;color:#526078;font-size:.82rem;line-height:1.55}
        .ci-conclusion{margin-top:1.4rem;padding:1.2rem 1.3rem;border-radius:.8rem;color:#fff;background:linear-gradient(120deg,#173f73,#2563eb)}.ci-conclusion .label{font-size:.76rem;font-weight:800;letter-spacing:.08em;opacity:.78}.ci-conclusion p{margin:.45rem 0 0;font-size:1.02rem;font-weight:700;line-height:1.65}
        [data-testid="stPlotlyChart"]{border:1px solid #e1e7ef;border-radius:.75rem;background:#fff;padding:.25rem}
        </style><header class="ci-hero"><h1>통화 패턴 및 핵심 인사이트</h1><p>보이스피싱은 돈 요구 이전부터 위험 신호가 누적됐음</p></header>
        """,unsafe_allow_html=True)

        coverage=_load_csv("10_event_coverage_summary.csv")
        for col,(code,label,tone) in zip(st.columns(4,gap="small"),[("strategy","심리전략",BLUE),("impersonation","사칭",NAVY),("requested_action","요구행동",ORANGE),("amount","금액",RED)]):
            row=coverage.loc[coverage.event_type.eq(code)].iloc[0]
            with col: _kpi(label,row.coverage_rate*100,int(row.covered_cases),int(row.total_cases),tone)

        left,right=st.columns(2,gap="medium")
        with left:
            _section("위험 신호 등장 순서","두 이벤트가 함께 탐지된 사건에서 앞선 신호의 선행·동시 비율")
            order=_load_csv("11_event_order_pairwise.csv").sort_values("선행_또는_동시_pct")
            fig=px.bar(order,x="선행_또는_동시_pct",y="비교",orientation="h",text="선행_또는_동시_pct",color_discrete_sequence=[BLUE])
            fig.update_traces(texttemplate="%{text:.1f}%",textposition="outside",hovertemplate="%{y}<br>선행·동시 %{x:.1f}%<extra></extra>"); fig.update_xaxes(title="선행 또는 동시 등장 비율(%)",range=[0,105]); fig.update_yaxes(title=None)
            st.plotly_chart(_layout(fig),width="stretch",config={"displayModeBar":False}); _insight("심리전략이 기반층으로 먼저 나타나고 사칭·행동·금액 신호가 뒤이어 결합하는 경향이 관찰됐음.")
        with right:
            _section("대표 사칭 분포","대표 사칭을 정할 수 있었던 494건 기준이며 전체 776건이 분모가 아님")
            imp=_load_csv("primary_impersonation_group_distribution.csv"); names={"FINANCIAL_INSTITUTION":"금융기관","PUBLIC_AGENCY":"공공기관","MULTI_TIE":"공동 1위","ACQUAINTANCE":"지인","FAMILY":"가족","TELECOM_COMPANY":"통신사","DELIVERY_LOGISTICS":"배송·물류"}
            imp=imp[imp.대표_사칭그룹.ne("NO_IMPERSONATION")].copy(); imp["사칭그룹"]=imp.대표_사칭그룹.map(names).fillna(imp.대표_사칭그룹); imp=imp.sort_values("사칭사건중_pct")
            fig=px.bar(imp,x="사칭사건중_pct",y="사칭그룹",orientation="h",text="사칭사건중_pct",color_discrete_sequence=[TEAL]); fig.update_traces(texttemplate="%{text:.1f}%",textposition="outside",customdata=imp[["사건수"]],hovertemplate="%{y}<br>%{x:.1f}% · %{customdata[0]}건<extra></extra>"); fig.update_xaxes(title="대표 사칭 사건 중 비율(%)",range=[0,72]); fig.update_yaxes(title=None)
            st.plotly_chart(_layout(fig),width="stretch",config={"displayModeBar":False}); _insight("대표 사칭 사건에서는 금융기관 65.2%, 공공기관 25.7% 순으로 관찰됐음.")

        _section("주요 심리전략 × 요구행동 관계","가해자 역할 확인 사건의 조건부 비율과 Lift이며, 함께 나타난 연관성을 인과로 해석하지 않았음")
        rel=_load_csv("08_strategy_x_action_relationship.csv"); sk={"ISOLATION_SECRECY":"고립·비밀유지","INFORMATION_EXTRACTION":"정보추출","BENEFIT_INCENTIVE":"혜택·이익제시","MONEY_REQUEST":"금전요구"}; ak={"AVOID_OUTSIDE_CONTACT":"외부연락 차단","DISCLOSE_ACCOUNT":"계좌정보 제공","REPAY_LOAN":"대출상환","TRANSFER_MONEY":"송금"}
        pairs=[("ISOLATION_SECRECY","AVOID_OUTSIDE_CONTACT"),("INFORMATION_EXTRACTION","DISCLOSE_ACCOUNT"),("BENEFIT_INCENTIVE","REPAY_LOAN"),("MONEY_REQUEST","TRANSFER_MONEY"),("BENEFIT_INCENTIVE","TRANSFER_MONEY")]
        chosen=pd.concat([rel[(rel.심리전략==a)&(rel.요구행동==b)] for a,b in pairs],ignore_index=True); chosen["관계"]=chosen.apply(lambda r:f"{sk[r.심리전략]} → {ak[r.요구행동]}",axis=1); chosen=chosen.sort_values("Lift")
        fig=px.bar(chosen,x="Lift",y="관계",orientation="h",color="P(행동|전략)_pct",color_continuous_scale="Blues",text="Lift",labels={"P(행동|전략)_pct":"전략 사건 중<br>행동 동반(%)"}); fig.update_traces(texttemplate="Lift %{text:.2f}",textposition="outside",customdata=chosen[["동반사건수","심리전략_사건수","P(행동|전략)_pct"]],hovertemplate="%{y}<br>Lift %{x:.2f}<br>%{customdata[0]} / %{customdata[1]}건 · %{customdata[2]:.1f}%<extra></extra>"); fig.update_xaxes(title="Lift (1보다 클수록 함께 관찰되는 비율이 상대적으로 높음)"); fig.update_yaxes(title=None)
        st.plotly_chart(_layout(fig,350),width="stretch",config={"displayModeBar":False}); _insight("정보추출–계좌정보 제공, 금전요구–송금 등이 상대적으로 자주 함께 관찰됐으나 일부 라벨은 의미가 겹쳐 과해석하지 않았음.")

        left,right=st.columns(2,gap="medium")
        with left:
            _section("피해자 질문 기능","LLM SILVER 라벨 중 의미유형이 일관된 질문 1,347개 기준")
            qf=_load_csv("11_question_function_summary.csv"); fig=px.bar(qf,x="질문기능",y="비율_pct",color="질문기능",text="비율_pct",color_discrete_map={"대화지속·수행":BLUE,"경계·의심":ORANGE,"기타":"#b8c2cf"}); fig.update_traces(texttemplate="%{text:.1f}%",textposition="outside",customdata=qf[["질문수"]],hovertemplate="%{x}<br>%{y:.1f}% · %{customdata[0]}개<extra></extra>"); fig.update_yaxes(title="질문 비율(%)",range=[0,80]); fig.update_xaxes(title=None); fig.update_layout(showlegend=False)
            st.plotly_chart(_layout(fig),width="stretch",config={"displayModeBar":False}); _insight("질문의 약 71%는 내용확인·절차수행, 약 27%는 경계·의심 기능으로 분류됐음.")
        with right:
            _section("질문 기능 Transition","질문이 2개 이상인 211개 사건과 연속 질문쌍을 구분해 해석했음")
            trans=_load_csv("18_question_transition_pct.csv").set_index("prev_group"); fig=px.imshow(trans,text_auto=".1f",aspect="auto",color_continuous_scale="Blues",labels=dict(x="다음 질문 기능",y="직전 질문 기능",color="전이 비율(%)")); fig.update_traces(hovertemplate="%{y} → %{x}<br>%{z:.1f}%<extra></extra>")
            st.plotly_chart(_layout(fig),width="stretch",config={"displayModeBar":False}); ct=_load_csv("18_question_transition_case_summary.csv"); back=ct[ct.지표.str.startswith("경계")].iloc[0]; _insight(f"경계·의심 뒤 대화지속·수행으로 다시 전환된 사건은 {int(back.사건수)}/{int(back.질문2개이상_사건수)}건({back.비율_pct:.1f}%)이었음. 이는 다시 믿었다는 뜻이 아니라 대화가 이어진 구조임.")

        _section("★ 고위험 행동 이전 위험신호 Lead Time","첫 송금·현금인출·민감정보 제공 등 고위험 행동요구가 탐지된 231건을 기준으로 계산했음")
        st.markdown("<div class='ci-lead'><h3>탐지 가능한 개입 여유가 Turn 단위로 관찰됐음</h3><p>Lead Time은 첫 신호 Turn과 첫 고위험 행동요구 Turn의 차이임. 초 단위 시간이 아니며, 발췌·편집된 통화의 선후관계이므로 실제 전체 통화 시간으로 일반화하지 않았음.</p></div>",unsafe_allow_html=True)
        lead=_load_csv("16_risk_signal_lead_time_summary.csv").sort_values("LeadTime_중앙값_turn"); fig=go.Figure(go.Bar(x=lead.LeadTime_중앙값_turn,y=lead.신호,orientation="h",marker_color=BLUE,error_x=dict(type="data",symmetric=False,array=lead.LeadTime_Q3_turn-lead.LeadTime_중앙값_turn,arrayminus=lead.LeadTime_중앙값_turn-lead.LeadTime_Q1_turn),customdata=lead[["행동이전_신호사건수","고위험행동사건수","행동이전_등장률_pct","5Turn이상_pct"]],text=lead.LeadTime_중앙값_turn,texttemplate="중앙 %{text:.1f}T",textposition="outside",hovertemplate="%{y}<br>중앙 Lead Time %{x:.1f}T<br>행동 이전 등장 %{customdata[0]}/%{customdata[1]}건 (%{customdata[2]:.1f}%)<br>선행 사건 중 5T 이상 %{customdata[3]:.1f}%<extra></extra>")); fig.update_xaxes(title="첫 고위험 행동요구까지 Lead Time (Turn, 막대=중앙값·오차선=Q1~Q3)"); fig.update_yaxes(title=None)
        st.plotly_chart(_layout(fig,440),width="stretch",config={"displayModeBar":False}); _insight("행동 이전에 탐지된 사건에서 사칭은 중앙 14.5T, 긴급성 16T, 권위·신뢰 14T 앞서 나타났음. '먼저 등장'은 선후관계이지 인과관계가 아님.")

        _section("통화 전 구간 Sliding Window","최근 10개 역할확인 Turn을 5 Turn씩 이동시키고, 다음 10개 Turn의 고위험 행동요구 탐지 여부를 확인했음")
        phase=_load_csv("15_phase_future_risk_summary.csv"); fig=go.Figure(); fig.add_trace(go.Scatter(x=phase.phase,y=phase.이후_고위험행동률_pct,mode="lines+markers+text",name="이후 고위험 행동요구",line=dict(color=RED,width=3),text=phase.이후_고위험행동률_pct,texttemplate="%{text:.1f}%",textposition="top center",customdata=phase[["이후_고위험행동_window수","window수","사건수"]],hovertemplate="%{x}<br>%{y:.1f}% · %{customdata[0]}/%{customdata[1]}개 Window<br>포함 사건 %{customdata[2]}건<extra></extra>")); fig.add_trace(go.Scatter(x=phase.phase,y=phase.평균_신호수,mode="lines+markers+text",name="Window 평균 신호 수",yaxis="y2",line=dict(color=BLUE,width=3,dash="dot"),text=phase.평균_신호수,texttemplate="%{text:.2f}",textposition="bottom center",hovertemplate="%{x}<br>평균 신호 %{y:.2f}개<extra></extra>")); fig.update_layout(yaxis=dict(title="이후 고위험 행동요구 Window 비율(%)",range=[0,12]),yaxis2=dict(title="평균 신호 수",overlaying="y",side="right",range=[0,3])); fig.update_xaxes(title="통화 진행 구간")
        st.plotly_chart(_layout(fig,360),width="stretch",config={"displayModeBar":False}); _insight("초반·중반·후반 모두에서 이후 고위험 행동요구가 관찰돼, 특정 한 시점이 아니라 통화 전 구간에서 위험도를 반복 갱신하는 설계 근거가 됐음.")
        st.markdown("<div class='ci-conclusion'><div class='label'>CORE CONCLUSION</div><p>보이스피싱은 송금 요구 순간에 갑자기 시작된 것이 아니라, 사칭·권위·긴급성·피해자 반응 등 여러 신호가 통화 과정에서 먼저 나타났음. 따라서 통화 전체를 지속 분석하는 조기경보 방식이 타당했음.</p></div>",unsafe_allow_html=True)
        st.caption("자료: 03_01_핵심데이터_선별본 및 핵심데이터_결과/tables · 자동 추출·LLM 분류가 포함된 SILVER 데이터이므로 사람 검수 GOLD 표본에서 추가 검증이 필요함.")
