# -*- coding: utf-8 -*-
"""
pfe_4_ip_lifecycle_analysis.py
Local VS Code version.

Input:
    backend/data/processed/final_data.csv
Output:
    backend/data/processed/first_ip_summary.csv
    backend/data/processed/IP_Analyse.csv
    backend/data/processed/IP_LifeCycle.xlsx
"""

from pathlib import Path
import pandas as pd
import numpy as np

pd.set_option("display.float_format", lambda x: f"{x:,.2f}")


# ============================================================
# PATHS
# ============================================================
BACKEND_DIR = Path(__file__).resolve().parent
PROCESSED_DIR = BACKEND_DIR / "data" / "processed"

INPUT_FINAL_DATA = PROCESSED_DIR / "final_data.csv"
OUTPUT_FIRST_IP_SUMMARY_CSV = PROCESSED_DIR / "first_ip_summary.csv"
OUTPUT_IP_ANALYSE_CSV = PROCESSED_DIR / "IP_Analyse.csv"
OUTPUT_IP_LIFECYCLE_XLSX = PROCESSED_DIR / "IP_LifeCycle.xlsx"


# ============================================================
# HELPERS
# ============================================================
def load_final_data(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(
            f"Missing input file: {path}\n"
            "Run pfe_3_dataCleaning.py first to generate final_data.csv."
        )

    df = pd.read_csv(path)
    print(f"Loaded final_data: {df.shape} from {path}")

    required_cols = [
        "campaign_id", "server", "entity", "ip", "datetime_gride", "sent_detail",
        "r_sent_detail", "sent_per_ip", "r_sent_per_ip", "offset", "limit",
        "limit_per_ip", "outSum", "error_type_from_error"
    ]

    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"final_data.csv is missing required columns: {missing}")

    return df


def clean_and_round_numeric_columns(dataframe: pd.DataFrame, cols_to_fix: list[str]) -> pd.DataFrame:
    dataframe = dataframe.copy()
    for col in cols_to_fix:
        if col in dataframe.columns:
            dataframe[col] = pd.to_numeric(dataframe[col], errors="coerce").round().astype("Int64")
    return dataframe


def categorize_volume(v) -> str:
    try:
        v = float(v)
    except Exception:
        return "Unknown"

    if v < 10_000:
        return "Low"
    elif v <= 50_000:
        return "Medium"
    return "High"


# ============================================================
# MAIN PIPELINE
# ============================================================
def main() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # 1) Load final_data from pfe_3
    df = load_final_data(INPUT_FINAL_DATA)

    # 2) Basic preparation
    df["datetime_gride"] = pd.to_datetime(df["datetime_gride"], errors="coerce")
    df = df.dropna(subset=["ip", "datetime_gride"]).copy()
    df = df.sort_values(by=["ip", "datetime_gride"]).reset_index(drop=True)

    numeric_cols = [
        "campaign_id", "sent_detail", "r_sent_detail", "sent_per_ip",
        "r_sent_per_ip", "offset", "limit", "limit_per_ip", "outSum"
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(",", "", regex=False), errors="coerce")

    df["error_type_from_error"] = df["error_type_from_error"].fillna("No error")

    # 3) Detect first usage per IP
    first_usage = (
        df.groupby("ip", as_index=False)
        .first()
        .rename(
            columns={
                "datetime_gride": "first_used_at",
                "sent_per_ip": "first_sent_per_ip",
                "error_type_from_error": "first_error",
                "limit_per_ip": "first_limit",
                "offset": "first_offset",
            }
        )
    )

    first_usage = first_usage[
    [
        "ip", "server", "entity", "first_used_at",
        "first_sent_per_ip", "r_sent_per_ip",
        "first_error", "first_limit", "first_offset"
    ]
    ].copy()

    first_usage = first_usage.rename(columns={
    "r_sent_per_ip": "first_r_sent_per_ip"
    })

    success_errors = ["No error"]

    success_cond = (
    first_usage["first_error"].isin(success_errors)
    & (
        pd.to_numeric(first_usage["first_r_sent_per_ip"], errors="coerce")
        >= pd.to_numeric(first_usage["first_sent_per_ip"], errors="coerce") * 0.95
    )
    )
    first_usage["first_launch_success"] = success_cond.astype(int)

    first_ip_summary = first_usage[
    [
        "ip", "server", "entity", "first_used_at",
        "first_sent_per_ip", "first_r_sent_per_ip",
        "first_error", "first_limit", "first_offset",
        "first_launch_success"
    ]
    ].copy()

    # 4) Row-level lifecycle features
    df["drop_number"] = df.groupby("ip").cumcount() + 1
    df["is_first_drop"] = (df["drop_number"] == 1).astype(int)

    first_used_map = first_usage.set_index("ip")["first_used_at"]
    df["first_used_at"] = df["ip"].map(first_used_map)
    df["first_used_at"] = pd.to_datetime(df["first_used_at"], errors="coerce")
    df["days_since_launch"] = (df["datetime_gride"] - df["first_used_at"]).dt.days

    df["previous_r_sent_per_ip"] = (
    df.groupby("ip")["r_sent_per_ip"].shift(1).fillna(0)
    )

    df["volume_change"] = (
    df["r_sent_per_ip"] - df["previous_r_sent_per_ip"]
    )

    df["growth_rate"] = np.where(
    df["previous_r_sent_per_ip"] > 0,
    df["volume_change"] / df["previous_r_sent_per_ip"],
    0
    )

    df["sent_ratio"] = np.where(
    df["sent_per_ip"] > 0,
    df["r_sent_per_ip"] / df["sent_per_ip"],
    0
    )

    df["lost_volume"] = df["sent_per_ip"] - df["r_sent_per_ip"]

   
    df["growth_rate"] = df["growth_rate"].replace([np.inf, -np.inf], 0).fillna(0)

    df["cumulative_r_sent_per_ip"] = (
    df.groupby("ip")["r_sent_per_ip"].cumsum()
    )
    df["hour"] = df["datetime_gride"].dt.hour
    df["day_of_week"] = df["datetime_gride"].dt.dayofweek
    df["date"] = df["datetime_gride"].dt.date

    df["daily_cumulative_r_sent_per_ip"] = (
    df.groupby(["ip", "date"])["r_sent_per_ip"]
    .transform("cumsum")
    .fillna(0)
    )

    drops_per_day = df.groupby(["ip", "date"]).size().reset_index(name="drops_per_day")
    df = df.merge(drops_per_day, on=["ip", "date"], how="left")

    error_map = {
        "No error": 0,
        "Rate limit SPF": 1,
        "Rate limit DKIM": 2,
        "Rate limit IP Netblock": 3,
    }
    df["error_code"] = df["error_type_from_error"].map(error_map).fillna(0)
    df["volume_category"] = df["r_sent_per_ip"].apply(categorize_volume)
    fill_cols = [
    "days_since_launch", "previous_r_sent_per_ip", "volume_change",
    "cumulative_r_sent_per_ip", "daily_cumulative_r_sent_per_ip",
    "sent_ratio", "lost_volume", "hour", "day_of_week",
    "drops_per_day", "error_code"
    ]
    for col in fill_cols:
        if col in df.columns:
            df[col] = df[col].fillna(0)

    # 5) Final IP_Analyse dataframe
    final_cols = [
    "campaign_id", "server", "entity", "ip", "datetime_gride",
    "sent_detail", "r_sent_detail", "sent_per_ip", "r_sent_per_ip",
    "offset", "limit", "limit_per_ip", "error_type_from_error", "outSum",
    "drop_number", "is_first_drop", "first_used_at",
    "previous_r_sent_per_ip", "volume_change", "growth_rate",
    "sent_ratio", "lost_volume",
    "cumulative_r_sent_per_ip", "daily_cumulative_r_sent_per_ip",
    "volume_category", "hour", "day_of_week", "drops_per_day",
    "error_code", "date", "days_since_launch"
    ]
    available_cols = [c for c in final_cols if c in df.columns]
    IP_Analyse = df[available_cols].copy()

    # Important: do NOT round growth_rate because it is a percentage ratio.
    cols_to_round = [
        "campaign_id", "sent_detail", "r_sent_detail", "sent_per_ip", "r_sent_per_ip",
        "offset", "limit", "limit_per_ip", "outSum", "drop_number", "is_first_drop",
        "previous_sent_per_ip", "volume_change", "cumulative_sent_per_ip",
        "daily_cumulative_sent_per_ip", "hour", "day_of_week", "drops_per_day",
        "error_code", "days_since_launch"
    ]
    IP_Analyse = clean_and_round_numeric_columns(IP_Analyse, cols_to_round)

    # 6) Save outputs for next scripts
    first_ip_summary.to_csv(OUTPUT_FIRST_IP_SUMMARY_CSV, index=False, encoding="utf-8-sig")
    IP_Analyse.to_csv(OUTPUT_IP_ANALYSE_CSV, index=False, encoding="utf-8-sig")
    IP_Analyse.to_excel(OUTPUT_IP_LIFECYCLE_XLSX, index=False)

    # 7) Terminal summary
    print("\nPFE 4 completed successfully.")
    print(f"Saved: {OUTPUT_FIRST_IP_SUMMARY_CSV} | shape={first_ip_summary.shape}")
    print(f"Saved: {OUTPUT_IP_ANALYSE_CSV} | shape={IP_Analyse.shape}")
    print(f"Saved: {OUTPUT_IP_LIFECYCLE_XLSX}")
    first_ip_summary.to_json(
    PROCESSED_DIR / "first_ip_summary.json",
    orient="records",
    indent=4,
    date_format="iso"
    )

    IP_Analyse.to_json(
    PROCESSED_DIR / "IP_Analyse.json",
    orient="records",
    indent=4,
    date_format="iso"
    )
    print("\nFirst launch summary:")
    print(f"Unique IPs: {df['ip'].nunique()}")
    print(f"Successful first launches: {int(first_ip_summary['first_launch_success'].sum())}")
    print(f"Failed first launches: {int(df['ip'].nunique() - first_ip_summary['first_launch_success'].sum())}")
    print("\nFirst error distribution:")
    print(first_ip_summary["first_error"].value_counts(dropna=False))


if __name__ == "__main__":

    main()

   