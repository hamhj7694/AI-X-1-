import ast, json
from pathlib import Path
from textwrap import dedent

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'05_new_preprocessing_v1.ipynb'
def md(s): return {'cell_type':'markdown','metadata':{},'source':dedent(s).strip().splitlines(True)}
def code(s): return {'cell_type':'code','execution_count':None,'metadata':{},'outputs':[],'source':dedent(s).strip().splitlines(True)}

cells=[
md('''
# 신규 전처리 데이터셋 v1

목적은 원본을 삭제하거나 덮어쓰지 않고, 확인된 수집 한계를 반영한 **분석용 선별본과 모델 후보 데이터**를 새로 만드는 것입니다.

핵심 원칙:

- 보이스피싱 자료는 핵심 구간 발췌본이므로 시간·길이·초반·후반 변수는 모델 입력에서 제외합니다.
- `UNKNOWN`을 정상·0·없음으로 바꾸지 않습니다.
- 애매한 행은 원본에서 삭제하지 않고 `analysis_eligible`과 `exclusion_reason`을 기록합니다.
- 화자별 분석에서 `UNKNOWN` 발화는 제외하되 전체 원문 분석에는 보존합니다.
- 정상·사기 데이터는 스타일이 다르므로 이진 분류용 최종 학습셋을 만들지 않고 **교란 진단용 표본**만 만듭니다.
- 자동 추출 `SILVER` 값은 확정 정답이 아니라 조건부 분석값으로 표시합니다.
'''),
code('''
!pip -q install pandas pyarrow
from google.colab import drive
drive.mount('/content/drive')

from pathlib import Path
import re, json
import numpy as np
import pandas as pd

pd.set_option('display.max_columns',150)
pd.set_option('display.max_colwidth',160)

PROJECT_ROOT=Path('/content/drive/MyDrive/보이스피싱_분석')
INPUT_ROOT=PROJECT_ROOT/'구축 데이터셋_v4'/'01_standard_tables'
OUTPUT_ROOT=PROJECT_ROOT/'신규 전처리 데이터셋_v1'
FULL_ROOT=OUTPUT_ROOT/'01_원본보존_플래그추가'
ANALYSIS_ROOT=OUTPUT_ROOT/'02_분석용'
MODEL_ROOT=OUTPUT_ROOT/'03_모델후보'
AUDIT_ROOT=OUTPUT_ROOT/'04_전처리감사'
for p in [FULL_ROOT,ANALYSIS_ROOT,MODEL_ROOT,AUDIT_ROOT]: p.mkdir(parents=True,exist_ok=True)

TABLE_NAMES=['vp_files','vp_cases','vp_utterances','vp_impersonations','vp_requested_actions','vp_strategy_events','vp_amount_events','normal_finance_calls']
def read_table(name):
    pq=INPUT_ROOT/f'{name}.parquet'; csv=INPUT_ROOT/f'{name}.csv'
    if pq.exists(): return pd.read_parquet(pq)
    if csv.exists(): return pd.read_csv(csv,low_memory=False)
    raise FileNotFoundError(name)
tables={n:read_table(n) for n in TABLE_NAMES}
print({k:v.shape for k,v in tables.items()})
'''),
md('''## 전처리 기준

임의 결측 대체를 하지 않습니다. 명백하게 사용할 수 없는 상태값과 불명확 범주만 제외하며, 신뢰도 임계값은 검증 전이므로 강제로 적용하지 않습니다.
'''),
code('''
AMBIGUOUS={'','UNKNOWN','OTHER','MIXED_UNKNOWN','UNASSIGNED','NOT_MENTIONED','NO_DIRECTION','N/A','NA','NONE','NULL'}
BAD_QUALITY={'UNUSABLE','INVALID','REJECT','REJECTED','FAILED','ERROR'}
BAD_LABEL_STATUS={'REJECT','REJECTED','INVALID','FAILED'}
HUMAN_VERIFIED={'GOLD','HUMAN_VERIFIED','VERIFIED','MANUAL_CONFIRMED'}

def norm_value(x): return '' if pd.isna(x) else str(x).strip().upper()
def is_ambiguous(s): return s.map(norm_value).isin(AMBIGUOUS)
def is_bad_status(s, bad): return s.map(norm_value).isin(bad)
def bool_true(s): return s.astype(str).str.strip().str.lower().isin(['true','1','yes','y'])
def nonblank(s): return s.notna() & s.astype(str).str.strip().ne('')

def combine_reasons(parts):
    result=pd.Series('',index=parts[0][1].index,dtype='object')
    for reason,mask in parts:
        result=np.where(mask,np.where(pd.Series(result,index=mask.index).eq(''),reason,pd.Series(result,index=mask.index)+'; '+reason),result)
    return pd.Series(result,index=parts[0][1].index)

def save_table(df,folder,name,csv=True):
    df.to_parquet(folder/f'{name}.parquet',index=False)
    if csv: df.to_csv(folder/f'{name}.csv',index=False,encoding='utf-8-sig')
    print(name,df.shape)
'''),
md('''# 1. 사건·발화 품질 플래그

사건 자체는 보존합니다. 역할별 분석에는 범죄자 텍스트가 존재하고 명백한 품질 거절 상태가 아닌 사건만 포함합니다.
'''),
code('''
cases=tables['vp_cases'].copy()
bad_quality=is_bad_status(cases['quality_flag'],BAD_QUALITY) if 'quality_flag' in cases else pd.Series(False,index=cases.index)
needs_review=bool_true(cases['needs_review']) if 'needs_review' in cases else pd.Series(False,index=cases.index)
no_offender=~nonblank(cases['normalized_offender_text'])
cases['role_text_eligible']=~bad_quality & ~no_offender
cases['confirmed_analysis_eligible']=cases['role_text_eligible'] & ~needs_review
cases['exclusion_reason']=combine_reasons([
 ('명백한_품질거절상태',bad_quality),('범죄자_텍스트없음',no_offender),('추가검토필요',needs_review)])
cases['unknown_role_quality_note']=np.where(pd.to_numeric(cases.get('unknown_role_ratio',0),errors='coerce').fillna(0).gt(0),
                                            '역할불명발화존재','역할불명발화없음')

utter=tables['vp_utterances'].copy()
utter_bad=is_bad_status(utter['quality_flag'],BAD_QUALITY) if 'quality_flag' in utter else pd.Series(False,index=utter.index)
utter_text=nonblank(utter['content_text'])
role=utter['auto_role'].map(norm_value)
utter['full_text_eligible']=~utter_bad & utter_text
utter['offender_text_eligible']=utter['full_text_eligible'] & role.eq('OFFENDER')
utter['victim_text_eligible']=utter['full_text_eligible'] & role.eq('VICTIM')
utter['ambiguous_role']=~role.isin(['OFFENDER','VICTIM'])
utter['exclusion_reason_role_analysis']=combine_reasons([
 ('텍스트없음',~utter_text),('명백한_품질거절상태',utter_bad),('역할불명',utter['ambiguous_role'])])

save_table(cases,FULL_ROOT,'vp_cases_flagged')
save_table(utter,FULL_ROOT,'vp_utterances_flagged')
save_table(utter.loc[utter.offender_text_eligible],ANALYSIS_ROOT,'offender_utterances_ready')
save_table(utter.loc[utter.victim_text_eligible],ANALYSIS_ROOT,'victim_utterances_ready')
save_table(utter.loc[utter.full_text_eligible],ANALYSIS_ROOT,'all_role_utterances_ready')
'''),
md('''# 2. 사칭·요구행동·전략 이벤트 선별

확정 분석용 조건은 근거 문장 존재, 범죄자 근거, 명백히 불명확하지 않은 유형, 거절 상태 아님입니다. 자동 `SILVER` 결과는 별도 검수단계로 표시합니다.
'''),
code('''
EVENT_SPECS={
'vp_impersonations':['impersonation_group','impersonation_subtype'],
'vp_requested_actions':['action_group','action_type'],
'vp_strategy_events':['strategy_type']}
event_ready={}
for name,category_cols in EVENT_SPECS.items():
    df=tables[name].copy()
    evidence_ok=nonblank(df['evidence_text'])
    offender=df['evidence_role'].map(norm_value).eq('OFFENDER')
    category_ok=pd.Series(True,index=df.index)
    for col in category_cols: category_ok &= ~is_ambiguous(df[col])
    status_ok=~is_bad_status(df['label_status'],BAD_LABEL_STATUS) if 'label_status' in df else pd.Series(True,index=df.index)
    df['analysis_eligible']=evidence_ok & offender & category_ok & status_ok
    df['review_tier']=np.where(df.get('label_status',pd.Series('',index=df.index)).map(norm_value).isin(HUMAN_VERIFIED),
                               '사람검수확정','자동추출_조건부')
    df['exclusion_reason']=combine_reasons([
      ('근거문장없음',~evidence_ok),('범죄자근거아님',~offender),('불명확범주',~category_ok),('라벨상태거절',~status_ok)])
    save_table(df,FULL_ROOT,f'{name}_flagged')
    ready=df.loc[df.analysis_eligible].copy(); event_ready[name]=ready
    save_table(ready,ANALYSIS_ROOT,f'{name}_ready')
'''),
md('''# 3. 금액 이벤트 선별

언급 금액 분석과 실제 피해액 분석을 분리합니다.
'''),
code('''
amount=tables['vp_amount_events'].copy()
evidence_ok=nonblank(amount['evidence_text'])
offender=amount['evidence_role'].map(norm_value).eq('OFFENDER')
amount_ok=pd.to_numeric(amount['amount_krw'],errors='coerce').notna() & pd.to_numeric(amount['amount_krw'],errors='coerce').gt(0)
status_ok=~is_bad_status(amount['label_status'],BAD_LABEL_STATUS)
amount['mentioned_amount_eligible']=evidence_ok & offender & amount_ok & status_ok
verified_status=amount['verification_status'].map(norm_value).isin(HUMAN_VERIFIED)
verified_value=pd.to_numeric(amount['verified_loss_amount_krw'],errors='coerce').notna() & pd.to_numeric(amount['verified_loss_amount_krw'],errors='coerce').ge(0)
amount['verified_loss_eligible']=verified_status & verified_value
amount['exclusion_reason_mentioned']=combine_reasons([
 ('근거문장없음',~evidence_ok),('범죄자근거아님',~offender),('유효금액없음',~amount_ok),('라벨상태거절',~status_ok)])
amount['direction_is_ambiguous']=is_ambiguous(amount['amount_direction'])
amount['purpose_is_ambiguous']=is_ambiguous(amount['amount_purpose'])
save_table(amount,FULL_ROOT,'vp_amount_events_flagged')
save_table(amount.loc[amount.mentioned_amount_eligible],ANALYSIS_ROOT,'mentioned_amount_events_ready')
save_table(amount.loc[amount.verified_loss_eligible],ANALYSIS_ROOT,'verified_loss_events_ready')
'''),
md('''# 4. 보이스피싱 내부 모델 후보 데이터

시간·길이·ID·품질 상태를 예측변수로 넣지 않습니다. ID는 그룹 분할과 추적을 위한 메타데이터로만 유지합니다.
'''),
code('''
def target_valid(s): return nonblank(s) & ~is_ambiguous(s)

# 사기유형 모델: 같은 보이스피싱 체계 내부 비교
type_mask=cases['confirmed_analysis_eligible'] & target_valid(cases['supervised_target'])
fraud_type_ready=cases.loc[type_mask,['case_id','file_id','supervised_target','normalized_offender_text']].copy()
fraud_type_ready=fraud_type_ready.rename(columns={'file_id':'group_id','supervised_target':'target','normalized_offender_text':'model_input_text'})
fraud_type_ready['task']='FRAUD_TYPE_CLASSIFICATION'
save_table(fraud_type_ready,MODEL_ROOT,'fraud_type_model_ready')

# 대표 사칭 상위 그룹 모델
imp_mask=cases['confirmed_analysis_eligible'] & target_valid(cases['primary_impersonation_group'])
imp_group_ready=cases.loc[imp_mask,['case_id','file_id','primary_impersonation_group','normalized_offender_text']].copy()
imp_group_ready=imp_group_ready.rename(columns={'file_id':'group_id','primary_impersonation_group':'target','normalized_offender_text':'model_input_text'})
imp_group_ready['task']='IMPERSONATION_GROUP_CLASSIFICATION'
save_table(imp_group_ready,MODEL_ROOT,'impersonation_group_model_ready')

# 대표 사칭 세부유형 모델: 희소범주는 여기서 임의 통합하지 않고 분포표로 판단
sub_mask=cases['confirmed_analysis_eligible'] & target_valid(cases['primary_impersonation_subtype'])
imp_sub_ready=cases.loc[sub_mask,['case_id','file_id','primary_impersonation_subtype','normalized_offender_text']].copy()
imp_sub_ready=imp_sub_ready.rename(columns={'file_id':'group_id','primary_impersonation_subtype':'target','normalized_offender_text':'model_input_text'})
imp_sub_ready['task']='IMPERSONATION_SUBTYPE_CLASSIFICATION'
save_table(imp_sub_ready,MODEL_ROOT,'impersonation_subtype_model_candidates')

for name,df in [('fraud_type',fraud_type_ready),('impersonation_group',imp_group_ready),('impersonation_subtype',imp_sub_ready)]:
    dist=df['target'].value_counts(dropna=False).rename_axis('target').reset_index(name='count')
    dist['task']=name; dist['usable_for_model']=dist['count'].ge(20)
    save_table(dist,AUDIT_ROOT,f'{name}_target_distribution')
'''),
md('''# 5. 정상·사기 비교는 스타일 교란 진단용으로만 생성

최종 탐지 학습셋이 아닙니다. 양쪽에 같은 텍스트 정규화를 적용하고, 형식 변수만으로도 라벨이 구분되는지 먼저 확인하기 위한 표입니다.
'''),
code('''
normal=tables['normal_finance_calls'].copy()
fraud_diag=cases.loc[cases.role_text_eligible,['case_id','file_id','normalized_offender_text']].copy()
fraud_diag.columns=['record_id','group_id','text']
fraud_diag['label']='VOICE_PHISHING'; fraud_diag['source_dataset']='vp_cases'

# 정상 표본은 보이스피싱의 3배까지만 고정 시드로 진단용 추출
n_take=min(len(normal),len(fraud_diag)*3)
normal_diag=normal.sample(n=n_take,random_state=42).copy()
normal_diag=pd.DataFrame({'record_id':normal_diag['conversation_id'],'group_id':normal_diag['source_id'],
                          'text':normal_diag['normalized_text'],'label':'LEGITIMATE_FINANCIAL_CALL',
                          'source_dataset':'normal_finance_calls'})
style_diag=pd.concat([fraud_diag,normal_diag],ignore_index=True)

def style_features(text):
    text='' if pd.isna(text) else str(text)
    n=max(len(text),1)
    return {'char_count':len(text),'line_count':text.count('\\n')+1,
      'punctuation_ratio':len(re.findall(r'[^가-힣A-Za-z0-9\\s]',text))/n,
      'digit_ratio':len(re.findall(r'[0-9]',text))/n,
      'latin_ratio':len(re.findall(r'[A-Za-z]',text))/n,
      'mask_token_count':len(re.findall(r'\\[MASK\\]|XX|OO|○○',text,flags=re.I))}
style=pd.DataFrame(style_diag['text'].map(style_features).tolist())
style_diag=pd.concat([style_diag,style],axis=1)
style_diag['usage_warning']='출처·스타일_교란진단용_최종탐지성능보고금지'
save_table(style_diag,MODEL_ROOT,'fraud_vs_normal_style_diagnostic_sample')
'''),
md('''# 6. 전처리 감사표와 제외 사유 저장'''),
code('''
audit_rows=[]
def audit(name,source,flag):
    audit_rows.append({'dataset':name,'input_rows':len(source),'included_rows':int(source[flag].sum()),
                       'excluded_rows':int((~source[flag]).sum()),'included_rate':float(source[flag].mean()),'flag':flag})
audit('vp_cases_role_text',cases,'role_text_eligible')
audit('vp_cases_confirmed',cases,'confirmed_analysis_eligible')
audit('vp_utterances_offender',utter,'offender_text_eligible')
audit('vp_utterances_victim',utter,'victim_text_eligible')
for name,df in [(k,tables[k]) for k in EVENT_SPECS]: audit(name, pd.read_parquet(FULL_ROOT/f'{name}_flagged.parquet'),'analysis_eligible')
audit('mentioned_amount',amount,'mentioned_amount_eligible')
audit('verified_loss',amount,'verified_loss_eligible')
audit_df=pd.DataFrame(audit_rows)
save_table(audit_df,AUDIT_ROOT,'preprocessing_summary')

reason_tables=[]
for name,df,col in [
 ('vp_cases',cases,'exclusion_reason'),('vp_utterances',utter,'exclusion_reason_role_analysis'),
 ('vp_amount_events',amount,'exclusion_reason_mentioned')]:
    out=df[col].replace('','포함').value_counts().rename_axis('reason').reset_index(name='count'); out['dataset']=name
    reason_tables.append(out)
for name in EVENT_SPECS:
    df=pd.read_parquet(FULL_ROOT/f'{name}_flagged.parquet')
    out=df['exclusion_reason'].replace('','포함').value_counts().rename_axis('reason').reset_index(name='count'); out['dataset']=name
    reason_tables.append(out)
reason_df=pd.concat(reason_tables,ignore_index=True)
save_table(reason_df,AUDIT_ROOT,'exclusion_reason_summary')
display(audit_df); display(reason_df)
'''),
md('''# 7. 산출물 목록과 재현 정보'''),
code('''
config={
'version':'new_preprocessing_v1','input_root':str(INPUT_ROOT),'output_root':str(OUTPUT_ROOT),
'ambiguous_values':sorted(AMBIGUOUS),'bad_quality_values':sorted(BAD_QUALITY),
'bad_label_status_values':sorted(BAD_LABEL_STATUS),'human_verified_values':sorted(HUMAN_VERIFIED),
'confidence_threshold':None,
'important_notes':['보이스피싱은 핵심구간 발췌본','시간길이 변수 모델 제외','정상사기 표본은 스타일 교란 진단용']}
(AUDIT_ROOT/'preprocessing_config.json').write_text(json.dumps(config,ensure_ascii=False,indent=2),encoding='utf-8')
files=[]
for p in OUTPUT_ROOT.rglob('*'):
    if p.is_file(): files.append({'folder':p.parent.name,'file':p.name,'size_bytes':p.stat().st_size})
manifest=pd.DataFrame(files); manifest.to_csv(AUDIT_ROOT/'output_manifest.csv',index=False,encoding='utf-8-sig')
display(manifest)
print('완료:',OUTPUT_ROOT)
''')]

nb={'cells':cells,'metadata':{'colab':{'provenance':[]},'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},'language_info':{'name':'python','version':'3.x'}},'nbformat':4,'nbformat_minor':5}
for i,c in enumerate(cells):
    if c['cell_type']!='code': continue
    src=''.join(c['source']); cleaned='\n'.join('pass' if x.lstrip().startswith(('!','%')) else x for x in src.splitlines())
    ast.parse(cleaned)
OUT.write_text(json.dumps(nb,ensure_ascii=False,indent=1),encoding='utf-8')
print(OUT)
