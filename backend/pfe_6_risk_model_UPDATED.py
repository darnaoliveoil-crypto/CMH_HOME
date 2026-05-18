# -*- coding: utf-8 -*-
"""
pfe_6_risk_model.py
Local VS Code version.

Goal:
- Load df_ml created by pfe_5 from backend/data/processed/
- Train risk classification models: Safe / Risk / Dangerous
- Avoid direct error-leakage features in X
- Save best model + imputer + feature list in backend/models/risk_model.pkl
- Save evaluation outputs in backend/outputs/ and backend/data/processed/
"""

from pathlib import Path
import warnings

import joblib
import numpy as np
import pandas as pd

from sklearn.ensemble import ExtraTreesClassifier, GradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

warnings.filterwarnings("ignore")


# =========================================================
# 1) Paths
# =========================================================
BACKEND_DIR = Path(__file__).resolve().parent
PROCESSED_DIR = BACKEND_DIR / "data" / "processed"
DATA_DIR = BACKEND_DIR / "data"
MODELS_DIR = BACKEND_DIR / "models"
OUTPUTS_DIR = BACKEND_DIR / "outputs"

MODELS_DIR.mkdir(parents=True, exist_ok=True)
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

INPUT_CSV = PROCESSED_DIR / "df_ml.csv"
INPUT_XLSX = PROCESSED_DIR / "df_ml.xlsx"

MODEL_PATH = MODELS_DIR / "risk_model.pkl"
RESULTS_PATH = OUTPUTS_DIR / "risk_model_evaluation_results.csv"
FEATURE_IMPORTANCE_PATH = OUTPUTS_DIR / "risk_model_feature_importance.csv"
PREDICTIONS_PATH = OUTPUTS_DIR / "risk_model_test_predictions.csv"
CONFUSION_MATRIX_PATH = OUTPUTS_DIR / "risk_model_confusion_matrix.csv"

# Copy important outputs also to processed for next scripts/dashboard if needed
RESULTS_PROCESSED_PATH = PROCESSED_DIR / "risk_model_evaluation_results.csv"
FEATURE_IMPORTANCE_PROCESSED_PATH = PROCESSED_DIR / "risk_model_feature_importance.csv"


# =========================================================
# 2) Load data
# =========================================================
def load_df() -> pd.DataFrame:
    if INPUT_CSV.exists():
        print(f"Loading: {INPUT_CSV}")
        return pd.read_csv(INPUT_CSV)
    if INPUT_XLSX.exists():
        print(f"Loading: {INPUT_XLSX}")
        return pd.read_excel(INPUT_XLSX)
    raise FileNotFoundError(
        f"Cannot find df_ml. Expected one of:\n- {INPUT_CSV}\n- {INPUT_XLSX}\nRun pfe_5_feature_engineering_labels.py first."
    )


df = load_df()
print("\nDataset loaded successfully.")
print("Shape:", df.shape)
print("Columns:", list(df.columns))


# =========================================================
# 3) Feature selection — avoid leakage
# =========================================================
TARGET_COLUMN = "risk_label_encoded"

# Direct error columns are excluded because they almost directly define the label.
LEAKAGE_FEATURES = [
    "error_flag",
    "spf_error",
    "ratelimit_error",
    "dkim_error",
    "netblock_error",
    "error_count_last_24h",
    "blocked_before",
    "risk_label",
    "risk_label_encoded",
    "error_type_from_error",
]

NUMERIC_FEATURES = [
    "sent_per_ip",
    "r_sent_per_ip",
    "limit_per_ip",
    "offset",
    "previous_sent_per_ip",
    "volume_change",
    "growth_rate",
    "cumulative_sent_per_ip",
    "daily_cumulative_sent_per_ip",
    "daily_volume",
    "volume_per_drop",
    "sent_ratio",
    "limit_usage_ratio",
    "drops_per_day",
    "time_gap_min",
    "days_since_launch",
    "hour",
    "day_of_week",
]

CATEGORICAL_FEATURES = [
    "entity"
]

ALLOWED_FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES

if TARGET_COLUMN not in df.columns:
    raise KeyError(f"Missing target column: {TARGET_COLUMN}. Run pfe_5 first and check df_ml.csv.")

existing_features = [col for col in ALLOWED_FEATURES if col in df.columns]
missing_features = [col for col in ALLOWED_FEATURES if col not in df.columns]

if missing_features:
    print("\nWarning: these allowed features are missing and will be ignored:")
    print(missing_features)

if not existing_features:
    raise ValueError("No allowed features found. Check df_ml.csv columns.")

leakage_in_x = [col for col in existing_features if col in LEAKAGE_FEATURES]
if leakage_in_x:
    raise ValueError(f"Leakage features detected in X: {leakage_in_x}")

model_df = df.copy()
model_df[TARGET_COLUMN] = pd.to_numeric(model_df[TARGET_COLUMN], errors="coerce")
model_df = model_df.dropna(subset=[TARGET_COLUMN]).copy()
model_df[TARGET_COLUMN] = model_df[TARGET_COLUMN].astype(int)

X_raw = model_df[existing_features].copy()
y = model_df[TARGET_COLUMN].copy()

for col in NUMERIC_FEATURES:
    if col in X_raw.columns:
        X_raw[col] = pd.to_numeric(X_raw[col], errors="coerce")

for col in CATEGORICAL_FEATURES:
    if col in X_raw.columns:
        X_raw[col] = X_raw[col].fillna("unknown").astype(str)

X_raw = X_raw.replace([np.inf, -np.inf], np.nan)

print("\nFeature selection successful: no leakage features used.")
print("X shape:", X_raw.shape)
print("y distribution:")
print(y.value_counts().sort_index())


# =========================================================
# 4) Imputation
# =========================================================
existing_numeric_features = [c for c in NUMERIC_FEATURES if c in X_raw.columns]
existing_categorical_features = [c for c in CATEGORICAL_FEATURES if c in X_raw.columns]

preprocessor = ColumnTransformer(
    transformers=[
        ("num", SimpleImputer(strategy="median"), existing_numeric_features),
        ("cat", OneHotEncoder(handle_unknown="ignore"), existing_categorical_features),
    ]
)

X = X_raw.copy()

print("\nPreprocessor created successfully.")
print("Numeric features:", existing_numeric_features)
print("Categorical features:", existing_categorical_features)


# =========================================================
# 5) Train / test split
# =========================================================
class_counts = y.value_counts()
can_stratify = len(class_counts) > 1 and class_counts.min() >= 2

if can_stratify:
    stratify_arg = y
    print("\nUsing stratified train/test split.")
else:
    stratify_arg = None
    print("\nWarning: not enough samples per class for stratify. Using normal split.")

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=stratify_arg,
)

print("Train shape:", X_train.shape)
print("Test shape:", X_test.shape)


# =========================================================
# 6) Train models
# =========================================================
base_models = {
    "RandomForestClassifier": RandomForestClassifier(
        n_estimators=300,
        random_state=42,
        class_weight="balanced",
        n_jobs=-1,
    ),
    "ExtraTreesClassifier": ExtraTreesClassifier(
        n_estimators=300,
        random_state=42,
        class_weight="balanced",
        n_jobs=-1,
    ),
    "GradientBoostingClassifier": GradientBoostingClassifier(random_state=42),
}

models = {
    name: Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("model", estimator),
        ]
    )
    for name, estimator in base_models.items()
}

for name, model in models.items():
    print(f"\nTraining {name}...")
    model.fit(X_train, y_train)
    print(f"{name} trained.")


# =========================================================
# 7) Evaluate models
# =========================================================
label_names = {0: "Safe", 1: "Risk", 2: "Dangerous"}
evaluation_results = []
classification_reports = {}

for name, model in models.items():
    print(f"\n--- Evaluating {name} ---")
    y_pred = model.predict(X_test)

    accuracy = accuracy_score(y_test, y_pred)
    precision_macro = precision_score(y_test, y_pred, average="macro", zero_division=0)
    recall_macro = recall_score(y_test, y_pred, average="macro", zero_division=0)
    f1_macro = f1_score(y_test, y_pred, average="macro", zero_division=0)

    report_dict = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
    classification_reports[name] = report_dict

    row = {
        "Model": name,
        "Accuracy": accuracy,
        "Precision_Macro": precision_macro,
        "Recall_Macro": recall_macro,
        "F1_Macro": f1_macro,
    }

    for label_id, label_name in label_names.items():
        label_key = str(label_id)
        row[f"Precision_{label_name}"] = report_dict.get(label_key, {}).get("precision", 0)
        row[f"Recall_{label_name}"] = report_dict.get(label_key, {}).get("recall", 0)
        row[f"F1_{label_name}"] = report_dict.get(label_key, {}).get("f1-score", 0)

    evaluation_results.append(row)

    print(f"Accuracy: {accuracy:.4f}")
    print(f"Macro F1: {f1_macro:.4f}")
    print(classification_report(y_test, y_pred, zero_division=0))

results_df = pd.DataFrame(evaluation_results).sort_values("F1_Macro", ascending=False)
print("\nModel comparison:")
print(results_df.round(4))

best_model_name = results_df.iloc[0]["Model"]
best_model = models[best_model_name]
print(f"\nBest model selected: {best_model_name}")


# =========================================================
# 8) Save outputs
# =========================================================
results_df.to_csv(RESULTS_PATH, index=False)
results_df.to_csv(RESULTS_PROCESSED_PATH, index=False)

# Feature importance
final_model = best_model.named_steps["model"]
preprocessor_fitted = best_model.named_steps["preprocessor"]

try:
    feature_names = preprocessor_fitted.get_feature_names_out()
except Exception:
    feature_names = existing_features

if hasattr(final_model, "feature_importances_"):
    feature_importance_df = pd.DataFrame({
        "feature": feature_names,
        "importance": final_model.feature_importances_,
    }).sort_values("importance", ascending=False)
else:
    feature_importance_df = pd.DataFrame({"feature": feature_names, "importance": np.nan})

# Predictions for test rows
best_y_pred = best_model.predict(X_test)
predictions_df = pd.DataFrame({
    "row_index": X_test.index,
    "actual_risk_label_encoded": y_test.values,
    "predicted_risk_label_encoded": best_y_pred,
    "actual_risk_label": [label_names.get(int(v), str(v)) for v in y_test.values],
    "predicted_risk_label": [label_names.get(int(v), str(v)) for v in best_y_pred],
})

if hasattr(best_model, "predict_proba"):
    proba = best_model.predict_proba(X_test)
    for i, cls in enumerate(best_model.classes_):
        predictions_df[f"proba_{label_names.get(int(cls), cls)}"] = proba[:, i]

predictions_df.to_csv(PREDICTIONS_PATH, index=False)

# Confusion matrix of best model
cm = confusion_matrix(y_test, best_y_pred, labels=[0, 1, 2])
cm_df = pd.DataFrame(cm, index=["Actual_Safe", "Actual_Risk", "Actual_Dangerous"], columns=["Pred_Safe", "Pred_Risk", "Pred_Dangerous"])
cm_df.to_csv(CONFUSION_MATRIX_PATH)

# Save full model package, not only estimator, so next scripts can reuse features and imputer safely.
model_package = {
    "model": best_model,
    "model_name": best_model_name,
    "preprocessor": preprocessor,
    "features": existing_features,
    "label_mapping": {"Safe": 0, "Risk": 1, "Dangerous": 2},
    "inverse_label_mapping": label_names,
    "evaluation_results": results_df,
}
joblib.dump(model_package, MODEL_PATH)

print("\nSaved files:")
print(f"- Model package: {MODEL_PATH}")
print(f"- Evaluation results: {RESULTS_PATH}")
print(f"- Feature importance: {FEATURE_IMPORTANCE_PATH}")
print(f"- Test predictions: {PREDICTIONS_PATH}")
print(f"- Confusion matrix: {CONFUSION_MATRIX_PATH}")
print("\npfe_6_risk_model.py completed successfully.")
