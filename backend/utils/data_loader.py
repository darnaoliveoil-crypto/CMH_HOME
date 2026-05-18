from pathlib import Path
import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
OUTPUTS_DIR = BASE_DIR / "outputs"
MODELS_DIR = BASE_DIR / "models"

@st.cache_data
def load_csv(path: Path):
    if not path.exists():
        return None
    return pd.read_csv(path)

def require_df(df, name):
    if df is None:
        st.warning(f"{name} not found. Please run the pipeline first.")
        return False
    return True

def load_final_data():
    return load_csv(PROCESSED_DIR / "final_data.csv")

def load_ip_analyse():
    return load_csv(PROCESSED_DIR / "IP_Analyse.csv")

def load_df_ml():
    return load_csv(PROCESSED_DIR / "df_ml.csv")

def load_inference_predictions():
    return load_csv(PROCESSED_DIR / "inference_predictions.csv")

def load_strategy_recommendations():
    return load_csv(PROCESSED_DIR / "strategy_recommendations.csv")

def load_warmup_plan():
    return load_csv(PROCESSED_DIR / "warmup_strategy_plan.csv")

def load_warmup_summary():
    return load_csv(OUTPUTS_DIR / "warmup_strategy_summary.csv")

def load_forecast_all_ips():
    return load_csv(PROCESSED_DIR / "forecast_all_ips_7_days.csv")

def load_simulation_all_scenarios():
    return load_csv(PROCESSED_DIR / "simulation_results_all_scenarios.csv")

def load_decision_results():
    return load_csv(PROCESSED_DIR / "decision_engine_results.csv")

def load_decision_summary():
    return load_csv(OUTPUTS_DIR / "decision_engine_summary.csv")

def load_risk_feature_importance():
    return load_csv(OUTPUTS_DIR / "risk_model_feature_importance.csv")

def load_error_feature_importance():
    return load_csv(OUTPUTS_DIR / "error_prediction_feature_importance.csv")

def load_entity_recommendations():
    return load_csv(PROCESSED_DIR / "entity_initial_volume_recommendations.csv")