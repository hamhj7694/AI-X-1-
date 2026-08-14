# 02 데이터셋 품질 테스트 실행 가이드

## 목적

1단계에서 생성한 17개 영문 데이터테이블의 구조와 품질을 검사하고 핵심 발화 40개 테스트 표본을 생성한다.

## 필요한 파일

```text
02_dataset_quality_review.ipynb
review_voicephishing_datasets_v2.py
```

두 파일을 다음 위치에 넣는다.

```text
보이스피싱_분석/분석 결과/데이터셋/02_dataset_quality_review/
```

1단계 결과는 다음 위치에 있어야 한다.

```text
보이스피싱_분석/구축 데이터셋_v2/
```

## 실행 결과

- `table_summary.csv`: 17개 테이블의 행·열·결측 현황
- `column_inventory.csv`: 영문 컬럼과 데이터 형식 목록
- `quality_checks.csv`: ID 중복·누락·테이블 연결 오류 검사
- `human_review_sample_40.xlsx`: 의미 있는 핵심 발화 40개 테스트 표본
- `quality_test_manifest.json`: 실행 결과 요약

이 단계에서는 한글 컬럼 복사본이나 머신러닝 모델을 생성하지 않는다.
