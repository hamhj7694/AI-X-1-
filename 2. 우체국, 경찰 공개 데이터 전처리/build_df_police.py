from pathlib import Path
import hashlib
import re

import pandas as pd


DOWNLOADS = Path.home() / "Downloads"
OUTPUT = Path(__file__).resolve().parent / "df_police.csv"

FILES = {
    "overall": "경찰청_보이스피싱 현황_20251231.csv",
    "gender": "경찰청_전화금융사기 피해자 성별 현황_20251231.csv",
    "age": "경찰청_전화금융사기 피해자 연령별 현황_20251231.csv",
    "region": "경찰청_전화금융사기_시도경찰청별_피해_현황_20251231.csv",
    "monthly": "경찰청_보이스피싱 월별 발생 건수_20180101~20231031.csv",
}


def read_csv(name: str) -> pd.DataFrame:
    path = DOWNLOADS / name
    if not path.exists():
        raise FileNotFoundError(path)
    for encoding in ("utf-8-sig", "cp949", "euc-kr"):
        try:
            df = pd.read_csv(path, encoding=encoding, dtype="string")
            break
        except UnicodeDecodeError:
            continue
    else:
        raise ValueError(f"인코딩을 확인할 수 없습니다: {path}")
    df.columns = df.columns.str.strip()
    for column in df.columns:
        df[column] = df[column].str.strip()
    df = df.replace(["", "-", "NA", "N/A", "null", "NULL"], pd.NA)
    return df


tables = {key: read_csv(name) for key, name in FILES.items()}

# 원본 결측치 및 완전 중복 검사
for key, df in tables.items():
    if int(df.isna().sum().sum()) != 0:
        raise ValueError(f"원본 결측치 발견: {FILES[key]}\n{df.isna().sum()}")
    if int(df.duplicated().sum()) != 0:
        raise ValueError(f"원본 완전 중복행 발견: {FILES[key]}")

parts = []


def append_part(frame: pd.DataFrame, source_key: str, time_unit: str) -> None:
    x = frame.copy()
    x["시간단위"] = time_unit
    x["출처파일"] = FILES[source_key]
    parts.append(x)


# 전국 연도별 사기유형 지표
overall = tables["overall"]
for fraud_type in ("기관사칭형", "대출사기형"):
    for metric, suffix, unit in (
        ("발생건수", "발생건수", "건"),
        ("피해액", "피해액_억원", "억원"),
        ("검거인원", "검거인원", "명"),
    ):
        append_part(
            pd.DataFrame(
                {
                    "연도": overall["구분"],
                    "월": pd.NA,
                    "지역": "전국",
                    "분류축": "사기유형",
                    "분류값": fraud_type,
                    "지표": metric,
                    "값": overall[f"{fraud_type}_{suffix}"],
                    "단위": unit,
                }
            ),
            "overall",
            "연",
        )

# 전국 연도별 성별 피해자 수
gender = tables["gender"].melt(
    id_vars="구분", value_vars=["남성", "여성"], var_name="분류값", value_name="값"
)
append_part(
    gender.rename(columns={"구분": "연도"}).assign(
        월=pd.NA, 지역="전국", 분류축="성별", 지표="피해자수", 단위="명"
    )[["연도", "월", "지역", "분류축", "분류값", "지표", "값", "단위"]],
    "gender",
    "연",
)

# 전국 연도별 연령대 피해자 수
age_columns = ["20대이하", "30대", "40대", "50대", "60대", "70대이상"]
age = tables["age"].melt(
    id_vars="구분", value_vars=age_columns, var_name="분류값", value_name="값"
)
append_part(
    age.rename(columns={"구분": "연도"}).assign(
        월=pd.NA, 지역="전국", 분류축="연령대", 지표="피해자수", 단위="명"
    )[["연도", "월", "지역", "분류축", "분류값", "지표", "값", "단위"]],
    "age",
    "연",
)

# 시도경찰청별 연도별 피해 발생건수
region = tables["region"]
year_columns = [column for column in region.columns if re.fullmatch(r"20\d{2}년", column)]
region = region.melt(
    id_vars="시도청", value_vars=year_columns, var_name="연도", value_name="값"
)
region["연도"] = region["연도"].str.extract(r"(20\d{2})", expand=False)
append_part(
    region.rename(columns={"시도청": "지역"}).assign(
        월=pd.NA, 분류축="전체", 분류값="전체", 지표="발생건수", 단위="건"
    )[["연도", "월", "지역", "분류축", "분류값", "지표", "값", "단위"]],
    "region",
    "연",
)

# 전국 월별 발생건수
monthly = tables["monthly"]
append_part(
    pd.DataFrame(
        {
            "연도": monthly["년"],
            "월": monthly["월"],
            "지역": "전국",
            "분류축": "전체",
            "분류값": "전체",
            "지표": "발생건수",
            "값": monthly["전화금융사기 발생건수"],
            "단위": "건",
        }
    ),
    "monthly",
    "월",
)

df_police = pd.concat(parts, ignore_index=True)
df_police["연도"] = pd.to_numeric(df_police["연도"], errors="raise").astype("Int64")
df_police["월"] = pd.to_numeric(df_police["월"], errors="coerce").astype("Int64")
df_police["값"] = pd.to_numeric(
    df_police["값"].str.replace(",", "", regex=False), errors="raise"
).astype("Int64")
df_police["월_결측유형"] = df_police["월"].isna().map(
    {True: "연간자료_비해당", False: "월정보_존재"}
)

columns = [
    "연도", "월", "지역", "분류축", "분류값", "지표", "값", "단위",
    "시간단위", "월_결측유형", "출처파일",
]
df_police = df_police[columns].sort_values(
    ["연도", "월", "지역", "분류축", "분류값", "지표"], na_position="last"
).reset_index(drop=True)

# 품질 검증 1: 연령/성별/지역 합계가 전국 발생건수와 일치해야 함
national_cases = (
    df_police.query("지역 == '전국' and 분류축 == '사기유형' and 지표 == '발생건수'")
    .groupby("연도")["값"].sum()
)
age_total = df_police.query("분류축 == '연령대'").groupby("연도")["값"].sum()
gender_total = df_police.query("분류축 == '성별'").groupby("연도")["값"].sum()
region_total = (
    df_police.query("지역 != '전국' and 지표 == '발생건수'")
    .groupby("연도")["값"].sum()
)
assert national_cases.equals(age_total), "연령별 합계 불일치"
assert national_cases.equals(gender_total), "성별 합계 불일치"
assert national_cases.equals(region_total), "지역별 합계 불일치"

# 품질 검증 2: 구조적 월 결측 외에는 결측치가 없어야 함
missing = df_police.isna().sum()
assert missing.drop("월").sum() == 0, f"예상하지 않은 결측치:\n{missing}"
assert missing["월"] == (df_police["시간단위"] == "연").sum()
assert not df_police.duplicated().any(), "통합 후 완전 중복행 발견"

df_police.to_csv(OUTPUT, index=False, encoding="utf-8-sig")
print(f"saved={OUTPUT}")
print(f"rows={len(df_police)}, columns={len(df_police.columns)}")
print(f"month_structural_na={int(df_police['월'].isna().sum())}")
print("source_rows=")
print(df_police.groupby("출처파일").size().to_string())
