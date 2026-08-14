# 05 데이터셋 전체 컬럼 사전

대상: `01_standard_tables`의 8개 논리 테이블

> CSV와 Parquet은 동일 테이블의 저장 형식이므로 컬럼 사전에서는 한 번만 기재합니다.  
> 한글 컬럼명은 이해를 위한 설명용 이름이며 원본 컬럼을 변경하지 않습니다.  
> `auto_*`, `*_score`, `extraction_*`, `label_status`와 전략·행동·금액 이벤트는 자동 처리 정보가 포함되므로 사람 확정값과 구분해야 합니다.

## 전체 요약

| 데이터셋 | 한글명 | 행 단위 | 컬럼 수 |
|---|---|---|---:|
| `vp_files` | 원본 파일 | 원본 미디어·전사 파일 1개 | 13 |
| `vp_cases` | 보이스피싱 사건 | 분리된 보이스피싱 사건 1건 | 61 |
| `vp_utterances` | 발화 | 사건 안의 발화 1개 | 18 |
| `vp_impersonations` | 사칭 이벤트 | 사칭 후보·언급 1건 | 29 |
| `vp_requested_actions` | 요구행동 이벤트 | 요구행동 추출 1건 | 18 |
| `vp_strategy_events` | 전략 이벤트 | 전략 표현 추출 1건 | 13 |
| `vp_amount_events` | 금액 이벤트 | 금액 표현 추출 1건 | 24 |
| `normal_finance_calls` | 정상 금융상담 | 정상 금융상담 통화 1건 | 12 |

## 연결키 요약

- `vp_files.file_id` → 모든 보이스피싱 표의 `file_id`: 원본 파일 기준 연결
- `vp_cases.case_id` → 발화·사칭·요구행동·전략·금액 표의 `case_id`: 사건 기준 1:N 연결
- `vp_utterances.turn_id` → 각 이벤트 표의 `evidence_turn_id`: 근거 발화 연결
- `normal_finance_calls`는 정상상담 별도 코퍼스이며 보이스피싱 표와 직접 연결되는 공통 사건 키가 없습니다.

## `vp_files` — 원본 파일

- 행 단위: 원본 미디어·전사 파일 1개
- 컬럼 수: 13

| 번호 | 영어 컬럼명 | 한글명 | 컬럼 역할 |
|---:|---|---|---|
| 1 | `file_id` | 파일 ID | 원본 파일을 식별하고 다른 보이스피싱 표와 연결하는 기본키 |
| 2 | `source_category` | 원본 분류 | 원자료에서 부여된 사기 유형·출처 분류 |
| 3 | `source_file` | 원본 파일 | 원본 미디어 파일명 또는 상대 경로 |
| 4 | `json_path` | JSON 경로 | 구축에 사용한 분석 결과 JSON 위치 |
| 5 | `publication_date` | 게시일 | 원자료의 공개·게시일; 실제 범죄 발생일과 같다고 단정할 수 없음 |
| 6 | `media_type` | 미디어 유형 | MP3 등 원본 매체 형식 |
| 7 | `duration_sec` | 파일 길이(초) | 원본 미디어의 전체 재생시간 |
| 8 | `case_count` | 사건 수 | 해당 원본에서 분리된 사건 개수 |
| 9 | `turn_count` | 발화 수 | 해당 원본에 포함된 전체 발화 개수 |
| 10 | `empty_transcript` | 빈 전사 여부 | 전사문이 비어 있는지 표시 |
| 11 | `multi_case_file` | 다중사건 파일 여부 | 한 원본 파일에서 여러 사건이 분리됐는지 표시 |
| 12 | `media_composition` | 미디어 구성 | 원본 매체의 구성 형태 분류 |
| 13 | `quality_flag` | 품질 상태 | 파일 수준 데이터 품질 표시 |

## `vp_cases` — 보이스피싱 사건

- 행 단위: 분리된 보이스피싱 사건 1건
- 컬럼 수: 61

| 번호 | 영어 컬럼명 | 한글명 | 컬럼 역할 |
|---:|---|---|---|
| 1 | `file_id` | 파일 ID | 상위 원본 파일 연결키 |
| 2 | `case_id` | 사건 ID | 사건을 식별하고 하위 상세표와 연결하는 기본키 |
| 3 | `source_category` | 원본 분류 | 원자료의 사기 유형·출처 분류 |
| 4 | `source_file` | 원본 파일 | 사건이 나온 원본 파일명 |
| 5 | `case_start_sec` | 사건 시작(초) | 원본 미디어 안에서 사건이 시작하는 상대시간 |
| 6 | `case_end_sec` | 사건 종료(초) | 원본 미디어 안에서 사건이 끝나는 상대시간 |
| 7 | `duration_sec` | 사건 길이(초) | 분리 사건의 지속시간 |
| 8 | `turn_count` | 발화 수 | 사건의 전체 발화 개수 |
| 9 | `speaker_count` | 화자 수 | 사건에서 식별된 화자 수 |
| 10 | `offender_turn_count` | 범죄자 발화 수 | 범죄자 역할로 분류된 발화 개수 |
| 11 | `victim_turn_count` | 피해자 발화 수 | 피해자 역할로 분류된 발화 개수 |
| 12 | `unknown_turn_count` | 역할불명 발화 수 | 화자 역할을 확정하지 못한 발화 개수 |
| 13 | `unknown_role_ratio` | 역할불명 비율 | 전체 발화 중 역할불명 발화 비율 |
| 14 | `short_turn_count` | 짧은 발화 수 | 짧은 발화로 표시된 개수 |
| 15 | `short_turn_ratio` | 짧은 발화 비율 | 전체 발화 중 짧은 발화 비율 |
| 16 | `raw_full_text` | 전체 원문 | 사건 전체의 원본 전사문 |
| 17 | `normalized_full_text` | 정규화 전체문 | 사건 전체 전사문을 정규화한 텍스트 |
| 18 | `raw_offender_text` | 범죄자 원문 | 범죄자 역할 발화만 모은 원문 |
| 19 | `normalized_offender_text` | 정규화 범죄자문 | 범죄자 역할 발화를 정규화한 텍스트 |
| 20 | `raw_victim_text` | 피해자 원문 | 피해자 역할 발화만 모은 원문 |
| 21 | `normalized_victim_text` | 정규화 피해자문 | 피해자 역할 발화를 정규화한 텍스트 |
| 22 | `asr_avg_logprob` | ASR 평균 로그확률 | 음성인식 결과의 평균 신뢰 관련 값 |
| 23 | `needs_review` | 검토 필요 여부 | 사건에 사람 검토가 필요한지 표시 |
| 24 | `quality_flag` | 품질 상태 | 사건 수준 데이터 품질 표시 |
| 25 | `label_status` | 라벨 상태 | 라벨의 생성·검수 상태 |
| 26 | `supervised_target` | 지도학습 목표 유형 | 학습용으로 선택된 사건 유형 라벨 |
| 27 | `primary_impersonation_group` | 주요 사칭 그룹 | 사건의 대표 사칭 대상 상위 그룹 |
| 28 | `primary_impersonation_subtype` | 주요 사칭 세부유형 | 사건의 대표 사칭 대상 세부 유형 |
| 29 | `primary_claimed_org_name` | 주요 사칭기관명 | 대표적으로 주장한 기관명 |
| 30 | `primary_claimed_role_title` | 주요 사칭직책 | 대표적으로 주장한 직책명 |
| 31 | `primary_impersonation_confidence_tier` | 주요 사칭 신뢰등급 | 대표 사칭 자동 선정 결과의 신뢰 등급 |
| 32 | `primary_impersonation_score` | 주요 사칭 점수 | 대표 사칭 후보의 자동 선정 점수 |
| 33 | `primary_impersonation_evidence` | 주요 사칭 근거 | 대표 사칭을 뒷받침하는 원문 문장 |
| 34 | `impersonation_count` | 사칭 건수 | 사건에서 추출된 사칭 기록 수 |
| 35 | `impersonation_group_count` | 사칭 그룹 수 | 사건에 나타난 서로 다른 사칭 상위 그룹 수 |
| 36 | `access_impersonation_subtype` | 접근 사칭유형 | 통화 접근 단계에서의 사칭 세부 유형 |
| 37 | `secondary_impersonation_subtypes` | 보조 사칭유형 | 대표 사칭 외에 추출된 보조 사칭 유형 목록 |
| 38 | `mentioned_impersonation_subtypes` | 언급 사칭유형 | 사건에서 언급된 사칭 유형 목록 |
| 39 | `explicit_claim_subtypes` | 명시 주장 사칭유형 | 화자가 신분을 명시적으로 주장한 사칭 유형 목록 |
| 40 | `impersonation_transition_sequence` | 사칭 전환 순서 | 통화 중 사칭 대상이 전환된 순서 |
| 41 | `impersonation_review_required` | 사칭 검토 필요 | 사칭 결과에 추가 검토가 필요한지 표시 |
| 42 | `impersonation_label_source` | 사칭 라벨 출처 | 사칭 라벨이 만들어진 근거·출처 |
| 43 | `primary_requested_action` | 주요 요구행동 | 사건의 대표 피해자 요구행동 |
| 44 | `requested_action_count` | 요구행동 수 | 사건에서 추출된 요구행동 개수 |
| 45 | `risky_action_diversity` | 위험행동 다양성 | 서로 다른 위험 요구행동 유형 수 |
| 46 | `first_risky_action_turn` | 최초 위험행동 발화순서 | 위험 요구가 처음 등장한 발화 순서 |
| 47 | `first_risky_action_sec` | 최초 위험행동 시점(초) | 위험 요구가 처음 등장한 상대시간 |
| 48 | `mentioned_amount_max_krw` | 최대 언급금액(원) | 사건에서 언급된 금액 중 최대값; 실제 피해액과 다를 수 있음 |
| 49 | `risky_action_count` | 위험행동 건수 | 사건에서 검출된 위험 요구행동 수 |
| 50 | `authority_trust_count` | 권위·신뢰 표현 수 | 권위 또는 신뢰 형성 규칙에 검출된 표현 수 |
| 51 | `behavior_control_count` | 행동통제 표현 수 | 피해자 행동 통제 규칙에 검출된 표현 수 |
| 52 | `benefit_promise_count` | 혜택약속 표현 수 | 혜택·이익 약속 규칙에 검출된 표현 수 |
| 53 | `fear_threat_count` | 공포·위협 표현 수 | 공포·협박 규칙에 검출된 표현 수 |
| 54 | `information_extraction_count` | 정보요구 표현 수 | 개인·금융정보 탐색 규칙에 검출된 표현 수 |
| 55 | `isolation_secrecy_count` | 고립·비밀유지 표현 수 | 고립·비밀 유지 규칙에 검출된 표현 수 |
| 56 | `legitimacy_building_count` | 정당성형성 표현 수 | 합법성·정당성 연출 규칙에 검출된 표현 수 |
| 57 | `money_request_count` | 금전요구 표현 수 | 금전 요구 규칙에 검출된 표현 수 |
| 58 | `resistance_handling_count` | 저항대응 표현 수 | 피해자의 의심·저항 대응 규칙에 검출된 표현 수 |
| 59 | `urgency_time_pressure_count` | 긴급·시간압박 표현 수 | 긴급성·시간 압박 규칙에 검출된 표현 수 |
| 60 | `strategy_diversity` | 전략 다양성 | 사건에서 검출된 서로 다른 전략 유형 수 |
| 61 | `has_multiple_impersonations` | 복수사칭 여부 | 사건에 복수 사칭 유형이 존재하는지 표시 |

## `vp_utterances` — 발화

- 행 단위: 사건 안의 발화 1개
- 컬럼 수: 18

| 번호 | 영어 컬럼명 | 한글명 | 컬럼 역할 |
|---:|---|---|---|
| 1 | `file_id` | 파일 ID | 원본 파일 연결키 |
| 2 | `case_id` | 사건 ID | 상위 사건 연결키 |
| 3 | `turn_id` | 발화 ID | 발화를 식별하고 증거 이벤트와 연결하는 기본키 |
| 4 | `turn_order` | 발화 순서 | 사건 안에서 발화가 등장한 순서 |
| 5 | `start_sec` | 발화 시작(초) | 원본 미디어 안의 발화 시작 상대시간 |
| 6 | `end_sec` | 발화 종료(초) | 원본 미디어 안의 발화 종료 상대시간 |
| 7 | `duration_sec` | 발화 길이(초) | 발화 지속시간 |
| 8 | `speaker_id` | 화자 ID | 원본 전사에서 구분된 화자 식별값 |
| 9 | `auto_role` | 자동 화자역할 | 규칙으로 추정한 범죄자·피해자·불명 역할 |
| 10 | `role_heuristic_score` | 화자역할 점수 | 자동 화자 역할 추정 점수 |
| 11 | `raw_text` | 발화 원문 | 해당 발화의 원본 전사문 |
| 12 | `normalized_text` | 정규화 발화문 | 발화 원문을 정규화한 텍스트 |
| 13 | `content_text` | 분석용 발화문 | 분석에 사용하도록 정리한 발화 본문 |
| 14 | `avg_logprob` | 평균 로그확률 | 발화 음성인식 신뢰 관련 값 |
| 15 | `voice_modified` | 변조음성 여부 | 변조 음성으로 표시됐는지 여부 |
| 16 | `is_short_turn` | 짧은 발화 여부 | 짧은 발화로 판정됐는지 표시 |
| 17 | `is_low_information` | 저정보 발화 여부 | 분석 정보량이 낮은 발화인지 표시 |
| 18 | `quality_flag` | 품질 상태 | 발화 수준 데이터 품질 표시 |

## `vp_impersonations` — 사칭 이벤트

- 행 단위: 사칭 후보·언급 1건
- 컬럼 수: 29

| 번호 | 영어 컬럼명 | 한글명 | 컬럼 역할 |
|---:|---|---|---|
| 1 | `impersonation_id` | 사칭 ID | 사칭 기록 기본키 |
| 2 | `file_id` | 파일 ID | 원본 파일 연결키 |
| 3 | `case_id` | 사건 ID | 상위 사건 연결키 |
| 4 | `evidence_turn_id` | 근거 발화 ID | 사칭 근거가 나온 발화 연결키 |
| 5 | `evidence_role` | 근거 화자역할 | 근거 문장을 말한 화자 역할 |
| 6 | `impersonation_group` | 사칭 그룹 | 사칭 대상 상위 그룹 |
| 7 | `impersonation_subtype` | 사칭 세부유형 | 사칭 대상 세부 유형 |
| 8 | `claimed_org_name_raw` | 주장 기관명 원문 | 원문에서 추출된 기관명 |
| 9 | `claimed_org_name_normalized` | 정규화 주장 기관명 | 표준화한 주장 기관명 |
| 10 | `claimed_department_normalized` | 정규화 주장 부서명 | 표준화한 주장 부서명 |
| 11 | `claimed_role_title_normalized` | 정규화 주장 직책 | 표준화한 주장 직책명 |
| 12 | `claimed_person_name_raw` | 주장 인물명 원문 | 원문에서 추출된 인물명 |
| 13 | `claimed_person_name_masked` | 마스킹 주장 인물명 | 개인정보를 가린 주장 인물명 |
| 14 | `claimed_relationship` | 주장 관계 | 가족·지인 등 주장한 관계 |
| 15 | `identity_claim_type` | 신분주장 유형 | 신분을 주장한 방식의 분류 |
| 16 | `is_primary_impersonation` | 주요 사칭 여부 | 사건의 대표 사칭으로 선정됐는지 표시 |
| 17 | `first_mention_turn` | 최초 언급 발화순서 | 해당 사칭이 처음 등장한 발화 순서 |
| 18 | `first_mention_sec` | 최초 언급 시점(초) | 해당 사칭이 처음 등장한 상대시간 |
| 19 | `mention_count` | 언급 수 | 해당 사칭 표현의 언급 횟수 |
| 20 | `evidence_text` | 근거 문장 | 사칭 추출의 실제 근거 문장 |
| 21 | `institution_role` | 기관 역할 | 통화에서 해당 기관이 맡은 역할 분류 |
| 22 | `case_candidate_score` | 사건 후보 점수 | 사건 내 대표 사칭 후보 점수 |
| 23 | `candidate_rank` | 후보 순위 | 사건 안에서 사칭 후보의 순위 |
| 24 | `primary_confidence_tier` | 주요 사칭 신뢰등급 | 대표 사칭 선정 신뢰 등급 |
| 25 | `case_review_required` | 사건 검토 필요 | 사칭 결과의 사건 단위 검토 필요 여부 |
| 26 | `extraction_method` | 추출 방법 | 사칭 레코드를 생성한 방법 |
| 27 | `extraction_confidence` | 추출 신뢰도 | 자동 추출 신뢰값 |
| 28 | `extraction_version` | 추출 버전 | 사용된 추출 규칙·로직 버전 |
| 29 | `label_status` | 라벨 상태 | 사칭 라벨의 생성·검수 상태 |

## `vp_requested_actions` — 요구행동 이벤트

- 행 단위: 요구행동 추출 1건
- 컬럼 수: 18

| 번호 | 영어 컬럼명 | 한글명 | 컬럼 역할 |
|---:|---|---|---|
| 1 | `action_id` | 행동 ID | 요구행동 기록 기본키 |
| 2 | `file_id` | 파일 ID | 원본 파일 연결키 |
| 3 | `case_id` | 사건 ID | 상위 사건 연결키 |
| 4 | `evidence_turn_id` | 근거 발화 ID | 요구행동 근거 발화 연결키 |
| 5 | `evidence_role` | 근거 화자역할 | 근거 문장을 말한 화자 역할 |
| 6 | `action_group` | 행동 그룹 | 요구행동 상위 그룹 |
| 7 | `action_type` | 행동 세부유형 | 요구행동의 세부 유형 |
| 8 | `action_status` | 행동 상태 | 요구가 언급·확인된 상태 분류 |
| 9 | `mentioned_amount_krw` | 관련 언급금액(원) | 요구행동과 함께 언급된 금액 |
| 10 | `is_primary_action` | 주요 행동 여부 | 사건의 대표 요구행동인지 표시 |
| 11 | `first_mention_turn` | 최초 언급 발화순서 | 해당 요구행동 최초 등장 순서 |
| 12 | `first_mention_sec` | 최초 언급 시점(초) | 해당 요구행동 최초 등장 상대시간 |
| 13 | `mention_count` | 언급 수 | 해당 요구행동 언급 횟수 |
| 14 | `evidence_text` | 근거 문장 | 요구행동 추출의 실제 근거 문장 |
| 15 | `extraction_method` | 추출 방법 | 요구행동 레코드를 생성한 방법 |
| 16 | `extraction_confidence` | 추출 신뢰도 | 자동 추출 신뢰값 |
| 17 | `extraction_version` | 추출 버전 | 사용된 추출 규칙·로직 버전 |
| 18 | `label_status` | 라벨 상태 | 요구행동 라벨의 생성·검수 상태 |

## `vp_strategy_events` — 전략 이벤트

- 행 단위: 전략 표현 추출 1건
- 컬럼 수: 13

| 번호 | 영어 컬럼명 | 한글명 | 컬럼 역할 |
|---:|---|---|---|
| 1 | `strategy_event_id` | 전략 이벤트 ID | 전략 표현 기록 기본키 |
| 2 | `file_id` | 파일 ID | 원본 파일 연결키 |
| 3 | `case_id` | 사건 ID | 상위 사건 연결키 |
| 4 | `evidence_turn_id` | 근거 발화 ID | 전략 표현 근거 발화 연결키 |
| 5 | `evidence_role` | 근거 화자역할 | 근거 문장을 말한 화자 역할 |
| 6 | `turn_order` | 발화 순서 | 전략 표현이 나온 사건 내 발화 순서 |
| 7 | `mention_sec` | 언급 시점(초) | 전략 표현이 나온 상대시간 |
| 8 | `strategy_type` | 전략 유형 | 규칙으로 검출된 전략 표현 유형 |
| 9 | `evidence_text` | 근거 문장 | 전략 검출의 실제 근거 문장 |
| 10 | `extraction_method` | 추출 방법 | 전략 이벤트를 생성한 방법 |
| 11 | `extraction_confidence` | 추출 신뢰도 | 자동 추출 신뢰값 |
| 12 | `extraction_version` | 추출 버전 | 사용된 추출 규칙·로직 버전 |
| 13 | `label_status` | 라벨 상태 | 전략 라벨의 생성·검수 상태 |

## `vp_amount_events` — 금액 이벤트

- 행 단위: 금액 표현 추출 1건
- 컬럼 수: 24

| 번호 | 영어 컬럼명 | 한글명 | 컬럼 역할 |
|---:|---|---|---|
| 1 | `amount_event_id` | 금액 이벤트 ID | 금액 기록 기본키 |
| 2 | `file_id` | 파일 ID | 원본 파일 연결키 |
| 3 | `case_id` | 사건 ID | 상위 사건 연결키 |
| 4 | `evidence_turn_id` | 근거 발화 ID | 금액 판단 근거 발화 연결키 |
| 5 | `amount_source_turn_id` | 금액 원천 발화 ID | 금액 표현이 직접 나온 발화 연결키 |
| 6 | `evidence_role` | 근거 화자역할 | 금액 근거를 말한 화자 역할 |
| 7 | `turn_order` | 발화 순서 | 금액이 등장한 사건 내 발화 순서 |
| 8 | `mention_sec` | 언급 시점(초) | 금액이 등장한 상대시간 |
| 9 | `amount_krw` | 언급금액(원) | 원화로 정규화한 금액; 실제 피해액과 다를 수 있음 |
| 10 | `amount_text` | 금액 원문 | 전사문에 나타난 원래 금액 표현 |
| 11 | `amount_status` | 금액 상태 | 금액이 언급·확정된 상태 분류 |
| 12 | `amount_direction` | 금액 방향 | 송금·입금·출금 등 자금 이동 방향 분류 |
| 13 | `amount_purpose` | 금액 용도 | 대출금·수수료·세금·잔액 등 금액 용도 분류 |
| 14 | `amount_direction_evidence` | 금액 방향 근거 | 자금 방향 판단에 사용한 문장 |
| 15 | `amount_direction_confidence` | 금액 방향 신뢰도 | 자금 방향 자동 판단 신뢰값 |
| 16 | `related_action_type` | 관련 행동유형 | 금액과 연결된 요구행동 유형 |
| 17 | `evidence_text` | 근거 문장 | 금액 추출의 실제 근거 문장 |
| 18 | `inferred_from_context` | 문맥추정 여부 | 금액 정보가 주변 문맥에서 추론됐는지 표시 |
| 19 | `verified_loss_amount_krw` | 검증 피해액(원) | 별도 확인을 거친 실제 피해액 필드 |
| 20 | `extraction_method` | 추출 방법 | 금액 이벤트를 생성한 방법 |
| 21 | `extraction_confidence` | 추출 신뢰도 | 자동 추출 신뢰값 |
| 22 | `extraction_version` | 추출 버전 | 사용된 추출 규칙·로직 버전 |
| 23 | `verification_status` | 검증 상태 | 피해액·금액 정보의 검증 상태 |
| 24 | `label_status` | 라벨 상태 | 금액 라벨의 생성·검수 상태 |

## `normal_finance_calls` — 정상 금융상담

- 행 단위: 정상 금융상담 통화 1건
- 컬럼 수: 12

| 번호 | 영어 컬럼명 | 한글명 | 컬럼 역할 |
|---:|---|---|---|
| 1 | `conversation_id` | 통화 ID | 정상상담 통화를 식별하는 기본키 |
| 2 | `source_id` | 원자료 ID | 정상상담 원자료의 식별자 |
| 3 | `source_date` | 상담일 | 원자료에 기록된 상담 날짜 |
| 4 | `source_institution` | 상담기관 | 정상상담을 제공한 기관 |
| 5 | `consulting_category` | 상담 대분류 | 원자료의 상담 업무 대분류 |
| 6 | `consulting_topic` | 상담 주제 | 원자료의 세부 상담 주제 |
| 7 | `raw_text` | 상담 원문 | 정상상담의 원본 전사문 |
| 8 | `normalized_text` | 정규화 상담문 | 화자 태그 등을 정리한 상담 텍스트 |
| 9 | `turn_count` | 발화 수 | 정상상담 통화의 발화 개수 |
| 10 | `client_age_group` | 고객 연령대 | 원자료에 기록된 고객 연령 구간 |
| 11 | `client_gender` | 고객 성별 | 원자료에 기록된 고객 성별 |
| 12 | `dataset_split` | 원자료 분할 | 원자료의 TRAIN·VALIDATION 구분 |

## 해석 시 공통 주의사항

1. `source_category`는 원자료 분류이고 `supervised_target`은 학습용으로 선택된 라벨이므로 동일 개념이라고 가정하지 않습니다.
2. `amount_krw`와 `mentioned_amount_*`는 통화에서 언급된 금액이며 실제 피해액이 아닐 수 있습니다.
3. `auto_role`은 자동 추정 화자 역할입니다. `UNKNOWN`과 `role_heuristic_score`를 함께 확인해야 합니다.
4. 사칭·행동·전략·금액 상세표는 한 사건에 여러 행이 존재합니다. 사건 수를 계산할 때 `case_id`를 중복 제거합니다.
5. 전략·사칭·행동 자동 추출 결과는 반드시 `evidence_text`, `extraction_method`, `extraction_confidence`, `label_status`와 함께 검토합니다.
6. `publication_date`와 `source_date`는 데이터에 기록된 날짜이며 실제 범죄 발생일을 의미하는지는 별도 확인이 필요합니다.
