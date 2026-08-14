import ast
import json
from pathlib import Path
from textwrap import dedent

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "05_dataset_structure_audit" / "05_dataset_structure_audit_v1.ipynb"

def md(s): return {"cell_type":"markdown","metadata":{},"source":dedent(s).strip().splitlines(True)}
def code(s): return {"cell_type":"code","execution_count":None,"metadata":{},"outputs":[],"source":dedent(s).strip().splitlines(True)}

cells=[
md('''
# 05. 데이터셋 구조 완전 파악 — 중립적 데이터 감사

목표는 분석이나 모델링이 아니라 **원본 데이터에 실제로 존재하는 정보와 구조를 확인하는 것**입니다.

- 가설·서비스 아이디어를 적용하지 않습니다.
- 새로운 라벨이나 위험점수를 만들지 않습니다.
- 감정·의도·심리상태를 추론하지 않습니다.
- 실제 컬럼과 실제 값에 근거하고, 의미는 `확실 / 추정 / 의미 확인 필요`로 구분합니다.
- CSV와 Parquet은 동일 테이블의 저장 형식이므로 Parquet만 읽습니다.
'''),
code('''
!pip -q install pandas pyarrow openpyxl

from google.colab import drive
drive.mount('/content/drive')

from pathlib import Path
import json, re
import numpy as np
import pandas as pd

pd.set_option('display.max_columns',150)
pd.set_option('display.max_colwidth',180)

PROJECT_ROOT=Path('/content/drive/MyDrive/보이스피싱_분석')
DATASET_ROOT=PROJECT_ROOT/'구축 데이터셋_v4'
STANDARD_ROOT=DATASET_ROOT/'01_standard_tables'
OUTPUT_ROOT=PROJECT_ROOT/'데이터셋_구조감사_v1'
OUTPUT_ROOT.mkdir(parents=True,exist_ok=True)

TABLE_NAMES=['vp_files','vp_cases','vp_utterances','vp_impersonations',
             'vp_requested_actions','vp_strategy_events','vp_amount_events','normal_finance_calls']

def read_table(name):
    pq=STANDARD_ROOT/f'{name}.parquet'
    csv=STANDARD_ROOT/f'{name}.csv'
    if pq.exists(): return pd.read_parquet(pq)
    if csv.exists(): return pd.read_csv(csv,low_memory=False)
    raise FileNotFoundError(name)

tables={name:read_table(name) for name in TABLE_NAMES}
print({k:v.shape for k,v in tables.items()})
'''),
md('''## 의미 사전

아래 설명은 구축 스키마와 실제 값으로 확인 가능한 최소 의미만 기록합니다. 자동 추출 관련 컬럼은 그 사실을 명시합니다.
'''),
code('''
GRAIN={
'vp_files':'원본 미디어/전사 파일 1개','vp_cases':'분리된 보이스피싱 사건 1건',
'vp_utterances':'사건 안의 발화 1개','vp_impersonations':'사칭 후보·언급 1건',
'vp_requested_actions':'요구행동 추출 1건','vp_strategy_events':'전략 표현 추출 1건',
'vp_amount_events':'금액 표현 추출 1건','normal_finance_calls':'정상 금융상담 통화 1건'}
PURPOSE={
'vp_files':'원본 파일의 출처·길이·품질·사건 분리 상태 기록',
'vp_cases':'사건 원문·화자 구성·라벨·사건 수준 자동 추출 요약 기록',
'vp_utterances':'발화 순서·시간·화자 추정·전사문 기록',
'vp_impersonations':'사칭 대상과 근거 문장 및 자동 추출 상태 기록',
'vp_requested_actions':'요구행동과 근거 문장 및 자동 추출 상태 기록',
'vp_strategy_events':'규칙으로 검출된 전략 유형과 근거 문장 기록',
'vp_amount_events':'금액 표현·방향·용도·검증 상태 기록',
'normal_finance_calls':'정상 금융상담 원문과 원자료 메타데이터 기록'}

EXACT_MEANING={
'file_id':'원본 파일 식별자','case_id':'분리 사건 식별자','turn_id':'발화 식별자',
'evidence_turn_id':'근거 발화 식별자','source_id':'정상상담 원자료 식별자',
'conversation_id':'정상상담 통화 식별자','turn_order':'사건 내 발화 순서',
'start_sec':'시작 시간(초)','end_sec':'종료 시간(초)','duration_sec':'길이(초)',
'raw_text':'원본 텍스트','normalized_text':'정규화 텍스트','content_text':'분석용 발화 텍스트',
'raw_full_text':'사건 전체 원문','normalized_full_text':'정규화한 사건 전체 원문',
'raw_offender_text':'범죄자 역할 발화 원문','normalized_offender_text':'정규화한 범죄자 역할 발화',
'raw_victim_text':'피해자 역할 발화 원문','normalized_victim_text':'정규화한 피해자 역할 발화',
'evidence_text':'자동 추출 결과의 근거 문장','extraction_method':'추출 방법',
'extraction_confidence':'자동 추출 신뢰도','extraction_version':'추출 규칙/로직 버전',
'label_status':'라벨 상태','quality_flag':'품질 상태','needs_review':'검토 필요 표시',
'supervised_target':'지도학습용 사건 유형 라벨','source_category':'원자료 출처 분류',
'amount_krw':'원화로 정규화한 언급 금액','amount_text':'원문 금액 표현',
'verified_loss_amount_krw':'별도로 검증된 피해금액','verification_status':'금액 검증 상태',
'strategy_type':'검출된 전략 표현 유형','action_type':'요구행동 세부 유형',
'impersonation_group':'사칭 대상 상위 그룹','impersonation_subtype':'사칭 대상 세부 유형',
'auto_role':'자동 추정 화자 역할','role_heuristic_score':'화자 역할 휴리스틱 점수',
'source_date':'정상상담 원자료 날짜','source_institution':'정상상담 기관',
'consulting_category':'정상상담 대분류','consulting_topic':'정상상담 주제',
'client_age_group':'정상상담 고객 연령대','client_gender':'정상상담 고객 성별',
'dataset_split':'원자료 학습/검증 구분'}

def infer_meaning(col):
    if col in EXACT_MEANING: return EXACT_MEANING[col],'확실'
    if col.endswith('_id'): return '해당 개체의 식별자 또는 연결키','추정'
    if col.endswith('_count'): return col[:-6]+'의 기록된 횟수','추정'
    if col.endswith('_ratio'): return col[:-6]+'의 비율','추정'
    if col.endswith('_sec'): return col[:-4]+'의 초 단위 값','추정'
    if col.startswith(('primary_','first_','mentioned_','secondary_','explicit_')): return '컬럼명에 해당하는 사건 수준 요약값','추정'
    if any(x in col for x in ['confidence','score','rank','review','status','version','method']): return '자동 처리·검수 메타데이터','추정'
    return '데이터 사전 또는 구축 담당자 확인 필요','의미 확인 필요'
'''),
md('''# A. 데이터셋 전체 지도'''),
code('''
map_rows=[]
for name,df in tables.items():
    map_rows.append({'데이터셋':name,'데이터_성격':PURPOSE[name],'데이터_단위':GRAIN[name],
                     '한_행의_의미':GRAIN[name],'행_수':len(df),'컬럼_수':df.shape[1],
                     '핵심_내용':PURPOSE[name],
                     '연결키':'file_id, case_id, turn_id 계열' if name!='normal_finance_calls' else '표준 보이스피싱 표와 직접 공통키 없음'})
dataset_map=pd.DataFrame(map_rows)
display(dataset_map)
dataset_map.to_csv(OUTPUT_ROOT/'A_데이터셋_전체지도.csv',index=False,encoding='utf-8-sig')
'''),
md('''# B. 전 컬럼 사전과 품질 통계

고유값이 많은 텍스트·ID 컬럼은 전체 분포 대신 실제 값 예시와 고유값 수를 기록합니다. 범주형 후보는 상위 값 분포를 별도 표로 저장합니다.
'''),
code('''
def examples(series,n=3):
    vals=series.dropna().astype(str)
    vals=vals[vals.str.strip().ne('')].drop_duplicates().head(n)
    return ' | '.join(v.replace('\\n',' ')[:120] for v in vals)

def blank_count(series):
    return int(series.fillna('').astype(str).str.strip().eq('').sum()) if series.dtype=='object' else 0

dictionary=[]; category_rows=[]
for name,df in tables.items():
    for col in df.columns:
        s=df[col]; miss=int(s.isna().sum()); blank=blank_count(s)
        meaning,confidence=infer_meaning(col)
        dictionary.append({'데이터셋':name,'컬럼명':col,'실제_값_예시':examples(s),
            '데이터형':str(s.dtype),'의미':meaning,'결측_수':miss,'결측률':miss/len(df) if len(df) else np.nan,
            '빈문자열_수':blank,'고유값_수':int(s.nunique(dropna=True)),'해석_신뢰도':confidence})
        nunique=s.nunique(dropna=True)
        if 0<nunique<=50:
            vc=s.fillna('[결측]').astype(str).value_counts(dropna=False).head(30)
            for value,count in vc.items():
                category_rows.append({'데이터셋':name,'컬럼명':col,'값':value,'건수':int(count),'비율':count/len(df)})
column_dictionary=pd.DataFrame(dictionary)
category_distribution=pd.DataFrame(category_rows)
display(column_dictionary)
column_dictionary.to_csv(OUTPUT_ROOT/'B_컬럼사전.csv',index=False,encoding='utf-8-sig')
category_distribution.to_csv(OUTPUT_ROOT/'B_범주형값분포.csv',index=False,encoding='utf-8-sig')
'''),
md('''## 수치형 분포와 중복 점검'''),
code('''
numeric_rows=[]; duplicate_rows=[]
ID_CANDIDATES=['file_id','case_id','turn_id','impersonation_id','action_id','strategy_event_id','amount_event_id','source_id','conversation_id']
for name,df in tables.items():
    for col in df.select_dtypes(include=np.number).columns:
        s=pd.to_numeric(df[col],errors='coerce')
        numeric_rows.append({'데이터셋':name,'컬럼명':col,'유효수':int(s.notna().sum()),
          '최소':s.min(),'Q1':s.quantile(.25),'중앙값':s.median(),'평균':s.mean(),
          'Q3':s.quantile(.75),'최대':s.max(),'0_개수':int(s.eq(0).sum()),'음수_개수':int(s.lt(0).sum())})
    keys=[c for c in ID_CANDIDATES if c in df.columns]
    for key in keys:
        duplicate_rows.append({'데이터셋':name,'점검기준':key,'결측_ID':int(df[key].isna().sum()),
                               '중복_ID_행수':int(df[key].duplicated(keep=False).sum()),
                               '고유값수':int(df[key].nunique(dropna=True))})
    duplicate_rows.append({'데이터셋':name,'점검기준':'완전동일행','결측_ID':np.nan,
                           '중복_ID_행수':int(df.duplicated(keep=False).sum()),'고유값수':np.nan})
numeric_distribution=pd.DataFrame(numeric_rows)
duplicate_summary=pd.DataFrame(duplicate_rows)
display(numeric_distribution); display(duplicate_summary)
numeric_distribution.to_csv(OUTPUT_ROOT/'B_수치형분포.csv',index=False,encoding='utf-8-sig')
duplicate_summary.to_csv(OUTPUT_ROOT/'D_중복_식별자점검.csv',index=False,encoding='utf-8-sig')
'''),
md('''# C. 데이터셋 간 관계와 실제 참조 무결성

관계는 실제 키 포함 여부와 값의 포함 관계를 검사해 기록합니다.
'''),
code('''
RELATIONS=[
('vp_files','file_id','vp_cases','file_id','1:N'),
('vp_files','file_id','vp_utterances','file_id','1:N'),
('vp_cases','case_id','vp_utterances','case_id','1:N'),
('vp_cases','case_id','vp_impersonations','case_id','1:N'),
('vp_cases','case_id','vp_requested_actions','case_id','1:N'),
('vp_cases','case_id','vp_strategy_events','case_id','1:N'),
('vp_cases','case_id','vp_amount_events','case_id','1:N'),
('vp_utterances','turn_id','vp_impersonations','evidence_turn_id','1:N'),
('vp_utterances','turn_id','vp_requested_actions','evidence_turn_id','1:N'),
('vp_utterances','turn_id','vp_strategy_events','evidence_turn_id','1:N'),
('vp_utterances','turn_id','vp_amount_events','evidence_turn_id','1:N')]
relation_rows=[]
for parent,pk,child,fk,expected in RELATIONS:
    p=tables[parent][pk]; c=tables[child][fk]
    orphan=~c.isna() & ~c.isin(set(p.dropna()))
    relation_rows.append({'부모_데이터셋':parent,'부모키':pk,'자식_데이터셋':child,'자식키':fk,
      '예상관계':expected,'부모키_중복수':int(p.duplicated().sum()),'자식키_중복수':int(c.duplicated().sum()),
      '자식키_결측수':int(c.isna().sum()),'연결불가_자식행수':int(orphan.sum()),
      '실제_연결가능':bool(orphan.sum()==0)})
relations_df=pd.DataFrame(relation_rows)
display(relations_df)
relations_df.to_csv(OUTPUT_ROOT/'C_데이터셋간_관계.csv',index=False,encoding='utf-8-sig')
'''),
md('''# D. 데이터 품질 문제 후보

아래는 자동 탐지된 **검토 후보**입니다. 오류라고 단정하지 않습니다.
'''),
code('''
issues=[]
for name,df in tables.items():
    for col in df.columns:
        s=df[col]; miss=s.isna().mean()
        if miss>0: issues.append({'데이터셋':name,'컬럼명':col,'문제유형':'결측','근거':f'{miss:.2%}','판정':'확실'})
        if s.dtype=='object':
            stripped=s.dropna().astype(str).str.strip()
            if stripped.eq('').any(): issues.append({'데이터셋':name,'컬럼명':col,'문제유형':'빈문자열','근거':str(int(stripped.eq('').sum()))+'건','판정':'확실'})
            variants=stripped.groupby(stripped.str.lower()).nunique()
            if (variants>1).any(): issues.append({'데이터셋':name,'컬럼명':col,'문제유형':'대소문자·공백 범주 불일치 가능','근거':'정규화 후 중복 범주 존재','판정':'추정'})
        nunique=s.nunique(dropna=True)
        if 2<=nunique<=50:
            rare=(s.value_counts(dropna=True)<5).sum()
            if rare: issues.append({'데이터셋':name,'컬럼명':col,'문제유형':'희소 범주','근거':f'5건 미만 범주 {rare}개','판정':'확실'})

# 구조적으로 중요한 편향·주의사항
for row in [
('vp_cases','source_category','출처 분류가 실제 사건 정답과 동일한지 별도 확인 필요'),
('vp_utterances','auto_role','화자 역할이 자동 추정값이며 오분류 가능'),
('vp_strategy_events','strategy_type','규칙 기반 추출 결과를 사람 확정 사실로 해석하면 안 됨'),
('vp_amount_events','amount_krw','언급 금액이며 실제 피해액과 다름'),
('normal_finance_calls','source_institution','보이스피싱과 출처·수집방식 차이가 비교 결과에 영향을 줄 수 있음')]:
    issues.append({'데이터셋':row[0],'컬럼명':row[1],'문제유형':'분석 주의','근거':row[2],'판정':'확실'})
quality_issues=pd.DataFrame(issues)
display(quality_issues)
quality_issues.to_csv(OUTPUT_ROOT/'D_데이터품질_검토목록.csv',index=False,encoding='utf-8-sig')
'''),
md('''# E. 현재 데이터에 실제로 존재하는 정보

새로운 변수를 만들지 않고, 실제 컬럼 묶음으로 확인 가능한 정보만 목록화합니다.
'''),
code('''
information=[
('원본 미디어 정보','vp_files','media_type, duration_sec, publication_date'),
('원본별 사건·발화 수','vp_files','case_count, turn_count'),
('사건 전체·역할별 전사문','vp_cases','raw/normalized full, offender, victim text'),
('사건 시간과 발화 구성','vp_cases','case_start_sec, case_end_sec, duration_sec, turn counts'),
('원자료 분류와 지도학습 라벨','vp_cases','source_category, supervised_target, label_status'),
('발화 순서·시간·화자 추정','vp_utterances','turn_order, start/end_sec, speaker_id, auto_role'),
('사칭 대상·직책·기관명과 근거','vp_impersonations','impersonation_*, claimed_*, evidence_text'),
('요구행동과 근거','vp_requested_actions','action_group, action_type, evidence_text'),
('규칙 검출 전략 표현과 근거','vp_strategy_events','strategy_type, evidence_text'),
('금액 표현·방향·용도·검증상태','vp_amount_events','amount_*, verification_status, evidence_text'),
('정상 금융상담 원문·기관·주제','normal_finance_calls','raw_text, normalized_text, source_institution, consulting_*'),
('정상상담 고객 메타데이터','normal_finance_calls','source_date, client_age_group, client_gender, dataset_split')]
available_information=pd.DataFrame(information,columns=['직접_확인가능_정보','데이터셋','근거_컬럼'])
display(available_information)
available_information.to_csv(OUTPUT_ROOT/'E_현재데이터에_존재하는정보.csv',index=False,encoding='utf-8-sig')
'''),
md('''# F. 추가 확인이 필요한 부분'''),
code('''
uncertain=column_dictionary.query('해석_신뢰도 != "확실"').copy()
uncertain['추가확인사항']=np.where(uncertain['해석_신뢰도'].eq('의미 확인 필요'),
  '구축 코드·데이터 사전·담당자 확인 필요','실제 값 분포와 구축 로직을 함께 확인해야 의미 확정 가능')
display(uncertain)
uncertain.to_csv(OUTPUT_ROOT/'F_추가확인필요.csv',index=False,encoding='utf-8-sig')
'''),
md('''# 텍스트·음성 구조 확인'''),
code('''
text_audio_rows=[
{'점검항목':'원본 음성 존재 여부','결과':'source_file과 media_type에 원본 미디어 참조가 존재','근거':'vp_files.source_file, media_type','한계':'현재 표 안에 음성 바이너리가 포함된 것은 아님'},
{'점검항목':'전사문 존재','결과':'존재','근거':'vp_cases 및 vp_utterances의 raw/normalized text','한계':''},
{'점검항목':'발화별 분리','결과':'존재','근거':'vp_utterances.turn_id','한계':''},
{'점검항목':'화자 정보','결과':'speaker_id와 auto_role 존재','근거':'vp_utterances','한계':'auto_role은 자동 추정'},
{'점검항목':'시간 정보','결과':'사건·발화 시작/종료 초 존재','근거':'vp_cases, vp_utterances','한계':'원본 절대시각이 아니라 미디어 내 상대시간'},
{'점검항목':'문장 순서','결과':'turn_order로 보존','근거':'vp_utterances.turn_order','한계':''},
{'점검항목':'라벨 생성 방식','결과':'label_status, extraction_method, extraction_version으로 일부 확인 가능','근거':'각 이벤트 표','한계':'모든 라벨의 사람 검수 여부는 값별 확인 필요'},
{'점검항목':'한 사건과 여러 음성 관계','결과':'case_id는 단일 file_id에 속하고 한 file_id가 여러 case_id를 가질 수 있음','근거':'vp_files↔vp_cases','한계':'동일 사건의 복수 원본 파일 여부를 직접 나타내는 키는 없음'}]
text_audio_df=pd.DataFrame(text_audio_rows)
display(text_audio_df)
text_audio_df.to_csv(OUTPUT_ROOT/'텍스트음성_구조확인.csv',index=False,encoding='utf-8-sig')
'''),
md('''# 통합 저장 및 완료 점검'''),
code('''
# CSV가 원본 산출물이며, Excel은 사람이 한 번에 검토하기 위한 묶음본입니다.
with pd.ExcelWriter(OUTPUT_ROOT/'데이터셋_구조감사_A-F.xlsx',engine='openpyxl') as writer:
    dataset_map.to_excel(writer,sheet_name='A_전체지도',index=False)
    column_dictionary.to_excel(writer,sheet_name='B_컬럼사전',index=False)
    category_distribution.to_excel(writer,sheet_name='B_범주분포',index=False)
    numeric_distribution.to_excel(writer,sheet_name='B_수치분포',index=False)
    relations_df.to_excel(writer,sheet_name='C_관계',index=False)
    duplicate_summary.to_excel(writer,sheet_name='D_중복식별자',index=False)
    quality_issues.to_excel(writer,sheet_name='D_품질문제',index=False)
    available_information.to_excel(writer,sheet_name='E_존재정보',index=False)
    uncertain.to_excel(writer,sheet_name='F_추가확인',index=False)
    text_audio_df.to_excel(writer,sheet_name='텍스트음성구조',index=False)

manifest=pd.DataFrame([{'파일명':p.name,'크기_bytes':p.stat().st_size} for p in sorted(OUTPUT_ROOT.glob('*'))])
manifest.to_csv(OUTPUT_ROOT/'산출물목록.csv',index=False,encoding='utf-8-sig')
display(manifest)
print('완료:',OUTPUT_ROOT)
''')]

nb={"cells":cells,"metadata":{"colab":{"provenance":[]},"kernelspec":{"display_name":"Python 3","language":"python","name":"python3"},"language_info":{"name":"python","version":"3.x"}},"nbformat":4,"nbformat_minor":5}
all_code=[]
for i,c in enumerate(cells):
    if c['cell_type']!='code': continue
    src=''.join(c['source']); all_code.append(src)
    cleaned='\n'.join('pass' if x.lstrip().startswith(('!','%')) else x for x in src.splitlines())
    ast.parse(cleaned)
for forbidden in ['LogisticRegression','RandomForest','KMeans(','SVC(','.predict(','sentiment','감정점수','위험점수']:
    if forbidden in '\n'.join(all_code): raise ValueError(forbidden)
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps(nb,ensure_ascii=False,indent=1),encoding='utf-8')
print(OUT)
