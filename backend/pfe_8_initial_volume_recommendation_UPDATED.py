# -*- coding: utf-8 -*-
"""
pfe_8_initial_volume_recommendation.py
Local VS Code version.

Reads:
- backend/data/processed/first_ip_summary.csv
- backend/data/processed/df_ml.csv

Saves:
- backend/data/processed/initial_behavior_summary.csv
- backend/data/processed/safe_start_ips.csv
- backend/data/processed/initial_volume_recommendations.csv
- backend/outputs/safe_start_diagnostics.csv
"""

from pathlib import Path
import pandas as pd
import numpy as np

# -------------------------------------------------------------------
# Paths
# -------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1] if Path(__file__).resolve().parent.name.lower() in {"script", "scripts", "backend"} else Path.cwd()
# If script is directly inside backend, parents[1] gives project root. If inside backend/Script also works.
if not (PROJECT_ROOT / "backend").exists() and (Path.cwd() / "backend").exists():
    PROJECT_ROOT = Path.cwd()

BACKEND_DIR = PROJECT_ROOT / "backend"
PROCESSED_DIR = BACKEND_DIR / "data" / "processed"
OUTPUTS_DIR = BACKEND_DIR / "outputs"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

FIRST_IP_PATH = PROCESSED_DIR / "first_ip_summary.csv"
DF_ML_PATH = PROCESSED_DIR / "df_ml.csv"

INITIAL_BEHAVIOR_PATH = PROCESSED_DIR / "initial_behavior_summary.csv"
SAFE_START_PATH = PROCESSED_DIR / "safe_start_ips.csv"
RECOMMENDATIONS_PATH = PROCESSED_DIR / "initial_volume_recommendations.csv"
DIAGNOSTICS_PATH = OUTPUTS_DIR / "safe_start_diagnostics.csv"


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------
def read_csv_required(path: Path, name: str) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing {name}: {path}")
    return pd.read_csv(path)


def clean_numeric(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    df = df.copy()
    for col in columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def safe_median(series: pd.Series, default: float = 0.0) -> float:
    value = pd.to_numeric(series, errors="coerce").median()
    if pd.isna(value):
        return default
    return float(value)


def safe_mode(series: pd.Series, default: float = 0.0) -> float:
    mode_values = pd.to_numeric(series, errors="coerce").dropna().mode()
    if mode_values.empty:
        return default
    return float(mode_values.iloc[0])


# -------------------------------------------------------------------
# Step 1 - Load data
# -------------------------------------------------------------------
print("=" * 70)
print("PFE 8 - Initial Volume Recommendation")
print("=" * 70)

first_ip_summary = read_csv_required(FIRST_IP_PATH, "first_ip_summary.csv")
df_ml = read_csv_required(DF_ML_PATH, "df_ml.csv")

print(f"Loaded first_ip_summary: {first_ip_summary.shape}")
print(f"Loaded df_ml: {df_ml.shape}")

# Datetime conversion
if "datetime_gride" in df_ml.columns:
    df_ml["datetime_gride"] = pd.to_datetime(df_ml["datetime_gride"], errors="coerce")
else:
    raise KeyError("df_ml.csv must contain column: datetime_gride")

if "first_used_at" in first_ip_summary.columns:
    first_ip_summary["first_used_at"] = pd.to_datetime(first_ip_summary["first_used_at"], errors="coerce")
else:
    raise KeyError("first_ip_summary.csv must contain column: first_used_at")

# Required columns safety
required_first_cols = ["ip", "first_used_at", "first_sent_per_ip", "first_error", "first_launch_success"]
required_ml_cols = ["ip", "datetime_gride", "risk_label", "daily_volume", "growth_rate", "time_gap_min", "drops_per_day"]
missing_first = [c for c in required_first_cols if c not in first_ip_summary.columns]
missing_ml = [c for c in required_ml_cols if c not in df_ml.columns]
if missing_first:
    raise KeyError(f"Missing columns in first_ip_summary.csv: {missing_first}")
if missing_ml:
    raise KeyError(f"Missing columns in df_ml.csv: {missing_ml}")

numeric_first_cols = ["first_sent_per_ip", "first_limit", "first_offset", "first_launch_success"]
numeric_ml_cols = ["daily_volume", "growth_rate", "time_gap_min", "drops_per_day", "netblock_error"]
first_ip_summary = clean_numeric(first_ip_summary, numeric_first_cols)
df_ml = clean_numeric(df_ml, numeric_ml_cols)

# Ensure netblock_error exists; if not, derive from error text if possible
if "netblock_error" not in df_ml.columns:
    if "error_type_from_error" in df_ml.columns:
        df_ml["netblock_error"] = (df_ml["error_type_from_error"].astype(str).str.contains("Netblock", case=False, na=False)).astype(int)
    else:
        df_ml["netblock_error"] = 0

# -------------------------------------------------------------------
# Step 2 - Compute IP behavior metrics
# -------------------------------------------------------------------
df_combined = df_ml.merge(first_ip_summary[["ip", "first_used_at"]], on="ip", how="left")
df_combined = df_combined.sort_values(["ip", "datetime_gride"]).reset_index(drop=True)

metrics = []
for ip_address, ip_data in df_combined.groupby("ip", dropna=False):
    ip_data = ip_data.sort_values("datetime_gride").copy()
    first_used_at = ip_data["first_used_at"].dropna().min()

    if pd.isna(first_used_at):
        first_used_at = ip_data["datetime_gride"].dropna().min()

    error_events = ip_data[ip_data["risk_label"].astype(str) != "Safe"]
    first_error_day = error_events["datetime_gride"].min() if not error_events.empty else pd.NaT

    netblock_events = ip_data[ip_data["netblock_error"].fillna(0).astype(int) == 1]
    first_netblock_day = netblock_events["datetime_gride"].min() if not netblock_events.empty else pd.NaT

    if pd.isna(first_used_at):
        safe_period_data = ip_data.iloc[0:0]
        safe_duration_days = 0.0
    elif pd.isna(first_error_day):
        safe_period_data = ip_data
        last_dt = ip_data["datetime_gride"].dropna().max()
        duration_delta = last_dt - first_used_at if pd.notna(last_dt) else pd.Timedelta(0)
        safe_duration_days = max(duration_delta.total_seconds() / 86400, 0)
    else:
        safe_period_data = ip_data[ip_data["datetime_gride"] < first_error_day]
        duration_delta = first_error_day - first_used_at
        safe_duration_days = max(duration_delta.total_seconds() / 86400, 0)

    maximum_safe_volume = safe_period_data["daily_volume"].max() if not safe_period_data.empty else 0
    average_safe_growth_rate = safe_period_data["growth_rate"].mean() if not safe_period_data.empty else 0
    average_time_gap_min = safe_period_data["time_gap_min"].mean() if not safe_period_data.empty else 0

    metrics.append({
        "ip": ip_address,
        "safe_duration_days": safe_duration_days,
        "first_error_day": first_error_day,
        "first_netblock_day": first_netblock_day,
        "maximum_safe_volume": 0 if pd.isna(maximum_safe_volume) else maximum_safe_volume,
        "average_safe_growth_rate": 0 if pd.isna(average_safe_growth_rate) else average_safe_growth_rate,
        "average_time_gap_min": 0 if pd.isna(average_time_gap_min) else average_time_gap_min,
    })

ip_behavior_summary_df = pd.DataFrame(metrics)
print(f"Computed IP behavior metrics: {ip_behavior_summary_df.shape}")

# -------------------------------------------------------------------
# Step 3 - Merge initial + behavior summaries
# -------------------------------------------------------------------
initial_behavior_summary = first_ip_summary.merge(
    ip_behavior_summary_df,
    on="ip",
    how="left"
)

initial_behavior_summary.to_csv(INITIAL_BEHAVIOR_PATH, index=False)
print(f"Saved: {INITIAL_BEHAVIOR_PATH}")

# -------------------------------------------------------------------
# Step 4 - Select safe-start IPs
# -------------------------------------------------------------------
cond_launch_success = initial_behavior_summary["first_launch_success"].fillna(0).astype(int) == 1
cond_no_error = initial_behavior_summary["first_error"].astype(str).str.strip().eq("No error")
cond_sent_volume = pd.to_numeric(initial_behavior_summary["first_sent_per_ip"], errors="coerce") < 10_000
cond_safe_duration = pd.to_numeric(initial_behavior_summary["safe_duration_days"], errors="coerce").fillna(0) > 0

safe_start_ips = initial_behavior_summary[
    cond_launch_success & cond_no_error & cond_sent_volume & cond_safe_duration
].copy()

# Fallback: if too strict, relax safe_duration condition but keep launch/no-error/low-volume
if safe_start_ips.empty:
    print("WARNING: No safe-start IPs found with all conditions. Applying relaxed fallback: safe_duration_days >= 0.")
    safe_start_ips = initial_behavior_summary[
        cond_launch_success & cond_no_error & cond_sent_volume
    ].copy()

safe_start_ips.to_csv(SAFE_START_PATH, index=False)
print(f"Safe-start IPs found: {len(safe_start_ips)}")
print(f"Saved: {SAFE_START_PATH}")

# Diagnostics
conditions = {
    "first_launch_success == 1": int(cond_launch_success.sum()),
    "first_error == No error": int(cond_no_error.sum()),
    "first_sent_per_ip < 10000": int(cond_sent_volume.sum()),
    "safe_duration_days > 0": int(cond_safe_duration.sum()),
    "launch_success & no_error": int((cond_launch_success & cond_no_error).sum()),
    "launch_success & no_error & sent_volume": int((cond_launch_success & cond_no_error & cond_sent_volume).sum()),
    "ALL strict conditions": int((cond_launch_success & cond_no_error & cond_sent_volume & cond_safe_duration).sum()),
}

diagnostics_df = pd.DataFrame({
    "condition": list(conditions.keys()),
    "count": list(conditions.values()),
    "total_ips": len(initial_behavior_summary)
})
diagnostics_df.to_csv(DIAGNOSTICS_PATH, index=False)
print(f"Saved: {DIAGNOSTICS_PATH}")

# -------------------------------------------------------------------
# Step 5 - Compute recommendations
# -------------------------------------------------------------------
if safe_start_ips.empty:
    print("WARNING: Still no safe-start IPs found. Recommendations will use all IPs as fallback.")
    recommendation_base = initial_behavior_summary.copy()
else:
    recommendation_base = safe_start_ips.copy()

safe_ips_list = recommendation_base["ip"].dropna().unique().tolist()
df_ml_safe_ips = df_ml[df_ml["ip"].isin(safe_ips_list)].copy()
df_ml_safe_ips = df_ml_safe_ips.merge(
    initial_behavior_summary[["ip", "first_error_day"]],
    on="ip",
    how="left"
)

# keep safe-period events only
safe_period_events = df_ml_safe_ips[
    df_ml_safe_ips.apply(
        lambda row: pd.isna(row.get("first_error_day")) or row["datetime_gride"] < row.get("first_error_day"),
        axis=1
    )
].copy()

recommended_initial_volume = safe_median(recommendation_base["first_sent_per_ip"])
recommended_drops_per_day = safe_mode(safe_period_events["drops_per_day"] if "drops_per_day" in safe_period_events.columns else pd.Series(dtype=float))
recommended_growth_rate = safe_median(recommendation_base["average_safe_growth_rate"])
recommended_time_gap = safe_median(recommendation_base["average_time_gap_min"])
recommended_max_safe_volume = safe_median(recommendation_base["maximum_safe_volume"])

recommendations_df = pd.DataFrame({
    "metric": [
        "recommended_initial_volume",
        "recommended_drops_per_day",
        "recommended_growth_rate",
        "recommended_time_gap_min",
        "recommended_maximum_safe_volume",
        "number_of_safe_start_ips_used",
    ],
    "value": [
        recommended_initial_volume,
        recommended_drops_per_day,
        recommended_growth_rate,
        recommended_time_gap,
        recommended_max_safe_volume,
        len(safe_start_ips),
    ]
})

recommendations_df.to_csv(RECOMMENDATIONS_PATH, index=False)
print(f"Saved: {RECOMMENDATIONS_PATH}")

# -------------------------------------------------------------------
# Step 6 - Entity-based historical recommendations
# -------------------------------------------------------------------
ENTITY_RECOMMENDATIONS_PATH = PROCESSED_DIR / "entity_initial_volume_recommendations.csv"

if "entity" in recommendation_base.columns:
    entity_recommendations = []

    for entity_name, entity_data in recommendation_base.groupby("entity"):
        entity_ips = entity_data["ip"].dropna().unique().tolist()

        entity_safe_events = safe_period_events[
            safe_period_events["ip"].isin(entity_ips)
        ].copy()

        entity_recommendations.append({
            "entity": entity_name,
            "recommended_initial_volume": safe_median(entity_data["first_sent_per_ip"]),
            "recommended_drops_per_day": safe_mode(
                entity_safe_events["drops_per_day"]
                if "drops_per_day" in entity_safe_events.columns
                else pd.Series(dtype=float)
            ),
            "recommended_growth_rate": safe_median(entity_data["average_safe_growth_rate"]),
            "recommended_time_gap_min": safe_median(entity_data["average_time_gap_min"]),
            "recommended_maximum_safe_volume": safe_median(entity_data["maximum_safe_volume"]),
            "number_of_safe_start_ips_used": len(entity_data),
        })

    entity_recommendations_df = pd.DataFrame(entity_recommendations)
    entity_recommendations_df.to_csv(ENTITY_RECOMMENDATIONS_PATH, index=False)

    print(f"Saved entity recommendations: {ENTITY_RECOMMENDATIONS_PATH}")
    print("\nEntity-based recommendations:")
    print(entity_recommendations_df.to_string(index=False))

else:
    print("WARNING: entity column not found. Entity-based recommendations skipped.")

print("\nRecommendations:")
print(recommendations_df.to_string(index=False))
print("\nPFE 8 completed successfully.")
