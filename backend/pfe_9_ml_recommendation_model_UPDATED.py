# -*- coding: utf-8 -*-
"""
PFE 9 - ML Recommendation Model
Local VS Code version.

Reads:
- backend/data/processed/initial_behavior_summary.csv
- backend/data/processed/df_ml.csv

Saves:
- backend/models/model_initial_volume.pkl
- backend/models/model_growth_rate.pkl
- backend/models/model_max_safe_volume.pkl
- backend/models/model_time_gap_min.pkl
- backend/models/model_drops_per_day.pkl
- backend/data/processed/ml_recommendation_training_data.csv
- backend/outputs/ml_recommendation_evaluation.csv
- backend/outputs/ml_recommendation_feature_importance.csv
- backend/outputs/ml_recommendation_sample_output.csv
"""

from pathlib import Path
import warnings

import joblib
import numpy as np
import pandas as pd

from sklearn.ensemble import ExtraTreesRegressor, GradientBoostingRegressor, RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder

warnings.filterwarnings("ignore")
pd.set_option("display.max_columns", None)
pd.set_option("display.max_rows", 100)

print("=" * 70)
print("PFE 9 - ML Recommendation Model")
print("=" * 70)

# ---------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
PROCESSED_DIR = DATA_DIR / "processed"
MODELS_DIR = BASE_DIR / "models"
OUTPUTS_DIR = BASE_DIR / "outputs"

MODELS_DIR.mkdir(parents=True, exist_ok=True)
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

INITIAL_BEHAVIOR_PATH = PROCESSED_DIR / "initial_behavior_summary.csv"
DF_ML_PATH = PROCESSED_DIR / "df_ml.csv"


def read_csv_required(path: Path, name: str) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing {name}: {path}")
    return pd.read_csv(path)


# ---------------------------------------------------------------------
# Step 1 - Load data
# ---------------------------------------------------------------------
initial_behavior_summary = read_csv_required(INITIAL_BEHAVIOR_PATH, "initial_behavior_summary.csv")
df_ml = read_csv_required(DF_ML_PATH, "df_ml.csv")

print(f"Loaded initial_behavior_summary: {initial_behavior_summary.shape}")
print(f"Loaded df_ml: {df_ml.shape}")

# ---------------------------------------------------------------------
# Step 2 - Datetime conversion
# ---------------------------------------------------------------------
for col in ["first_used_at", "first_error_day", "first_netblock_day"]:
    if col in initial_behavior_summary.columns:
        initial_behavior_summary[col] = pd.to_datetime(initial_behavior_summary[col], errors="coerce")

if "datetime_gride" in df_ml.columns:
    df_ml["datetime_gride"] = pd.to_datetime(df_ml["datetime_gride"], errors="coerce")

# ---------------------------------------------------------------------
# Step 3 - Prepare safe historical IPs
# ---------------------------------------------------------------------
required_initial_cols = [
    "ip", "entity", "first_sent_per_ip", "first_limit", "first_offset", "first_launch_success",
    "first_error", "safe_duration_days", "maximum_safe_volume",
    "average_safe_growth_rate", "average_time_gap_min"
]
missing_initial_cols = [c for c in required_initial_cols if c not in initial_behavior_summary.columns]
if missing_initial_cols:
    raise ValueError(f"Missing columns in initial_behavior_summary: {missing_initial_cols}")

required_ml_cols = [
    "ip", "drops_per_day", "growth_rate", "time_gap_min", "limit_usage_ratio",
    "sent_ratio", "spf_error", "dkim_error", "netblock_error"
]
missing_ml_cols = [c for c in required_ml_cols if c not in df_ml.columns]
if missing_ml_cols:
    raise ValueError(f"Missing columns in df_ml: {missing_ml_cols}")

error_cols = ["spf_error", "dkim_error", "netblock_error"]
for col in error_cols:
    df_ml[col] = pd.to_numeric(df_ml[col], errors="coerce").fillna(0).astype(int)

# IPs with any historical error
ips_with_error = set(df_ml.loc[df_ml[error_cols].any(axis=1), "ip"].dropna().unique())

# Safe IP filtering: use positive historical starts but not too strict, so model has enough rows.
safe_mask = (
    (initial_behavior_summary["first_launch_success"] == 1) &
    (~initial_behavior_summary["ip"].isin(ips_with_error)) &
    (pd.to_numeric(initial_behavior_summary["first_sent_per_ip"], errors="coerce") > 0)
)
training_df = initial_behavior_summary.loc[safe_mask].copy()

# Fallback: if too few perfect safe IPs, use first_launch_success IPs without forcing no-error lifetime.
if len(training_df) < 5:
    print("Warning: fewer than 5 strict safe IPs. Using fallback: first_launch_success == 1.")
    training_df = initial_behavior_summary.loc[
        (initial_behavior_summary["first_launch_success"] == 1) &
        (pd.to_numeric(initial_behavior_summary["first_sent_per_ip"], errors="coerce") > 0)
    ].copy()

# Last fallback: use all IPs with valid target values.
if len(training_df) < 5:
    print("Warning: fewer than 5 successful IPs. Using all valid IPs for training.")
    training_df = initial_behavior_summary.loc[
        pd.to_numeric(initial_behavior_summary["first_sent_per_ip"], errors="coerce").notna()
    ].copy()

print(f"Training IP rows selected: {len(training_df)}")

# ---------------------------------------------------------------------
# Step 4 - Aggregate df_ml per IP
# ---------------------------------------------------------------------
agg_df = df_ml.groupby("ip", as_index=False).agg(
    avg_growth_rate=("growth_rate", "mean"),
    avg_time_gap_min=("time_gap_min", "mean"),
    avg_limit_usage_ratio=("limit_usage_ratio", "mean"),
    avg_sent_ratio=("sent_ratio", "mean"),
    avg_drops_per_day=("drops_per_day", "mean"),
    max_daily_volume=("daily_volume", "max") if "daily_volume" in df_ml.columns else ("sent_per_ip", "max"),
)

merged_df = training_df.merge(agg_df, on="ip", how="left")

# Fill numeric aggregation gaps
for col in ["avg_growth_rate", "avg_time_gap_min", "avg_limit_usage_ratio", "avg_sent_ratio", "avg_drops_per_day", "max_daily_volume"]:
    if col in merged_df.columns:
        merged_df[col] = pd.to_numeric(merged_df[col], errors="coerce").fillna(0)

# ---------------------------------------------------------------------
# Step 5 - Define features and targets
# ---------------------------------------------------------------------
numeric_features = [
    "first_limit",
    "first_offset",
    "safe_duration_days",
    "avg_limit_usage_ratio",
    "avg_sent_ratio",
    "avg_time_gap_min",
    "avg_drops_per_day",
    "max_daily_volume",
]

categorical_features = ["entity"]

features = numeric_features + categorical_features
existing_features = [c for c in features if c in merged_df.columns]

if len(existing_features) == 0:
    raise ValueError("No valid feature columns found for PFE 9 training.")

# Targets: prefer historical safe metrics, fallback to aggregated metrics when needed.
merged_df["target_initial_volume"] = pd.to_numeric(merged_df["first_sent_per_ip"], errors="coerce")
merged_df["target_growth_rate"] = pd.to_numeric(merged_df.get("average_safe_growth_rate"), errors="coerce").fillna(merged_df["avg_growth_rate"])
merged_df["target_max_safe_volume"] = pd.to_numeric(merged_df.get("maximum_safe_volume"), errors="coerce").fillna(merged_df["max_daily_volume"])
merged_df["target_time_gap_min"] = pd.to_numeric(merged_df.get("average_time_gap_min"), errors="coerce").fillna(merged_df["avg_time_gap_min"])
merged_df["target_drops_per_day"] = pd.to_numeric(merged_df["avg_drops_per_day"], errors="coerce")

targets = {
    "initial_volume": "target_initial_volume",
    "growth_rate": "target_growth_rate",
    "max_safe_volume": "target_max_safe_volume",
    "time_gap_min": "target_time_gap_min",
    "drops_per_day": "target_drops_per_day",
}

# Save training dataset
training_data_path = PROCESSED_DIR / "ml_recommendation_training_data.csv"
merged_df.to_csv(training_data_path, index=False)
print(f"Saved training data: {training_data_path}")

# ---------------------------------------------------------------------
# Step 6 - Train and evaluate models
# ---------------------------------------------------------------------
model_candidates = {
    "RandomForestRegressor": RandomForestRegressor(n_estimators=200, random_state=42),
    "ExtraTreesRegressor": ExtraTreesRegressor(n_estimators=200, random_state=42),
    "GradientBoostingRegressor": GradientBoostingRegressor(random_state=42),
}

evaluation_rows = []
feature_importance_rows = []
best_models = {}

for target_name, target_col in targets.items():
    temp = merged_df[existing_features + [target_col]].copy()

    for col in numeric_features:
        if col in temp.columns:
         temp[col] = pd.to_numeric(temp[col], errors="coerce")

    for col in categorical_features:
        if col in temp.columns:
            temp[col] = temp[col].fillna("unknown").astype(str)

    temp[target_col] = pd.to_numeric(temp[target_col], errors="coerce")

    temp = temp.replace([np.inf, -np.inf], np.nan).dropna(subset=[target_col])

    if len(temp) < 3:
        print(f"Skipping {target_name}: not enough rows ({len(temp)}).")
        continue

    X = temp[existing_features]
    y = temp[target_col]

    if len(temp) >= 10:
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    else:
        X_train, X_test, y_train, y_test = X, X, y, y
        print(f"Small dataset for {target_name}; evaluating on training data.")

    best_score = -np.inf
    best_model = None
    best_model_name = None

    print(f"\nTraining target: {target_name}")
    for model_name, regressor in model_candidates.items():
        existing_numeric_features = [c for c in numeric_features if c in X_train.columns]
        existing_categorical_features = [c for c in categorical_features if c in X_train.columns]

        preprocessor = ColumnTransformer(
            transformers=[
                ("num", SimpleImputer(strategy="median"), existing_numeric_features),
                ("cat", OneHotEncoder(handle_unknown="ignore"), existing_categorical_features),
            ]
        )

        pipeline = Pipeline([
            ("preprocessor", preprocessor),
            ("model", regressor),
        ])
        pipeline.fit(X_train, y_train)
        y_pred = pipeline.predict(X_test)

        mae = mean_absolute_error(y_test, y_pred)
        rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
        r2 = r2_score(y_test, y_pred) if len(y_test) > 1 else 0.0

        evaluation_rows.append({
            "Target": target_name,
            "Model": model_name,
            "MAE": mae,
            "RMSE": rmse,
            "R2": r2,
            "Rows": len(temp),
        })

        print(f"  {model_name}: MAE={mae:.4f}, RMSE={rmse:.4f}, R2={r2:.4f}")

        # choose best by R2, then RMSE lower
        score = r2 - (rmse * 1e-9)
        if score > best_score:
            best_score = score
            best_model = pipeline
            best_model_name = model_name

    if best_model is not None:
        best_models[target_name] = best_model
        model_path = MODELS_DIR / f"model_{target_name}.pkl"
        joblib.dump(best_model, model_path)
        print(f"  Saved best model for {target_name}: {best_model_name} -> {model_path}")

        fitted_model = best_model.named_steps["model"]
        if hasattr(fitted_model, "feature_importances_"):
            try:
                feature_names = best_model.named_steps["preprocessor"].get_feature_names_out()
            except Exception:
                feature_names = existing_features

            for feature, importance in zip(feature_names, fitted_model.feature_importances_):
                feature_importance_rows.append({
                    "Target": target_name,
                    "Best_Model": best_model_name,
                    "Feature": feature,
                    "Importance": importance,
                })

# Save evaluations
evaluation_df = pd.DataFrame(evaluation_rows)
evaluation_path = OUTPUTS_DIR / "ml_recommendation_evaluation.csv"
evaluation_df.to_csv(evaluation_path, index=False)
print(f"\nSaved evaluation: {evaluation_path}")

feature_importance_df = pd.DataFrame(feature_importance_rows)
feature_importance_path = OUTPUTS_DIR / "ml_recommendation_feature_importance.csv"
feature_importance_df.to_csv(feature_importance_path, index=False)
print(f"Saved feature importance: {feature_importance_path}")

# ---------------------------------------------------------------------
# Step 7 - Recommendation function + sample output
# ---------------------------------------------------------------------
def recommend_new_ip_strategy(new_ip_features: pd.DataFrame) -> pd.DataFrame:
    """Return recommended initial strategy using saved/trained PFE 9 models."""
    missing = [c for c in existing_features if c not in new_ip_features.columns]
    if missing:
        raise ValueError(f"Missing input features: {missing}")

    X_new = new_ip_features[existing_features].copy()
    recommendations = {}

    for target_name, model in best_models.items():
        value = float(model.predict(X_new)[0])
        if target_name in ["initial_volume", "max_safe_volume", "drops_per_day"]:
            value = max(0, round(value))
        elif target_name in ["growth_rate"]:
            value = round(value, 4)
        else:
            value = round(max(0, value), 2)

        recommendations[f"recommended_{target_name}"] = value

    return pd.DataFrame([recommendations])

sample_input = pd.DataFrame([{
    "first_limit": float(merged_df["first_limit"].median()) if "first_limit" in merged_df.columns else 80000,
    "first_offset": float(merged_df["first_offset"].median()) if "first_offset" in merged_df.columns else 20000,
    "safe_duration_days": float(merged_df["safe_duration_days"].median()) if "safe_duration_days" in merged_df.columns else 3,
    "avg_limit_usage_ratio": float(merged_df["avg_limit_usage_ratio"].median()) if "avg_limit_usage_ratio" in merged_df.columns else 0.5,
    "avg_sent_ratio": float(merged_df["avg_sent_ratio"].median()) if "avg_sent_ratio" in merged_df.columns else 0.9,
    "avg_time_gap_min": float(merged_df["avg_time_gap_min"].median()) if "avg_time_gap_min" in merged_df.columns else 0,
    "avg_drops_per_day": float(merged_df["avg_drops_per_day"].median()) if "avg_drops_per_day" in merged_df.columns else 0,
    "max_daily_volume": float(merged_df["max_daily_volume"].median()) if "max_daily_volume" in merged_df.columns else 0,
    "entity": str(merged_df["entity"].mode().iloc[0]) if "entity" in merged_df.columns and not merged_df["entity"].mode().empty else "unknown",
}])
sample_recommendation = recommend_new_ip_strategy(sample_input)
sample_path = OUTPUTS_DIR / "ml_recommendation_sample_output.csv"
sample_recommendation.to_csv(sample_path, index=False)
print(f"Saved sample recommendation: {sample_path}")
print("\nSample recommendation:")
print(sample_recommendation.to_string(index=False))
features_path = MODELS_DIR / "ml_recommendation_features.pkl"
joblib.dump(existing_features, features_path)
print(f"Saved recommendation feature list: {features_path}")
print("\nPFE 9 completed successfully.")
