# 머신러닝 데이터 전처리·EDA 핵심 순서

## 0. 데이터 불러오기

```python
pd.read_csv()
```

---

## 1. 데이터 기본 구조 확인

### 데이터 생김새
```python
df.head()
df.tail()
```

### 행·열 개수
```python
df.shape
```

### 컬럼 이름
```python
df.columns
```

### 데이터 타입 / 결측치 기본 확인
```python
df.info()
```

### 기초 통계량
```python
df.describe()
```

**확인할 것**
- 데이터가 몇 행인가?
- 변수가 몇 개인가?
- 숫자형 / 문자형 변수는 무엇인가?
- 값의 범위가 이상하지 않은가?

---

## 2. 결측치 확인

```python
df.isnull().sum()
```

또는

```python
df.isna().sum()
```

### 처리
```python
df.dropna()
df.fillna()
```

**확인할 것**
- 어떤 컬럼에 결측값이 있는가?
- 결측값이 너무 많은 변수는 없는가?

---

## 3. 중복 데이터 확인

```python
df.duplicated().sum()
```

### 제거
```python
df.drop_duplicates()
```

---

## 4. 변수별 값 확인

특히 **범주형 변수** 확인에 중요.

```python
df['컬럼'].unique()
df['컬럼'].nunique()
df['컬럼'].value_counts()
```

예:

```python
df['사기유형'].value_counts()
df['연령대'].value_counts()
```

**확인할 것**
- 범주가 어떤 것들이 있는가?
- 오타나 이상한 카테고리가 있는가?
- 특정 범주에 데이터가 지나치게 몰려 있는가?

---

## 5. 데이터 분포 확인

### 히스토그램
```python
df.hist()
```

또는

```python
plt.hist()
```

### 박스플롯
```python
sns.boxplot()
```

**확인할 것**
- 값이 어느 구간에 많이 몰려 있는가?
- 분포가 한쪽으로 치우쳐 있는가?
- 이상치가 존재하는가?

---

## 6. 이상치 확인

### Box Plot
```python
sns.boxplot(x=df['컬럼'])
```

대표적으로:

```python
피해금액
매출액
소득
연령
이용시간
```

등을 확인.

필요하면:

```python
Q1
Q3
IQR
```

기준으로 이상치 탐색 가능.

---

# 7. 변수 간 관계 시각화

## 산점도 Scatter Plot

숫자형 X와 Y 관계 확인.

```python
plt.scatter()
```

또는

```python
sns.scatterplot()
```

예:

```text
광고비 ↔ 매출
연령 ↔ 피해금액
통화시간 ↔ 피해금액
```

**눈으로 선형관계나 패턴이 있는지 먼저 확인.**

---

# 8. 상관계수 확인 ★

수업에서 중요하게 배운 부분.

```python
df.corr()
```

### Heatmap

```python
sns.heatmap(df.corr(), annot=True)
```

**확인할 것**

```text
X ↔ y 관계가 강한가?
X ↔ X끼리 너무 비슷하지 않은가?
```

상관계수는:

```text
+1    강한 양의 관계
 0    선형관계 거의 없음
-1    강한 음의 관계
```

---

# 9. Pearson / Spearman 상관검정 ★

## Pearson

선형적인 관계 확인.

```python
pearsonr()
```

예:

```python
from scipy.stats import pearsonr

r, p = pearsonr(df['X'], df['Y'])
```

---

## Spearman

순위·단조 관계 확인.

```python
spearmanr()
```

```python
from scipy.stats import spearmanr
```

---

# 10. p-value 확인 ★

Pearson / Spearman과 함께 확인.

```python
r, p = pearsonr(X, Y)
```

보통:

```text
p < 0.05
→ 통계적으로 유의한 관계

p ≥ 0.05
→ 관계가 있다고 보기 어려움
```

단,

> p-value가 작다고 반드시 중요한 변수라는 뜻은 아님.

**상관계수 크기도 같이 봐야 함.**

---

# 11. 범주형 변수 인코딩

머신러닝 모델은 문자를 그대로 처리하지 못하는 경우가 많음.

예:

```text
봄
여름
가을
겨울
```

### One-Hot Encoding

```python
pd.get_dummies()
```

또는

```python
OneHotEncoder
```

---

# 12. 변수 크기 맞추기 — Scaling

특히 **KNN / K-Means / PCA**에서는 매우 중요.

## StandardScaler

```python
StandardScaler()
```

평균 0, 표준편차 1 기준으로 맞춤.

## MinMaxScaler

```python
MinMaxScaler()
```

보통 0~1 사이로 맞춤.

### 중요한 이유

예:

```text
연령 = 20~80
피해금액 = 100,000~100,000,000
```

그대로 거리계산하면 피해금액이 모델을 거의 지배할 수 있음.

---

# 13. X와 y 분리

### 독립변수

```python
X = df[['변수1', '변수2', '변수3']]
```

### 목표변수

```python
y = df['target']
```

여기서 가장 중요한 질문:

> **내가 무엇을 예측하려는가?**

그게 `y`.

나머지 예측에 사용할 정보가 `X`.

---

# 14. Train / Test 데이터 분리 ★

```python
train_test_split()
```

예:

```python
X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.2,
    random_state=42
)
```

보통:

```text
Train 80%
Test 20%
```

---

# 15. 분류 문제라면 클래스 비율 확인 ★

```python
y.value_counts()
```

비율까지:

```python
y.value_counts(normalize=True)
```

예:

```text
정상 95%
사기 5%
```

라면 **Accuracy만 믿으면 안 됨.**

이런 불균형 데이터에서는:

```text
Precision
Recall
F1
ROC-AUC
PR-AUC
```

등을 봐야 함.

---

# 16. 모델 학습 후 변수 중요도 확인

Random Forest / Tree 등:

```python
model.feature_importances_
```

확인 목적:

> 모델이 어떤 변수를 많이 사용했는가?

예:

```text
피해금액       0.32
통화시간       0.27
연령           0.18
사기유형       0.13
```

---

# 17. 회귀계수 확인

Linear Regression 등:

```python
model.coef_
```

```python
model.intercept_
```

어떤 변수가 Y와

```text
+ 방향인지
- 방향인지
```

확인 가능.

---

# 18. 모델 성능 확인

## 분류

```python
accuracy_score()
precision_score()
recall_score()
f1_score()
confusion_matrix()
classification_report()
roc_auc_score()
```

### 특히 기억

```text
Accuracy  = 전체적으로 얼마나 맞췄나
Precision = 위험이라 한 것 중 진짜 위험은?
Recall    = 실제 위험 중 얼마나 잡았나
F1        = Precision + Recall 균형
```

---

## 회귀

```python
mean_absolute_error()
mean_squared_error()
r2_score()
```

즉:

```text
MAE
MSE
R²
```

---

# 19. 교차검증 ★

한 번 Train/Test를 나눈 결과만 믿지 않고 여러 번 검증.

```python
cross_val_score()
```

대표:

```text
5-Fold Cross Validation
```

모델 선택이나 과적합 확인에 중요.

---

# 20. 군집분석을 한다면

K-Means:

```python
KMeans()
```

### 적절한 군집 수 확인

```python
model.inertia_
```

그리고:

```text
Elbow Method
```

로 K값 결정.

---

# 21. PCA를 한다면

먼저:

```python
StandardScaler()
```

이후:

```python
PCA()
```

정보를 얼마나 보존했는지:

```python
explained_variance_ratio_
```

---

# 22. 텍스트 유사성을 본다면

## TF-IDF

```python
TfidfVectorizer()
```

## 단어 빈도

```python
CountVectorizer()
```

## 유사도

```python
cosine_similarity()
```

즉:

> 문장 A와 문장 B가 얼마나 유사한가?

를 숫자로 계산.

---

# ★ 정말 핵심만 외우면

새 데이터 받으면 우선 이 순서로 보면 된다.

```text
① df.head()
② df.shape
③ df.info()
④ df.describe()

⑤ df.isnull().sum()
⑥ df.duplicated().sum()

⑦ value_counts()
⑧ unique()

⑨ histogram
⑩ boxplot
⑪ scatterplot

⑫ df.corr()
⑬ heatmap()
⑭ pearsonr() / spearmanr()
⑮ p-value

⑯ get_dummies()
⑰ StandardScaler() / MinMaxScaler()

⑱ X / y 분리
⑲ train_test_split()

⑳ 모델 학습

→ Accuracy / Precision / Recall / F1
또는
→ MAE / MSE / R²

→ cross_val_score()

→ feature_importances_ / coef_
```

## 초압축 기억법

**구조 → 오류 → 분포 → 관계 → 전처리 → 분리 → 학습 → 검증 → 해석**

```text
구조
head / shape / info / describe

↓

오류
isnull / duplicated

↓

분포
value_counts / hist / boxplot

↓

관계
scatter / corr / heatmap
Pearson / Spearman / p-value

↓

전처리
get_dummies / StandardScaler / MinMaxScaler

↓

분리
X / y / train_test_split

↓

학습
fit / predict

↓

검증
Accuracy / F1 / AUC
MAE / MSE / R²
Cross Validation

↓

해석
feature_importances_
coef_
```