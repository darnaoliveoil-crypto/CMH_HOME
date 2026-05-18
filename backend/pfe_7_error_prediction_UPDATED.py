# -*- coding: utf-8 -*-
"""
pfe_7_error_prediction.py
VS Code/local version.

Input:
    backend/data/processed/df_ml.csv
Outputs:
    backend/models/best_model_spf_error.pkl
    backend/models/best_model_dkim_error.pkl
    backend/models/best_model_netblock_error.pkl
    backend/outputs/error_prediction_summary.csv
    backend/outputs/error_prediction_feature_importance.csv
"""

from pathlib import Path
import warnings
import joblib
import numpy as np
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier, GradientBoostingClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, classification_report, confusion_matrix
from sklearn.dummy import DummyClassifier
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.impute import SimpleImputer

warnings.filterwarnings("ignore")

# --------------------------------------------------
# Paths
# --------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data" / "processed"
MODEL_DIR = BASE_DIR / "models"
OUTPUT_DIR = BASE_DIR / "outputs"

MODEL_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

INPUT_FILE = DATA_DIR / "df_ml.csv"

if not INPUT_FILE.exists():
    raise FileNotFoundError(f"Input file not found: {INPUT_FILE}\nRun pfe_5_feature_engineering_labels.py first.")

# --------------------------------------------------
# Load data
# --------------------------------------------------
df = pd.read_csv(INPUT_FILE)
print(f"Dataset loaded: {INPUT_FILE}")
print(f"Shape: {df.shape}")

# --------------------------------------------------
# Ensure needed columns exist
# --------------------------------------------------
numeric_features = [
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

categorical_features = ["entity"]

behavioral_features = numeric_features + categorical_features

targets = ["spf_error", "dkim_error", "netblock_error"]

missing_features = [c for c in behavioral_features if c not in df.columns]
missing_targets = [c for c in targets if c not in df.columns]

if missing_features:
    raise ValueError(f"Missing behavioral feature columns in df_ml.csv: {missing_features}")
if missing_targets:
    raise ValueError(f"Missing target columns in df_ml.csv: {missing_targets}")

# --------------------------------------------------
# Clean X
# --------------------------------------------------
X = df[behavioral_features].copy()

for col in numeric_features:
    if col in X.columns:
        X[col] = pd.to_numeric(X[col], errors="coerce")

for col in categorical_features:
    if col in X.columns:
        X[col] = X[col].fillna("unknown").astype(str)

X = X.replace([np.inf, -np.inf], np.nan)

preprocessor = ColumnTransformer(
    transformers=[
        ("num", SimpleImputer(strategy="median"), numeric_features),
        ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_features),
    ]
)

print("Behavioral features cleaned successfully.")
print(f"X shape: {X.shape}")

# --------------------------------------------------
# Train models per error target
# --------------------------------------------------
base_classifiers = {
    "RandomForestClassifier": RandomForestClassifier(random_state=42, class_weight="balanced"),
    "ExtraTreesClassifier": ExtraTreesClassifier(random_state=42, class_weight="balanced"),
    "GradientBoostingClassifier": GradientBoostingClassifier(random_state=42),
}

classifiers = {
    name: Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("model", estimator),
        ]
    )
    for name, estimator in base_classifiers.items()
}

all_results = []
best_models = {}
feature_importance_rows = []

for target in targets:
    print("\n" + "=" * 70)
    print(f"Target: {target}")
    y = pd.to_numeric(df[target], errors="coerce").fillna(0).astype(int)

    print("Class distribution:")
    print(y.value_counts(dropna=False))

    # If target has only one class, use DummyClassifier safely
    if y.nunique() < 2:
        print(f"Only one class found for {target}. Using DummyClassifier.")
        dummy = DummyClassifier(strategy="most_frequent")
        dummy.fit(X, y)
        best_models[target] = dummy

        y_pred = dummy.predict(X)
        result = {
            "Target": target,
            "Model": "DummyClassifier",
            "Accuracy": accuracy_score(y, y_pred),
            "Precision": precision_score(y, y_pred, zero_division=0),
            "Recall": recall_score(y, y_pred, zero_division=0),
            "F1-Score": f1_score(y, y_pred, zero_division=0),
            "ROC-AUC": 0.0,
            "Train_Rows": len(X),
            "Test_Rows": 0,
            "Note": "Only one class available; dummy model used",
        }
        all_results.append(result)
        continue

    # Stratify only if each class has at least 2 samples
    class_counts = y.value_counts()
    stratify_arg = y if class_counts.min() >= 2 else None

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=stratify_arg,
    )

    best_score = -1
    best_model_name = None
    best_model = None

    for model_name, model in classifiers.items():
        print(f"\nTraining {model_name} for {target}...")

        # GradientBoosting fails if train split has one class
        if y_train.nunique() < 2:
            print(f"Skipped {model_name}: training split has only one class.")
            continue

        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)

        if hasattr(model, "predict_proba"):
            proba = model.predict_proba(X_test)
            final_model = model.named_steps["model"]

            if 1 in final_model.classes_:
                class_1_idx = list(final_model.classes_).index(1)
        
                y_proba = proba[:, class_1_idx]
            else:
                y_proba = np.zeros(len(y_test))
        else:
            y_proba = np.zeros(len(y_test))

        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, zero_division=0)
        recall = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        roc_auc = roc_auc_score(y_test, y_proba) if y_test.nunique() > 1 else 0.0

        print(f"Accuracy : {accuracy:.4f}")
        print(f"Precision: {precision:.4f}")
        print(f"Recall   : {recall:.4f}")
        print(f"F1-Score : {f1:.4f}")
        print(f"ROC-AUC  : {roc_auc:.4f}")
        print("Confusion matrix:")
        print(confusion_matrix(y_test, y_pred))
        print("Classification report:")
        print(classification_report(y_test, y_pred, zero_division=0))

        all_results.append({
            "Target": target,
            "Model": model_name,
            "Accuracy": accuracy,
            "Precision": precision,
            "Recall": recall,
            "F1-Score": f1,
            "ROC-AUC": roc_auc,
            "Train_Rows": len(X_train),
            "Test_Rows": len(X_test),
            "Note": "",
        })

        # Business priority: recall > f1 > roc_auc
        selection_score = (recall * 10000) + (f1 * 100) + roc_auc
        if selection_score > best_score:
            best_score = selection_score
            best_model_name = model_name
            best_model = model

    if best_model is None:
        print(f"No valid model trained for {target}. Using DummyClassifier.")
        best_model = DummyClassifier(strategy="most_frequent")
        best_model.fit(X, y)
        best_model_name = "DummyClassifier"

    best_models[target] = best_model
    print(f"Best model for {target}: {best_model_name}")

    final_model = best_model.named_steps["model"]
    preprocessor_fitted = best_model.named_steps["preprocessor"]

    try:
        feature_names = preprocessor_fitted.get_feature_names_out()
    except Exception:
        feature_names = behavioral_features

    if hasattr(final_model, "feature_importances_"):
        importances = pd.Series(final_model.feature_importances_, index=feature_names).sort_values(ascending=False)
        for feature, importance in importances.items():
            feature_importance_rows.append({
                "Target": target,
                "Best_Model": best_model_name,
                "Feature": feature,
                "Importance": importance,
            })

# --------------------------------------------------
# Save models and outputs
# --------------------------------------------------
for target, model in best_models.items():
    model_path = MODEL_DIR / f"best_model_{target}.pkl"
    joblib.dump(model, model_path)
    print(f"Saved model: {model_path}")

summary_df = pd.DataFrame(all_results)
summary_path = OUTPUT_DIR / "error_prediction_summary.csv"
summary_df.to_csv(summary_path, index=False)
print(f"Saved summary: {summary_path}")

if feature_importance_rows:
    importance_df = pd.DataFrame(feature_importance_rows)
else:
    importance_df = pd.DataFrame(columns=["Target", "Best_Model", "Feature", "Importance"])

importance_path = OUTPUT_DIR / "error_prediction_feature_importance.csv"
importance_df.to_csv(importance_path, index=False)
print(f"Saved feature importance: {importance_path}")

# Save feature list for later dashboard/simulation use
features_path = MODEL_DIR / "error_prediction_features.pkl"
joblib.dump(behavioral_features, features_path)
print(f"Saved feature list: {features_path}")

print("\npfe_7_error_prediction completed successfully.")
