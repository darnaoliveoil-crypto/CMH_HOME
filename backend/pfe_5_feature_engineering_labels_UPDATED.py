# -*- coding: utf-8 -*-
"""
pfe_5_feature_engineering_labels.py
Local VS Code version.

Input:
    backend/data/processed/IP_Analyse.csv
Output:
    backend/data/processed/df_ml.csv
    backend/data/processed/df_ml.xlsx
    backend/data/processed/risk_label_distribution.csv
"""

from pathlib import Path
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore", category=FutureWarning)


# =========================================================
# 0. Paths
# =========================================================
BACKEND_DIR = Path(__file__).resolve().parent
PROCESSED_DIR = BACKEND_DIR / "data" / "processed"
OUTPUTS_DIR = BACKEND_DIR / "outputs"

INPUT_FILE = PROCESSED_DIR / "IP_Analyse.csv"
OUTPUT_CSV = PROCESSED_DIR / "df_ml.csv"
OUTPUT_XLSX = PROCESSED_DIR / "df_ml.xlsx"
RISK_DIST_FILE = PROCESSED_DIR / "risk_label_distribution.csv"
OUTPUT_JSON = PROCESSED_DIR / "df_ml.json"
RISK_DIST_JSON = PROCESSED_DIR / "risk_label_distribution.json"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 1000)


# =========================================================
# 1. Helpers
# =========================================================
def safe_divide(numerator: pd.Series, denominator: pd.Series, fill_value: float = 0.0) -> pd.Series:
    """Safe division: handles zero, NaN, and infinite values."""
    result = numerator / denominator.replace(0, np.nan)
    result = result.replace([np.inf, -np.inf], np.nan).fillna(fill_value)
    return result


def normalize_error_text(s: pd.Series) -> pd.Series:
    """Clean error labels to avoid problems caused by spaces/case."""
    return s.fillna("No error").astype(str).str.strip()


# =========================================================
# 2. Load data from pfe_4 output
# =========================================================
print("=" * 70)
print("PFE 5 - Feature Engineering + Risk Labels")
print("=" * 70)

if not INPUT_FILE.exists():
    raise FileNotFoundError(
        f"Input file not found: {INPUT_FILE}\n"
        "Run pfe_4_ip_lifecycle_analysis.py first."
    )

print(f"Reading: {INPUT_FILE}")
df = pd.read_csv(INPUT_FILE)
print(f"Loaded IP_Analyse shape: {df.shape}")

required_cols = [
    "ip", "server", "entity", "datetime_gride", "first_used_at",
    "sent_per_ip", "r_sent_per_ip", "drops_per_day",
    "growth_rate", "error_type_from_error"
]
missing_required = [c for c in required_cols if c not in df.columns]
if missing_required:
    raise ValueError(f"Missing required columns in IP_Analyse.csv: {missing_required}")


# =========================================================
# 3. Data type conversion
# =========================================================
df["datetime_gride"] = pd.to_datetime(df["datetime_gride"], errors="coerce")
df["first_used_at"] = pd.to_datetime(df["first_used_at"], errors="coerce")
df["error_type_from_error"] = normalize_error_text(df["error_type_from_error"])

numeric_cols = [
    "campaign_id", "sent_per_ip", "r_sent_per_ip", "offset",
    "previous_r_sent_per_ip", "volume_change", "growth_rate",
    "cumulative_r_sent_per_ip", "daily_cumulative_r_sent_per_ip",
    "sent_ratio", "lost_volume",
    "drops_per_day", "hour", "day_of_week", "outSum"
]
for col in numeric_cols:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

# sort for lifecycle/time calculations
df = df.sort_values(["ip", "datetime_gride"]).reset_index(drop=True)

# =========================================================
# 4. Feature engineering
# =========================================================

df["days_since_launch"] = (df["datetime_gride"] - df["first_used_at"]).dt.days.fillna(0)

df["sent_ratio"] = safe_divide(df["r_sent_per_ip"], df["sent_per_ip"]).round(3)

df["lost_volume"] = (df["sent_per_ip"] - df["r_sent_per_ip"]).clip(lower=0)
df["lost_ratio"] = safe_divide(df["lost_volume"], df["sent_per_ip"]).round(3)

df["date"] = df["datetime_gride"].dt.date

real_daily_volume_df = (
    df.groupby(["ip", "date"], dropna=False)["r_sent_per_ip"]
      .sum()
      .reset_index(name="real_daily_volume")
)
df = df.merge(real_daily_volume_df, on=["ip", "date"], how="left")

df["real_volume_per_drop"] = safe_divide(df["real_daily_volume"], df["drops_per_day"]).round(2)


df["time_gap_min"] = (
    df.groupby("ip")["datetime_gride"]
      .diff()
      .dt.total_seconds()
      .div(60)
      .fillna(0)
      .round(2)
)

df["error_flag"] = (df["error_type_from_error"] != "No error").astype(int)
df["spf_error"] = (df["error_type_from_error"] == "Rate limit SPF").astype(int)
df["dkim_error"] = (df["error_type_from_error"] == "Rate limit DKIM").astype(int)
df["netblock_error"] = (df["error_type_from_error"] == "Rate limit IP Netblock").astype(int)

rolled = (
    df.set_index("datetime_gride")
      .groupby("ip")["error_flag"]
      .rolling("24h")
      .sum()
      .reset_index(level=0, drop=True)
)

df["error_count_last_24h"] = rolled.values - df["error_flag"].values
df["error_count_last_24h"] = df["error_count_last_24h"].clip(lower=0).fillna(0).astype(int)

df["blocked_before"] = (
    df.groupby("ip")["netblock_error"]
      .cumsum()
      .shift(1)
      .fillna(0)
      .clip(lower=0)
      .astype(int)
)

first_idx_each_ip = df.groupby("ip").head(1).index
df.loc[first_idx_each_ip, "blocked_before"] = 0
df["blocked_before"] = (df["blocked_before"] > 0).astype(int)

df["is_high_growth"] = (df["growth_rate"] > 0.5).astype(int)
df["is_low_performance"] = (df["sent_ratio"] < 0.9).astype(int)
df["is_volume_loss"] = (df["lost_ratio"] > 0.1).astype(int)

engineered_cols = [
    "days_since_launch", "sent_ratio", "lost_volume", "lost_ratio",
    "real_daily_volume", "real_volume_per_drop", "time_gap_min", "error_count_last_24h",
    "blocked_before", "is_high_growth", "is_low_performance", "is_volume_loss",
    "error_flag", "spf_error", "dkim_error", "netblock_error"
]

df[engineered_cols] = df[engineered_cols].replace([np.inf, -np.inf], np.nan).fillna(0)


# =========================================================
# 5. Risk + Action label creation
# =========================================================

df["risk_label"] = "Safe"

dangerous_conditions = (
    (df["error_type_from_error"] == "Rate limit IP Netblock") |
    (df["blocked_before"] == 1) |
    (df["sent_ratio"] < 0.60)
)

risk_conditions = (
    (df["error_type_from_error"].isin(["Rate limit SPF", "Rate limit DKIM"])) |
    (df["growth_rate"] > 0.50) |
    (df["sent_ratio"] < 0.90) |
    (df["lost_ratio"] > 0.10) |
    (df["error_count_last_24h"] >= 2)
)

df.loc[dangerous_conditions, "risk_label"] = "Dangerous"
df.loc[~dangerous_conditions & risk_conditions, "risk_label"] = "Risk"

risk_mapping = {"Safe": 0, "Risk": 1, "Dangerous": 2}
df["risk_label_encoded"] = df["risk_label"].map(risk_mapping).astype(int)

df["action_label"] = "CONTINUE"
df["recommended_pause_hours"] = 0

df.loc[
    (df["risk_label"] == "Risk") & (df["sent_ratio"] >= 0.80),
    ["action_label", "recommended_pause_hours"]
] = ["PAUSE_2H", 2]

df.loc[
    (df["risk_label"] == "Risk") & (df["sent_ratio"] < 0.80),
    ["action_label", "recommended_pause_hours"]
] = ["PAUSE_6H", 6]

df.loc[
    (df["risk_label"] == "Dangerous"),
    ["action_label", "recommended_pause_hours"]
] = ["STOP_24H", 24]

action_mapping = {
    "CONTINUE": 0,
    "PAUSE_2H": 1,
    "PAUSE_6H": 2,
    "STOP_24H": 3
}

df["action_label_encoded"] = df["action_label"].map(action_mapping).astype(int)


# =========================================================
# 6. Select ML-ready columns
# =========================================================
ml_ready_columns = [
    "ip", "server", "entity", "datetime_gride", "campaign_id",

    "sent_per_ip", "r_sent_per_ip",
    "sent_ratio", "lost_volume", "lost_ratio",

    "previous_r_sent_per_ip", "volume_change", "growth_rate",
    "cumulative_r_sent_per_ip", "daily_cumulative_r_sent_per_ip",

    "real_daily_volume", "real_volume_per_drop",

    "drops_per_day", "time_gap_min", "days_since_launch",
    "hour", "day_of_week",

    "error_flag", "spf_error", "dkim_error", "netblock_error",
    "error_count_last_24h", "blocked_before",

    "is_high_growth", "is_low_performance", "is_volume_loss",

    "risk_label", "risk_label_encoded",
    "action_label", "action_label_encoded", "recommended_pause_hours"
]

existing_ml_columns = [c for c in ml_ready_columns if c in df.columns]
missing_ml_columns = [c for c in ml_ready_columns if c not in df.columns]
if missing_ml_columns:
    print(f"Warning - missing columns excluded: {missing_ml_columns}")

df_ml = df[existing_ml_columns].copy()

# Final cleaning
for col in df_ml.select_dtypes(include=["float64", "float32", "int64", "int32", "Int64"]).columns:
    df_ml[col] = pd.to_numeric(df_ml[col], errors="coerce").replace([np.inf, -np.inf], np.nan).fillna(0)


# =========================================================
# 7. Save outputs
# =========================================================
df_ml.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
df_ml.to_excel(OUTPUT_XLSX, index=False)
df_ml.to_json(
    OUTPUT_JSON,
    orient="records",
    indent=4,
    date_format="iso"
)

risk_dist = df_ml["risk_label"].value_counts().rename_axis("risk_label").reset_index(name="count")
risk_dist.to_csv(RISK_DIST_FILE, index=False, encoding="utf-8-sig")
risk_dist.to_json(
    RISK_DIST_JSON,
    orient="records",
    indent=4
)

print("\nRisk label distribution:")
print(risk_dist.to_string(index=False))

print("\nError type distribution:")
print(df["error_type_from_error"].value_counts().to_string())

print("\nSaved outputs:")
print(f"- {OUTPUT_CSV}")
print(f"- {OUTPUT_XLSX}")
print(f"- {RISK_DIST_FILE}")
print(f"- {OUTPUT_JSON}")
print(f"- {RISK_DIST_JSON}")
print(f"\nFinal df_ml shape: {df_ml.shape}")
print("PFE 5 completed successfully.")
