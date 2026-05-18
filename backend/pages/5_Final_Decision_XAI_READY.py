import streamlit as st
import pandas as pd
from pathlib import Path

from utils.data_loader import (
    load_decision_results,
    load_risk_feature_importance,
    load_error_feature_importance,
    load_strategy_recommendations,
    load_ip_analyse,
)

# Optional loaders may not exist in old data_loader.py, so we load these manually too
BASE_DIR = Path(__file__).resolve().parents[1]
PROCESSED_DIR = BASE_DIR / "data" / "processed"
OUTPUTS_DIR = BASE_DIR / "outputs"


def safe_load_csv(path):
    if path.exists():
        return pd.read_csv(path)
    return None


def load_pfe8_global_recommendations():
    return safe_load_csv(PROCESSED_DIR / "initial_volume_recommendations.csv")


def load_pfe8_entity_recommendations():
    return safe_load_csv(PROCESSED_DIR / "entity_initial_volume_recommendations.csv")


def get_metric_from_pfe8(df, metric_name, default="N/A"):
    if df is None or df.empty:
        return default
    if "metric" not in df.columns or "value" not in df.columns:
        return default

    row = df[df["metric"] == metric_name]
    if row.empty:
        return default

    return row["value"].iloc[0]


def format_number(value):
    try:
        return f"{int(float(value)):,}"
    except Exception:
        return "N/A"


def format_float(value, digits=3):
    try:
        return round(float(value), digits)
    except Exception:
        return "N/A"


def classify_future_risk(risk_level, blocking_probability):
    risk_level = str(risk_level)

    if risk_level == "Dangerous" or blocking_probability >= 0.50:
        return (
            "High Future Risk",
            "Stop aggressive sending. Reduce volume, increase time gap, and avoid growth until the IP becomes stable."
        )

    if risk_level == "Risk" or blocking_probability >= 0.20:
        return (
            "Moderate Future Risk",
            "Continue carefully. Slow down growth, monitor errors, and avoid high volume jumps."
        )

    return (
        "Low Future Risk",
        "The IP can continue sending with progressive and controlled growth."
    )


# --------------------------------------------------
# Page config
# --------------------------------------------------
st.set_page_config(page_title="Final Decision & Strategy Summary", layout="wide")

st.title("Final Decision & Strategy Summary Dashboard")

# --------------------------------------------------
# Load data
# --------------------------------------------------
decision_df = load_decision_results()
ip_analyse = load_ip_analyse()
pfe9_strategy = load_strategy_recommendations()
pfe8_global = load_pfe8_global_recommendations()
pfe8_entity = load_pfe8_entity_recommendations()
risk_importance = load_risk_feature_importance()
error_importance = load_error_feature_importance()

if decision_df is None:
    st.warning("No decision results found. Run pfe_12 decision engine first.")
    st.stop()

if "datetime_gride" in decision_df.columns:
    decision_df["datetime_gride"] = pd.to_datetime(decision_df["datetime_gride"], errors="coerce")

# --------------------------------------------------
# Select IP
# --------------------------------------------------
ip_list = sorted(decision_df["ip"].dropna().unique())

if not ip_list:
    st.warning("No IP found in decision results.")
    st.stop()

selected_ip = st.sidebar.selectbox("Select IP", ip_list)

ip_decision = decision_df[decision_df["ip"] == selected_ip].copy()

if ip_decision.empty:
    st.error("No decision data found for selected IP.")
    st.stop()

if "datetime_gride" in ip_decision.columns:
    ip_decision = ip_decision.sort_values("datetime_gride")

latest = ip_decision.iloc[-1]

# --------------------------------------------------
# Selected IP lifecycle
# --------------------------------------------------
ip_lifecycle = None

if ip_analyse is not None and "ip" in ip_analyse.columns:
    ip_lifecycle = ip_analyse[ip_analyse["ip"] == selected_ip].copy()

if ip_lifecycle is not None and not ip_lifecycle.empty:
    ip_lifecycle["datetime_gride"] = pd.to_datetime(ip_lifecycle["datetime_gride"], errors="coerce")
    ip_lifecycle = ip_lifecycle.sort_values("datetime_gride")

    if "entity" not in ip_lifecycle.columns and "server" in ip_lifecycle.columns:
        ip_lifecycle["entity"] = ip_lifecycle["server"].astype(str).str.extract(r"s_(cmh\d+)")

# --------------------------------------------------
# Header final decision
# --------------------------------------------------
st.subheader(f"Final Operational Decision for IP: {selected_ip}")

final_decision = latest.get("final_decision", latest.get("decision", "N/A"))
current_risk = latest.get("current_risk_level", latest.get("predicted_risk_label", "N/A"))
latest_volume = latest.get("latest_daily_volume", latest.get("sent_per_ip", 0))
blocking_probability = float(latest.get("blocking_probability", latest.get("netblock_error_probability", 0)))

k1, k2, k3, k4 = st.columns(4)
k1.metric("Final Decision", final_decision)
k2.metric("Current Risk", current_risk)
k3.metric("Latest Volume", format_number(latest_volume))
k4.metric("Blocking Probability", format_float(blocking_probability, 3))

main_reason = latest.get("main_reason", "No reason available.")
recommended_action = latest.get("recommended_action", latest.get("recommendation", "No recommendation available."))

st.info(f"Main reason: {main_reason}")
st.success(f"Recommended action: {recommended_action}")

# --------------------------------------------------
# Lifecycle summary
# --------------------------------------------------
st.divider()
st.subheader("IP Lifecycle Summary")

if ip_lifecycle is not None and not ip_lifecycle.empty:
    total_sent = pd.to_numeric(ip_lifecycle.get("sent_per_ip", 0), errors="coerce").fillna(0).sum()
    total_rsent = pd.to_numeric(ip_lifecycle.get("r_sent_per_ip", 0), errors="coerce").fillna(0).sum()
    max_sent = pd.to_numeric(ip_lifecycle.get("sent_per_ip", 0), errors="coerce").fillna(0).max()
    avg_growth = pd.to_numeric(ip_lifecycle.get("growth_rate", 0), errors="coerce").fillna(0).mean()
    avg_drops = pd.to_numeric(ip_lifecycle.get("drops_per_day", 0), errors="coerce").fillna(0).mean()

    avg_sent_ratio = total_rsent / total_sent if total_sent > 0 else 0
    active_days = ip_lifecycle["datetime_gride"].dt.date.nunique() if "datetime_gride" in ip_lifecycle.columns else 0

    entity = (
        ip_lifecycle["entity"].dropna().astype(str).iloc[-1]
        if "entity" in ip_lifecycle.columns and not ip_lifecycle["entity"].dropna().empty
        else "unknown"
    )

    server = (
        ip_lifecycle["server"].dropna().astype(str).iloc[-1]
        if "server" in ip_lifecycle.columns and not ip_lifecycle["server"].dropna().empty
        else "N/A"
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Entity", entity)
    c2.metric("Server", server)
    c3.metric("Active Days", int(active_days))
    c4.metric("Lifecycle Rows", len(ip_lifecycle))

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Total R_Sent", format_number(total_rsent))
    c6.metric("Max Sent Volume", format_number(max_sent))
    c7.metric("Avg Sent Ratio", format_float(avg_sent_ratio, 3))
    c8.metric("Avg Growth", format_float(avg_growth, 3))

    c9, c10 = st.columns(2)
    c9.metric("Avg Drops/Day", format_float(avg_drops, 2))
    c10.metric("Total Sent", format_number(total_sent))

else:
    st.warning("No lifecycle data found for this IP.")

# --------------------------------------------------
# PFE8 vs PFE9 strategy comparison
# --------------------------------------------------
st.divider()
st.subheader("PFE8 vs PFE9 Strategy Comparison")

comparison_rows = []

# PFE8 global rule-based recommendation
if pfe8_global is not None:
    comparison_rows.append({
        "Source": "PFE8 - Historical Rule-Based Global",
        "Initial Volume": get_metric_from_pfe8(pfe8_global, "recommended_initial_volume"),
        "Growth Rate": get_metric_from_pfe8(pfe8_global, "recommended_growth_rate"),
        "Drops/Day": get_metric_from_pfe8(pfe8_global, "recommended_drops_per_day"),
        "Time Gap": get_metric_from_pfe8(pfe8_global, "recommended_time_gap_min"),
        "Max Safe Volume": get_metric_from_pfe8(pfe8_global, "recommended_maximum_safe_volume"),
        "Meaning": "General safe strategy calculated from historically safe IP starts.",
    })

# PFE8 entity recommendation
entity_name = None
if ip_lifecycle is not None and not ip_lifecycle.empty and "entity" in ip_lifecycle.columns:
    valid_entities = ip_lifecycle["entity"].dropna().astype(str)
    if not valid_entities.empty:
        entity_name = valid_entities.iloc[-1]

if pfe8_entity is not None and entity_name is not None and "entity" in pfe8_entity.columns:
    entity_match = pfe8_entity[pfe8_entity["entity"].astype(str) == entity_name]
    if not entity_match.empty:
        row = entity_match.iloc[0]
        comparison_rows.append({
            "Source": "PFE8 - Historical Rule-Based Entity",
            "Initial Volume": row.get("recommended_initial_volume", "N/A"),
            "Growth Rate": row.get("recommended_growth_rate", "N/A"),
            "Drops/Day": row.get("recommended_drops_per_day", "N/A"),
            "Time Gap": row.get("recommended_time_gap_min", "N/A"),
            "Max Safe Volume": row.get("recommended_maximum_safe_volume", "N/A"),
            "Meaning": f"Safe strategy calculated from historically safe IPs in entity {entity_name}.",
        })

# PFE9 IP-specific ML recommendation
ip_strategy = None
if pfe9_strategy is not None and "ip" in pfe9_strategy.columns:
    match = pfe9_strategy[pfe9_strategy["ip"] == selected_ip]
    if not match.empty:
        ip_strategy = match.iloc[0]

if ip_strategy is not None:
    comparison_rows.append({
        "Source": "PFE9 - ML-Based IP Strategy",
        "Initial Volume": ip_strategy.get("recommended_initial_volume", "N/A"),
        "Growth Rate": ip_strategy.get("recommended_growth_rate", "N/A"),
        "Drops/Day": ip_strategy.get("recommended_drops_per_day", "N/A"),
        "Time Gap": ip_strategy.get("recommended_time_gap_min", "N/A"),
        "Max Safe Volume": ip_strategy.get("recommended_max_safe_volume", "N/A"),
        "Meaning": "Personalized strategy predicted specifically for this IP using ML.",
    })

if comparison_rows:
    comparison_df = pd.DataFrame(comparison_rows)
    st.dataframe(comparison_df, use_container_width=True)

    if len(comparison_df) >= 2:
        st.caption(
            "PFE8 gives historical safe benchmarks, while PFE9 gives an IP-specific ML recommendation. "
            "If both are close, the strategy has higher confidence. If they differ strongly, operator review is required."
        )
else:
    st.warning("No PFE8/PFE9 recommendation data found.")

# --------------------------------------------------
# Future risk interpretation
# --------------------------------------------------
st.divider()
st.subheader("Future Risk Interpretation")

future_status, future_action = classify_future_risk(current_risk, blocking_probability)

f1, f2 = st.columns(2)
f1.metric("Future Risk Status", future_status)
f2.metric("Recommended Future Action", final_decision)

if future_status == "High Future Risk":
    st.error(future_action)
elif future_status == "Moderate Future Risk":
    st.warning(future_action)
else:
    st.success(future_action)

# --------------------------------------------------
# Current status table
# --------------------------------------------------
st.divider()
st.subheader("Latest Decision Records")

status_cols = [
    col for col in [
        "ip",
        "datetime_gride",
        "current_risk_level",
        "predicted_risk_label",
        "final_decision",
        "decision",
        "latest_daily_volume",
        "sent_per_ip",
        "latest_error",
        "error_type_from_error",
        "spf_error_probability",
        "dkim_error_probability",
        "netblock_error_probability",
        "blocking_probability",
        "main_reason",
        "recommended_action",
        "recommendation",
    ]
    if col in ip_decision.columns
]

st.dataframe(ip_decision[status_cols].tail(10), use_container_width=True)

# --------------------------------------------------
# Explainable AI feature importance
# --------------------------------------------------
st.divider()
st.subheader("Explainable AI - Feature Importance")

tab1, tab2 = st.tabs(["Risk Model", "Error Model"])

with tab1:
    if risk_importance is not None:
        st.dataframe(risk_importance.head(20), use_container_width=True)

        feature_col = "Feature" if "Feature" in risk_importance.columns else "feature"
        importance_col = "Importance" if "Importance" in risk_importance.columns else "importance"

        if feature_col in risk_importance.columns and importance_col in risk_importance.columns:
            chart_df = risk_importance.head(10).set_index(feature_col)[importance_col]
            st.bar_chart(chart_df)
    else:
        st.warning("Risk feature importance file not found.")

with tab2:
    if error_importance is not None:
        st.dataframe(error_importance.head(20), use_container_width=True)
    else:
        st.warning("Error feature importance file not found.")

# --------------------------------------------------
# Decision history
# --------------------------------------------------
st.divider()
st.subheader("Decision History for Selected IP")

history_cols = [
    col for col in [
        "datetime_gride",
        "final_decision",
        "decision",
        "current_risk_level",
        "predicted_risk_label",
        "main_reason",
        "recommended_action",
        "recommendation",
    ]
    if col in ip_decision.columns
]

st.dataframe(ip_decision[history_cols], use_container_width=True)
