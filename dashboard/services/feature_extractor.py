from __future__ import annotations

import re
from typing import Any


WINDOW_TURNS = 10
WINDOW_STRIDE = 5
EXTRACTOR_NAME = "RULE_PROXY_V1"
EXTRACTOR_MATCHES_TRAINING_PIPELINE = False

SPEAKER_PREFIX = re.compile(
    r"^\s*(범인|가해자|피해자|상담원|고객|직원|수사관|검사|경찰|화자\s*\d+)\s*[:：]\s*",
    re.IGNORECASE,
)

PATTERNS: dict[str, list[str]] = {
    "imp_financial": [
        r"(은행|카드사|카드회사|저축은행|캐피탈|금융감독원|금감원).{0,25}(직원|상담원|담당|소속|입니다|에서\s*연락)",
        r"(직원|상담원|담당자).{0,20}(은행|카드사|저축은행|캐피탈|금융감독원|금감원)",
    ],
    "imp_public": [
        r"(검찰|검찰청|경찰|경찰청|법원|수사관|검사).{0,25}(담당|소속|입니다|에서\s*연락|수사)",
        r"(수사관|검사|경찰).{0,15}(입니다|인데요|담당)",
    ],
    "imp_personal": [
        r"(아들|딸|엄마|어머니|아빠|아버지|가족|친구|지인).{0,20}(나야|저야|인데|급해|사고|납치|문제)",
    ],
    "strategy_authority": [
        r"검찰|검찰청|경찰|법원|수사관|검사|금융감독원|금감원",
        r"법적\s*조치|수사\s*중|사건번호|담당\s*(수사관|검사|직원)",
    ],
    "strategy_fear": [
        r"체포|구속|압류|처벌|범죄|공범|고소|수사|피해금|명의도용|문제가\s*생",
        r"계좌가\s*(정지|압류)|신용.{0,10}(문제|하락)",
    ],
    "strategy_isolation": [
        r"아무에게도\s*말|누구에게도\s*말|비밀로|보안상\s*말하면\s*안",
        r"통화\s*(끊지|유지)|전화를\s*(끊지|끊으면\s*안)|다른\s*사람.{0,15}(연락|말).{0,10}(하지|마)",
    ],
    "strategy_urgency": [
        r"지금\s*바로|당장|즉시|오늘\s*안에|오늘까지|빨리|서둘러|시간이\s*없|시간\s*없",
        r"곧\s*마감|지체하면|늦으면|지금\s*처리",
    ],
    "strategy_money_request": [
        r"(송금|이체|입금|납부|상환|출금|인출|현금).{0,25}(하세요|해주|하셔|바랍니다|필요)",
        r"(돈|금액|수수료|보증금).{0,20}(보내|입금|납부|이체)",
    ],
    "strategy_legitimacy": [
        r"본인\s*확인|신원\s*확인|공식\s*(절차|기관|번호)|대표번호|사건번호|접수번호",
        r"담당자|확인\s*절차|보안\s*절차|규정상|법적으로",
    ],
    "strategy_info_extraction": [
        r"(계좌번호|주민등록번호|주민번호|카드번호|OTP|비밀번호|인증번호|신분증).{0,25}(말씀|알려|불러|보내|입력|확인)",
        r"(말씀|알려|불러|보내|입력).{0,20}(계좌번호|주민등록번호|카드번호|OTP|비밀번호|인증번호)",
    ],
    "strategy_benefit": [
        r"저금리|금리\s*인하|환급|혜택|지원금|대출\s*승인|한도\s*상향|수수료\s*면제",
        r"돌려드|보상해드|지급해드|혜택을\s*드",
    ],
    "money_movement_request": [
        r"(송금|이체|입금|출금|인출|현금\s*준비|상환|납부).{0,25}(하세요|해주|하셔|바랍니다|해야)",
        r"(보내|입금|이체|납부).{0,15}(주세|주세요|하세요|하셔)",
    ],
    "sensitive_info_request": [
        r"(계좌번호|주민등록번호|주민번호|카드번호|신분증).{0,25}(알려|말씀|불러|보내|찍어서|제출)",
    ],
    "auth_info_request": [
        r"(OTP|비밀번호|인증번호|보안카드).{0,25}(알려|말씀|불러|입력|전송)",
    ],
    "device_control_request": [
        r"(앱|어플|애플리케이션|프로그램).{0,20}(설치|깔아|다운로드)",
        r"원격\s*(제어|지원)|화면\s*공유",
    ],
    "isolation_request": [
        r"통화\s*(끊지|유지)|전화를\s*(끊지|끊으면\s*안)",
        r"(가족|은행|경찰|다른\s*사람).{0,20}(연락|전화).{0,12}(하지|마)",
    ],
}

FEATURE_META = {
    "imp_public": ("사칭", "공공기관 사칭"),
    "imp_financial": ("사칭", "금융기관 사칭"),
    "imp_personal": ("사칭", "지인·가족 사칭"),
    "strategy_authority": ("심리전략", "권위·신뢰 형성"),
    "strategy_fear": ("심리전략", "공포·위협"),
    "strategy_isolation": ("심리전략", "고립·비밀 유지"),
    "strategy_urgency": ("심리전략", "긴급성·시간 압박"),
    "strategy_money_request": ("심리전략", "금전 요구 압박"),
    "strategy_legitimacy": ("심리전략", "절차·정당성 강조"),
    "strategy_info_extraction": ("심리전략", "정보 추출"),
    "strategy_benefit": ("심리전략", "이익·혜택 제안"),
    "money_movement_request": ("요구행동", "송금·인출·납부 요구"),
    "sensitive_info_request": ("요구행동", "민감정보 요구"),
    "auth_info_request": ("요구행동", "인증정보 요구"),
    "device_control_request": ("요구행동", "앱 설치·원격제어 요구"),
    "isolation_request": ("요구행동", "외부 연락 차단 요구"),
    "strategy_diversity_sem": ("복합신호", "심리전략 다양성"),
    "action_diversity_sem": ("복합신호", "요구행동 다양성"),
    "signal_family_count_sem": ("복합신호", "위험신호 계열 수"),
    "signal_family_count_delta_sem": ("복합신호", "위험신호 증가량"),
    "ix_identityclaim_authority_sem": ("상호작용", "신분주장 × 권위"),
    "ix_info_sensitive_sem": ("상호작용", "정보추출 × 민감정보"),
}

CASE_FEATURES = [
    "strategy_authority",
    "strategy_fear",
    "imp_public",
    "imp_financial",
    "strategy_info_extraction_sem",
    "sensitive_info_request_sem",
    "auth_info_request_sem",
    "strategy_diversity_sem",
    "action_diversity_sem",
    "signal_family_count_sem",
    "ix_identityclaim_authority_sem",
    "ix_info_sensitive_sem",
]

WINDOW_FEATURES = [
    feature if feature != "signal_family_count_sem" else "signal_family_count_delta_sem"
    for feature in CASE_FEATURES
]


def normalize_text(text: str) -> str:
    return " ".join(str(text or "").strip().split())


def parse_turns(raw_text: str) -> list[dict[str, Any]]:
    raw = str(raw_text or "")
    lines = [normalize_text(line) for line in raw.splitlines()]
    lines = [line for line in lines if line]
    # 화자 표기가 없는 한 문단도 문장 단위 발화로 받아들인다. 화자 추정은 하지 않는다.
    if len(lines) == 1 and not SPEAKER_PREFIX.match(lines[0]):
        sentences = [normalize_text(item) for item in re.split(r"(?<=[.!?。！？])\s+", lines[0])]
        lines = [item for item in sentences if item]
    if not lines and normalize_text(raw):
        lines = [normalize_text(raw)]

    turns = []
    for index, line in enumerate(lines, start=1):
        match = SPEAKER_PREFIX.match(line)
        speaker = match.group(1) if match else "미지정"
        text = line[match.end() :] if match else line
        turns.append({"turn_order": index, "speaker": speaker, "text": text, "raw_text": line})
    return turns


def mask_personal_information(text: str) -> str:
    masked = re.sub(r"(?<!\d)01[016789][- ]?\d{3,4}[- ]?\d{4}(?!\d)", "[전화번호]", text)
    masked = re.sub(r"(?<!\d)\d{6}[- ]?[1-4]\d{6}(?!\d)", "[주민번호]", masked)
    masked = re.sub(r"(?<!\d)\d{2,6}[- ]\d{2,6}[- ]\d{2,8}(?!\d)", "[계좌번호]", masked)
    return masked


def make_windows(turns: list[dict[str, Any]], window_turns: int = WINDOW_TURNS, stride: int = WINDOW_STRIDE) -> list[dict[str, Any]]:
    windows = []
    if len(turns) < window_turns:
        return windows
    for window_index, start in enumerate(range(0, len(turns) - window_turns + 1, stride)):
        subset = turns[start : start + window_turns]
        windows.append(
            {
                "window_index": window_index,
                "start_turn": start + 1,
                "end_turn": start + window_turns,
                "turns": subset,
                "text": " ".join(turn["text"] for turn in subset),
            }
        )
    return windows


def _pattern_hits(text: str, patterns: list[str]) -> list[str]:
    hits = []
    for pattern in patterns:
        for match in re.finditer(pattern, text, flags=re.IGNORECASE):
            value = normalize_text(match.group(0))
            if value and value not in hits:
                hits.append(value)
    return hits


def extract_features(text: str) -> dict[str, float]:
    normalized = normalize_text(text)
    raw = {name: int(bool(_pattern_hits(normalized, patterns))) for name, patterns in PATTERNS.items()}

    features: dict[str, float] = dict(raw)
    for base in (
        "strategy_info_extraction",
        "sensitive_info_request",
        "auth_info_request",
        "strategy_urgency",
        "strategy_money_request",
        "strategy_legitimacy",
        "strategy_benefit",
        "money_movement_request",
        "device_control_request",
    ):
        features[f"{base}_sem"] = float(raw.get(base, 0))

    features["identity_claim_any_cue"] = float(
        max(raw.get("imp_public", 0), raw.get("imp_financial", 0), raw.get("imp_personal", 0))
    )
    strategy_columns = [
        "strategy_authority",
        "strategy_fear",
        "strategy_isolation",
        "strategy_urgency_sem",
        "strategy_money_request_sem",
        "strategy_legitimacy_sem",
        "strategy_info_extraction_sem",
        "strategy_benefit_sem",
    ]
    action_columns = [
        "money_movement_request_sem",
        "sensitive_info_request_sem",
        "auth_info_request_sem",
        "device_control_request_sem",
        "isolation_request",
    ]
    features["strategy_diversity_sem"] = float(sum(features.get(name, 0) for name in strategy_columns))
    features["action_diversity_sem"] = float(sum(features.get(name, 0) for name in action_columns))
    features["ix_identityclaim_authority_sem"] = float(
        features["identity_claim_any_cue"] * features.get("strategy_authority", 0)
    )
    features["ix_info_sensitive_sem"] = float(
        features.get("strategy_info_extraction_sem", 0) * features.get("sensitive_info_request_sem", 0)
    )
    family_columns = [
        "identity_claim_any_cue",
        "strategy_authority",
        "strategy_fear",
        "strategy_isolation",
        "strategy_urgency_sem",
        "strategy_money_request_sem",
        "strategy_legitimacy_sem",
        "strategy_info_extraction_sem",
        "money_movement_request_sem",
        "sensitive_info_request_sem",
        "auth_info_request_sem",
        "device_control_request_sem",
        "isolation_request",
    ]
    features["signal_family_count_sem"] = float(sum(features.get(name, 0) for name in family_columns))
    return features


def extract_evidence(turns: list[dict[str, Any]]) -> list[dict[str, Any]]:
    evidence = []
    for turn in turns:
        for feature, patterns in PATTERNS.items():
            hits = _pattern_hits(turn["text"], patterns)
            if not hits:
                continue
            category, label = FEATURE_META.get(feature, ("기타", feature))
            evidence.append(
                {
                    "발화번호": turn["turn_order"],
                    "화자": turn["speaker"],
                    "위험범주": category,
                    "탐지변수": label,
                    "모델변수": feature,
                    "근거표현": " · ".join(hits),
                    "근거발화": mask_personal_information(turn["raw_text"]),
                    "추출방식": "RULE_CANDIDATE",
                }
            )
    return evidence
