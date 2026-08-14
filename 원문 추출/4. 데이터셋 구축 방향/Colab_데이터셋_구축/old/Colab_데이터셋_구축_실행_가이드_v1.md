# Colab 데이터셋 구축 실행 가이드

## 준비 파일

Google Drive의 `보이스피싱_분석` 폴더 안에 다음 파일과 폴더를 둡니다.

```text
보이스피싱_분석/
├─ 분석 결과/                       # cases.json이 들어 있는 3개 분류 폴더
│  └─ 00.금융분야 고객상담 데이터/ # 정상상담 ZIP, 프로젝트 바로 아래도 자동 인식
├─ 외부 데이터/
│  └─ df_postal.csv                 # 위치는 달라도 자동 검색됨
├─ 보이스피싱_데이터셋_구축_Colab.ipynb
└─ build_voicephishing_datasets.py
```

`build_voicephishing_datasets.py`와 `df_postal.csv`가 프로젝트 폴더 안에 없으면 노트북 실행 중 파일 선택 창이 열립니다. 선택한 파일은 Drive에 저장되어 다음 실행부터 자동으로 사용됩니다.

## 실행 방법

1. `보이스피싱_데이터셋_구축_Colab.ipynb`를 Colab으로 엽니다.
2. 셀을 위에서 아래로 순서대로 실행합니다.
3. Google Drive 접근 권한을 허용합니다.
4. 경로 셀에서 JSON과 정상상담 ZIP 개수를 확인합니다.
5. 마지막 검증 셀에 `기본 ID·입력 수·추가 비교표 검증 완료`가 표시되는지 확인합니다.

GPU는 필요하지 않습니다. 정상상담 ZIP이 많으면 압축파일을 읽는 데 시간이 걸릴 수 있습니다.

## 생성 결과

```text
구축 데이터셋/
├─ 01_standard_tables/
│  ├─ vp_files
│  ├─ vp_cases
│  ├─ vp_utterances
│  ├─ vp_impersonations
│  ├─ vp_requested_actions
│  ├─ vp_strategy_events
│  ├─ vp_amount_events
│  └─ normal_finance_calls
├─ 02_ml_tables/
│  ├─ fraud_detection_ml
│  ├─ fraud_type_ml
│  ├─ segment_detection_ml
│  └─ case_clustering_ml
├─ 03_dashboard_tables/
│  ├─ dashboard_case_summary
│  ├─ 보이스피싱_사건요약_한글
│  ├─ 우체국_피해사례_표준화
│  ├─ 사기유형_매핑표
│  └─ 사기유형_통합비교
└─ 04_reports/
   ├─ dataset_manifest.json
   └─ validation_report.json
```

각 표는 CSV와 Parquet으로 저장됩니다. CSV는 Excel·Power BI·Tableau에서, Parquet은 Colab·Python 분석에서 사용하면 됩니다.

논리적 데이터테이블은 표준 8개, 머신러닝용 4개, 대시보드용 5개로 총 17개입니다.
각각 CSV와 Parquet으로 저장되고 보고서 JSON 2개가 추가되어 전체 출력 파일은 총 36개입니다.

## 새 비교표의 용도

- `보이스피싱_사건요약_한글`: 전사 사건을 한 행씩 정리한 대시보드용 한글 표
- `vp_amount_events`: 금액이 나온 발화와 문맥을 기준으로 단순 언급·요구·합의·이체완료 주장을 구분한 표
- `우체국_피해사례_표준화`: `df_postal.csv`를 공통 사기유형·사칭대상 체계로 변환한 표
- `사기유형_매핑표`: 원본 값과 표준 분류의 대응 기준
- `사기유형_통합비교`: 두 출처의 사건 수·유형·사칭대상을 함께 비교하는 집계표

## 반드시 구분할 금액

- 우체국 자료의 `피해액`: 실제 피해사례 금액
- 전사자료의 `언급금액·요구금액·합의금액·이체주장금액`: 통화에서 탐지한 상태로 실제 송금·피해 여부는 확인 불가

두 금액은 직접 합산하거나 같은 의미로 비교하지 않습니다. 자동 추출한 사칭·요구행동·심리전략은 `SILVER` 라벨로 취급하고 보고서에 검수 한계를 적습니다.
