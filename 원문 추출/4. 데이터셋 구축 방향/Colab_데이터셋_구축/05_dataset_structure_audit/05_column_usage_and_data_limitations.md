# 수집 한계를 반영한 컬럼 사용·보류·제외 기준

참고 문서:

- [`05_dataset_columns_dictionary.md`](./05_dataset_columns_dictionary.md)
- [`05_dataset_analysis_questions_and_hypotheses.md`](./05_dataset_analysis_questions_and_hypotheses.md)
- [`05_machine_learning_prediction_targets.md`](./05_machine_learning_prediction_targets.md)

## 1. 확인된 데이터 한계

### 보이스피싱 자료

- 전체 통화가 아니라 핵심 구간만 발췌한 자료다.
- 기록된 길이와 시간은 원래 통화의 길이와 진행 단계를 대표하지 않는다.
- 발췌 기준이 사건마다 다르면 횟수형 특징도 편집 방식의 영향을 받는다.

### 정상 금융상담 자료

- 보이스피싱 자료와 수집기관, 전사 방식, 텍스트 형식, 익명화 방식, 통화 단위가 다를 수 있다.
- 정상·사기 분류의 높은 정확도가 실제 내용이 아니라 데이터 출처와 스타일 차이에서 나왔을 수 있다.

## 2. 컬럼 판단 상태

모든 컬럼은 분석 전에 다음 네 상태 중 하나로 지정한다.

| 상태 | 의미 | 처리 원칙 |
|---|---|---|
| 사용 | 의미·단위·생성방식이 확인되고 분석 목적에 적합 | 분석 또는 모델에 사용 |
| 조건부 사용 | 의미는 있으나 자동 추출·결측·편향 문제가 있음 | 검증·민감도 분석 후 사용 |
| 보류 | 의미나 값 구분이 불명확 | 데이터 사전·구축 코드·표본 검수 전까지 사용하지 않음 |
| 제외 | 분석 목적과 맞지 않거나 누수·편집 편향 위험이 큼 | 통계·모델 입력에서 제외 |

## 3. 기본적으로 사용할 컬럼

### 연결과 집계용

```text
file_id
case_id
turn_id
evidence_turn_id
conversation_id
source_id
```

- 데이터 연결과 중복 제거에 사용한다.
- 예측 모델의 독립변수로는 사용하지 않는다.

### 텍스트 확인용

```text
vp_cases.raw_full_text
vp_cases.normalized_full_text
vp_cases.raw_offender_text
vp_cases.normalized_offender_text
vp_cases.raw_victim_text
vp_cases.normalized_victim_text
vp_utterances.raw_text
vp_utterances.normalized_text
vp_utterances.content_text
normal_finance_calls.raw_text
normal_finance_calls.normalized_text
```

- 원문과 정규화문을 비교해 전처리 손실을 점검한다.
- 사칭 대상·사기유형 예측에는 범죄자 역할 텍스트를 우선 검토한다.
- 정상·사기 비교에는 동일한 정규화 규칙을 다시 적용한다.

### 자동 추출 결과 검증용

```text
evidence_text
extraction_method
extraction_confidence
extraction_version
label_status
verification_status
```

- 예측 특징이라기보다 자동 추출값의 신뢰성과 생성 방식을 확인하는 품질 컬럼이다.

## 4. 조건부로 사용할 컬럼

### 사기유형 라벨

```text
source_category
supervised_target
```

조건:

- 두 컬럼의 정의와 불일치 사례를 확인한다.
- 원본 파일명에서 직접 파생된 라벨인지 확인한다.
- 모델 목표가 `supervised_target`이면 `source_category`를 독립변수로 넣지 않는다.

### 사칭 라벨

```text
primary_impersonation_group
primary_impersonation_subtype
impersonation_group
impersonation_subtype
```

조건:

- `label_status`, `extraction_confidence`, `case_review_required`를 확인한다.
- 최소한 유형별 실제 근거 문장을 표본 검수한다.
- 목표변수로 사용하면 해당 사칭정보 파생 컬럼을 독립변수에서 제거한다.

### 요구행동과 전략

```text
primary_requested_action
action_group
action_type
strategy_type
*_count
strategy_diversity
risky_action_diversity
```

조건:

- 자동 추출 정탐률을 유형별로 확인한다.
- 단순 횟수보다 사건 내 존재 여부를 우선한다.
- 발췌 길이 차이에 민감한 횟수형 변수는 민감도 분석을 수행한다.
- `evidence_role`이 범죄자인지 확인한다.

### 화자 역할

```text
auto_role
role_heuristic_score
offender_turn_count
victim_turn_count
unknown_turn_count
unknown_role_ratio
```

조건:

- `auto_role` 표본을 사람이 검수한다.
- 역할 점수가 낮거나 `UNKNOWN` 비율이 높은 사건은 역할별 텍스트 분석에서 제외하거나 별도 보고한다.

### 금액

```text
amount_krw
amount_direction
amount_purpose
related_action_type
verified_loss_amount_krw
verification_status
```

조건:

- `amount_krw`는 언급 금액 분석에만 사용한다.
- 실제 피해액 분석은 검증 상태가 유효한 `verified_loss_amount_krw`만 사용한다.
- 금액 방향·용도가 `UNKNOWN`, `NO_DIRECTION` 등으로 많이 남으면 확정 분석에서 제외하고 값 분포만 보고한다.

## 5. 기본적으로 제외할 컬럼

### 시간·길이·순서 기반 예측변수

```text
duration_sec
case_start_sec
case_end_sec
start_sec
end_sec
first_mention_sec
first_mention_turn
first_risky_action_sec
first_risky_action_turn
mention_sec
turn_order
turn_count
```

제외 이유:

- 보이스피싱 자료가 전체 통화가 아니라 발췌본이다.
- 실제 통화의 길이·초반·후반·최초 등장 시점을 대표하지 않는다.
- 모델이 범죄 특징보다 편집·발췌 방식을 학습할 수 있다.

예외:

- 전사 순서 검증
- 이벤트 근거 문장의 앞뒤 문맥 복원
- ID·시간 정합성 검사
- 스타일 교란 진단 실험

### 경로·출처 식별 컬럼

```text
source_file
json_path
file_id
case_id
turn_id
source_id
conversation_id
```

제외 이유:

- 파일명과 경로에 사기유형·기관명이 포함될 수 있다.
- 모델이 의미가 아니라 원본 출처를 암기할 수 있다.

### 목표 라벨에서 파생된 컬럼

사칭 대상을 예측할 때 제외:

```text
primary_impersonation_group
primary_impersonation_subtype
primary_claimed_org_name
primary_claimed_role_title
primary_impersonation_evidence
mentioned_impersonation_subtypes
explicit_claim_subtypes
impersonation_transition_sequence
```

사기유형을 예측할 때 제외 후보:

```text
source_category
source_file
```

제외 이유는 라벨 누수다.

## 6. 값 구분이 애매한 컬럼의 처리 방법

### 바로 제외해야 하는 경우

- 컬럼 정의를 구축 코드나 데이터 사전에서도 확인할 수 없음
- 값이 대부분 하나의 범주이거나 결측
- 범주 간 의미 차이를 설명할 수 없음
- 자동 추출 신뢰도와 근거 문장이 없음
- 목표변수의 정답을 직접 포함함
- 원본 출처만 식별하는 값임

### 보류 후 재검토할 수 있는 경우

- `UNKNOWN`, `OTHER`, `MIXED`가 많지만 실제 문장이 존재함
- 자동 추출값이지만 `evidence_text`가 있음
- 범주명이 불일치하지만 매핑 근거가 있음
- 표본 수가 적지만 상위 그룹으로 통합 가능함

### 가능한 대안

1. 실제 값과 근거 문장을 유형별로 30~50건 표본 검수한다.
2. 의미가 같은 범주만 근거를 기록하고 통합한다.
3. 희소 세부유형은 상위 그룹 또는 `OTHER`로 통합한다.
4. 불명확한 값은 임의로 채우지 않고 `UNKNOWN`으로 유지한다.
5. 검수 완료 자료와 미검수 자료를 분리해 성능을 비교한다.
6. 해당 컬럼을 포함한 모델과 제외한 모델을 비교해 민감도를 확인한다.

## 7. 정상·사기 자료 스타일 교란 확인 절차

### 단계 A: 원자료 차이표 작성

- 텍스트 단위
- 화자 태그 형식
- 줄바꿈과 문장부호
- 익명화 토큰
- 숫자·영문 비율
- 평균 문자 수
- 상담기관·주제
- 전사 방식

### 단계 B: 공통 어휘와 화법 확인

- 집단별 상위 단어·2-gram
- 공통 단어 비율과 Jaccard 유사도
- 집단별 문서 존재율
- 정상과 사기에서 모두 등장하는 금융용어의 실제 문장
- 집단을 가장 잘 구분하는 단어가 내용인지 출처 표식인지 검수

### 단계 C: 스타일 전용 분류기

내용 단어를 제외하고 길이, 문장부호, 태그, 마스킹 비율만으로 `fraud_label`을 예측한다.

- 성능이 높으면 출처·스타일 누수가 강하다.
- 이 경우 기존 높은 정확도를 보이스피싱 탐지 성능으로 해석하지 않는다.

### 단계 D: 정규화·매칭 후 재실험

- 동일 텍스트 정규화
- 화자 태그·출처 표식 제거
- 유사한 텍스트 단위로 통일
- 가능한 경우 상담 주제와 길이를 매칭
- 동일 원본 그룹을 학습·테스트에 중복 배치하지 않음

정규화·매칭 후에도 성능이 유지될 때만 내용 기반 분류 가능성을 인정한다.

## 8. 현재 권장 분석 경로

### 경로 1: 보이스피싱 내부 분석 — 우선 진행

- 사기유형별 텍스트와 요구행동 비교
- 주요 사칭 그룹·세부 유형 분류
- 기관명 포함 모델과 마스킹 모델 비교
- 사칭·행동·전략 근거 문장 검수
- 유사 과거 사건 검색

장점:

- 같은 보이스피싱 수집체계 안에서 비교하므로 정상상담과의 출처 차이 문제가 상대적으로 작다.

### 경로 2: 정상 vs 보이스피싱 — 진단 후 조건부 진행

- 어휘·화법 중첩 분석
- 스타일 전용 분류기
- 정규화 전후 성능 비교
- 그룹 홀드아웃과 외부 평가

검증에 실패하면:

- 정상·사기 분류 모델을 최종 성과로 사용하지 않는다.
- ‘현재 데이터로는 내용 기반 탐지 성능과 출처 구분 성능을 분리하기 어렵다’고 결론 내린다.
- 동일 형식으로 수집한 정상·사기 비교자료를 추가 확보한다.

## 9. 최종 권장 우선순위

1. 컬럼별 사용·조건부·보류·제외 상태 확정
2. 자동 추출 라벨과 근거 문장 표본 검수
3. 보이스피싱 내부 사기유형 분류
4. 주요 사칭 그룹·세부유형 분류
5. 정상·사기 어휘와 화법 중첩 분석
6. 출처·스타일 교란 진단
7. 교란 검증을 통과한 경우에만 정상·사기 이진 분류
8. 동일 형식의 외부 테스트 자료 확보 및 최종 평가
