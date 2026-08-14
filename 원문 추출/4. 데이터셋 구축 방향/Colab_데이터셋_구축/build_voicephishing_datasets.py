from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from zipfile import ZipFile

import numpy as np
import pandas as pd


RANDOM_SEED = 42
MIN_TEXT_LENGTH = 20
NORMAL_TO_FRAUD_RATIO = 3
WINDOW_SIZES = (5, 10)
WINDOW_STRIDE_RATIO = 0.5

KOREAN_CATEGORY_MAP = {
    "LOAN_FRAUD": "대출사기형",
    "INSTITUTION_IMPERSONATION": "수사기관사칭형",
    "MIXED_UNKNOWN": "혼합·미분류",
    "UNKNOWN": "미분류",
}

KOREAN_IMPERSONATION_GROUP_MAP = {
    "PUBLIC_AGENCY": "공공기관",
    "FINANCIAL_INSTITUTION": "금융기관",
    "DELIVERY_LOGISTICS": "배송·물류기관",
    "TELECOM_COMPANY": "통신기관",
    "FAMILY": "가족",
    "ACQUAINTANCE": "지인",
    "EMPLOYER_RECRUITER": "고용·채용관계자",
    "ONLINE_PLATFORM": "온라인플랫폼",
    "OTHER": "기타",
    "UNKNOWN": "미분류",
    "NOT_MENTIONED": "언급없음",
}

KOREAN_IMPERSONATION_SUBTYPE_MAP = {
    "PROSECUTION": "검찰",
    "POLICE": "경찰",
    "COURT": "법원",
    "FSS": "금융감독원",
    "FSC": "금융위원회",
    "TAX_AUTHORITY": "세무기관",
    "GOVERNMENT_OTHER": "기타정부기관",
    "PUBLIC_UNKNOWN": "공공기관_세부불명",
    "BANK": "은행",
    "SAVINGS_BANK": "저축은행",
    "CARD_COMPANY": "카드사",
    "CAPITAL_COMPANY": "캐피탈사",
    "LOAN_COMPANY": "대출업체",
    "INSURANCE_COMPANY": "보험사",
    "SECURITIES_COMPANY": "증권사",
    "FINANCIAL_ASSOCIATION": "금융협회",
    "FINANCIAL_UNKNOWN": "금융기관_세부불명",
    "POST_OFFICE": "우체국",
    "DELIVERY_COMPANY": "택배·배송회사",
    "TELECOM": "통신사",
    "KIDNAPPING_CLAIM": "가족납치협박",
    "BUSINESS_CONTACT": "업무관계자",
    "PERSONAL_CONTACT": "개인지인",
    "RECRUITER": "채용담당자",
    "NOT_MENTIONED": "언급없음",
}

KOREAN_ROLE_TITLE_MAP = {
    "PROSECUTOR": "검사",
    "INVESTIGATOR": "수사관",
    "POLICE_OFFICER": "경찰관",
    "DETECTIVE": "형사",
    "COURT_OFFICIAL": "법원직원",
    "FSS_INVESTIGATOR": "금융감독기관조사관",
    "BANK_EMPLOYEE": "은행원",
    "LOAN_OFFICER": "대출담당자",
    "LOAN_REVIEWER": "대출심사담당자",
    "FINANCIAL_COUNSELOR": "금융상담사",
    "CARD_COMPANY_EMPLOYEE": "카드사직원",
    "DELIVERY_AGENT": "배송기사",
    "RECRUITER": "채용담당자",
    "MANAGER": "관리자급직원",
    "OTHER_ROLE": "기타직책",
    "UNKNOWN": "미분류",
    "NOT_MENTIONED": "언급없음",
}

KOREAN_RELATIONSHIP_MAP = {
    "SON": "아들", "DAUGHTER": "딸", "CHILD": "자녀",
    "MOTHER": "어머니", "FATHER": "아버지", "PARENT": "부모",
    "SPOUSE": "배우자", "SIBLING": "형제자매", "RELATIVE": "친척",
    "FRIEND": "친구", "COWORKER": "직장동료", "BOSS": "직장상사",
    "OTHER_RELATION": "기타지인", "RELATION_UNKNOWN": "관계불명",
    "NOT_MENTIONED": "언급없음",
}

KOREAN_ACTION_MAP = {
    "TRANSFER_MONEY": "송금·이체",
    "PAY_FEE": "수수료·비용납부",
    "REPAY_LOAN": "기존대출상환",
    "WITHDRAW_CASH": "현금인출",
    "DELIVER_CASH": "현금전달",
    "VISIT_ATM": "ATM방문",
    "VISIT_BANK": "은행방문",
    "INSTALL_APP": "앱설치",
    "ALLOW_REMOTE_ACCESS": "원격접속허용",
    "OPEN_URL": "링크접속",
    "DISCLOSE_ACCOUNT": "계좌정보제공",
    "DISCLOSE_CARD": "카드정보제공",
    "DISCLOSE_PASSWORD": "비밀번호제공",
    "DISCLOSE_OTP": "인증번호제공",
    "DISCLOSE_ID_NUMBER": "주민번호·생년월일제공",
    "SEND_ID_COPY": "신분증사본전송",
    "SEND_TRANSACTION_HISTORY": "거래내역전송",
    "KEEP_CALL_CONNECTED": "통화유지",
    "AVOID_OUTSIDE_CONTACT": "외부연락금지",
    "RENT_ACCOUNT": "통장·계좌대여",
    "HAND_OVER_CARD": "카드·통장전달",
    "NOT_MENTIONED": "언급없음",
}

ROLE_VALUES = {"OFFENDER", "VICTIM", "REVIEW", "UNKNOWN"}

IMPERSONATION_RULES = [
    ("PUBLIC_AGENCY", "FSS", r"금융\s*감독원|금감원"),
    ("PUBLIC_AGENCY", "FSC", r"금융\s*위원회|금융위"),
    ("PUBLIC_AGENCY", "PROSECUTION", r"검찰(?:청)?|지방검찰청|지검|검사(?:님)?|수사관"),
    ("PUBLIC_AGENCY", "POLICE", r"경찰(?:청|서|관)?|사이버\s*수사|형사(?:님)?"),
    ("PUBLIC_AGENCY", "COURT", r"법원|법원\s*직원"),
    ("PUBLIC_AGENCY", "TAX_AUTHORITY", r"국세청|세무서"),
    ("FINANCIAL_INSTITUTION", "CARD_COMPANY", r"[가-힣A-Za-z●○OOXX]{0,12}카드(?:사)?"),
    ("FINANCIAL_INSTITUTION", "CAPITAL_COMPANY", r"[가-힣A-Za-z●○OOXX]{0,12}캐피탈"),
    ("FINANCIAL_INSTITUTION", "SAVINGS_BANK", r"[가-힣A-Za-z●○OOXX]{0,12}저축은행"),
    ("FINANCIAL_INSTITUTION", "BANK", r"[가-힣A-Za-z●○OOXX]{0,12}은행|은행원|은행\s*직원"),
    ("FINANCIAL_INSTITUTION", "FINANCIAL_ASSOCIATION", r"은행연합(?:회|센터)|여신금융협회"),
    ("FINANCIAL_INSTITUTION", "LOAN_COMPANY", r"대부업체|대출\s*회사|금융사"),
    ("DELIVERY_LOGISTICS", "POST_OFFICE", r"우체국"),
    ("DELIVERY_LOGISTICS", "DELIVERY_COMPANY", r"택배(?:사|기사)?|배송(?:업체|기사)?"),
    ("TELECOM_COMPANY", "TELECOM", r"통신사|전화국|휴대폰\s*대리점"),
    ("FAMILY", "KIDNAPPING_CLAIM", r"납치|아들|딸|자녀|엄마|어머니|아빠|아버지|배우자|남편|아내"),
    ("ACQUAINTANCE", "BUSINESS_CONTACT", r"직장\s*상사|회사\s*대표|거래처|동료"),
    ("ACQUAINTANCE", "PERSONAL_CONTACT", r"친구|지인|선배|후배"),
    ("EMPLOYER_RECRUITER", "RECRUITER", r"채용\s*담당|인사\s*담당|취업|아르바이트|알바"),
]

ROLE_TITLE_RULES = [
    ("PROSECUTOR", r"검사(?:님)?"),
    ("INVESTIGATOR", r"수사관(?:님)?"),
    ("POLICE_OFFICER", r"경찰관|경찰\s*직원"),
    ("DETECTIVE", r"형사(?:님)?"),
    ("FSS_INVESTIGATOR", r"금융\s*(?:조사관|감독관)|금감원\s*(?:조사관|직원)"),
    ("LOAN_REVIEWER", r"대출\s*심사|심사과|여신\s*심사"),
    ("LOAN_OFFICER", r"대출\s*(?:담당자|상담사)"),
    ("BANK_EMPLOYEE", r"은행원|은행\s*직원"),
    ("FINANCIAL_COUNSELOR", r"금융\s*상담사|상담\s*담당자"),
    ("CARD_COMPANY_EMPLOYEE", r"카드사\s*(?:직원|담당자)"),
    ("DELIVERY_AGENT", r"택배\s*기사|배송\s*기사"),
    ("RECRUITER", r"채용\s*담당|인사\s*담당"),
    ("MANAGER", r"과장|차장|부장|팀장|실장"),
]

RELATIONSHIP_RULES = [
    ("SON", r"아들"),
    ("DAUGHTER", r"딸"),
    ("CHILD", r"자녀|아이"),
    ("MOTHER", r"엄마|어머니"),
    ("FATHER", r"아빠|아버지"),
    ("SPOUSE", r"배우자|남편|아내"),
    ("SIBLING", r"형|오빠|누나|언니|남동생|여동생"),
    ("RELATIVE", r"친척|삼촌|이모|고모|조카"),
    ("FRIEND", r"친구"),
    ("COWORKER", r"직장\s*동료|회사\s*동료|동료"),
    ("BOSS", r"직장\s*상사|회사\s*대표|사장님"),
    ("OTHER_RELATION", r"지인|선배|후배"),
]

ACTION_RULES = [
    ("MONEY_MOVEMENT", "TRANSFER_MONEY", r"송금|이체|계좌로\s*(?:보내|넣)|돈을\s*(?:보내|넣)"),
    ("MONEY_MOVEMENT", "PAY_FEE", r"수수료|공증료|보증료|발급비|인지대"),
    ("MONEY_MOVEMENT", "REPAY_LOAN", r"대출.*상환|상환.*대출|기존\s*대출.*갚|변제"),
    ("CASH_HANDLING", "WITHDRAW_CASH", r"현금.*인출|인출.*현금|돈.*뽑|출금"),
    ("CASH_HANDLING", "DELIVER_CASH", r"현금.*전달|직원.*전달|수거책|전달책"),
    ("PHYSICAL_MOVEMENT", "VISIT_ATM", r"ATM|에이티엠|자동화기기|현금인출기|인출기"),
    ("PHYSICAL_MOVEMENT", "VISIT_BANK", r"은행으로\s*(?:가|이동)|은행에\s*(?:가|방문)"),
    ("DIGITAL_CONTROL", "INSTALL_APP", r"앱.*설치|어플.*설치|설치.*앱|설치.*어플"),
    ("DIGITAL_CONTROL", "ALLOW_REMOTE_ACCESS", r"원격\s*(?:제어|접속)|팀뷰어|퀵서포트"),
    ("DIGITAL_CONTROL", "OPEN_URL", r"링크.*(?:누르|접속)|주소.*(?:누르|접속)"),
    ("PERSONAL_INFORMATION", "DISCLOSE_ID_NUMBER", r"주민\s*(?:등록)?번호|생년월일"),
    ("PERSONAL_INFORMATION", "DISCLOSE_ACCOUNT", r"계좌번호|통장번호"),
    ("PERSONAL_INFORMATION", "DISCLOSE_CARD", r"카드번호|보안카드"),
    ("AUTHENTICATION_INFORMATION", "DISCLOSE_PASSWORD", r"비밀번호|비번"),
    ("AUTHENTICATION_INFORMATION", "DISCLOSE_OTP", r"OTP|오티피|인증번호"),
    ("DOCUMENT_SUBMISSION", "SEND_ID_COPY", r"신분증.*(?:사진|사본|보내)|(?:사진|사본).*신분증"),
    ("DOCUMENT_SUBMISSION", "SEND_TRANSACTION_HISTORY", r"거래내역.*(?:보내|제출)|입출금.*내역"),
    ("COMMUNICATION_CONTROL", "KEEP_CALL_CONNECTED", r"전화.*끊지|통화.*유지|계속.*통화"),
    ("COMMUNICATION_CONTROL", "AVOID_OUTSIDE_CONTACT", r"말하지\s*마|알리지\s*마|연락.*받지\s*마|전화.*받지\s*마|비밀"),
    ("ACCOUNT_USE", "RENT_ACCOUNT", r"통장.*(?:대여|임대)|계좌.*(?:대여|임대)"),
    ("ACCOUNT_USE", "HAND_OVER_CARD", r"카드.*(?:전달|보내)|통장.*(?:전달|보내)"),
]

STRATEGY_RULES = [
    ("AUTHORITY_TRUST", r"검찰|경찰|금융감독원|금감원|법원|은행|수사관|검사|사건번호|담당자"),
    ("FEAR_THREAT", r"체포|구속|처벌|압수|범죄|명의\s*도용|고소|불이익|피해|연루"),
    ("URGENCY_TIME_PRESSURE", r"지금|바로|즉시|오늘|빨리|시간이\s*없|몇\s*분"),
    ("ISOLATION_SECRECY", r"비밀|말하지\s*마|알리지\s*마|연락.*받지\s*마|전화.*받지\s*마|혼자"),
    ("BEHAVIOR_CONTROL", r"이동하|가세요|누르세요|입력하세요|설치하세요|통화.*유지|대기하세요"),
    ("MONEY_REQUEST", r"송금|이체|입금|현금|상환|수수료|보증금|공증료|금액|돈"),
    ("BENEFIT_PROMISE", r"승인|저금리|한도|신용\s*(?:등급|점수).*상향|우대|환불|지원금"),
    ("INFORMATION_EXTRACTION", r"주민\s*(?:등록)?번호|생년월일|계좌번호|카드번호|비밀번호|인증번호|신분증"),
    ("LEGITIMACY_BUILDING", r"사건번호|직원번호|공문|녹취|본인확인|담당\s*부서|연결해"),
    ("RESISTANCE_HANDLING", r"의심|못\s*믿|직접\s*확인|그게\s*아니|다시\s*설명"),
]

CLAIM_CUE_PATTERN = re.compile(
    r"(?:입니다|이라고\s*합니다|라고\s*합니다|소속|담당자|직원|수사관|검사|경찰관|형사|연결해\s*드리)",
    re.IGNORECASE,
)

MONEY_PATTERN = re.compile(
    r"(?P<number>\d[\d,]*(?:\.\d+)?)\s*(?P<unit>억|천만|백만|만|천)?\s*원"
)

AMOUNT_REQUEST_PATTERN = re.compile(
    r"(?:송금|이체|입금|인출|출금|준비|납부|상환|전달).{0,12}(?:하세요|해\s*주세요|해주시면|해야\s*합니다|하셔야|하십시오|바랍니다|부탁드립니다)"
    r"|(?:보내|넣|뽑)(?:세요|주세요|주시면|아야\s*합니다|어야\s*합니다)"
)
AMOUNT_AGREEMENT_PATTERN = re.compile(
    r"보내겠|이체하겠|입금하겠|인출하겠|출금하겠|준비하겠|전달하겠|납부하겠|상환하겠|그렇게\s*하겠|알겠"
)
AMOUNT_COMPLETION_PATTERN = re.compile(
    r"보냈|송금했|이체했|입금했|인출했|출금했|뽑았|준비했|전달했|납부했|상환했"
)
SHORT_CONFIRMATION_PATTERN = re.compile(r"^(?:네|예|응|알겠습니다|그렇게\s*하겠습니다)[.!? ]*$")


def normalize_unicode(value: object) -> str:
    return unicodedata.normalize("NFC", str(value or ""))


def normalize_text(value: object) -> str:
    text = normalize_unicode(value)
    text = html.unescape(text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"(?:●+|○+|□+|■+|\bO{2,}\b|\bX{2,}\b)", " [MASK] ", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def remove_speaker_tags(value: object) -> str:
    lines = []
    for line in normalize_unicode(value).splitlines():
        line = re.sub(r"^(?:TX|RX)\s+", "", line.strip(), flags=re.IGNORECASE)
        if line:
            lines.append(line)
    return normalize_text(" ".join(lines))


def safe_float(value: object, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_mean(values: list[float]) -> float | None:
    cleaned = [float(value) for value in values if value is not None and np.isfinite(float(value))]
    return float(np.mean(cleaned)) if cleaned else None


def stable_id(prefix: str, value: str, length: int = 12) -> str:
    digest = hashlib.sha1(value.encode("utf-8")).hexdigest()[:length]
    return f"{prefix}_{digest}"


def find_source_category(path_text: str) -> str:
    text = normalize_unicode(path_text)
    if "대출사기형" in text:
        return "LOAN_FRAUD"
    if "수사기관형" in text or "수사기관" in text:
        return "INSTITUTION_IMPERSONATION"
    if "바로 이 목소리" in text:
        return "MIXED_UNKNOWN"
    return "UNKNOWN"


def build_file_id(source_file: str, json_path: Path) -> str:
    match = re.search(r"(?:^|[/\\])(\d{4,})[_-]", normalize_unicode(source_file))
    if not match:
        match = re.search(r"^(\d{4,})[_-]", json_path.parent.name)
    return f"vp_{match.group(1)}" if match else stable_id("vp", str(json_path.parent))


def parse_publication_date(source_file: str) -> str | None:
    match = re.search(r"(20\d{2})[-_.](\d{2})[-_.](\d{2})", source_file)
    return "-".join(match.groups()) if match else None


def normalize_role(value: object) -> str:
    role = normalize_unicode(value).strip().upper()
    if role in ROLE_VALUES:
        return role
    return "UNKNOWN"


def is_low_information(text: str) -> bool:
    compact = re.sub(r"[^0-9A-Za-z가-힣]", "", text)
    return len(compact) <= 3


def first_match_label(text: str, rules: list[tuple[str, str]]) -> str:
    for label, pattern in rules:
        if re.search(pattern, text, flags=re.IGNORECASE):
            return label
    return "NOT_MENTIONED"


def extract_person_name(text: str) -> tuple[str, str]:
    title_pattern = r"([가-힣]{2,4}|[김이박최정강조윤장임한][O○X●]{1,3})\s*(검사|수사관|형사|과장|차장|부장|팀장|실장|담당자)"
    match = re.search(title_pattern, text)
    if not match:
        return "NOT_MENTIONED", "NOT_MENTIONED"
    raw_name = match.group(1)
    return raw_name, "[PERSON_01]"


def infer_claim_type(text: str, group: str) -> str:
    if group in {"FAMILY", "ACQUAINTANCE"} and re.search(r"(?:나야|휴대폰.*고장|번호.*바뀌|대신.*연락)", text):
        return "ASSOCIATE_IMPERSONATION"
    if re.search(r"(?:연결|이관).*(?:담당|검사|수사관|금감원|은행)", text):
        return "TRANSFERRED_AGENT_CLAIM"
    if group == "FAMILY" and re.search(r"납치|다쳤|잡고\s*있", text):
        return "VICTIM_ASSOCIATE_CLAIM"
    if CLAIM_CUE_PATTERN.search(text):
        return "CALLER_SELF_CLAIM"
    return "THIRD_PARTY_REFERENCE"


def normalize_org_name(text: str, subtype: str, matched_text: str) -> str:
    matchers = {
        "PROSECUTION": r"[가-힣]{2,15}(?:지방)?검찰청|[가-힣]{2,10}지검",
        "POLICE": r"[가-힣]{2,15}(?:경찰청|경찰서)",
        "COURT": r"[가-힣]{2,15}법원",
        "BANK": r"[가-힣A-Za-z\[\]MASK]{1,15}은행",
        "SAVINGS_BANK": r"[가-힣A-Za-z\[\]MASK]{1,15}저축은행",
        "CARD_COMPANY": r"[가-힣A-Za-z\[\]MASK]{1,15}카드(?:사)?",
        "CAPITAL_COMPANY": r"[가-힣A-Za-z\[\]MASK]{1,15}캐피탈",
    }
    pattern = matchers.get(subtype)
    if pattern:
        match = re.search(pattern, text)
        if match:
            return normalize_text(match.group(0))
    fixed = {
        "FSS": "금융감독원",
        "FSC": "금융위원회",
        "POST_OFFICE": "우체국",
    }
    return fixed.get(subtype, normalize_text(matched_text) or "UNKNOWN")


def extract_department(text: str) -> str:
    match = re.search(r"([가-힣A-Za-z0-9]{2,20}(?:부|과|팀|센터))", text)
    return normalize_text(match.group(1)) if match else "NOT_MENTIONED"


def parse_amount_krw(text: str) -> float | None:
    amounts = []
    multipliers = {"억": 100_000_000, "천만": 10_000_000, "백만": 1_000_000, "만": 10_000, "천": 1_000, None: 1}
    for match in MONEY_PATTERN.finditer(text):
        number = float(match.group("number").replace(",", ""))
        amounts.append(number * multipliers.get(match.group("unit"), 1))
    return max(amounts) if amounts else None


def amount_from_match(match: re.Match) -> float:
    multipliers = {"억": 100_000_000, "천만": 10_000_000, "백만": 1_000_000, "만": 10_000, "천": 1_000, None: 1}
    number = float(match.group("number").replace(",", ""))
    return number * multipliers.get(match.group("unit"), 1)


def related_money_action(text: str) -> str:
    money_action_types = {
        "TRANSFER_MONEY", "PAY_FEE", "REPAY_LOAN", "WITHDRAW_CASH",
        "DELIVER_CASH", "VISIT_ATM", "VISIT_BANK",
    }
    for _, action_type, pattern in ACTION_RULES:
        if action_type in money_action_types and re.search(pattern, text, flags=re.IGNORECASE):
            return action_type
    return "NOT_MENTIONED"


def classify_amount_status(text: str, role: str) -> str:
    if AMOUNT_COMPLETION_PATTERN.search(text):
        return "CLAIMED_COMPLETED"
    if role == "VICTIM" and AMOUNT_AGREEMENT_PATTERN.search(text):
        return "AGREED"
    if AMOUNT_REQUEST_PATTERN.search(text):
        return "REQUESTED"
    return "MENTIONED"


def extract_amount_events(case_turns: list[dict]) -> list[dict]:
    """발화의 금액을 추출하고, 바로 뒤 피해자의 금액 없는 동의·완료 표현도 연결한다."""
    rows = []
    recent_request = None
    for turn in case_turns:
        text = turn["normalized_text"]
        matches = list(MONEY_PATTERN.finditer(text))
        for match_index, match in enumerate(matches, start=1):
            amount_status = classify_amount_status(text, turn["auto_role"])
            row = {
                "amount_event_id": stable_id("amt", f"{turn['turn_id']}|{match.start()}|{match_index}|{amount_status}"),
                "file_id": turn["file_id"],
                "case_id": turn["case_id"],
                "evidence_turn_id": turn["turn_id"],
                "amount_source_turn_id": turn["turn_id"],
                "evidence_role": turn["auto_role"],
                "turn_order": turn["turn_order"],
                "mention_sec": turn["start_sec"],
                "amount_krw": amount_from_match(match),
                "amount_text": normalize_text(match.group(0)),
                "amount_status": amount_status,
                "related_action_type": related_money_action(text),
                "evidence_text": text,
                "inferred_from_context": False,
                "verified_loss_amount_krw": np.nan,
                "extraction_method": "RULE_EXPLICIT_AMOUNT",
                "extraction_confidence": 0.70 if amount_status != "MENTIONED" else 0.50,
                "extraction_version": "amount_rule_v1",
                "verification_status": "AUTO_SILVER",
                "label_status": "SILVER",
            }
            rows.append(row)
            if amount_status == "REQUESTED":
                recent_request = row

        # "네, 보내겠습니다"처럼 금액을 반복하지 않은 피해자 응답은 직전 요구금액과 연결한다.
        if not matches and turn["auto_role"] == "VICTIM" and recent_request:
            turn_gap = turn["turn_order"] - recent_request["turn_order"]
            is_completed = bool(AMOUNT_COMPLETION_PATTERN.search(text))
            is_agreed = bool(AMOUNT_AGREEMENT_PATTERN.search(text) or SHORT_CONFIRMATION_PATTERN.fullmatch(text))
            if 0 < turn_gap <= 2 and (is_completed or is_agreed):
                amount_status = "CLAIMED_COMPLETED" if is_completed else "AGREED"
                rows.append({
                    "amount_event_id": stable_id("amt", f"{turn['turn_id']}|linked|{amount_status}"),
                    "file_id": turn["file_id"],
                    "case_id": turn["case_id"],
                    "evidence_turn_id": turn["turn_id"],
                    "amount_source_turn_id": recent_request["evidence_turn_id"],
                    "evidence_role": turn["auto_role"],
                    "turn_order": turn["turn_order"],
                    "mention_sec": turn["start_sec"],
                    "amount_krw": recent_request["amount_krw"],
                    "amount_text": recent_request["amount_text"],
                    "amount_status": amount_status,
                    "related_action_type": recent_request["related_action_type"],
                    "evidence_text": text,
                    "inferred_from_context": True,
                    "verified_loss_amount_krw": np.nan,
                    "extraction_method": "RULE_CONTEXT_LINK",
                    "extraction_confidence": 0.45,
                    "extraction_version": "amount_rule_v1",
                    "verification_status": "AUTO_REVIEW_RECOMMENDED",
                    "label_status": "SILVER",
                })
    columns = [
        "amount_event_id", "file_id", "case_id", "evidence_turn_id", "amount_source_turn_id",
        "evidence_role", "turn_order", "mention_sec", "amount_krw", "amount_text",
        "amount_status", "related_action_type", "evidence_text", "inferred_from_context",
        "verified_loss_amount_krw", "extraction_method", "extraction_confidence",
        "extraction_version", "verification_status", "label_status",
    ]
    return [{column: row.get(column) for column in columns} for row in rows]


def extract_action_status(text: str) -> str:
    if re.search(r"(?:보냈|송금했|이체했|입금했|인출했|설치했|제출했)", text):
        return "CLAIMED_COMPLETED"
    if re.search(r"(?:하겠|할게|가겠|보내겠|설치하겠)", text):
        return "INTENDED"
    if re.search(r"(?:하세요|해 주세요|해야|부탁|바랍니다|가세요|누르세요|입력하세요)", text):
        return "REQUESTED"
    return "MENTIONED"


def load_phishing_tables(result_root: Path):
    file_rows = []
    case_rows = []
    turn_rows = []
    impersonation_hits = []
    action_hits = []
    strategy_rows = []
    amount_rows = []

    json_paths = sorted(result_root.rglob("cases.json"))
    if not json_paths:
        raise FileNotFoundError(f"cases.json을 찾지 못했습니다: {result_root}")

    seen_file_ids = Counter()
    for json_path in json_paths:
        try:
            payload = json.loads(json_path.read_text(encoding="utf-8"))
        except Exception as exc:
            print(f"[경고] JSON 읽기 실패: {json_path} / {exc}")
            continue

        cases = payload if isinstance(payload, list) else payload.get("cases", [])
        source_file = normalize_unicode(payload.get("source_file", json_path.parent.name)) if isinstance(payload, dict) else json_path.parent.name
        source_category = find_source_category(f"{json_path} {source_file}")
        file_id_base = build_file_id(source_file, json_path)
        seen_file_ids[file_id_base] += 1
        file_id = file_id_base if seen_file_ids[file_id_base] == 1 else f"{file_id_base}_{seen_file_ids[file_id_base]:02d}"
        metadata = payload.get("metadata", {}) if isinstance(payload, dict) else {}
        file_duration = safe_float(metadata.get("duration"), 0.0)

        file_turn_count = sum(len(case.get("turns", [])) for case in cases)
        file_rows.append({
            "file_id": file_id,
            "source_category": source_category,
            "source_file": source_file,
            "json_path": str(json_path),
            "publication_date": parse_publication_date(source_file),
            "media_type": Path(source_file).suffix.upper().lstrip(".") or "UNKNOWN",
            "duration_sec": file_duration,
            "case_count": len(cases),
            "turn_count": file_turn_count,
            "empty_transcript": file_turn_count == 0,
            "multi_case_file": len(cases) > 1,
            "media_composition": "UNKNOWN",
            "quality_flag": "EMPTY" if file_turn_count == 0 else "USABLE",
        })

        for case_index, case in enumerate(cases, start=1):
            local_case_id = normalize_unicode(case.get("case_id", f"case_{case_index:03d}"))
            case_id = f"{file_id}_{local_case_id}"
            raw_turns = case.get("turns", [])
            current_turn_rows = []

            for turn_index, turn in enumerate(raw_turns, start=1):
                turn_id = f"{case_id}_turn_{turn_index:04d}"
                raw_text = normalize_unicode(turn.get("text", "")).strip()
                normalized = normalize_text(raw_text)
                role = normalize_role(turn.get("role"))
                row = {
                    "file_id": file_id,
                    "case_id": case_id,
                    "turn_id": turn_id,
                    "turn_order": turn_index,
                    "start_sec": safe_float(turn.get("start"), 0.0),
                    "end_sec": safe_float(turn.get("end"), 0.0),
                    "duration_sec": max(0.0, safe_float(turn.get("end"), 0.0) - safe_float(turn.get("start"), 0.0)),
                    "speaker_id": normalize_unicode(turn.get("speaker_id", "UNKNOWN")) or "UNKNOWN",
                    "auto_role": role,
                    "role_heuristic_score": safe_float(turn.get("role_confidence"), 0.0),
                    "raw_text": raw_text,
                    "normalized_text": normalized,
                    "content_text": "" if is_low_information(normalized) else normalized,
                    "avg_logprob": safe_float(turn.get("avg_logprob"), np.nan),
                    "voice_modified": turn.get("voice_modified"),
                    "is_short_turn": len(re.sub(r"[^0-9A-Za-z가-힣]", "", normalized)) <= 5,
                    "is_low_information": is_low_information(normalized),
                    "quality_flag": "EMPTY" if not normalized else "USABLE",
                }
                turn_rows.append(row)
                current_turn_rows.append(row)

                if not normalized or role == "VICTIM":
                    continue

                for group, subtype, pattern in IMPERSONATION_RULES:
                    for match in re.finditer(pattern, normalized, flags=re.IGNORECASE):
                        role_title = first_match_label(normalized, ROLE_TITLE_RULES)
                        relationship = first_match_label(normalized, RELATIONSHIP_RULES)
                        person_raw, person_masked = extract_person_name(normalized)
                        impersonation_hits.append({
                            "file_id": file_id,
                            "case_id": case_id,
                            "evidence_turn_id": turn_id,
                            "evidence_role": role,
                            "turn_order": turn_index,
                            "mention_sec": row["start_sec"],
                            "impersonation_group": group,
                            "impersonation_subtype": subtype,
                            "claimed_org_name_raw": normalize_text(match.group(0)),
                            "claimed_org_name_normalized": normalize_org_name(normalized, subtype, match.group(0)),
                            "claimed_department_normalized": extract_department(normalized),
                            "claimed_role_title_normalized": role_title,
                            "claimed_person_name_raw": person_raw,
                            "claimed_person_name_masked": person_masked,
                            "claimed_relationship": relationship,
                            "identity_claim_type": infer_claim_type(normalized, group),
                            "evidence_text": normalized,
                        })

                for action_group, action_type, pattern in ACTION_RULES:
                    if re.search(pattern, normalized, flags=re.IGNORECASE):
                        action_hits.append({
                            "file_id": file_id,
                            "case_id": case_id,
                            "evidence_turn_id": turn_id,
                            "evidence_role": role,
                            "turn_order": turn_index,
                            "mention_sec": row["start_sec"],
                            "action_group": action_group,
                            "action_type": action_type,
                            "action_status": extract_action_status(normalized),
                            "mentioned_amount_krw": parse_amount_krw(normalized),
                            "evidence_text": normalized,
                        })

                for strategy_type, pattern in STRATEGY_RULES:
                    if re.search(pattern, normalized, flags=re.IGNORECASE):
                        strategy_rows.append({
                            "strategy_event_id": stable_id("str", f"{turn_id}|{strategy_type}"),
                            "file_id": file_id,
                            "case_id": case_id,
                            "evidence_turn_id": turn_id,
                            "evidence_role": role,
                            "turn_order": turn_index,
                            "mention_sec": row["start_sec"],
                            "strategy_type": strategy_type,
                            "evidence_text": normalized,
                            "extraction_method": "RULE",
                            "extraction_confidence": 0.60,
                            "extraction_version": "rule_v1",
                            "label_status": "SILVER",
                        })

            amount_rows.extend(extract_amount_events(current_turn_rows))

            roles = Counter(row["auto_role"] for row in current_turn_rows)
            texts = [row["raw_text"] for row in current_turn_rows if row["raw_text"]]
            offender_texts = [row["raw_text"] for row in current_turn_rows if row["auto_role"] == "OFFENDER" and row["raw_text"]]
            victim_texts = [row["raw_text"] for row in current_turn_rows if row["auto_role"] == "VICTIM" and row["raw_text"]]
            logprobs = [row["avg_logprob"] for row in current_turn_rows]
            case_start = safe_float(case.get("start"), current_turn_rows[0]["start_sec"] if current_turn_rows else 0.0)
            case_end = safe_float(case.get("end"), current_turn_rows[-1]["end_sec"] if current_turn_rows else 0.0)

            case_rows.append({
                "file_id": file_id,
                "case_id": case_id,
                "source_category": source_category,
                "source_file": source_file,
                "case_start_sec": case_start,
                "case_end_sec": case_end,
                "duration_sec": max(0.0, case_end - case_start),
                "turn_count": len(current_turn_rows),
                "speaker_count": len({row["speaker_id"] for row in current_turn_rows}),
                "offender_turn_count": roles["OFFENDER"],
                "victim_turn_count": roles["VICTIM"],
                "unknown_turn_count": roles["UNKNOWN"] + roles["REVIEW"],
                "unknown_role_ratio": (roles["UNKNOWN"] + roles["REVIEW"]) / max(1, len(current_turn_rows)),
                "short_turn_count": sum(row["is_short_turn"] for row in current_turn_rows),
                "short_turn_ratio": sum(row["is_short_turn"] for row in current_turn_rows) / max(1, len(current_turn_rows)),
                "raw_full_text": " ".join(texts),
                "normalized_full_text": normalize_text(" ".join(texts)),
                "raw_offender_text": " ".join(offender_texts),
                "normalized_offender_text": normalize_text(" ".join(offender_texts)),
                "raw_victim_text": " ".join(victim_texts),
                "normalized_victim_text": normalize_text(" ".join(victim_texts)),
                "asr_avg_logprob": safe_mean(logprobs),
                "needs_review": bool(case.get("needs_review", False)),
                "quality_flag": "EMPTY" if not texts else ("REVIEW" if case.get("needs_review", False) else "USABLE"),
                "label_status": "SILVER",
                "supervised_target": source_category if source_category in {"LOAN_FRAUD", "INSTITUTION_IMPERSONATION"} else "NOT_LABELED",
            })

    files_df = pd.DataFrame(file_rows)
    cases_df = pd.DataFrame(case_rows)
    utterances_df = pd.DataFrame(turn_rows)
    impersonations_df = aggregate_impersonations(impersonation_hits)
    actions_df = aggregate_actions(action_hits)
    strategies_df = pd.DataFrame(strategy_rows)
    amount_columns = [
        "amount_event_id", "file_id", "case_id", "evidence_turn_id", "amount_source_turn_id",
        "evidence_role", "turn_order", "mention_sec", "amount_krw", "amount_text",
        "amount_status", "related_action_type", "evidence_text", "inferred_from_context",
        "verified_loss_amount_krw", "extraction_method", "extraction_confidence",
        "extraction_version", "verification_status", "label_status",
    ]
    amounts_df = pd.DataFrame(amount_rows, columns=amount_columns)
    cases_df = enrich_cases(cases_df, impersonations_df, actions_df, strategies_df)
    return files_df, cases_df, utterances_df, impersonations_df, actions_df, strategies_df, amounts_df


def aggregate_impersonations(hits: list[dict]) -> pd.DataFrame:
    columns = [
        "impersonation_id", "file_id", "case_id", "evidence_turn_id", "evidence_role",
        "impersonation_group", "impersonation_subtype", "claimed_org_name_raw",
        "claimed_org_name_normalized", "claimed_department_normalized",
        "claimed_role_title_normalized", "claimed_person_name_raw",
        "claimed_person_name_masked", "claimed_relationship", "identity_claim_type",
        "is_primary_impersonation", "first_mention_turn", "first_mention_sec", "mention_count",
        "evidence_text", "extraction_method", "extraction_confidence", "extraction_version", "label_status",
    ]
    if not hits:
        return pd.DataFrame(columns=columns)
    grouped = defaultdict(list)
    for hit in hits:
        key = (
            hit["case_id"], hit["impersonation_group"], hit["impersonation_subtype"],
            hit["claimed_org_name_normalized"], hit["claimed_role_title_normalized"],
            hit["claimed_relationship"], hit["identity_claim_type"],
        )
        grouped[key].append(hit)
    rows = []
    for key, group_hits in grouped.items():
        group_hits.sort(key=lambda item: item["turn_order"])
        first = group_hits[0]
        rows.append({
            "impersonation_id": stable_id("imp", "|".join(map(str, key))),
            "file_id": first["file_id"],
            "case_id": first["case_id"],
            "evidence_turn_id": first["evidence_turn_id"],
            "evidence_role": first["evidence_role"],
            "impersonation_group": first["impersonation_group"],
            "impersonation_subtype": first["impersonation_subtype"],
            "claimed_org_name_raw": first["claimed_org_name_raw"],
            "claimed_org_name_normalized": first["claimed_org_name_normalized"],
            "claimed_department_normalized": first["claimed_department_normalized"],
            "claimed_role_title_normalized": first["claimed_role_title_normalized"],
            "claimed_person_name_raw": first["claimed_person_name_raw"],
            "claimed_person_name_masked": first["claimed_person_name_masked"],
            "claimed_relationship": first["claimed_relationship"],
            "identity_claim_type": first["identity_claim_type"],
            "is_primary_impersonation": False,
            "first_mention_turn": first["turn_order"],
            "first_mention_sec": first["mention_sec"],
            "mention_count": len(group_hits),
            "evidence_text": first["evidence_text"],
            "extraction_method": "RULE",
            "extraction_confidence": 0.70 if first["identity_claim_type"] == "CALLER_SELF_CLAIM" else 0.50,
            "extraction_version": "rule_v1",
            "label_status": "SILVER",
        })
    result = pd.DataFrame(rows, columns=columns)
    for _, group in result.groupby("case_id"):
        preferred = group.assign(
            claim_priority=group["identity_claim_type"].eq("CALLER_SELF_CLAIM").astype(int),
            role_priority=group["evidence_role"].eq("OFFENDER").astype(int),
        ).sort_values(["claim_priority", "role_priority", "first_mention_turn"], ascending=[False, False, True])
        result.loc[preferred.index[0], "is_primary_impersonation"] = True
    return result


def aggregate_actions(hits: list[dict]) -> pd.DataFrame:
    columns = [
        "action_id", "file_id", "case_id", "evidence_turn_id", "evidence_role",
        "action_group", "action_type", "action_status", "mentioned_amount_krw",
        "is_primary_action", "first_mention_turn", "first_mention_sec", "mention_count",
        "evidence_text", "extraction_method", "extraction_confidence", "extraction_version", "label_status",
    ]
    if not hits:
        return pd.DataFrame(columns=columns)
    grouped = defaultdict(list)
    for hit in hits:
        grouped[(hit["case_id"], hit["action_group"], hit["action_type"])].append(hit)
    rows = []
    for key, group_hits in grouped.items():
        group_hits.sort(key=lambda item: item["turn_order"])
        first = group_hits[0]
        amounts = [item["mentioned_amount_krw"] for item in group_hits if item["mentioned_amount_krw"] is not None]
        rows.append({
            "action_id": stable_id("act", "|".join(map(str, key))),
            "file_id": first["file_id"],
            "case_id": first["case_id"],
            "evidence_turn_id": first["evidence_turn_id"],
            "evidence_role": first["evidence_role"],
            "action_group": first["action_group"],
            "action_type": first["action_type"],
            "action_status": max((item["action_status"] for item in group_hits), key=lambda value: {"MENTIONED": 0, "REQUESTED": 1, "INTENDED": 2, "CLAIMED_COMPLETED": 3}.get(value, 0)),
            "mentioned_amount_krw": max(amounts) if amounts else None,
            "is_primary_action": False,
            "first_mention_turn": first["turn_order"],
            "first_mention_sec": first["mention_sec"],
            "mention_count": len(group_hits),
            "evidence_text": first["evidence_text"],
            "extraction_method": "RULE",
            "extraction_confidence": 0.65,
            "extraction_version": "rule_v1",
            "label_status": "SILVER",
        })
    result = pd.DataFrame(rows, columns=columns)
    for _, group in result.groupby("case_id"):
        preferred = group.sort_values(["first_mention_turn", "mention_count"], ascending=[True, False])
        result.loc[preferred.index[0], "is_primary_action"] = True
    return result


def enrich_cases(cases_df, impersonations_df, actions_df, strategies_df):
    result = cases_df.copy()
    if not impersonations_df.empty:
        primary = impersonations_df[impersonations_df["is_primary_impersonation"]].drop_duplicates("case_id")
        primary = primary[[
            "case_id", "impersonation_group", "impersonation_subtype",
            "claimed_org_name_normalized", "claimed_role_title_normalized",
        ]].rename(columns={
            "impersonation_group": "primary_impersonation_group",
            "impersonation_subtype": "primary_impersonation_subtype",
            "claimed_org_name_normalized": "primary_claimed_org_name",
            "claimed_role_title_normalized": "primary_claimed_role_title",
        })
        counts = impersonations_df.groupby("case_id").agg(
            impersonation_count=("impersonation_id", "count"),
            impersonation_group_count=("impersonation_group", "nunique"),
        ).reset_index()
        result = result.merge(primary, on="case_id", how="left").merge(counts, on="case_id", how="left")
    if not actions_df.empty:
        primary_action = actions_df[actions_df["is_primary_action"]][["case_id", "action_type"]].drop_duplicates("case_id").rename(columns={"action_type": "primary_requested_action"})
        action_counts = actions_df.groupby("case_id").agg(
            requested_action_count=("action_id", "count"),
            risky_action_diversity=("action_type", "nunique"),
            first_risky_action_turn=("first_mention_turn", "min"),
            first_risky_action_sec=("first_mention_sec", "min"),
            mentioned_amount_max_krw=("mentioned_amount_krw", "max"),
        ).reset_index()
        action_counts["risky_action_count"] = action_counts["requested_action_count"]
        result = result.merge(primary_action, on="case_id", how="left").merge(action_counts, on="case_id", how="left")
    if not strategies_df.empty:
        pivot = pd.crosstab(strategies_df["case_id"], strategies_df["strategy_type"]).reset_index()
        rename = {column: f"{column.lower()}_count" for column in pivot.columns if column != "case_id"}
        pivot = pivot.rename(columns=rename)
        pivot["strategy_diversity"] = (pivot.drop(columns="case_id") > 0).sum(axis=1)
        result = result.merge(pivot, on="case_id", how="left")

    defaults = {
        "primary_impersonation_group": "NOT_MENTIONED",
        "primary_impersonation_subtype": "NOT_MENTIONED",
        "primary_claimed_org_name": "NOT_MENTIONED",
        "primary_claimed_role_title": "NOT_MENTIONED",
        "impersonation_count": 0,
        "impersonation_group_count": 0,
        "primary_requested_action": "NOT_MENTIONED",
        "requested_action_count": 0,
        "risky_action_count": 0,
        "risky_action_diversity": 0,
        "strategy_diversity": 0,
    }
    for column, default in defaults.items():
        if column not in result:
            result[column] = default
        result[column] = result[column].fillna(default)
    result["has_multiple_impersonations"] = result["impersonation_count"] > 1
    return result


def parse_normal_turns(raw_text: str) -> list[str]:
    turns = []
    for line in normalize_unicode(raw_text).splitlines():
        line = re.sub(r"^(?:TX|RX)\s+", "", line.strip(), flags=re.IGNORECASE)
        line = normalize_text(line)
        if line:
            turns.append(line)
    if len(turns) <= 1:
        normalized = remove_speaker_tags(raw_text)
        return [normalized] if normalized else []
    return turns


def load_normal_calls(normal_root: Path) -> pd.DataFrame:
    columns = [
        "conversation_id", "source_id", "source_date", "source_institution",
        "consulting_category", "consulting_topic", "raw_text", "normalized_text",
        "turn_count", "client_age_group", "client_gender", "dataset_split",
    ]
    if not normal_root.exists():
        print(f"[안내] 정상 상담 경로가 없어 건너뜁니다: {normal_root}")
        return pd.DataFrame(columns=columns)

    zip_paths = sorted([
        path for path in normal_root.rglob("*.zip")
        if path.name.startswith(("TL_", "VL_"))
    ])
    if not zip_paths:
        print(f"[안내] TL_/VL_ ZIP을 찾지 못했습니다: {normal_root}")
        return pd.DataFrame(columns=columns)

    records = {}
    for zip_path in zip_paths:
        split = "TRAIN" if zip_path.name.startswith("TL_") else "VALIDATION"
        print(f"정상 상담 읽는 중: {zip_path.name}")
        with ZipFile(zip_path) as archive:
            for member in archive.infolist():
                if member.is_dir() or not member.filename.lower().endswith(".json"):
                    continue
                try:
                    item = json.loads(archive.read(member).decode("utf-8-sig"))
                except Exception:
                    continue
                source = item.get("source", {})
                consulting = item.get("consulting", {})
                source_id = normalize_unicode(source.get("source_id", "")).strip()
                raw_text = normalize_unicode(source.get("consulting_content", "")).strip()
                if not source_id or not raw_text:
                    continue
                key = source_id
                candidate = {
                    "conversation_id": f"normal_{source_id}",
                    "source_id": source_id,
                    "source_date": normalize_unicode(source.get("source_date", "")),
                    "source_institution": normalize_unicode(source.get("source_institution", "")),
                    "consulting_category": normalize_unicode(consulting.get("consulting_category", "")),
                    "consulting_topic": normalize_unicode(consulting.get("consulting_topic", "")),
                    "raw_text": raw_text,
                    "normalized_text": remove_speaker_tags(raw_text),
                    "turn_count": len(parse_normal_turns(raw_text)),
                    "client_age_group": normalize_unicode(source.get("client_age", "")),
                    "client_gender": normalize_unicode(source.get("client_gender", "")),
                    "dataset_split": split,
                }
                if key not in records or candidate["turn_count"] > records[key]["turn_count"]:
                    records[key] = candidate
    return pd.DataFrame(records.values(), columns=columns)


def generic_text_features(text: str) -> dict:
    normalized = normalize_text(text)
    rule_groups = {
        "public_agency_term_count": [pattern for group, _, pattern in IMPERSONATION_RULES if group == "PUBLIC_AGENCY"],
        "financial_institution_term_count": [pattern for group, _, pattern in IMPERSONATION_RULES if group == "FINANCIAL_INSTITUTION"],
        "family_acquaintance_term_count": [pattern for group, _, pattern in IMPERSONATION_RULES if group in {"FAMILY", "ACQUAINTANCE"}],
        "risky_action_term_count": [pattern for _, _, pattern in ACTION_RULES],
        "urgency_term_count": [pattern for label, pattern in STRATEGY_RULES if label == "URGENCY_TIME_PRESSURE"],
        "fear_term_count": [pattern for label, pattern in STRATEGY_RULES if label == "FEAR_THREAT"],
    }
    features = {"text_length": len(normalized)}
    for name, patterns in rule_groups.items():
        features[name] = sum(len(re.findall(pattern, normalized, flags=re.IGNORECASE)) for pattern in patterns)
    return features


def sample_normal_for_ml(normal_df: pd.DataFrame, fraud_count: int) -> pd.DataFrame:
    if normal_df.empty:
        return normal_df
    preferred_topics = {
        "대출문의(만기/연장/조회등)", "이자/연체금액", "거래내역/잔액조회",
        "중계요청/착오송금", "자동이체조회", "금융거래한도/비대면한도계좌",
        "만기,연장/해지,수신",
    }
    bank_df = normal_df[
        normal_df["consulting_category"].eq("은행")
        & normal_df["consulting_topic"].isin(preferred_topics)
    ].copy()
    pool = bank_df if not bank_df.empty else normal_df
    target = min(len(pool), max(fraud_count, fraud_count * NORMAL_TO_FRAUD_RATIO))
    return pool.sample(n=target, random_state=RANDOM_SEED) if target < len(pool) else pool.copy()


def build_fraud_detection_ml(cases_df: pd.DataFrame, normal_df: pd.DataFrame) -> pd.DataFrame:
    fraud = cases_df[cases_df["normalized_full_text"].str.len().fillna(0) >= MIN_TEXT_LENGTH].copy()
    fraud_rows = pd.DataFrame({
        "conversation_id": "fraud_" + fraud["case_id"].astype(str),
        "group_id": fraud["file_id"],
        "fraud_label": "VOICE_PHISHING",
        "source_group": "FSS_VOICE_PHISHING",
        "sample_scope": "FULL",
        "window_position": "FULL",
        "model_input_text": fraud["normalized_full_text"],
        "financial_topic": fraud["source_category"],
        "quality_flag": fraud["quality_flag"],
    })
    selected_normal = sample_normal_for_ml(normal_df, len(fraud_rows))
    normal_rows = pd.DataFrame({
        "conversation_id": selected_normal["conversation_id"],
        "group_id": selected_normal["source_id"],
        "fraud_label": "LEGITIMATE_FINANCIAL_CALL",
        "source_group": "AIHUB_NORMAL_CALL",
        "sample_scope": "FULL",
        "window_position": "FULL",
        "model_input_text": selected_normal["normalized_text"],
        "financial_topic": selected_normal["consulting_topic"],
        "quality_flag": "USABLE",
    })
    result = pd.concat([fraud_rows, normal_rows], ignore_index=True)
    if not result.empty:
        features = pd.DataFrame(result["model_input_text"].apply(generic_text_features).tolist())
        result = pd.concat([result.reset_index(drop=True), features], axis=1)
    return result


def build_fraud_type_ml(cases_df: pd.DataFrame) -> pd.DataFrame:
    result = cases_df[cases_df["supervised_target"].isin({"LOAN_FRAUD", "INSTITUTION_IMPERSONATION"})].copy()
    result["model_input_text"] = np.where(
        result["normalized_offender_text"].str.len().fillna(0) >= MIN_TEXT_LENGTH,
        result["normalized_offender_text"],
        result["normalized_full_text"],
    )
    columns = [
        "case_id", "file_id", "supervised_target", "model_input_text",
        "primary_impersonation_group", "primary_impersonation_subtype",
        "primary_requested_action", "quality_flag",
    ]
    return result[columns]


def assign_window_position(start_index: int, end_index: int, total_turns: int) -> str:
    if total_turns <= 1:
        return "FULL"
    midpoint = ((start_index + end_index) / 2) / total_turns
    if midpoint <= 1 / 3:
        return "EARLY"
    if midpoint <= 2 / 3:
        return "MIDDLE"
    return "LATE"


def create_windows(turns: list[str], window_sizes=WINDOW_SIZES) -> list[dict]:
    rows = []
    total = len(turns)
    for window_size in window_sizes:
        if total < window_size:
            continue
        stride = max(1, int(round(window_size * WINDOW_STRIDE_RATIO)))
        starts = list(range(0, total - window_size + 1, stride))
        final_start = total - window_size
        if final_start not in starts:
            starts.append(final_start)
        for start in starts:
            end = start + window_size
            rows.append({
                "window_start_turn": start + 1,
                "window_end_turn": end,
                "window_size": window_size,
                "window_position": assign_window_position(start, end, total),
                "window_text": normalize_text(" ".join(turns[start:end])),
            })
    return rows


def build_segment_detection_ml(cases_df, utterances_df, normal_df, fraud_detection_df):
    selected_ids = set(fraud_detection_df["conversation_id"])
    rows = []

    for case_id, group in utterances_df.sort_values(["case_id", "turn_order"]).groupby("case_id"):
        conversation_id = f"fraud_{case_id}"
        if conversation_id not in selected_ids:
            continue
        turns = group["normalized_text"].fillna("").tolist()
        turns = [text for text in turns if text]
        full_text = normalize_text(" ".join(turns))
        file_id = group["file_id"].iloc[0]
        rows.append({
            "conversation_id": conversation_id,
            "group_id": file_id,
            "fraud_label": "VOICE_PHISHING",
            "sample_scope": "FULL",
            "window_start_turn": 1,
            "window_end_turn": len(turns),
            "window_size": len(turns),
            "window_position": "FULL",
            "window_text": full_text,
        })
        for window in create_windows(turns):
            rows.append({
                "conversation_id": conversation_id,
                "group_id": file_id,
                "fraud_label": "VOICE_PHISHING",
                "sample_scope": "WINDOW",
                **window,
            })

    selected_normal_ids = selected_ids & set(normal_df["conversation_id"])
    normal_lookup = normal_df.set_index("conversation_id") if not normal_df.empty else pd.DataFrame()
    for conversation_id in selected_normal_ids:
        item = normal_lookup.loc[conversation_id]
        turns = parse_normal_turns(item["raw_text"])
        full_text = normalize_text(" ".join(turns))
        rows.append({
            "conversation_id": conversation_id,
            "group_id": item["source_id"],
            "fraud_label": "LEGITIMATE_FINANCIAL_CALL",
            "sample_scope": "FULL",
            "window_start_turn": 1,
            "window_end_turn": len(turns),
            "window_size": len(turns),
            "window_position": "FULL",
            "window_text": full_text,
        })
        for window in create_windows(turns):
            rows.append({
                "conversation_id": conversation_id,
                "group_id": item["source_id"],
                "fraud_label": "LEGITIMATE_FINANCIAL_CALL",
                "sample_scope": "WINDOW",
                **window,
            })
    return pd.DataFrame(rows)


def build_clustering_ml(cases_df: pd.DataFrame) -> pd.DataFrame:
    result = cases_df.copy()
    result["model_input_text"] = np.where(
        result["normalized_offender_text"].str.len().fillna(0) >= MIN_TEXT_LENGTH,
        result["normalized_offender_text"],
        result["normalized_full_text"],
    )
    result = result[result["model_input_text"].str.len().fillna(0) >= MIN_TEXT_LENGTH]
    return result[[
        "case_id", "file_id", "source_category", "model_input_text",
        "primary_impersonation_subtype", "primary_requested_action", "quality_flag",
    ]]


def build_dashboard_summary(cases_df, impersonations_df, actions_df, strategies_df):
    result = cases_df.copy()
    if not impersonations_df.empty:
        subtype = pd.crosstab(impersonations_df["case_id"], impersonations_df["impersonation_subtype"])
        subtype.columns = [f"has_{column.lower()}_impersonation" for column in subtype.columns]
        subtype = subtype.gt(0).reset_index()
        result = result.merge(subtype, on="case_id", how="left")
    if not actions_df.empty:
        actions = pd.crosstab(actions_df["case_id"], actions_df["action_type"])
        actions.columns = [f"has_{column.lower()}" for column in actions.columns]
        actions = actions.gt(0).reset_index()
        result = result.merge(actions, on="case_id", how="left")
    boolean_columns = [column for column in result.columns if column.startswith("has_")]
    for column in boolean_columns:
        result[column] = result[column].fillna(False).astype(bool)
    return result


def join_unique(values, mapping=None) -> str:
    result = []
    for value in values:
        if pd.isna(value):
            continue
        value = str(value).strip()
        if not value or value in {"NOT_MENTIONED", "UNKNOWN"}:
            continue
        converted = mapping.get(value, value) if mapping else value
        if converted not in result:
            result.append(converted)
    return " | ".join(result) if result else "언급없음"


def build_korean_case_summary(files_df, cases_df, impersonations_df, actions_df, amounts_df):
    result = cases_df.merge(
        files_df[["file_id", "publication_date", "media_type", "media_composition"]],
        on="file_id",
        how="left",
        suffixes=("", "_file"),
    )

    if not impersonations_df.empty:
        impersonation_summary = impersonations_df.groupby("case_id").agg(
            사칭대상_대분류=("impersonation_group", lambda values: join_unique(values, KOREAN_IMPERSONATION_GROUP_MAP)),
            사칭대상_세부유형=("impersonation_subtype", lambda values: join_unique(values, KOREAN_IMPERSONATION_SUBTYPE_MAP)),
            사칭기관명=("claimed_org_name_normalized", join_unique),
            사칭부서명=("claimed_department_normalized", join_unique),
            사칭직책=("claimed_role_title_normalized", lambda values: join_unique(values, KOREAN_ROLE_TITLE_MAP)),
            사칭인물명=("claimed_person_name_masked", join_unique),
            피해자와의관계=("claimed_relationship", lambda values: join_unique(values, KOREAN_RELATIONSHIP_MAP)),
            사칭정보수=("impersonation_id", "count"),
        ).reset_index()
        result = result.merge(impersonation_summary, on="case_id", how="left")

    if not actions_df.empty:
        action_summary = actions_df.groupby("case_id").agg(
            요구행동_전체=("action_type", lambda values: join_unique(values, KOREAN_ACTION_MAP)),
            언급금액_최대_원=("mentioned_amount_krw", "max"),
        ).reset_index()
        action_flags = pd.crosstab(actions_df["case_id"], actions_df["action_type"]).gt(0)
        action_flags = action_flags.reindex(columns=[
            "TRANSFER_MONEY", "WITHDRAW_CASH", "DELIVER_CASH", "INSTALL_APP",
            "ALLOW_REMOTE_ACCESS", "DISCLOSE_ID_NUMBER", "DISCLOSE_ACCOUNT",
            "DISCLOSE_PASSWORD", "DISCLOSE_OTP", "KEEP_CALL_CONNECTED",
            "AVOID_OUTSIDE_CONTACT",
        ], fill_value=False).reset_index()
        action_flags = action_flags.rename(columns={
            "TRANSFER_MONEY": "송금요구여부",
            "WITHDRAW_CASH": "현금인출요구여부",
            "DELIVER_CASH": "현금전달요구여부",
            "INSTALL_APP": "앱설치요구여부",
            "ALLOW_REMOTE_ACCESS": "원격접속요구여부",
            "DISCLOSE_ID_NUMBER": "신원정보요구여부",
            "DISCLOSE_ACCOUNT": "계좌정보요구여부",
            "DISCLOSE_PASSWORD": "비밀번호요구여부",
            "DISCLOSE_OTP": "인증번호요구여부",
            "KEEP_CALL_CONNECTED": "통화유지요구여부",
            "AVOID_OUTSIDE_CONTACT": "외부연락차단요구여부",
        })
        result = result.merge(action_summary, on="case_id", how="left").merge(action_flags, on="case_id", how="left")

    if not amounts_df.empty:
        amount_summary = amounts_df.groupby("case_id").agg(
            전체언급금액_원=("amount_krw", lambda values: " | ".join(str(int(value)) for value in sorted(set(values.dropna())))),
            언급금액_최대_원_전체=("amount_krw", "max"),
            금액이벤트수=("amount_event_id", "count"),
        ).reset_index()
        for status, column in {
            "REQUESTED": "요구금액_최대_원",
            "AGREED": "합의금액_최대_원",
            "CLAIMED_COMPLETED": "이체주장금액_최대_원",
        }.items():
            status_summary = amounts_df[amounts_df["amount_status"] == status].groupby("case_id")["amount_krw"].max().rename(column).reset_index()
            amount_summary = amount_summary.merge(status_summary, on="case_id", how="left")
        completed_cases = set(amounts_df.loc[amounts_df["amount_status"] == "CLAIMED_COMPLETED", "case_id"])
        amount_summary["이체완료주장여부"] = amount_summary["case_id"].isin(completed_cases)
        result = result.merge(amount_summary, on="case_id", how="left")

    publication = pd.to_datetime(result["publication_date"], errors="coerce")
    result["게시년"] = publication.dt.year.astype("Int64")
    result["게시월"] = publication.dt.month.astype("Int64")
    result["원본분류"] = result["source_category"].map(KOREAN_CATEGORY_MAP).fillna("미분류")
    result["주요요구행동"] = result["primary_requested_action"].map(KOREAN_ACTION_MAP).fillna("언급없음")
    result["접근매체"] = "전화"
    result["자동추출여부"] = True
    result["라벨상태"] = "자동생성_실버"
    result["자료출처"] = "금융감독원 보이스피싱 공개 사례"
    result["실제피해액_원"] = pd.NA

    text_defaults = [
        "사칭대상_대분류", "사칭대상_세부유형", "사칭기관명", "사칭부서명",
        "사칭직책", "사칭인물명", "피해자와의관계", "요구행동_전체",
    ]
    for column in text_defaults:
        if column not in result:
            result[column] = "언급없음"
        result[column] = result[column].fillna("언급없음")
    if "사칭정보수" not in result:
        result["사칭정보수"] = 0
    result["사칭정보수"] = result["사칭정보수"].fillna(0).astype(int)
    if "언급금액_최대_원" not in result:
        result["언급금액_최대_원"] = np.nan
    if "언급금액_최대_원_전체" in result:
        result["언급금액_최대_원"] = result["언급금액_최대_원_전체"].combine_first(result["언급금액_최대_원"])
    for column in ["전체언급금액_원", "요구금액_최대_원", "합의금액_최대_원", "이체주장금액_최대_원"]:
        if column not in result:
            result[column] = np.nan
    if "금액이벤트수" not in result:
        result["금액이벤트수"] = 0
    result["금액이벤트수"] = result["금액이벤트수"].fillna(0).astype(int)
    if "이체완료주장여부" not in result:
        result["이체완료주장여부"] = False
    result["이체완료주장여부"] = result["이체완료주장여부"].fillna(False).astype(bool)

    flag_columns = [column for column in result.columns if column.endswith("요구여부")]
    for column in flag_columns:
        result[column] = result[column].fillna(False).astype(bool)

    korean_columns = [
        "case_id", "file_id", "source_file", "게시년", "게시월", "원본분류",
        "사칭대상_대분류", "사칭대상_세부유형", "사칭기관명", "사칭부서명",
        "사칭직책", "사칭인물명", "피해자와의관계", "사칭정보수",
        "주요요구행동", "요구행동_전체", "전체언급금액_원", "언급금액_최대_원",
        "요구금액_최대_원", "합의금액_최대_원", "이체주장금액_최대_원",
        "이체완료주장여부", "금액이벤트수", "실제피해액_원",
        "송금요구여부", "현금인출요구여부", "현금전달요구여부", "앱설치요구여부",
        "원격접속요구여부", "신원정보요구여부", "계좌정보요구여부",
        "비밀번호요구여부", "인증번호요구여부", "통화유지요구여부",
        "외부연락차단요구여부", "접근매체", "duration_sec", "turn_count",
        "offender_turn_count", "victim_turn_count", "unknown_turn_count",
        "raw_full_text", "raw_offender_text", "raw_victim_text", "quality_flag",
        "자동추출여부", "라벨상태", "자료출처", "media_type", "media_composition",
    ]
    rename = {
        "case_id": "사건ID", "file_id": "파일ID", "source_file": "원본파일",
        "duration_sec": "통화시간_초", "turn_count": "전체발화수",
        "offender_turn_count": "범인추정발화수", "victim_turn_count": "피해자추정발화수",
        "unknown_turn_count": "역할미분류발화수", "raw_full_text": "전체대화",
        "raw_offender_text": "범인추정대화", "raw_victim_text": "피해자추정대화",
        "quality_flag": "품질상태", "media_type": "매체형식",
        "media_composition": "매체구성",
    }
    return result.reindex(columns=korean_columns).rename(columns=rename)


def read_postal_data(postal_path: Path | None) -> pd.DataFrame:
    if postal_path is None or not postal_path.exists():
        print("[안내] df_postal.csv가 없어 우체국 통합 비교를 건너뜁니다.")
        return pd.DataFrame()
    for encoding in ("utf-8-sig", "cp949", "utf-8"):
        try:
            postal_df = pd.read_csv(postal_path, encoding=encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise UnicodeDecodeError("unknown", b"", 0, 1, f"인코딩 확인 필요: {postal_path}")
    postal_df.columns = [normalize_text(column) for column in postal_df.columns]
    postal_df["피해액"] = pd.to_numeric(postal_df.get("피해액"), errors="coerce")
    postal_df["최초 접수년"] = pd.to_numeric(postal_df.get("최초 접수년"), errors="coerce").astype("Int64")
    postal_df["최초 접수월"] = pd.to_numeric(postal_df.get("최초 접수월"), errors="coerce").astype("Int64")
    return postal_df


def map_postal_fraud_type(value: object) -> str:
    text = normalize_text(value)
    mapping = {
        "사건연루조사": "수사기관사칭형",
        "투자사기": "투자사기형",
        "가족납치.상해 협박": "가족납치협박형",
        "가족납치·상해 협박": "가족납치협박형",
        "카드배송사칭": "카드배송사칭형",
        "지인사칭(메신저피싱)": "지인사칭형",
        "개인정보유출방지, 보안강화": "개인정보·보안빙자형",
        "기타": "기타",
    }
    return mapping.get(text, text or "미분류")


def map_postal_org(value: object) -> tuple[str, str]:
    text = normalize_text(value)
    mapping = {
        "경찰, 검찰, 법원": ("공공기관", "수사·사법기관"),
        "금감원, 금융위": ("공공기관", "금융감독기관"),
        "금융투자업자": ("금융기관", "금융투자업자"),
        "할부금융(카드사 및 캐피탈)": ("금융기관", "카드·캐피탈사"),
        "우체국, 전화국, 택배회사": ("배송·통신기관", "우체국·전화국·택배회사"),
        "개인": ("개인", "가족·지인·기타개인"),
        "기타": ("기타", "기타"),
    }
    return mapping.get(text, ("미분류", text or "미분류"))


def standardize_postal_data(postal_df: pd.DataFrame) -> pd.DataFrame:
    if postal_df.empty:
        return postal_df
    result = postal_df.copy()
    result.insert(0, "피해사례ID", [f"postal_{index:04d}" for index in range(1, len(result) + 1)])
    result["사기유형_표준"] = result["사기유형"].apply(map_postal_fraud_type)
    mapped_org = result["사칭기관"].apply(map_postal_org)
    result["사칭대상_대분류"] = mapped_org.str[0]
    result["사칭대상_세부유형"] = mapped_org.str[1]
    result["자료출처"] = "우체국 피해사례"
    result["금액자료유형"] = "실제피해액"
    return result


def build_taxonomy_mapping() -> pd.DataFrame:
    rows = []
    postal_types = {
        "사건연루조사": "수사기관사칭형", "투자사기": "투자사기형",
        "가족납치.상해 협박": "가족납치협박형", "카드배송사칭": "카드배송사칭형",
        "지인사칭(메신저피싱)": "지인사칭형",
        "개인정보유출방지, 보안강화": "개인정보·보안빙자형", "기타": "기타",
    }
    for original, standard in postal_types.items():
        rows.append({"매핑구분": "사기유형", "원본데이터": "우체국 피해사례", "원본값": original, "표준대분류": standard, "표준세부유형": "", "설명": "우체국 사기유형 표준화"})
    for original, standard in {"LOAN_FRAUD": "대출사기형", "INSTITUTION_IMPERSONATION": "수사기관사칭형", "MIXED_UNKNOWN": "혼합·미분류"}.items():
        rows.append({"매핑구분": "사기유형", "원본데이터": "금감원 전사사례", "원본값": original, "표준대분류": standard, "표준세부유형": "", "설명": "전사 원본분류 표준화"})
    postal_orgs = ["경찰, 검찰, 법원", "금감원, 금융위", "금융투자업자", "할부금융(카드사 및 캐피탈)", "우체국, 전화국, 택배회사", "개인", "기타"]
    for original in postal_orgs:
        group, subtype = map_postal_org(original)
        rows.append({"매핑구분": "사칭기관", "원본데이터": "우체국 피해사례", "원본값": original, "표준대분류": group, "표준세부유형": subtype, "설명": "우체국 사칭기관 표준화"})
    for code, korean in KOREAN_IMPERSONATION_SUBTYPE_MAP.items():
        if code == "NOT_MENTIONED":
            continue
        group = next((KOREAN_IMPERSONATION_GROUP_MAP[group_code] for group_code, subtype, _ in IMPERSONATION_RULES if subtype == code), "기타")
        rows.append({"매핑구분": "사칭기관", "원본데이터": "금감원 전사사례", "원본값": code, "표준대분류": group, "표준세부유형": korean, "설명": "전사 자동추출 사칭유형 표준화"})
    return pd.DataFrame(rows)


def build_integrated_comparison(korean_cases_df: pd.DataFrame, postal_standard_df: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "데이터출처", "기준연도", "사기유형_표준", "사칭대상_대분류",
        "사칭대상_세부유형", "사칭기관명_표준", "접근매체", "사건수",
        "피해액합계_원", "피해액중앙값_원", "언급금액합계_원",
        "언급금액중앙값_원", "금액자료유형",
    ]
    parts = []
    if not korean_cases_df.empty:
        fraud = korean_cases_df.copy()
        fraud["기준연도"] = fraud["게시년"]
        fraud["사기유형_표준"] = fraud["원본분류"]
        fraud["사칭기관명_표준"] = fraud["사칭기관명"]
        fraud_group = fraud.groupby([
            "기준연도", "사기유형_표준", "사칭대상_대분류",
            "사칭대상_세부유형", "사칭기관명_표준", "접근매체",
        ], dropna=False).agg(
            사건수=("사건ID", "count"),
            언급금액합계_원=("언급금액_최대_원", "sum"),
            언급금액중앙값_원=("언급금액_최대_원", "median"),
        ).reset_index()
        fraud_group.insert(0, "데이터출처", "금감원 전사사례")
        fraud_group["피해액합계_원"] = np.nan
        fraud_group["피해액중앙값_원"] = np.nan
        fraud_group["금액자료유형"] = "대화언급금액"
        parts.append(fraud_group)

    if not postal_standard_df.empty:
        postal = postal_standard_df.copy()
        postal["기준연도"] = postal["최초 접수년"]
        postal["사칭기관명_표준"] = postal["사칭기관"]
        postal_group = postal.groupby([
            "기준연도", "사기유형_표준", "사칭대상_대분류",
            "사칭대상_세부유형", "사칭기관명_표준", "접근매체",
        ], dropna=False).agg(
            사건수=("피해사례ID", "count"),
            피해액합계_원=("피해액", "sum"),
            피해액중앙값_원=("피해액", "median"),
        ).reset_index()
        postal_group.insert(0, "데이터출처", "우체국 피해사례")
        postal_group["언급금액합계_원"] = np.nan
        postal_group["언급금액중앙값_원"] = np.nan
        postal_group["금액자료유형"] = "실제피해액"
        parts.append(postal_group)

    if not parts:
        return pd.DataFrame(columns=columns)
    return pd.concat(parts, ignore_index=True).reindex(columns=columns)


def save_table(df: pd.DataFrame, output_dir: Path, name: str) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / f"{name}.csv"
    parquet_path = output_dir / f"{name}.parquet"
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    parquet_saved = False
    try:
        df.to_parquet(parquet_path, index=False)
        parquet_saved = True
    except Exception as exc:
        print(f"[경고] Parquet 저장 생략: {name} / {exc}")
    return {
        "name": name,
        "rows": int(len(df)),
        "columns": int(len(df.columns)),
        "csv": str(csv_path),
        "parquet": str(parquet_path) if parquet_saved else None,
    }


def validate_outputs(tables: dict[str, pd.DataFrame]) -> dict:
    report = {}
    unique_checks = {
        "vp_files": "file_id",
        "vp_cases": "case_id",
        "vp_utterances": "turn_id",
        "vp_impersonations": "impersonation_id",
        "vp_requested_actions": "action_id",
        "vp_strategy_events": "strategy_event_id",
        "vp_amount_events": "amount_event_id",
        "normal_finance_calls": "source_id",
    }
    for name, df in tables.items():
        item = {
            "rows": int(len(df)),
            "columns": int(len(df.columns)),
            "empty": bool(df.empty),
        }
        id_column = unique_checks.get(name)
        if id_column and id_column in df:
            item["duplicate_id_count"] = int(df[id_column].duplicated().sum())
            item["missing_id_count"] = int(df[id_column].isna().sum())
        report[name] = item
    if not tables["vp_cases"].empty:
        report["vp_cases"]["source_category"] = tables["vp_cases"]["source_category"].value_counts(dropna=False).to_dict()
    if not tables["fraud_detection_ml"].empty:
        report["fraud_detection_ml"]["fraud_label"] = tables["fraud_detection_ml"]["fraud_label"].value_counts(dropna=False).to_dict()
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--result-root", type=Path, required=True)
    parser.add_argument("--normal-root", type=Path, required=False)
    parser.add_argument("--postal-path", type=Path, required=False)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()

    standard_dir = args.output_root / "01_standard_tables"
    ml_dir = args.output_root / "02_ml_tables"
    dashboard_dir = args.output_root / "03_dashboard_tables"
    report_dir = args.output_root / "04_reports"
    report_dir.mkdir(parents=True, exist_ok=True)

    print("1/6 보이스피싱 cases.json 처리")
    files_df, cases_df, utterances_df, impersonations_df, actions_df, strategies_df, amounts_df = load_phishing_tables(args.result_root)

    print("2/6 정상 금융상담 처리")
    normal_root = args.normal_root or Path("__normal_data_not_provided__")
    normal_df = load_normal_calls(normal_root)

    print("3/6 우체국 피해사례 및 한글 사건요약 처리")
    postal_raw_df = read_postal_data(args.postal_path)
    postal_standard_df = standardize_postal_data(postal_raw_df)
    korean_cases_df = build_korean_case_summary(files_df, cases_df, impersonations_df, actions_df, amounts_df)
    taxonomy_mapping_df = build_taxonomy_mapping()
    integrated_comparison_df = build_integrated_comparison(korean_cases_df, postal_standard_df)

    print("4/6 머신러닝용 테이블 생성")
    fraud_detection_df = build_fraud_detection_ml(cases_df, normal_df)
    fraud_type_df = build_fraud_type_ml(cases_df)
    segment_df = build_segment_detection_ml(cases_df, utterances_df, normal_df, fraud_detection_df)
    clustering_df = build_clustering_ml(cases_df)

    print("5/6 대시보드용 테이블 생성")
    dashboard_df = build_dashboard_summary(cases_df, impersonations_df, actions_df, strategies_df)

    tables = {
        "vp_files": files_df,
        "vp_cases": cases_df,
        "vp_utterances": utterances_df,
        "vp_impersonations": impersonations_df,
        "vp_requested_actions": actions_df,
        "vp_strategy_events": strategies_df,
        "vp_amount_events": amounts_df,
        "normal_finance_calls": normal_df,
        "보이스피싱_사건요약_한글": korean_cases_df,
        "우체국_피해사례_표준화": postal_standard_df,
        "사기유형_매핑표": taxonomy_mapping_df,
        "사기유형_통합비교": integrated_comparison_df,
        "fraud_detection_ml": fraud_detection_df,
        "fraud_type_ml": fraud_type_df,
        "segment_detection_ml": segment_df,
        "case_clustering_ml": clustering_df,
        "dashboard_case_summary": dashboard_df,
    }

    print("6/6 저장 및 검증")
    manifest = []
    for name in ["vp_files", "vp_cases", "vp_utterances", "vp_impersonations", "vp_requested_actions", "vp_strategy_events", "vp_amount_events", "normal_finance_calls"]:
        manifest.append(save_table(tables[name], standard_dir, name))
    for name in ["fraud_detection_ml", "fraud_type_ml", "segment_detection_ml", "case_clustering_ml"]:
        manifest.append(save_table(tables[name], ml_dir, name))
    manifest.append(save_table(tables["dashboard_case_summary"], dashboard_dir, "dashboard_case_summary"))
    for name in ["보이스피싱_사건요약_한글", "우체국_피해사례_표준화", "사기유형_매핑표", "사기유형_통합비교"]:
        manifest.append(save_table(tables[name], dashboard_dir, name))

    validation = validate_outputs(tables)
    (report_dir / "dataset_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    (report_dir / "validation_report.json").write_text(json.dumps(validation, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n=== 생성 완료 ===")
    for item in manifest:
        print(f"{item['name']}: {item['rows']:,}행 × {item['columns']:,}열")
    print("저장 위치:", args.output_root)
    print("검증 보고서:", report_dir / "validation_report.json")


if __name__ == "__main__":
    main()
