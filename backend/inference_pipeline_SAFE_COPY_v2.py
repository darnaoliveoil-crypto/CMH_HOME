from pathlib import Path
import pandas as pd
import numpy as np
import joblib

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
PROCESSED_DIR = DATA_DIR / "processed"
MODELS_DIR = BASE_DIR / "models"
OUTPUTS_DIR = BASE_DIR / "outputs"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------
# Helpers
# --------------------------------------------------
def check_required_files():
    required_files = [
        PROCESSED_DIR / "df_ml.csv",
        MODELS_DIR / "risk_model.pkl",
        MODELS_DIR / "best_model_spf_error.pkl",
        MODELS_DIR / "best_model_dkim_error.pkl",
        MODELS_DIR / "best_model_netblock_error.pkl",
        MODELS_DIR / "model_initial_volume.pkl",
        MODELS_DIR / "model_growth_rate.pkl",
        MODELS_DIR / "model_drops_per_day.pkl",
        MODELS_DIR / "model_time_gap_min.pkl",
        MODELS_DIR / "model_max_safe_volume.pkl",
    ]

    missing = [str(f) for f in required_files if not f.exists()]
    if missing:
        raise FileNotFoundError("Missing files:\n" + "\n".join(missing))

    print("All required files exist.")


def load_models():
    models = {
        "risk_model": joblib.load(MODELS_DIR / "risk_model.pkl"),
        "spf_model": joblib.load(MODELS_DIR / "best_model_spf_error.pkl"),
        "dkim_model": joblib.load(MODELS_DIR / "best_model_dkim_error.pkl"),
        "netblock_model": joblib.load(MODELS_DIR / "best_model_netblock_error.pkl"),
        "initial_volume_model": joblib.load(MODELS_DIR / "model_initial_volume.pkl"),
        "growth_rate_model": joblib.load(MODELS_DIR / "model_growth_rate.pkl"),
        "drops_per_day_model": joblib.load(MODELS_DIR / "model_drops_per_day.pkl"),
        "time_gap_model": joblib.load(MODELS_DIR / "model_time_gap_min.pkl"),
        "max_safe_volume_model": joblib.load(MODELS_DIR / "model_max_safe_volume.pkl"),
    }

    print("Models loaded successfully.")
    print("Risk model type:", type(models["risk_model"]))
    if isinstance(models["risk_model"], dict):
        print("Risk model keys:", models["risk_model"].keys())

    return models


def load_latest_features():
    df_ml = pd.read_csv(PROCESSED_DIR / "df_ml.csv")
    print(f"Loaded df_ml: {df_ml.shape}")
    return df_ml


def unwrap_model(model_obj):
    """Some saved models are dicts. This returns the real sklearn model."""
    if isinstance(model_obj, dict):
        return model_obj.get("model") or model_obj.get("best_model")
    return model_obj


def get_expected_features(model_obj):
    """
    Return the exact feature names expected by a sklearn model/pipeline.
    Works with pipelines containing SimpleImputer and with normal estimators.
    """
    model_obj = unwrap_model(model_obj)

    if hasattr(model_obj, "feature_names_in_"):
        return list(model_obj.feature_names_in_)

    if hasattr(model_obj, "named_steps"):
        for step in model_obj.named_steps.values():
            if hasattr(step, "feature_names_in_"):
                return list(step.feature_names_in_)

    return None


def build_model_input(base_features_df, model_obj):
    """
    Build X using exactly the feature names used during model training.
    If the model expects a feature that is not available, create it with 0.
    This prevents sklearn feature-name mismatch errors.
    """
    expected_features = get_expected_features(model_obj)

    if expected_features is None:
        X = base_features_df.copy()
    else:
        X = pd.DataFrame(index=base_features_df.index)
        for feature in expected_features:
            if feature in base_features_df.columns:
                X[feature] = base_features_df[feature]
            else:
                print(f"Warning: model expects missing feature '{feature}', filling with 0.")
                X[feature] = 0

        for col in X.columns:
            if col == "entity" or X[col].dtype == "object":
                X[col] = X[col].fillna("unknown").astype(str)
            else:
                X[col] = pd.to_numeric(X[col], errors="coerce")

        X = X.replace([np.inf, -np.inf], np.nan)

        for col in X.columns:
            if col == "entity" or X[col].dtype == "object":
                X[col] = X[col].fillna("unknown")
            else:
                X[col] = X[col].fillna(0)

    return X


def predict_positive_probability(model, X):
    """Return probability of class 1 safely, even for dummy/single-class models."""
    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(X)
        classes = list(getattr(model, "classes_", []))
        if 1 in classes:
            return proba[:, classes.index(1)]
    return np.zeros(len(X))


# --------------------------------------------------
# Risk + error inference
# --------------------------------------------------
def predict_risk_and_errors(df_ml, models):
    features = [
        "entity","sent_per_ip", "r_sent_per_ip", "limit_per_ip", "offset",
        "previous_sent_per_ip", "volume_change", "growth_rate",
        "cumulative_sent_per_ip", "daily_cumulative_sent_per_ip",
        "daily_volume", "volume_per_drop", "sent_ratio",
        "limit_usage_ratio", "drops_per_day", "time_gap_min",
        "days_since_launch", "hour", "day_of_week",
    ]

    missing = [c for c in features if c not in df_ml.columns]
    if missing:
        raise ValueError(f"df_ml.csv is missing required inference features: {missing}")

    base_X = df_ml[features].copy()

    result = df_ml.copy()

    risk_model_obj = unwrap_model(models["risk_model"])
    X_risk = build_model_input(base_X, risk_model_obj)

    result["predicted_risk_label_encoded"] = risk_model_obj.predict(X_risk)

    # Prefer mapping from saved model dict if available
    if isinstance(models["risk_model"], dict) and "inverse_label_mapping" in models["risk_model"]:
        inverse_map = models["risk_model"]["inverse_label_mapping"]
        result["predicted_risk_label"] = result["predicted_risk_label_encoded"].map(inverse_map)
    else:
        risk_map = {0: "Safe", 1: "Risk", 2: "Dangerous"}
        result["predicted_risk_label"] = result["predicted_risk_label_encoded"].map(risk_map)

    for name, model_key in [
        ("spf", "spf_model"),
        ("dkim", "dkim_model"),
        ("netblock", "netblock_model"),
    ]:
        model = unwrap_model(models[model_key])
        X_err = build_model_input(base_X, model)

        result[f"{name}_error_probability"] = predict_positive_probability(model, X_err)
        result[f"predicted_{name}_error"] = model.predict(X_err)

    output_path = PROCESSED_DIR / "inference_predictions.csv"
    result.to_csv(output_path, index=False)
    print(f"Saved predictions: {output_path}")

    return result


# --------------------------------------------------
# Strategy recommendations from PFE9 models
# --------------------------------------------------
def generate_strategy_recommendations(df_ml, models):
    df = df_ml.copy()

    if "datetime_gride" in df.columns:
        df["datetime_gride"] = pd.to_datetime(df["datetime_gride"], errors="coerce")
        df = df.sort_values(["ip", "datetime_gride"])
    else:
        df = df.sort_values(["ip"])

    # Build a wide feature table with several aliases.
    # The final X is selected dynamically based on each model's expected features.
    ip_features = (
    df.groupby("ip", as_index=False)
    .agg(
        entity=("entity", "first"),
        first_limit=("limit_per_ip", "first"),
        first_offset=("offset", "first"),
        avg_limit_usage_ratio=("limit_usage_ratio", "mean"),
        avg_sent_ratio=("sent_ratio", "mean"),
        safe_duration_days=("days_since_launch", "max"),
        avg_time_gap_min=("time_gap_min", "mean"),
        average_time_gap_min=("time_gap_min", "mean"),
        avg_growth_rate=("growth_rate", "mean"),
        avg_drops_per_day=("drops_per_day", "mean"),
        maximum_safe_volume=("daily_volume", "max"),
        max_daily_volume=("daily_volume", "max"),
    )
)
    # Extra aliases in case old models used slightly different names
    ip_features["first_sent_per_ip"] = (
        df.groupby("ip")["sent_per_ip"].first().reindex(ip_features["ip"]).values
        if "sent_per_ip" in df.columns else 0
    )

    recommendation_models = {
        "recommended_initial_volume": models["initial_volume_model"],
        "recommended_growth_rate": models["growth_rate_model"],
        "recommended_drops_per_day": models["drops_per_day_model"],
        "recommended_time_gap_min": models["time_gap_model"],
        "recommended_max_safe_volume": models["max_safe_volume_model"],
    }

    for output_col, model_obj in recommendation_models.items():
        model = unwrap_model(model_obj)
        X = build_model_input(ip_features, model)
        ip_features[output_col] = model.predict(X)

    # Clean recommendation values
    for col in [
        "recommended_initial_volume",
        "recommended_drops_per_day",
        "recommended_time_gap_min",
        "recommended_max_safe_volume",
    ]:
        if col in ip_features.columns:
            ip_features[col] = pd.to_numeric(ip_features[col], errors="coerce").fillna(0).clip(lower=0).round(0).astype(int)

    if "recommended_growth_rate" in ip_features.columns:
        ip_features["recommended_growth_rate"] = pd.to_numeric(
            ip_features["recommended_growth_rate"], errors="coerce"
        ).fillna(0).round(4)

    output_path = PROCESSED_DIR / "strategy_recommendations.csv"
    ip_features.to_csv(output_path, index=False)
    print(f"Saved strategy recommendations: {output_path}")

    return ip_features


# --------------------------------------------------
# Dashboard summary
# --------------------------------------------------
def create_dashboard_summary(predictions, strategy_df):
    risk_summary = (
        predictions["predicted_risk_label"]
        .value_counts(dropna=False)
        .rename_axis("predicted_risk_label")
        .reset_index(name="count")
    )
    risk_summary.to_csv(OUTPUTS_DIR / "inference_risk_summary.csv", index=False)

    error_summary = pd.DataFrame({
        "metric": [
            "avg_spf_error_probability",
            "avg_dkim_error_probability",
            "avg_netblock_error_probability",
        ],
        "value": [
            predictions["spf_error_probability"].mean(),
            predictions["dkim_error_probability"].mean(),
            predictions["netblock_error_probability"].mean(),
        ],
    })
    error_summary.to_csv(OUTPUTS_DIR / "inference_error_summary.csv", index=False)

    strategy_df.to_csv(OUTPUTS_DIR / "strategy_recommendations_summary.csv", index=False)

    print(f"Saved dashboard summaries in: {OUTPUTS_DIR}")


# --------------------------------------------------
# Main
# --------------------------------------------------
def main():
    check_required_files()
    models = load_models()
    df_ml = load_latest_features()

    predictions = predict_risk_and_errors(df_ml, models)
    strategy_df = generate_strategy_recommendations(df_ml, models)
    create_dashboard_summary(predictions, strategy_df)

    preview_cols = [
        "ip",
        "datetime_gride",
        "predicted_risk_label",
        "spf_error_probability",
        "dkim_error_probability",
        "netblock_error_probability",
    ]
    existing_preview_cols = [c for c in preview_cols if c in predictions.columns]

    print("\nPrediction preview:")
    print(predictions[existing_preview_cols].head().to_string(index=False))

    print("\nStrategy preview:")
    strategy_preview_cols = [
        "ip",
        "recommended_initial_volume",
        "recommended_growth_rate",
        "recommended_drops_per_day",
        "recommended_time_gap_min",
        "recommended_max_safe_volume",
    ]
    existing_strategy_cols = [c for c in strategy_preview_cols if c in strategy_df.columns]
    print(strategy_df[existing_strategy_cols].head().to_string(index=False))

    print("\nInference pipeline completed successfully.")


if __name__ == "__main__":
    main()
