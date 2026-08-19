# 데모 모델 배치 위치

Colab `08_01`에서 생성한 최종 배포 파일을 다음 이름으로 이 폴더에 넣습니다.

```text
dashboard/models/final_voice_phishing_risk_pipeline.pkl
```

파일이 확인되면 `demo.py`가 다음 항목을 번들에서 자동으로 읽습니다.

- Window Random Forest 모델과 특징 순서
- Window Platt 보정기
- Case `STACKED_SAFE` Random Forest 모델과 특징 순서
- Case 보정 방식
- Window 생성 크기·간격
- Window·Case 경고 임계값

모델이 없거나 번들 구조가 다르면 임의 점수를 만들지 않고 화면에 준비 상태를 표시합니다.

Pickle/Joblib은 Python 코드를 실행할 수 있으므로 팀이 직접 Colab에서 생성한 파일만 사용합니다.
