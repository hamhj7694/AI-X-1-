import json
import ast
from pathlib import Path
from textwrap import dedent


ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "04_non_ml_analysis"
OUT_PATH = OUT_DIR / "04_non_ml_analysis_v1.ipynb"


def md(text):
    return {"cell_type": "markdown", "metadata": {}, "source": dedent(text).strip().splitlines(True)}


def code(text):
    return {
        "cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [],
        "source": dedent(text).strip().splitlines(True),
    }


cells = [
md('''
# 04. 머신러닝 전에 확인하는 보이스피싱 데이터 분석

이 노트북은 **모델 학습 없이** 다음 순서로 데이터를 확인합니다.

1. 데이터 구조·품질: 출처, 기간, 행 단위, 결측, 중복, 불균형, 자동/수동 확정값
2. 현황 기술통계: 유형, 사칭기관, 요구행동, 금액, 공개데이터의 시기·성별·연령·지역
3. 원문 탐색: 단어·2-gram, 유형/화자별 표현, 실제 문맥
4. 통계 비교: 중앙값·분포, Mann–Whitney, 카이제곱/Fisher, FDR, 효과크기·신뢰구간

> 빈칸은 임의로 채우지 않습니다. 결측은 분석마다 분모에서 제외하고 제외 건수를 함께 기록합니다.  
> 단어 검출은 **관찰을 돕는 규칙 기반 탐색**일 뿐, 사실 판정이나 예측 결과가 아닙니다.
'''),
code('''
!pip -q install pandas pyarrow scipy seaborn matplotlib koreanize-matplotlib openpyxl
'''),
code('''
from google.colab import drive
drive.mount('/content/drive')

from pathlib import Path
from collections import Counter
import re, warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import mannwhitneyu, chi2_contingency, fisher_exact
import koreanize_matplotlib

warnings.filterwarnings('ignore')
pd.set_option('display.max_columns', 120)
pd.set_option('display.max_colwidth', 160)
sns.set_theme(style='whitegrid')

PROJECT_ROOT = Path('/content/drive/MyDrive/보이스피싱_분석')
DATASET_ROOT = PROJECT_ROOT / '구축 데이터셋_v4'
STANDARD_ROOT = DATASET_ROOT / '01_standard_tables'
ML_ROOT = DATASET_ROOT / '02_ml_tables'
DASHBOARD_ROOT = DATASET_ROOT / '03_dashboard_tables'
OUTPUT_ROOT = PROJECT_ROOT / '비머신러닝_분석결과_v1'
QUALITY_ROOT = OUTPUT_ROOT / '01_데이터품질'
DESCRIPTIVE_ROOT = OUTPUT_ROOT / '02_현황분석'
TEXT_ROOT = OUTPUT_ROOT / '03_텍스트탐색'
STATS_ROOT = OUTPUT_ROOT / '04_통계검정'
FIGURE_ROOT = OUTPUT_ROOT / '05_시각화'
REPORT_ROOT = OUTPUT_ROOT / '06_요약보고서'
for folder in [QUALITY_ROOT, DESCRIPTIVE_ROOT, TEXT_ROOT, STATS_ROOT, FIGURE_ROOT, REPORT_ROOT]:
    folder.mkdir(parents=True, exist_ok=True)

print('입력:', DATASET_ROOT)
print('출력:', OUTPUT_ROOT)
assert DATASET_ROOT.exists(), f'데이터 폴더가 없습니다: {DATASET_ROOT}'
'''),
md('''## 공통 함수와 테이블 로드

Parquet을 우선하고 CSV를 보조로 읽습니다. 같은 이름의 파일을 두 번 합치지 않습니다.
'''),
code('''
TABLE_LOCATIONS = {
    'vp_files': STANDARD_ROOT, 'vp_cases': STANDARD_ROOT, 'vp_utterances': STANDARD_ROOT,
    'vp_impersonations': STANDARD_ROOT, 'vp_requested_actions': STANDARD_ROOT,
    'vp_strategy_events': STANDARD_ROOT, 'vp_amount_events': STANDARD_ROOT,
    'normal_finance_calls': STANDARD_ROOT, 'fraud_detection_ml': ML_ROOT,
    'fraud_type_ml': ML_ROOT, 'segment_detection_ml': ML_ROOT,
    'case_clustering_ml': ML_ROOT, 'dashboard_case_summary': DASHBOARD_ROOT,
}

def read_table(folder, name):
    for suffix in ('.parquet', '.csv'):
        path = folder / f'{name}{suffix}'
        if path.exists():
            return pd.read_parquet(path) if suffix == '.parquet' else pd.read_csv(path, low_memory=False)
    return None

tables = {name: read_table(folder, name) for name, folder in TABLE_LOCATIONS.items()}
tables = {name: df for name, df in tables.items() if df is not None}
print('로드 완료:', list(tables))

def first_col(df, candidates):
    return next((c for c in candidates if c in df.columns), None)

def save_csv(df, path):
    df.to_csv(path, index=False, encoding='utf-8-sig')
    print('저장:', path.name, df.shape)

def safe_text(s):
    return s.fillna('').astype(str).str.strip()
'''),
md('''# 1단계. 데이터 자체 확인

표별 행 단위, 출처·기간, 결측·중복, 텍스트 길이와 클래스 불균형을 먼저 확인합니다.
'''),
code('''
ROW_GRAIN = {
 'vp_files':'원본 파일 1개', 'vp_cases':'보이스피싱 사건 1건', 'vp_utterances':'발화 1개',
 'vp_impersonations':'사칭 언급/확정 1개', 'vp_requested_actions':'요구행동 1개',
 'vp_strategy_events':'전략 표현 사건 1개', 'vp_amount_events':'금액 언급 1개',
 'normal_finance_calls':'정상 금융상담 통화 1건', 'fraud_detection_ml':'분류용 대화 1건',
 'fraud_type_ml':'사기유형 분류용 사건 1건', 'segment_detection_ml':'구간 1개',
 'case_clustering_ml':'사건 1건', 'dashboard_case_summary':'사건 요약 1건'
}
KEY_CANDIDATES = ['case_id','conversation_id','turn_id','file_id','impersonation_id','action_id','amount_event_id']
inventory=[]
for name,df in tables.items():
    key=first_col(df, KEY_CANDIDATES)
    inventory.append({
        '테이블':name, '행단위':ROW_GRAIN.get(name,'확인 필요'), '행수':len(df), '열수':df.shape[1],
        '대표키':key, '대표키_결측수':int(df[key].isna().sum()) if key else np.nan,
        '대표키_중복수':int(df[key].duplicated().sum()) if key else np.nan,
        '완전중복행수':int(df.duplicated().sum()),
    })
inventory_df=pd.DataFrame(inventory).sort_values('행수',ascending=False)
display(inventory_df)
save_csv(inventory_df, QUALITY_ROOT/'01_테이블_구조.csv')

plt.figure(figsize=(10,5))
sns.barplot(data=inventory_df,y='테이블',x='행수',color='#4C78A8')
plt.xscale('symlog'); plt.title('테이블별 행 수(로그형 축)'); plt.tight_layout()
plt.savefig(FIGURE_ROOT/'01_테이블별_행수.png',dpi=170); plt.show()
'''),
code('''
missing=[]
for name,df in tables.items():
    for col in df.columns:
        n=int(df[col].isna().sum())
        blank=int(safe_text(df[col]).eq('').sum()) if df[col].dtype=='object' else 0
        missing.append({'테이블':name,'컬럼':col,'결측수':n,'빈문자열수':blank,
                        '결측률':n/len(df) if len(df) else np.nan,
                        '결측또는빈문자열률':(n+blank)/len(df) if len(df) else np.nan})
missing_df=pd.DataFrame(missing).sort_values('결측또는빈문자열률',ascending=False)
display(missing_df.head(40))
save_csv(missing_df, QUALITY_ROOT/'02_컬럼별_결측현황.csv')

top_missing=missing_df.query('결측또는빈문자열률 > 0').head(30)
if len(top_missing):
    top_missing=top_missing.assign(항목=top_missing['테이블']+' · '+top_missing['컬럼'])
    plt.figure(figsize=(10,8)); sns.barplot(data=top_missing,y='항목',x='결측또는빈문자열률',color='#E45756')
    plt.xlim(0,1); plt.title('결측·빈문자열 비율 상위 30개'); plt.tight_layout()
    plt.savefig(FIGURE_ROOT/'02_결측률_상위30.png',dpi=170); plt.show()
'''),
code('''
# 날짜/연도형 컬럼에서 관측 범위를 찾습니다. 파싱 불가 값은 별도 집계합니다.
period_rows=[]
for name,df in tables.items():
    candidates=[c for c in df.columns if any(k in c.lower() for k in ['date','time','year','month','일자','연도','년월'])]
    for col in candidates:
        raw=df[col].dropna()
        parsed=pd.to_datetime(raw,errors='coerce')
        if parsed.notna().any():
            period_rows.append({'테이블':name,'기간컬럼':col,'최소':parsed.min(),'최대':parsed.max(),
                                '유효수':int(parsed.notna().sum()),'파싱불가수':int(parsed.isna().sum())})
period_df=pd.DataFrame(period_rows)
display(period_df)
save_csv(period_df, QUALITY_ROOT/'03_관측기간.csv')

# 자동 추출값·사람 검수값으로 추정되는 컬럼은 혼동 방지를 위해 목록만 먼저 공개합니다.
audit_words=['confidence','review','human','manual','verified','silver','gold','source','검수','확정','신뢰']
audit_rows=[]
for name,df in tables.items():
    for col in df.columns:
        if any(w in col.lower() for w in audit_words):
            audit_rows.append({'테이블':name,'컬럼':col,'고유값예시':' | '.join(map(str,df[col].dropna().unique()[:8]))})
audit_df=pd.DataFrame(audit_rows)
display(audit_df)
save_csv(audit_df, QUALITY_ROOT/'04_자동추출_검수관련컬럼.csv')
'''),
code('''
fd=tables.get('fraud_detection_ml')
label_col=None; text_col=None
if fd is not None:
    label_col=first_col(fd,['fraud_label','label','target'])
    text_col=first_col(fd,['model_input_text','normalized_full_text','raw_full_text','text'])
    if label_col:
        class_df=fd[label_col].fillna('MISSING').value_counts(dropna=False).rename_axis('분류').reset_index(name='건수')
        class_df['비율']=class_df['건수']/class_df['건수'].sum()
        display(class_df); save_csv(class_df, QUALITY_ROOT/'05_정상사기_분포.csv')
        plt.figure(figsize=(7,4)); sns.barplot(data=class_df,x='분류',y='건수',color='#4C78A8')
        plt.title('정상상담·보이스피싱 건수'); plt.xticks(rotation=15); plt.tight_layout()
        plt.savefig(FIGURE_ROOT/'03_클래스_분포.png',dpi=170); plt.show()
    if text_col:
        length_df=pd.DataFrame({'분류':fd[label_col] if label_col else '전체',
                                '문자수':safe_text(fd[text_col]).str.len(),
                                '결측원문':fd[text_col].isna() | safe_text(fd[text_col]).eq('')})
        length_summary=length_df.groupby('분류')['문자수'].agg(['count','mean','median','std','min','max']).reset_index()
        display(length_summary); save_csv(length_summary, QUALITY_ROOT/'06_텍스트길이_요약.csv')
        plt.figure(figsize=(8,4)); sns.boxplot(data=length_df.query('문자수 > 0'),x='분류',y='문자수',showfliers=False)
        plt.title('정상상담·보이스피싱 텍스트 길이 분포(이상치 표시 제외)'); plt.tight_layout()
        plt.savefig(FIGURE_ROOT/'04_텍스트길이_분포.png',dpi=170); plt.show()
'''),
md('''# 2단계. 보이스피싱 현황 기술통계

기존 확정 컬럼만 집계합니다. 사건 수와 언급 수를 구분하며, 사건 기준 표는 `case_id`를 중복 제거합니다.
'''),
code('''
def frequency_table(df, col, id_col=None, top=None):
    x=df[[c for c in [id_col,col] if c]].dropna(subset=[col]).copy()
    if id_col: x=x.drop_duplicates([id_col,col])
    out=x[col].astype(str).value_counts().rename_axis(col).reset_index(name='건수')
    out['비율']=out['건수']/out['건수'].sum() if len(out) else np.nan
    return out.head(top) if top else out

descriptive_specs=[
 ('fraud_type_ml',['supervised_target','fraud_type'], '사기유형', 15),
 ('vp_impersonations',['impersonation_group','impersonation_subtype','claimed_org_name'], '사칭기관', 20),
 ('vp_requested_actions',['action_type','primary_requested_action'], '요구행동', 20),
 ('vp_amount_events',['amount_direction'], '금액방향', 20),
 ('vp_amount_events',['amount_purpose'], '금액용도', 20),
 ('vp_amount_events',['amount_status'], '금액상태', 20),
]
plot_no=5
for table_name,candidates,title,top in descriptive_specs:
    df=tables.get(table_name)
    if df is None: continue
    col=first_col(df,candidates); id_col='case_id' if 'case_id' in df.columns else None
    if not col: continue
    out=frequency_table(df,col,id_col,top)
    display(out); save_csv(out,DESCRIPTIVE_ROOT/f'{title}_분포.csv')
    if len(out):
        plt.figure(figsize=(9,max(3,len(out)*.32))); sns.barplot(data=out,y=col,x='비율',color='#59A14F')
        plt.title(f'{title} 구성비 (사건 중복 제거 가능 시 적용)'); plt.tight_layout()
        plt.savefig(FIGURE_ROOT/f'{plot_no:02d}_{title}_분포.png',dpi=170); plt.show(); plot_no+=1

amount=tables.get('vp_amount_events')
if amount is not None and 'amount_krw' in amount.columns:
    amount_numeric=pd.to_numeric(amount['amount_krw'],errors='coerce')
    amount_summary=amount_numeric.describe(percentiles=[.25,.5,.75,.9,.95,.99]).rename('금액원').reset_index()
    display(amount_summary); save_csv(amount_summary,DESCRIPTIVE_ROOT/'금액_요약통계.csv')
'''),
md('''### 선택 분석: 경찰·우체국 공개데이터

아래 후보 폴더에 `df_police.csv`, `df_postal.csv`가 있으면 연도·월·성별·연령·지역·피해금액 컬럼을 자동 탐색해 **원자료 값의 분포**를 저장합니다. 없으면 건너뜁니다.
'''),
code('''
PUBLIC_CANDIDATES=[
    DATASET_ROOT/'04_public_tables', PROJECT_ROOT/'공개데이터_전처리',
    PROJECT_ROOT/'2. 우체국, 경찰 공개 데이터 전처리'
]
public_tables={}
for folder in PUBLIC_CANDIDATES:
    for name in ['df_police','df_postal']:
        if name in public_tables: continue
        for suffix in ['.csv','.parquet']:
            path=folder/f'{name}{suffix}'
            if path.exists():
                public_tables[name]=pd.read_csv(path,low_memory=False) if suffix=='.csv' else pd.read_parquet(path)
                print('공개데이터 로드:',path)

if not public_tables:
    print('공개데이터 통합본이 없어 이 절은 건너뜁니다. df_police/df_postal을 후보 폴더에 넣으면 자동 실행됩니다.')
else:
    keywords=['연도','년월','월','성별','연령','지역','시도','경찰청','피해금액','피해액','발생건수','건수']
    rows=[]
    for name,df in public_tables.items():
        for col in df.columns:
            if any(k in col for k in keywords):
                nonnull=df[col].dropna()
                rows.append({'테이블':name,'컬럼':col,'유효수':len(nonnull),'결측수':int(df[col].isna().sum()),
                             '고유값수':nonnull.nunique(),'값예시':' | '.join(map(str,nonnull.unique()[:12]))})
                if nonnull.nunique() <= 40:
                    out=nonnull.astype(str).value_counts().rename_axis(col).reset_index(name='행수')
                    save_csv(out,DESCRIPTIVE_ROOT/f'{name}_{col}_분포.csv')
    public_profile=pd.DataFrame(rows)
    display(public_profile); save_csv(public_profile,DESCRIPTIVE_ROOT/'공개데이터_분석가능컬럼.csv')
'''),
md('''# 3단계. 원문 텍스트 탐색

문서별 1회 이상 등장한 단어·2-gram의 **문서 존재율**을 비교합니다. 긴 통화가 단어 수를 독점하지 않도록 단순 빈도 대신 사건/통화 존재율을 사용합니다. 모든 주요 결과에 실제 문맥 예시를 함께 저장합니다.
'''),
code('''
TOKEN_RE=re.compile(r'[가-힣A-Za-z]{2,}')
STOPWORDS={'그거','그게','제가','저희','그러면','그래서','이제','지금','네네','아니요','근데','그냥','있는','없는','합니다','입니다','그리고','하면','해서','부터','까지','대한','통해서'}

def tokenize(text):
    return [t.lower() for t in TOKEN_RE.findall(str(text)) if t.lower() not in STOPWORDS]

def doc_feature_counter(texts, ngram=1):
    counter=Counter()
    for text in texts:
        tok=tokenize(text)
        feats=set(tok if ngram==1 else [' '.join(tok[i:i+ngram]) for i in range(len(tok)-ngram+1)])
        counter.update(feats)
    return counter

if fd is None or not label_col or not text_col:
    raise ValueError('fraud_detection_ml의 라벨/원문 컬럼이 필요합니다.')

corpus=fd[[c for c in ['conversation_id',label_col,text_col] if c in fd.columns]].copy()
corpus[text_col]=safe_text(corpus[text_col]); corpus=corpus.query(f'`{text_col}` != ""').copy()
labels=list(corpus[label_col].dropna().unique())
feature_outputs=[]
for ngram in [1,2]:
    counters={lab:doc_feature_counter(corpus.loc[corpus[label_col].eq(lab),text_col],ngram) for lab in labels}
    vocab=set().union(*[set(c) for c in counters.values()])
    rows=[]
    for term in vocab:
        row={'표현':term,'단위':'단어' if ngram==1 else '2-gram'}
        for lab in labels:
            denom=int(corpus[label_col].eq(lab).sum())
            row[f'{lab}_문서수']=counters[lab][term]
            row[f'{lab}_존재율']=counters[lab][term]/denom if denom else np.nan
        rows.append(row)
    out=pd.DataFrame(rows)
    if len(labels)==2:
        out['존재율차이']=out[f'{labels[0]}_존재율']-out[f'{labels[1]}_존재율']
    out=out.sort_values([f'{labels[0]}_문서수'],ascending=False)
    feature_outputs.append(out); save_csv(out,TEXT_ROOT/f'{ngram}gram_문서존재율.csv')
    display(out.head(30))
'''),
code('''
# 두 집단 간 존재율 차이가 큰 표현을 양쪽 모두 표시합니다.
term_df=feature_outputs[0]
if '존재율차이' in term_df:
    min_docs=5
    count_cols=[c for c in term_df if c.endswith('_문서수')]
    plot_terms=term_df.loc[term_df[count_cols].sum(axis=1).ge(min_docs)].sort_values('존재율차이')
    plot_terms=pd.concat([plot_terms.head(12),plot_terms.tail(12)]).drop_duplicates('표현')
    plt.figure(figsize=(10,8)); colors=np.where(plot_terms['존재율차이']>=0,'#E15759','#4E79A7')
    plt.barh(plot_terms['표현'],plot_terms['존재율차이']*100,color=colors)
    plt.axvline(0,color='black',lw=1); plt.xlabel(f'{labels[0]} - {labels[1]} 문서 존재율 차이(%p)')
    plt.title('단어 존재율 차이 (최소 5개 문서)'); plt.tight_layout()
    plt.savefig(FIGURE_ROOT/'20_단어_문서존재율차이.png',dpi=170); plt.show()

    selected=list(plot_terms.sort_values('존재율차이').head(8)['표현'])+list(plot_terms.sort_values('존재율차이').tail(8)['표현'])
    contexts=[]
    id_col='conversation_id' if 'conversation_id' in corpus else None
    for term in selected:
        pattern=re.compile(re.escape(term),re.IGNORECASE)
        for _,row in corpus.iterrows():
            match=pattern.search(row[text_col])
            if match:
                a=max(0,match.start()-70); b=min(len(row[text_col]),match.end()+70)
                contexts.append({'표현':term,'분류':row[label_col],
                                 'conversation_id':row[id_col] if id_col else None,
                                 '문맥':'…'+row[text_col][a:b].replace('\\n',' ')+'…'})
        # 표현별·분류별 최대 3건만 남김
    contexts_df=pd.DataFrame(contexts).groupby(['표현','분류'],as_index=False).head(3)
    display(contexts_df.head(50)); save_csv(contexts_df,TEXT_ROOT/'주요표현_실제문맥.csv')
'''),
code('''
# 사기유형별 표현: 각 사건이 해당 표현을 포함하는지 계산합니다.
ft=tables.get('fraud_type_ml')
if ft is not None:
    ft_label=first_col(ft,['supervised_target','fraud_type'])
    ft_text=first_col(ft,['model_input_text','normalized_full_text','raw_full_text','text'])
    if ft_label and ft_text:
        type_rows=[]
        for fraud_type,g in ft.dropna(subset=[ft_label]).groupby(ft_label):
            counter=doc_feature_counter(safe_text(g[ft_text]),1); denom=len(g)
            for term,n in counter.most_common(40):
                type_rows.append({'사기유형':fraud_type,'표현':term,'문서수':n,'문서존재율':n/denom,'유형전체건수':denom})
        type_terms=pd.DataFrame(type_rows)
        display(type_terms.groupby('사기유형').head(15)); save_csv(type_terms,TEXT_ROOT/'사기유형별_주요단어.csv')

# 화자별 표현: 화자 컬럼과 원문 컬럼이 있을 때만 수행합니다.
utt=tables.get('vp_utterances')
if utt is not None:
    speaker_col=first_col(utt,['speaker_role','speaker','role','화자'])
    utt_text=first_col(utt,['utterance_text','normalized_text','raw_text','text'])
    if speaker_col and utt_text:
        speaker_rows=[]
        for speaker,g in utt.dropna(subset=[speaker_col]).groupby(speaker_col):
            counter=doc_feature_counter(safe_text(g[utt_text]),1); denom=len(g)
            for term,n in counter.most_common(40):
                speaker_rows.append({'화자':speaker,'표현':term,'발화문서수':n,'발화존재율':n/denom,'전체발화수':denom})
        speaker_terms=pd.DataFrame(speaker_rows)
        display(speaker_terms.groupby('화자').head(12)); save_csv(speaker_terms,TEXT_ROOT/'화자별_주요단어.csv')
    else:
        print('화자 또는 발화 원문 컬럼이 없어 화자별 분석을 건너뜁니다.')
'''),
md('''# 4단계. 정상상담과 보이스피싱 통계 비교

- 연속형(문자수): 중앙값, Mann–Whitney U, rank-biserial 효과크기, 중앙값 차이 bootstrap 95% CI
- 이항형(표현 존재): 카이제곱 또는 기대빈도가 작은 경우 Fisher, 존재율 차이, 오즈비, φ 효과크기
- 여러 표현 검정: Benjamini–Hochberg FDR

통계적 유의성만으로 실무적 중요성을 판단하지 않습니다.
'''),
code('''
def bh_fdr(p_values):
    p=np.asarray(p_values,float); result=np.full(len(p),np.nan)
    valid=np.isfinite(p)
    pv=p[valid]; order=np.argsort(pv); ranked=pv[order]*len(pv)/(np.arange(len(pv))+1)
    ranked=np.minimum.accumulate(ranked[::-1])[::-1]
    adjusted=np.empty_like(ranked); adjusted[order]=np.clip(ranked,0,1); result[valid]=adjusted
    return result

def bootstrap_median_diff(a,b,n_boot=2000,seed=42):
    rng=np.random.default_rng(seed); a=np.asarray(a); b=np.asarray(b)
    diffs=np.empty(n_boot)
    for i in range(n_boot):
        diffs[i]=np.median(rng.choice(a,len(a),replace=True))-np.median(rng.choice(b,len(b),replace=True))
    return np.quantile(diffs,[.025,.975])

length_stats=[]
if len(labels)==2:
    a=safe_text(corpus.loc[corpus[label_col].eq(labels[0]),text_col]).str.len().to_numpy()
    b=safe_text(corpus.loc[corpus[label_col].eq(labels[1]),text_col]).str.len().to_numpy()
    u,p=mannwhitneyu(a,b,alternative='two-sided')
    ci=bootstrap_median_diff(a,b)
    length_stats.append({'집단A':labels[0],'집단B':labels[1],'A_n':len(a),'B_n':len(b),
      'A_중앙값':np.median(a),'B_중앙값':np.median(b),'중앙값차이_A-B':np.median(a)-np.median(b),
      '중앙값차이_CI95_하한':ci[0],'중앙값차이_CI95_상한':ci[1],
      'Mann_Whitney_U':u,'p_value':p,'rank_biserial_A우세':2*u/(len(a)*len(b))-1})
length_stats_df=pd.DataFrame(length_stats)
display(length_stats_df); save_csv(length_stats_df,STATS_ROOT/'01_텍스트길이_집단차이.csv')
'''),
code('''
# 단어 존재 여부 검정. 최소 10개 문서에 등장한 단어만 검정합니다.
if len(labels)==2:
    rows=[]; n0=int(corpus[label_col].eq(labels[0]).sum()); n1=int(corpus[label_col].eq(labels[1]).sum())
    count0=f'{labels[0]}_문서수'; count1=f'{labels[1]}_문서수'
    eligible=term_df.loc[(term_df[count0]+term_df[count1]).ge(10)]
    for _,r in eligible.iterrows():
        a=int(r[count0]); c=int(r[count1]); table=np.array([[a,n0-a],[c,n1-c]])
        expected=chi2_contingency(table,correction=False)[3]
        if (expected<5).any():
            odds,p=fisher_exact(table); method='Fisher exact'
        else:
            chi2,p,_,_=chi2_contingency(table,correction=False); odds=((a+.5)*(n1-c+.5))/((n0-a+.5)*(c+.5)); method='Chi-square'
        phi=(a/n0-c/n1)/np.sqrt(((a+c)/(n0+n1))*(1-(a+c)/(n0+n1))*(1/n0+1/n1)) if 0<a+c<n0+n1 else np.nan
        rows.append({'표현':r['표현'],f'{labels[0]}_존재율':a/n0,f'{labels[1]}_존재율':c/n1,
                     '존재율차이':a/n0-c/n1,'오즈비_A대B':odds,'phi_효과크기':phi,'검정':method,'p_value':p})
    presence_stats=pd.DataFrame(rows)
    presence_stats['fdr_p_value']=bh_fdr(presence_stats['p_value'])
    presence_stats['FDR_0.05_유의']=presence_stats['fdr_p_value']<.05
    presence_stats=presence_stats.sort_values('존재율차이',ascending=False)
    display(presence_stats.head(25)); display(presence_stats.tail(25))
    save_csv(presence_stats,STATS_ROOT/'02_단어존재율_집단차이검정.csv')

    sig=presence_stats.query('FDR_0.05_유의').copy()
    if len(sig):
        effect=pd.concat([sig.nlargest(12,'존재율차이'),sig.nsmallest(12,'존재율차이')]).drop_duplicates('표현').sort_values('존재율차이')
        plt.figure(figsize=(10,8)); colors=np.where(effect['존재율차이']>=0,'#E15759','#4E79A7')
        plt.barh(effect['표현'],effect['존재율차이']*100,color=colors); plt.axvline(0,color='black',lw=1)
        plt.xlabel(f'{labels[0]} - {labels[1]} 존재율 차이(%p)'); plt.title('FDR 0.05 통과 단어의 존재율 효과크기')
        plt.tight_layout(); plt.savefig(FIGURE_ROOT/'30_FDR통과_단어효과크기.png',dpi=170); plt.show()
'''),
md('''# 결과 해석 원칙 및 산출물 점검

1. **기술통계 → 원문 문맥 → 통계검정** 순서로 읽습니다.
2. 사칭기관·요구행동 표는 기관이 실제 행동했다는 뜻이 아니라, 범죄자가 **사칭하거나 요구한 내용**입니다.
3. 정상상담에서 어떤 표현의 존재율이 높더라도 “정상은행이 해당 행위를 더 한다”는 인과 해석을 하지 않습니다. 코퍼스 구성, 통화 길이, 상담 업무 문구의 영향부터 확인합니다.
4. 자동 추출 컬럼은 사람이 확정한 정답과 구분합니다.
5. 결측치는 0으로 바꾸지 않았으며, 각 분석의 유효 표본에서만 제외했습니다.
'''),
code('''
outputs=[]
for folder in [QUALITY_ROOT,DESCRIPTIVE_ROOT,TEXT_ROOT,STATS_ROOT,FIGURE_ROOT]:
    for path in sorted(folder.glob('*')):
        outputs.append({'구분':folder.name,'파일명':path.name,'경로':str(path)})
outputs_df=pd.DataFrame(outputs)
display(outputs_df)
save_csv(outputs_df,REPORT_ROOT/'산출물_목록.csv')

summary_lines=[
 '# 비머신러닝 분석 실행 요약','',
 f'- 로드한 테이블: {len(tables)}개',
 f'- 정상·사기 비교 문서: {len(corpus):,}건',
 f'- 결과 폴더: {OUTPUT_ROOT}',
 '',
 '## 해석 주의',
 '- 결측을 임의 대체하지 않았습니다.',
 '- 텍스트 표현 검출은 사실 판정이나 예측이 아닙니다.',
 '- 표현 차이는 실제 문맥 CSV와 함께 검토해야 합니다.',
 '- p-value뿐 아니라 존재율 차이·효과크기·신뢰구간을 함께 확인해야 합니다.'
]
(REPORT_ROOT/'실행요약.md').write_text('\\n'.join(summary_lines),encoding='utf-8')
print('완료:',OUTPUT_ROOT)
''')
]

notebook = {
    "cells": cells,
    "metadata": {
        "colab": {"provenance": []},
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.x"},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}

OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH.write_text(json.dumps(notebook, ensure_ascii=False, indent=1), encoding="utf-8")
syntax_errors = []
all_code = []
for index, cell in enumerate(cells):
    if cell["cell_type"] != "code":
        continue
    source = "".join(cell["source"])
    all_code.append(source)
    cleaned = "\n".join("pass" if line.lstrip().startswith(("!", "%")) else line for line in source.splitlines())
    try:
        ast.parse(cleaned)
    except SyntaxError as exc:
        syntax_errors.append((index, exc.lineno, exc.msg))
if syntax_errors:
    raise SyntaxError(f"노트북 코드 셀 문법 오류: {syntax_errors}")
for forbidden in ["LogisticRegression", "RandomForest", "SVC(", "KMeans(", "GridSearchCV", ".predict("]:
    if forbidden in "\n".join(all_code):
        raise ValueError(f"머신러닝 코드가 포함됨: {forbidden}")
print(OUT_PATH)
