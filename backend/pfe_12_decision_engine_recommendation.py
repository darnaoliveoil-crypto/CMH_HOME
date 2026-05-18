# -*- coding: utf-8 -*-
"""
PFE 12 - Final Decision & Explainable AI Engine

This version is designed for Dashboard 5.

Reads:
    backend/data/processed/inference_predictions.csv
    backend/data/processed/strategy_recommendations.csv        optional
    backend/data/processed/warmup_strategy_plan.csv            optional
    backend/outputs/warmup_strategy_summary.csv                optional
    backend/outputs/risk_model_feature_importance.csv          optional
    backend/outputs/error_prediction_feature_importance.csv    optional

Saves:
    backend/data/processed/decision_engine_results.csv
    backend/outputs/decision_engine_summary.csv
    backend/outputs/first_risky_day_summary.csv
    backend/outputs/xai_feature_explanation.csv
"""

from pathlib import Path
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
PROCESSED_DIR = DATA_DIR / "processed"
OUTPUTS_DIR = BASE_DIR / "outputs"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

INFERENCE_PATH = PROCESSED_DIR / "inference_predictions.csv"
STRATEGY_PATH = PROCESSED_DIR / "strategy_recommendations.csv"
WARMUP_PLAN_PATH = PROCESSED_DIR / "warmup_strategy_plan.csv"
WARMUP_SUMMARY_PATH = OUTPUTS_DIR / "warmup_strategy_summary.csv"

RISK_FEATURE_IMPORTANCE_PATH = OUTPUTS_DIR / "risk_model_feature_importance.csv"
ERROR_FEATURE_IMPORTANCE_PATH = OUTPUTS_DIR / "error_prediction_feature_importance.csv"

DECISION_RESULTS_PATH = PROCESSED_DIR / "decision_engine_results.csv"
DECISION_SUMMARY_PATH = OUTPUTS_DIR / "decision_engine_summary.csv"
FIRST_RISKY_DAY_PATH = OUTPUTS_DIR / "first_risky_day_summary.csv"
XAI_OUTPUT_PATH = OUTPUTS_DIR / "xai_feature_explanation.csv"


NETBLOCK_STOP_THRESHOLD = 0.50
LOW_SENT_RATIO_THRESHOLD = 0.70
HIGH_LIMIT_USAGE_THRESHOLD = 0.90
HIGH_GROWTH_THRESHOLD = 0.35
AUTH_ERROR_THRESHOLD = 0.10


def read_optional_csv(path: Path):
    if path.exists():
        return pd.read_csv(path)
    return None


def load_inputs():
    if not INFERENCE_PATH.exists():
        raise FileNotFoundError(f"Missing {INFERENCE_PATH}. Run inference_pipeline.py first.")

    inference_df = pd.read_csv(INFERENCE_PATH)
    strategy_df = read_optional_csv(STRATEGY_PATH)
    warmup_plan_df = read_optional_csv(WARMUP_PLAN_PATH)
    warmup_summary_df = read_optional_csv(WARMUP_SUMMARY_PATH)
    risk_importance_df = read_optional_csv(RISK_FEATURE_IMPORTANCE_PATH)
    error_importance_df = read_optional_csv(ERROR_FEATURE_IMPORTANCE_PATH)

    return (
        inference_df,
        strategy_df,
        warmup_plan_df,
        warmup_summary_df,
        risk_importance_df,
        error_importance_df,
    )


def prepare_latest_ip_status(inference_df: pd.DataFrame) -> pd.DataFrame:
    df = inference_df.copy()

    df["datetime_gride"] = pd.to_datetime(df["datetime_gride"], errors="coerce")
    df = df.dropna(subset=["ip", "datetime_gride"])

    numeric_cols = [
        "sent_per_ip",
        "r_sent_per_ip",
        "sent_ratio",
        "growth_rate",
        "limit_usage_ratio",
        "spf_error_probability",
        "dkim_error_probability",
        "netblock_error_probability",
        "predicted_risk_label_encoded",
    ]

    for col in numeric_cols:
        if col not in df.columns:
            df[col] = 0
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    if "predicted_risk_label" not in df.columns:
        risk_map = {0: "Safe", 1: "Risk", 2: "Dangerous"}
        df["predicted_risk_label"] = df["predicted_risk_label_encoded"].map(risk_map).fillna("Safe")

    latest_ip = (
        df.sort_values("datetime_gride")
        .groupby("ip", as_index=False)
        .tail(1)
        .copy()
    )

    hist = (
        df.groupby("ip", as_index=False)
        .agg(
            total_rows=("ip", "count"),
            active_days=("datetime_gride", lambda x: x.dt.date.nunique()),
            max_volume=("sent_per_ip", "max"),
            avg_sent_ratio=("sent_ratio", "mean"),
            avg_growth_rate=("growth_rate", "mean"),
            max_netblock_probability=("netblock_error_probability", "max"),
            max_spf_probability=("spf_error_probability", "max"),
            max_dkim_probability=("dkim_error_probability", "max"),
            risky_rows=("predicted_risk_label", lambda x: x.isin(["Risk", "Dangerous"]).sum()),
            dangerous_rows=("predicted_risk_label", lambda x: (x == "Dangerous").sum()),
        )
    )

    latest_ip = latest_ip.merge(hist, on="ip", how="left", suffixes=("", "_history"))

    return latest_ip


def attach_strategy_recommendations(latest_ip: pd.DataFrame, strategy_df: pd.DataFrame | None) -> pd.DataFrame:
    df = latest_ip.copy()

    defaults = {
        "recommended_initial_volume": np.nan,
        "recommended_growth_rate": 0.15,
        "recommended_drops_per_day": 10,
        "recommended_time_gap_min": 60,
        "recommended_max_safe_volume": np.nan,
    }

    if strategy_df is None or strategy_df.empty:
        for col, default in defaults.items():
            df[col] = default
        return df

    strategy = strategy_df.copy()

    if "ip" not in strategy.columns:
        for col, default in defaults.items():
            if col in strategy.columns:
                df[col] = pd.to_numeric(strategy[col], errors="coerce").median()
            else:
                df[col] = default
        return df

    useful_cols = ["ip"] + [c for c in defaults.keys() if c in strategy.columns]
    strategy = strategy[useful_cols].drop_duplicates("ip", keep="last")

    df = df.drop(columns=[c for c in defaults.keys() if c in df.columns], errors="ignore")
    df = df.merge(strategy, on="ip", how="left")

    for col, default in defaults.items():
        if col not in df.columns:
            df[col] = default
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(default)

    return df


def decide_ip(row: pd.Series) -> pd.Series:
    risk = str(row.get("predicted_risk_label", "Safe"))
    netblock_prob = float(row.get("netblock_error_probability", 0))
    spf_prob = float(row.get("spf_error_probability", 0))
    dkim_prob = float(row.get("dkim_error_probability", 0))
    sent_ratio = float(row.get("sent_ratio", 1))
    growth_rate = float(row.get("growth_rate", 0))
    limit_usage = float(row.get("limit_usage_ratio", 0))

    final_decision = "Continue Sending"
    severity = "LOW"
    main_reason = "IP is currently inside the safe operating zone."
    recommended_action = "Continue current strategy with slow controlled growth."

    suggested_drops = int(round(float(row.get("recommended_drops_per_day", 10))))
    suggested_growth = float(row.get("recommended_growth_rate", 0.15))
    suggested_time_gap = float(row.get("recommended_time_gap_min", 60))

    blocking_probability = netblock_prob

    if netblock_prob >= NETBLOCK_STOP_THRESHOLD:
        final_decision = "Stop Sending Immediately"
        severity = "CRITICAL"
        main_reason = f"High Netblock blocking probability ({netblock_prob:.1%})."
        recommended_action = (
            "Pause sending for 24h to 48h, investigate Netblock causes, "
            "then restart with lower volume and more drops per day."
        )
        suggested_drops = max(suggested_drops, 15)
        suggested_growth = min(suggested_growth, 0.08)
        suggested_time_gap = max(suggested_time_gap, 90)

    elif risk == "Dangerous":
        final_decision = "Reduce Volume"
        severity = "HIGH"
        main_reason = "The latest model prediction classifies this IP as Dangerous."
        recommended_action = (
            "Reduce daily volume immediately, stop growth, and keep the IP stable "
            "until risk decreases."
        )
        suggested_drops = max(suggested_drops, 15)
        suggested_growth = min(suggested_growth, 0.10)
        suggested_time_gap = max(suggested_time_gap, 75)

    elif risk == "Risk":
        final_decision = "Slow Down Growth"
        severity = "MEDIUM"
        main_reason = "The latest model prediction classifies this IP as Risk."
        recommended_action = "Decrease growth rate and increase time gap. Avoid aggressive warm-up."
        suggested_growth = min(suggested_growth, 0.15)
        suggested_time_gap = max(suggested_time_gap, 60)

    elif limit_usage > HIGH_LIMIT_USAGE_THRESHOLD:
        final_decision = "Reduce Volume"
        severity = "MEDIUM"
        main_reason = f"Limit usage ratio is too high ({limit_usage:.1%})."
        recommended_action = "Reduce daily volume to keep the IP below the pressure zone."
        suggested_growth = min(suggested_growth, 0.12)

    elif sent_ratio < LOW_SENT_RATIO_THRESHOLD:
        final_decision = "Reduce Volume"
        severity = "MEDIUM"
        main_reason = f"Sent ratio is low ({sent_ratio:.1%}), indicating poor delivery quality."
        recommended_action = "Reduce volume and check delivery quality before increasing again."
        suggested_growth = min(suggested_growth, 0.10)

    elif growth_rate > HIGH_GROWTH_THRESHOLD:
        final_decision = "Slow Down Growth"
        severity = "LOW"
        main_reason = f"Growth rate is high ({growth_rate:.1%})."
        recommended_action = "Use slower warm-up growth to protect IP reputation."
        suggested_growth = min(suggested_growth, 0.15)

    elif spf_prob > AUTH_ERROR_THRESHOLD or dkim_prob > AUTH_ERROR_THRESHOLD:
        final_decision = "Increase Time Gap"
        severity = "MEDIUM"
        main_reason = (
            f"Authentication-related error probability is elevated "
            f"(SPF={spf_prob:.1%}, DKIM={dkim_prob:.1%})."
        )
        recommended_action = "Verify SPF/DKIM configuration and increase time gap before volume increase."
        suggested_time_gap = max(suggested_time_gap, 75)

    return pd.Series(
        [
            final_decision,
            severity,
            main_reason,
            recommended_action,
            suggested_drops,
            round(suggested_growth, 4),
            round(suggested_time_gap, 2),
            round(blocking_probability, 4),
        ],
        index=[
            "final_decision",
            "severity",
            "main_reason",
            "recommended_action",
            "suggested_drops_per_day",
            "suggested_growth_rate",
            "suggested_time_gap_min",
            "blocking_probability",
        ],
    )


def fallback_xai(row: pd.Series):
    contributions = []

    growth = abs(float(row.get("growth_rate", 0)))
    limit_usage = float(row.get("limit_usage_ratio", 0))
    sent_ratio = float(row.get("sent_ratio", 1))
    netblock = float(row.get("netblock_error_probability", 0))
    spf = float(row.get("spf_error_probability", 0))
    dkim = float(row.get("dkim_error_probability", 0))

    contributions.append(("growth_rate", min(growth / 0.60, 1), "High growth increases reputation risk."))
    contributions.append(("limit_usage_ratio", min(limit_usage / 1.00, 1), "High limit usage puts pressure on the IP."))
    contributions.append(("sent_ratio", min(max(1 - sent_ratio, 0), 1), "Low sent ratio indicates delivery instability."))
    contributions.append(("netblock_error_probability", netblock, "Netblock probability directly increases blocking risk."))
    contributions.append(("spf_error_probability", spf, "SPF probability may indicate authentication issues."))
    contributions.append(("dkim_error_probability", dkim, "DKIM probability may indicate authentication issues."))

    return sorted(contributions, key=lambda x: x[1], reverse=True)[:3]


def build_xai(decision_df: pd.DataFrame):
    rows = []
    decision_df = decision_df.copy()

    for idx, row in decision_df.iterrows():
        top_features = fallback_xai(row)

        for rank, (feature, contribution, explanation) in enumerate(top_features, start=1):
            rows.append({
                "ip": row["ip"],
                "rank": rank,
                "feature": feature,
                "contribution_score": round(float(contribution), 4),
                "explanation": explanation,
            })

            decision_df.loc[idx, f"xai_top_feature_{rank}"] = feature
            decision_df.loc[idx, f"xai_top_feature_{rank}_contribution"] = round(float(contribution), 4)

    return decision_df, pd.DataFrame(rows)


def build_summary(decision_df: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame([{
        "total_ips": decision_df["ip"].nunique(),
        "continue_sending": (decision_df["final_decision"] == "Continue Sending").sum(),
        "slow_down_growth": (decision_df["final_decision"] == "Slow Down Growth").sum(),
        "increase_time_gap": (decision_df["final_decision"] == "Increase Time Gap").sum(),
        "reduce_volume": (decision_df["final_decision"] == "Reduce Volume").sum(),
        "stop_sending_immediately": (decision_df["final_decision"] == "Stop Sending Immediately").sum(),
        "critical_ips": (decision_df["severity"] == "CRITICAL").sum(),
        "high_severity_ips": (decision_df["severity"] == "HIGH").sum(),
        "average_blocking_probability": round(float(decision_df["blocking_probability"].mean()), 4),
    }])


def build_first_risky_day(warmup_plan_df):
    if warmup_plan_df is None or warmup_plan_df.empty:
        return pd.DataFrame()

    df = warmup_plan_df.copy()

    if "risk_zone" not in df.columns or "day" not in df.columns:
        return pd.DataFrame()

    risky = df[df["risk_zone"].isin(["Risk", "Dangerous"])].copy()

    if risky.empty:
        return pd.DataFrame()

    group_cols = ["plan_type", "drops_per_day"]
    if "selected_ip" in risky.columns:
        group_cols = ["selected_ip"] + group_cols

    first = (
        risky.sort_values("day")
        .groupby(group_cols, as_index=False)
        .first()
    )

    return first


def main():
    print("=" * 70)
    print("PFE 12 - Final Decision & Explainable AI Engine")
    print("=" * 70)

    (
        inference_df,
        strategy_df,
        warmup_plan_df,
        warmup_summary_df,
        risk_importance_df,
        error_importance_df,
    ) = load_inputs()

    print(f"Loaded inference predictions: {inference_df.shape}")

    latest_ip = prepare_latest_ip_status(inference_df)
    latest_ip = attach_strategy_recommendations(latest_ip, strategy_df)

    decision_cols = latest_ip.apply(decide_ip, axis=1)
    decision_df = pd.concat([latest_ip, decision_cols], axis=1)

    decision_df, xai_df = build_xai(decision_df)
    summary_df = build_summary(decision_df)
    first_risky_df = build_first_risky_day(warmup_plan_df)

    decision_df.to_csv(DECISION_RESULTS_PATH, index=False)
    summary_df.to_csv(DECISION_SUMMARY_PATH, index=False)
    first_risky_df.to_csv(FIRST_RISKY_DAY_PATH, index=False)
    xai_df.to_csv(XAI_OUTPUT_PATH, index=False)

    print(f"Saved decision results: {DECISION_RESULTS_PATH}")
    print(f"Saved decision summary: {DECISION_SUMMARY_PATH}")
    print(f"Saved first risky day summary: {FIRST_RISKY_DAY_PATH}")
    print(f"Saved XAI explanation: {XAI_OUTPUT_PATH}")

    print("\nDecision summary:")
    print(summary_df.to_string(index=False))

    print("\nPFE 12 completed successfully.")


if __name__ == "__main__":
    main()
