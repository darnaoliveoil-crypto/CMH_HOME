# -*- coding: utf-8 -*-
"""
PFE 11 - Simulation Engine (VS Code version)
Simulates IP warm-up strategies day by day using available trained models when possible,
and safe fallback formulas when model feature mismatch occurs.
"""

from pathlib import Path
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import joblib

# ======================================================
# PATHS
# ======================================================
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
PROCESSED_DIR = DATA_DIR / "processed"
MODELS_DIR = BASE_DIR / "models"
OUTPUTS_DIR = BASE_DIR / "outputs"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

print("=" * 70)
print("PFE 11 - Simulation Engine")
print("=" * 70)

# ======================================================
# MODEL LOADING
# ======================================================
def load_model(path: Path, name: str):
    if path.exists():
        try:
            model = joblib.load(path)
            print(f"Loaded {name}: {path}")
            return model
        except Exception as e:
            print(f"Could not load {name}: {e}")
    else:
        print(f"Missing {name}, fallback logic will be used: {path}")
    return None

risk_model = load_model(MODELS_DIR / "risk_model.pkl", "risk_model")
spf_error_model = load_model(MODELS_DIR / "best_model_spf_error.pkl", "spf_error_model")
dkim_error_model = load_model(MODELS_DIR / "best_model_dkim_error.pkl", "dkim_error_model")
netblock_error_model = load_model(MODELS_DIR / "best_model_netblock_error.pkl", "netblock_error_model")

model_initial_volume = load_model(MODELS_DIR / "model_initial_volume.pkl", "model_initial_volume")
model_growth_rate = load_model(MODELS_DIR / "model_growth_rate.pkl", "model_growth_rate")
model_max_safe_volume = load_model(MODELS_DIR / "model_max_safe_volume.pkl", "model_max_safe_volume")
model_time_gap_min = load_model(MODELS_DIR / "model_time_gap_min.pkl", "model_time_gap_min")
model_drops_per_day = load_model(MODELS_DIR / "model_drops_per_day.pkl", "model_drops_per_day")

# ======================================================
# HELPERS
# ======================================================
def safe_float(value, default=0.0):
    try:
        if pd.isna(value):
            return default
        return float(value)
    except Exception:
        return default


def model_predict_safe(model, features: pd.DataFrame, default_value: float):
    """Try model prediction. If feature mismatch occurs, return default."""
    if model is None:
        return default_value
    try:
        if hasattr(model, "feature_names_in_"):
            required = list(model.feature_names_in_)
            full_features = pd.DataFrame(columns=required)
            for col in required:
                if col in features.columns:
                    full_features[col] = features[col]
                else:
                    full_features[col] = 0
            features = full_features[required].fillna(0)
        pred = model.predict(features)[0]
        return safe_float(pred, default_value)
    except Exception:
        return default_value


def model_proba_safe(model, features: pd.DataFrame, positive_class=1, default_value=0.0):
    """Try predict_proba. If impossible, return default."""
    if model is None:
        return default_value
    try:
        if hasattr(model, "feature_names_in_"):
            required = list(model.feature_names_in_)
            full_features = pd.DataFrame(columns=required)
            for col in required:
                if col in features.columns:
                    full_features[col] = features[col]
                else:
                    full_features[col] = 0
            features = full_features[required].fillna(0)

        if hasattr(model, "predict_proba"):
            proba = model.predict_proba(features)
            classes = list(model.classes_)
            if positive_class in classes:
                idx = classes.index(positive_class)
                return safe_float(proba[0][idx], default_value)
            return default_value

        pred = model.predict(features)[0]
        return safe_float(pred, default_value)
    except Exception:
        return default_value


def classify_risk_zone(risk_probability, error_probability, limit_usage_ratio):
    if risk_probability >= 0.70 or error_probability >= 0.15 or limit_usage_ratio >= 1.00:
        return "Dangerous"
    if risk_probability >= 0.40 or error_probability >= 0.05 or limit_usage_ratio >= 0.90:
        return "Risk"
    return "Safe"


def get_recommended_defaults():
    rec_path = PROCESSED_DIR / "initial_volume_recommendations.csv"
    defaults = {
        "initial_volume": 1000,
        "drops_per_day": 5,
        "growth_rate": 0.10,
        "time_gap_min": 60,
        "max_safe_volume": 10000,
    }

    if rec_path.exists():
        try:
            rec_df = pd.read_csv(rec_path)
            metric_col = "Metric" if "Metric" in rec_df.columns else rec_df.columns[0]
            value_col = "Value" if "Value" in rec_df.columns else rec_df.columns[1]
            rec_map = dict(zip(rec_df[metric_col], rec_df[value_col]))
            defaults["initial_volume"] = safe_float(rec_map.get("Recommended Initial Volume"), defaults["initial_volume"])
            defaults["drops_per_day"] = int(round(safe_float(rec_map.get("Recommended Drops Per Day"), defaults["drops_per_day"])))
            defaults["growth_rate"] = safe_float(rec_map.get("Recommended Growth Rate"), defaults["growth_rate"])
            defaults["time_gap_min"] = safe_float(rec_map.get("Recommended Time Gap (min)"), defaults["time_gap_min"])
            defaults["max_safe_volume"] = safe_float(rec_map.get("Recommended Maximum Safe Volume"), defaults["max_safe_volume"])
        except Exception as e:
            print(f"Could not read recommendations file, using defaults: {e}")

    return defaults

# ======================================================
# SIMULATION CORE
# ======================================================
def simulate_ip_strategy(
    scenario_name: str,
    initial_volume: float,
    drops_per_day: int,
    growth_rate: float,
    limit: float,
    time_gap_min: float,
    number_of_days: int = 30,
    target_cumulative_volume: float | None = None,
):
    rows = []
    current_volume = float(initial_volume)
    cumulative_volume = 0.0

    for day in range(1, number_of_days + 1):
        if day == 1:
            daily_volume = current_volume
        else:
            daily_volume = current_volume * (1 + growth_rate)

        daily_volume = max(0, round(daily_volume))
        current_volume = daily_volume
        cumulative_volume += daily_volume

        drops = max(1, int(round(drops_per_day)))
        volume_per_drop = daily_volume / drops
        limit_usage_ratio = daily_volume / limit if limit > 0 else 1.0
        sent_ratio_est = max(0.0, min(1.0, 1 - (limit_usage_ratio - 0.85) * 0.6)) if limit_usage_ratio > 0.85 else 0.98

        feature_row = pd.DataFrame([{
            "sent_per_ip": daily_volume,
            "r_sent_per_ip": daily_volume * sent_ratio_est,
            "limit_per_ip": limit,
            "offset": 0,
            "previous_sent_per_ip": current_volume / (1 + growth_rate) if growth_rate > -1 and day > 1 else 0,
            "volume_change": daily_volume - (current_volume / (1 + growth_rate) if growth_rate > -1 and day > 1 else 0),
            "growth_rate": growth_rate,
            "cumulative_sent_per_ip": cumulative_volume,
            "daily_cumulative_sent_per_ip": daily_volume,
            "daily_volume": daily_volume,
            "volume_per_drop": volume_per_drop,
            "sent_ratio": sent_ratio_est,
            "limit_usage_ratio": limit_usage_ratio,
            "drops_per_day": drops,
            "time_gap_min": time_gap_min,
            "days_since_launch": day - 1,
            "hour": 10,
            "day_of_week": (day - 1) % 7,
        }])

        # Fallback formulas
        fallback_risk = min(0.99, 0.05 + max(0, limit_usage_ratio - 0.65) * 0.9 + max(0, growth_rate - 0.15) * 1.2)
        fallback_spf = min(0.60, 0.01 + max(0, limit_usage_ratio - 0.80) * 0.5)
        fallback_dkim = min(0.45, 0.005 + max(0, growth_rate - 0.25) * 0.8)
        fallback_netblock = min(0.80, 0.01 + max(0, limit_usage_ratio - 0.95) * 1.5 + max(0, growth_rate - 0.40) * 1.2)

        risk_prob_from_model = model_proba_safe(risk_model, feature_row, positive_class=2, default_value=fallback_risk)
        spf_prob = model_proba_safe(spf_error_model, feature_row, positive_class=1, default_value=fallback_spf)
        dkim_prob = model_proba_safe(dkim_error_model, feature_row, positive_class=1, default_value=fallback_dkim)
        netblock_prob = model_proba_safe(netblock_error_model, feature_row, positive_class=1, default_value=fallback_netblock)

        error_probability = max(spf_prob, dkim_prob, netblock_prob)
        risk_probability = max(risk_prob_from_model, fallback_risk)
        risk_zone = classify_risk_zone(risk_probability, error_probability, limit_usage_ratio)

        remaining_to_target = None
        if target_cumulative_volume is not None:
            remaining_to_target = max(0, target_cumulative_volume - cumulative_volume)

        rows.append({
            "scenario": scenario_name,
            "day": day,
            "daily_volume": int(daily_volume),
            "drops_per_day": drops,
            "volume_per_drop": round(volume_per_drop, 2),
            "cumulative_volume": int(cumulative_volume),
            "target_cumulative_volume": target_cumulative_volume,
            "remaining_to_target": remaining_to_target,
            "limit": int(limit),
            "limit_usage_ratio": round(limit_usage_ratio, 4),
            "growth_rate": round(growth_rate, 4),
            "time_gap_min": round(time_gap_min, 2),
            "estimated_sent_ratio": round(sent_ratio_est, 4),
            "risk_probability": round(risk_probability, 4),
            "spf_error_probability": round(spf_prob, 4),
            "dkim_error_probability": round(dkim_prob, 4),
            "netblock_error_probability": round(netblock_prob, 4),
            "error_probability": round(error_probability, 4),
            "risk_zone": risk_zone,
        })

    return pd.DataFrame(rows)

# ======================================================
# RUN DEFAULT SCENARIOS
# ======================================================
def main():
    defaults = get_recommended_defaults()
    print("\nRecommended defaults used:")
    for k, v in defaults.items():
        print(f"- {k}: {v}")

    # Limit fallback: use max safe volume if available, otherwise 10000
    base_limit = max(defaults["max_safe_volume"], defaults["initial_volume"] * 3, 5000)

    moderate = simulate_ip_strategy(
        scenario_name="moderate_strategy",
        initial_volume=defaults["initial_volume"],
        drops_per_day=defaults["drops_per_day"],
        growth_rate=max(defaults["growth_rate"], 0.08),
        limit=base_limit,
        time_gap_min=defaults["time_gap_min"],
        number_of_days=30,
        target_cumulative_volume=1_000_000,
    )

    safe = simulate_ip_strategy(
        scenario_name="safe_strategy",
        initial_volume=max(100, defaults["initial_volume"] * 0.7),
        drops_per_day=max(3, defaults["drops_per_day"]),
        growth_rate=0.05,
        limit=base_limit * 1.2,
        time_gap_min=max(defaults["time_gap_min"], 90),
        number_of_days=30,
        target_cumulative_volume=1_000_000,
    )

    aggressive = simulate_ip_strategy(
        scenario_name="aggressive_strategy",
        initial_volume=defaults["initial_volume"] * 1.4,
        drops_per_day=max(defaults["drops_per_day"], 8),
        growth_rate=0.20,
        limit=max(base_limit * 0.8, defaults["initial_volume"] * 2),
        time_gap_min=min(defaults["time_gap_min"], 30),
        number_of_days=30,
        target_cumulative_volume=1_000_000,
    )

    all_results = pd.concat([moderate, safe, aggressive], ignore_index=True)

    moderate.to_csv(OUTPUTS_DIR / "simulation_results_moderate_strategy.csv", index=False)
    safe.to_csv(OUTPUTS_DIR / "simulation_results_safe_strategy.csv", index=False)
    aggressive.to_csv(OUTPUTS_DIR / "simulation_results_aggressive_strategy.csv", index=False)
    all_results.to_csv(PROCESSED_DIR / "simulation_results_all_scenarios.csv", index=False)

    summary = all_results.groupby("scenario").agg(
        final_cumulative_volume=("cumulative_volume", "max"),
        max_daily_volume=("daily_volume", "max"),
        avg_risk_probability=("risk_probability", "mean"),
        max_error_probability=("error_probability", "max"),
        dangerous_days=("risk_zone", lambda s: (s == "Dangerous").sum()),
        risk_days=("risk_zone", lambda s: (s == "Risk").sum()),
        safe_days=("risk_zone", lambda s: (s == "Safe").sum()),
    ).reset_index()

    summary.to_csv(OUTPUTS_DIR / "simulation_summary.csv", index=False)

    print("\nSimulation completed.")
    print("Saved:")
    print(f"- {OUTPUTS_DIR / 'simulation_results_moderate_strategy.csv'}")
    print(f"- {OUTPUTS_DIR / 'simulation_results_safe_strategy.csv'}")
    print(f"- {OUTPUTS_DIR / 'simulation_results_aggressive_strategy.csv'}")
    print(f"- {PROCESSED_DIR / 'simulation_results_all_scenarios.csv'}")
    print(f"- {OUTPUTS_DIR / 'simulation_summary.csv'}")
    print("\nSummary:")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
