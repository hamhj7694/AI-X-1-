"""Stage 2: test the 17 datasets and create a small review sample."""

from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


SCRIPT_VERSION = "2.1.0"
DEFAULT_REVIEW_COUNT = 40
RANDOM_SEED = 42

TABLE_GROUPS = {
    "vp_files": "01_standard_tables",
    "vp_cases": "01_standard_tables",
    "vp_utterances": "01_standard_tables",
    "vp_impersonations": "01_standard_tables",
    "vp_requested_actions": "01_standard_tables",
    "vp_strategy_events": "01_standard_tables",
    "vp_amount_events": "01_standard_tables",
    "normal_finance_calls": "01_standard_tables",
    "fraud_detection_ml": "02_ml_tables",
    "fraud_type_ml": "02_ml_tables",
    "segment_detection_ml": "02_ml_tables",
    "case_clustering_ml": "02_ml_tables",
    "dashboard_case_summary": "03_dashboard_tables",
    "보이스피싱_사건요약_한글": "03_dashboard_tables",
    "우체국_피해사례_표준화": "03_dashboard_tables",
    "사기유형_매핑표": "03_dashboard_tables",
    "사기유형_통합비교": "03_dashboard_tables",
}

ID_COLUMNS = {
    "vp_files": "file_id",
    "vp_cases": "case_id",
    "vp_utterances": "turn_id",
    "vp_impersonations": "impersonation_id",
    "vp_requested_actions": "action_id",
    "vp_strategy_events": "strategy_event_id",
    "vp_amount_events": "amount_event_id",
    "normal_finance_calls": "conversation_id",
}


def load_table(dataset_root: Path, table_name: str) -> pd.DataFrame:
    folder = dataset_root / TABLE_GROUPS[table_name]
    parquet_path = folder / f"{table_name}.parquet"
    csv_path = folder / f"{table_name}.csv"
    if parquet_path.exists():
        return pd.read_parquet(parquet_path)
    if csv_path.exists():
        return pd.read_csv(csv_path, low_memory=False)
    raise FileNotFoundError(f"Missing table: {table_name}")


def load_all_tables(dataset_root: Path) -> dict[str, pd.DataFrame]:
    return {name: load_table(dataset_root, name) for name in TABLE_GROUPS}


def build_table_summary(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for name, df in tables.items():
        rows.append({
            "table_name": name,
            "row_count": len(df),
            "column_count": len(df.columns),
            "missing_cell_count": int(df.isna().sum().sum()),
            "duplicate_row_count": int(df.duplicated().sum()),
        })
    return pd.DataFrame(rows)


def build_column_inventory(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for table_name, df in tables.items():
        for order, column in enumerate(df.columns, 1):
            rows.append({
                "table_name": table_name,
                "column_order": order,
                "column_name": column,
                "dtype": str(df[column].dtype),
                "missing_count": int(df[column].isna().sum()),
                "unique_count": int(df[column].nunique(dropna=True)),
            })
    return pd.DataFrame(rows)


def add_check(rows: list[dict], check_name: str, error_count: int, required_zero: bool = True):
    rows.append({
        "check_name": check_name,
        "error_count": int(error_count),
        "is_gate_check": required_zero,
        "passed": int(error_count) == 0 if required_zero else True,
    })


def build_quality_checks(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for table_name, key in ID_COLUMNS.items():
        df = tables[table_name]
        add_check(rows, f"{table_name}.{key}.duplicate", df[key].duplicated().sum())
        add_check(rows, f"{table_name}.{key}.missing", df[key].isna().sum())

    files = set(tables["vp_files"]["file_id"].dropna())
    cases = set(tables["vp_cases"]["case_id"].dropna())
    turns = set(tables["vp_utterances"]["turn_id"].dropna())
    add_check(rows, "vp_cases.file_id.orphan", (~tables["vp_cases"]["file_id"].isin(files)).sum())
    add_check(rows, "vp_utterances.file_id.orphan", (~tables["vp_utterances"]["file_id"].isin(files)).sum())
    add_check(rows, "vp_utterances.case_id.orphan", (~tables["vp_utterances"]["case_id"].isin(cases)).sum())

    for name in ["vp_impersonations", "vp_requested_actions", "vp_strategy_events", "vp_amount_events"]:
        df = tables[name]
        add_check(rows, f"{name}.case_id.orphan", (~df["case_id"].isin(cases)).sum())
        add_check(rows, f"{name}.evidence_turn_id.orphan", (~df["evidence_turn_id"].isin(turns)).sum())

    utterances = tables["vp_utterances"]
    cases_df = tables["vp_cases"]
    amounts = tables["vp_amount_events"]
    add_check(rows, "utterance.empty_normalized_text", utterances["normalized_text"].fillna("").str.strip().eq("").sum(), False)
    add_check(rows, "utterance.review_role", utterances["auto_role"].eq("REVIEW").sum(), False)
    add_check(rows, "utterance.low_information", utterances["is_low_information"].fillna(False).astype(bool).sum(), False)
    add_check(rows, "case.needs_review", cases_df["needs_review"].fillna(False).astype(bool).sum(), False)
    add_check(rows, "amount.non_positive", pd.to_numeric(amounts["amount_krw"], errors="coerce").le(0).sum())
    add_check(rows, "amount.auto_filled_verified_loss", amounts["verified_loss_amount_krw"].notna().sum())
    return pd.DataFrame(rows)


def event_turn_set(df: pd.DataFrame) -> set:
    return set(df["evidence_turn_id"].dropna()) if not df.empty else set()


def select_review_sample(tables: dict[str, pd.DataFrame], review_count: int, seed: int) -> pd.DataFrame:
    utterances = tables["vp_utterances"].sort_values(["case_id", "turn_order"]).copy()
    cases = tables["vp_cases"][["case_id", "source_category", "source_file", "needs_review"]]
    files = tables["vp_files"][["file_id", "multi_case_file"]]
    sample = utterances.merge(cases, on="case_id", how="left").merge(files, on="file_id", how="left")
    sample["previous_text"] = sample.groupby("case_id")["raw_text"].shift(1).fillna("")
    sample["next_text"] = sample.groupby("case_id")["raw_text"].shift(-1).fillna("")

    event_sets = {
        "has_impersonation_event": event_turn_set(tables["vp_impersonations"]),
        "has_action_event": event_turn_set(tables["vp_requested_actions"]),
        "has_strategy_event": event_turn_set(tables["vp_strategy_events"]),
        "has_amount_event": event_turn_set(tables["vp_amount_events"]),
    }
    for column, values in event_sets.items():
        sample[column] = sample["turn_id"].isin(values)

    text_length = sample["normalized_text"].fillna("").str.replace(r"[^0-9A-Za-z가-힣]", "", regex=True).str.len()
    sample = sample[(text_length >= 8) & ~sample["is_low_information"].fillna(False).astype(bool)].copy()
    sample["priority_score"] = (
        sample["has_impersonation_event"].astype(int) * 3
        + sample["has_action_event"].astype(int) * 4
        + sample["has_strategy_event"].astype(int) * 2
        + sample["has_amount_event"].astype(int) * 4
        + sample["auto_role"].eq("REVIEW").astype(int) * 3
        + sample["needs_review"].fillna(False).astype(bool).astype(int) * 2
        + sample["multi_case_file"].fillna(False).astype(bool).astype(int)
        + sample["voice_modified"].fillna(False).astype(bool).astype(int) * 2
    )
    candidates = sample[sample["priority_score"] > 0].sort_values(
        ["priority_score", "avg_logprob"], ascending=[False, True]
    ).drop_duplicates(["case_id", "normalized_text"])

    review_count = min(max(30, review_count), 50, len(candidates))
    priority_count = min(len(candidates), int(math.ceil(review_count * 0.8)))
    selected = candidates.head(priority_count)
    remaining = candidates[~candidates["turn_id"].isin(selected["turn_id"])]
    random_count = review_count - len(selected)
    if random_count:
        selected = pd.concat([
            selected,
            remaining.sample(n=min(random_count, len(remaining)), random_state=seed),
        ])
    selected = selected.head(review_count).sort_values(["file_id", "case_id", "turn_order"]).reset_index(drop=True)
    selected.insert(0, "review_no", range(1, len(selected) + 1))

    output_columns = [
        "review_no", "file_id", "case_id", "turn_id", "source_category", "source_file",
        "start_sec", "end_sec", "turn_order", "previous_text", "raw_text", "next_text",
        "speaker_id", "auto_role", "role_heuristic_score", "avg_logprob", "voice_modified",
        "has_impersonation_event", "has_action_event", "has_strategy_event", "has_amount_event",
        "priority_score",
    ]
    selected = selected[output_columns]
    for column, default in [
        ("reviewer", ""), ("review_status", "NOT_REVIEWED"), ("gold_text", ""),
        ("gold_role", ""), ("impersonation_correct", ""), ("action_correct", ""),
        ("strategy_correct", ""), ("amount_correct", ""), ("review_note", ""),
    ]:
        selected[column] = default
    return selected


def save_review_workbook(path: Path, review_df: pd.DataFrame, force: bool):
    if path.exists() and not force:
        print(f"[KEEP] Existing review file: {path}")
        return
    guide = pd.DataFrame([
        ["scope", "Review only the selected 30-50 utterances."],
        ["gold_rule", "Only rows marked COMPLETED with human answers are HUMAN GOLD."],
        ["gold_role", "OFFENDER / VICTIM / THIRD_PARTY / REVIEW / EXCLUDE"],
        ["correct_fields", "TRUE / FALSE / NOT_APPLICABLE / UNSURE"],
    ], columns=["item", "description"])
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        guide.to_excel(writer, sheet_name="guide", index=False)
        review_df.to_excel(writer, sheet_name="review_sample", index=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--review-count", type=int, default=DEFAULT_REVIEW_COUNT)
    parser.add_argument("--seed", type=int, default=RANDOM_SEED)
    parser.add_argument("--force-review", action="store_true")
    args = parser.parse_args()
    args.output_root.mkdir(parents=True, exist_ok=True)

    print(f"Stage 2 dataset quality test v{SCRIPT_VERSION}")
    tables = load_all_tables(args.dataset_root)
    assert len(tables) == 17, f"Expected 17 tables, found {len(tables)}"

    summary = build_table_summary(tables)
    columns = build_column_inventory(tables)
    checks = build_quality_checks(tables)
    review = select_review_sample(tables, args.review_count, args.seed)

    summary.to_csv(args.output_root / "table_summary.csv", index=False, encoding="utf-8-sig")
    columns.to_csv(args.output_root / "column_inventory.csv", index=False, encoding="utf-8-sig")
    checks.to_csv(args.output_root / "quality_checks.csv", index=False, encoding="utf-8-sig")
    save_review_workbook(args.output_root / "human_review_sample_40.xlsx", review, args.force_review)

    gate_failed = checks[checks["is_gate_check"] & ~checks["passed"]]
    report = {
        "script_version": SCRIPT_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "table_count": len(tables),
        "review_sample_count": len(review),
        "gate_failed_count": len(gate_failed),
        "gate_passed": gate_failed.empty,
        "note": "This is a test result. Unreviewed automatic labels remain SILVER.",
    }
    (args.output_root / "quality_test_manifest.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("tables:", len(tables))
    print("review sample:", len(review))
    print("gate passed:", gate_failed.empty)
    print("saved:", args.output_root)


if __name__ == "__main__":
    main()
