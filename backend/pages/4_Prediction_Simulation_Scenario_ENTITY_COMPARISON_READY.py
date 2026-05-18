import streamlit as st
import pandas as pd

from warmup_strategy_engine import generate_daily_plan
from utils.data_loader import (
    load_inference_predictions,
    load_strategy_recommendations,
    load_entity_recommendations,
)

st.set_page_config(page_title="Entity Scenario Simulation", layout="wide")

st.title("Entity Scenario Simulation & Adaptive Warm-up Plan")

# --------------------------------------------------
# Helpers
# --------------------------------------------------
def add_error_probabilities(plan_df: pd.DataFrame) -> pd.DataFrame:
    plan_df = plan_df.copy()

    if "spf_probability" not in plan_df.columns:
        plan_df["spf_probability"] = (
            plan_df["estimated_error_probability"] * (0.4 + plan_df["growth_rate"])
        ).clip(0, 1).round(4)

    if "dkim_probability" not in plan_df.columns:
        plan_df["dkim_probability"] = (
            plan_df["estimated_error_probability"] * (0.3 + plan_df["limit_usage_ratio"])
        ).clip(0, 1).round(4)

    if "netblock_probability" not in plan_df.columns:
        plan_df["netblock_probability"] = (
            plan_df["estimated_error_probability"] * (0.5 + plan_df["volume_per_drop"] / 15000)
        ).clip(0, 1).round(4)

    return plan_df


def build_error_cause_table(plan_df: pd.DataFrame) -> pd.DataFrame:
    analysis_rows = []

    for _, row in plan_df.iterrows():
        reasons = []

        if row["growth_rate"] > 0.25:
            reasons.append("high growth rate")

        if row["volume_per_drop"] > 10000:
            reasons.append("high volume per drop")

        if row["estimated_error_probability"] > 0.30:
            reasons.append("high operational pressure")

        if row["limit_usage_ratio"] > 0.90:
            reasons.append("daily limit almost reached")

        if row["spf_probability"] > 0.30:
            reasons.append("possible SPF pressure")

        if row["dkim_probability"] > 0.30:
            reasons.append("possible DKIM pressure")

        if row["netblock_probability"] > 0.30:
            reasons.append("possible Netblock pressure")

        if not reasons:
            reasons.append("stable warm-up conditions")

        analysis_rows.append({
            "day": int(row["day"]),
            "daily_volume": int(row["daily_volume"]),
            "growth_rate": round(float(row["growth_rate"]), 4),
            "volume_per_drop": round(float(row["volume_per_drop"]), 2),
            "risk_zone": row["risk_zone"],
            "spf_probability": round(float(row["spf_probability"]), 4),
            "dkim_probability": round(float(row["dkim_probability"]), 4),
            "netblock_probability": round(float(row["netblock_probability"]), 4),
            "main_reason": ", ".join(reasons),
        })

    return pd.DataFrame(analysis_rows)


def get_entity_strategy(entity_df: pd.DataFrame, entity_name: str):
    if entity_df is None or entity_df.empty or "entity" not in entity_df.columns:
        return None

    match = entity_df[entity_df["entity"].astype(str) == str(entity_name)]
    if match.empty:
        return None

    return match.iloc[0]


def get_number(row, column, default):
    if row is None:
        return default

    if column not in row:
        return default

    value = pd.to_numeric(row[column], errors="coerce")

    if pd.isna(value):
        return default

    return float(value)


def simulate_entity_plan(
    entity_name,
    selected_ip,
    scenario_mode,
    latest,
    ip_strategy,
    entity_strategy,
    target_volume,
    max_days,
    manual_initial_volume,
    manual_growth_rate,
    manual_max_daily_limit,
    expected_sent_ratio,
    target_limit_usage_ratio,
    use_manual_values,
):
    # Defaults from latest IP behavior
    initial_volume = int(max(latest.get("sent_per_ip", 1000), 1000))
    growth_rate = 0.30
    max_daily_limit = 150000

    # IP-specific ML recommendation, mainly for existing IP
    if scenario_mode == "Existing IP" and ip_strategy is not None:
        initial_volume = int(max(get_number(ip_strategy, "recommended_initial_volume", initial_volume), 100))
        growth_rate = get_number(ip_strategy, "recommended_growth_rate", growth_rate)
        max_daily_limit = int(max(get_number(ip_strategy, "recommended_max_safe_volume", max_daily_limit), 150000))

    # Entity historical benchmark
    if entity_strategy is not None:
        entity_initial = get_number(entity_strategy, "recommended_initial_volume", initial_volume)
        entity_growth = get_number(entity_strategy, "recommended_growth_rate", growth_rate)
        entity_limit = get_number(entity_strategy, "recommended_maximum_safe_volume", max_daily_limit)

        if scenario_mode == "New IP":
            initial_volume = int(max(entity_initial, 100))
            growth_rate = entity_growth if entity_growth > 0.01 else growth_rate
            max_daily_limit = int(max(entity_limit, 150000))
        else:
            initial_volume = int(max((initial_volume + entity_initial) / 2, 100))
            if entity_growth > 0.01:
                growth_rate = float((growth_rate + entity_growth) / 2)
            max_daily_limit = int(max(entity_limit, max_daily_limit, 150000))

    # Manual override for selected detailed simulation
    if use_manual_values:
        initial_volume = manual_initial_volume
        growth_rate = manual_growth_rate
        max_daily_limit = manual_max_daily_limit

    growth_rate = max(0.01, min(float(growth_rate), 1.00))

    plan_df = generate_daily_plan(
        initial_volume=initial_volume,
        growth_rate=growth_rate,
        drops_per_day=20,
        target_volume=target_volume,
        max_days=max_days,
        max_daily_limit=max_daily_limit,
        expected_sent_ratio=expected_sent_ratio,
        target_limit_usage_ratio=target_limit_usage_ratio,
        plan_type=f"Adaptive Safe AI - {entity_name}",
    )

    plan_df = add_error_probabilities(plan_df)

    plan_df["selected_ip"] = selected_ip
    plan_df["scenario_mode"] = scenario_mode
    plan_df["target_entity"] = entity_name

    summary = {
        "entity": entity_name,
        "initial_volume": initial_volume,
        "growth_rate": round(growth_rate, 4),
        "max_daily_limit": max_daily_limit,
        "final_cumulative_volume": int(plan_df["cumulative_volume"].max()),
        "target_reached": bool(plan_df["target_reached"].max()),
        "safe_days": int((plan_df["risk_zone"] == "Safe").sum()),
        "risk_days": int((plan_df["risk_zone"] == "Risk").sum()),
        "dangerous_days": int((plan_df["risk_zone"] == "Dangerous").sum()),
        "avg_error_probability": round(float(plan_df["estimated_error_probability"].mean()), 4),
        "max_error_probability": round(float(plan_df["estimated_error_probability"].max()), 4),
        "max_spf_probability": round(float(plan_df["spf_probability"].max()), 4),
        "max_dkim_probability": round(float(plan_df["dkim_probability"].max()), 4),
        "max_netblock_probability": round(float(plan_df["netblock_probability"].max()), 4),
    }

    summary["score"] = (
        int(summary["target_reached"]) * 5000
        + summary["safe_days"] * 100
        - summary["risk_days"] * 200
        - summary["dangerous_days"] * 1000
        - summary["max_error_probability"] * 300
        - summary["max_netblock_probability"] * 500
    )

    return plan_df, summary


# --------------------------------------------------
# Load data
# --------------------------------------------------
pred_df = load_inference_predictions()
strategy_df = load_strategy_recommendations()
entity_df = load_entity_recommendations()

if pred_df is None:
    st.warning("No inference predictions found. Run Dashboard 1 first.")
    st.stop()

pred_df["datetime_gride"] = pd.to_datetime(pred_df["datetime_gride"], errors="coerce")

if entity_df is None:
    st.warning("Entity recommendations file not found. Run pfe_8 first.")
    entity_df = pd.DataFrame()

# --------------------------------------------------
# Scenario mode
# --------------------------------------------------
st.sidebar.header("IP Scenario Mode")

scenario_mode = st.sidebar.radio(
    "Choose scenario",
    ["Existing IP", "New IP"],
    index=0
)

available_entities = []

if "entity" in pred_df.columns:
    available_entities += pred_df["entity"].dropna().astype(str).unique().tolist()

if not entity_df.empty and "entity" in entity_df.columns:
    available_entities += entity_df["entity"].dropna().astype(str).unique().tolist()

available_entities = sorted(list(set(available_entities)))

if not available_entities:
    available_entities = ["unknown"]

selected_ip = None
latest = None
ip_strategy = None
current_entity = "unknown"
server_name = "N/A"

# --------------------------------------------------
# Existing IP scenario
# --------------------------------------------------
if scenario_mode == "Existing IP":
    ip_list = sorted(pred_df["ip"].dropna().unique())

    if not ip_list:
        st.warning("No IP found in inference predictions.")
        st.stop()

    selected_ip = st.sidebar.selectbox("Select Existing IP", ip_list)

    ip_history = pred_df[pred_df["ip"] == selected_ip].sort_values("datetime_gride").copy()

    if ip_history.empty:
        st.error("No data found for this IP.")
        st.stop()

    latest = ip_history.iloc[-1]
    current_entity = str(latest.get("entity", "unknown"))
    server_name = str(latest.get("server", "N/A"))

    st.sidebar.markdown(f"**Current entity:** `{current_entity}`")
    st.sidebar.markdown(f"**Current server:** `{server_name}`")

    if strategy_df is not None and "ip" in strategy_df.columns:
        match = strategy_df[strategy_df["ip"] == selected_ip]
        if not match.empty:
            ip_strategy = match.iloc[0]

# --------------------------------------------------
# New IP scenario
# --------------------------------------------------
else:
    selected_ip = st.sidebar.text_input("Write New IP", value="new.ip.example")

    latest = pd.Series({
        "sent_per_ip": 0,
        "r_sent_per_ip": 0,
        "sent_ratio": 0.90,
        "predicted_risk_label": "New IP",
        "entity": "New IP",
        "server": "Not assigned",
    })

    current_entity = "New IP"
    server_name = "Not assigned yet"

# --------------------------------------------------
# Header KPIs
# --------------------------------------------------
st.subheader(f"Scenario: {scenario_mode}")

if scenario_mode == "Existing IP":
    st.markdown(
        f"Testing IP **{selected_ip}** from current entity **{current_entity}** "
        "across all available target entities."
    )
else:
    st.markdown(
        f"Testing new IP **{selected_ip}** across all available entities."
    )

c1, c2, c3, c4 = st.columns(4)
c1.metric("Latest Sent", int(latest.get("sent_per_ip", 0)))
c2.metric("Latest R_Sent", int(latest.get("r_sent_per_ip", 0)))
c3.metric("Sent Ratio", round(float(latest.get("sent_ratio", 0)), 3))
c4.metric("Latest Risk", latest.get("predicted_risk_label", "N/A"))

c5, c6, c7, c8 = st.columns(4)
c5.metric("Current Entity", current_entity)
c6.metric("Entities Tested", len(available_entities))
c7.metric("Server", server_name)
c8.metric("Scenario Type", scenario_mode)

# --------------------------------------------------
# Global parameters
# --------------------------------------------------
st.sidebar.header("Plan Parameters")

target_volume = st.sidebar.number_input(
    "Target Cumulative Volume",
    min_value=10000,
    value=1_000_000,
    step=10000
)

max_days = st.sidebar.number_input(
    "Max Days",
    min_value=1,
    max_value=60,
    value=15,
    step=1
)

default_sent_ratio = float(latest.get("sent_ratio", 0.90))

# keep value between 0.10 and 1.00
default_sent_ratio = max(0.10, min(default_sent_ratio, 1.00))

expected_sent_ratio = st.sidebar.number_input(
    "Expected Sent Ratio",
    min_value=0.10,
    max_value=1.00,
    value=default_sent_ratio,
    step=0.01,
    format="%.2f"
)

target_limit_usage_ratio = st.sidebar.number_input(
    "Target Limit Usage Ratio",
    min_value=0.10,
    max_value=1.50,
    value=0.85,
    step=0.01,
    format="%.2f"
)

manual_override = st.sidebar.checkbox("Manual override for detailed entity", value=False)

manual_initial_volume = int(max(latest.get("sent_per_ip", 1000), 1000))
manual_growth_rate = 0.30
manual_max_daily_limit = 150000

if manual_override:
    manual_initial_volume = st.sidebar.number_input(
        "Manual Initial Daily Volume",
        min_value=100,
        value=manual_initial_volume,
        step=100
    )

    manual_growth_rate = st.sidebar.number_input(
        "Manual Max Growth Rate",
        min_value=0.01,
        max_value=1.00,
        value=0.30,
        step=0.01,
        format="%.2f"
    )

    manual_max_daily_limit = st.sidebar.number_input(
        "Manual Maximum Daily Limit",
        min_value=1000,
        value=150000,
        step=1000
    )

# --------------------------------------------------
# Run entity comparison
# --------------------------------------------------
if st.sidebar.button("Compare Entities"):

    plans_by_entity = {}
    summary_rows = []

    for entity_name in available_entities:
        entity_strategy = get_entity_strategy(entity_df, entity_name)

        plan_df, summary = simulate_entity_plan(
            entity_name=entity_name,
            selected_ip=selected_ip,
            scenario_mode=scenario_mode,
            latest=latest,
            ip_strategy=ip_strategy,
            entity_strategy=entity_strategy,
            target_volume=target_volume,
            max_days=max_days,
            manual_initial_volume=manual_initial_volume,
            manual_growth_rate=manual_growth_rate,
            manual_max_daily_limit=manual_max_daily_limit,
            expected_sent_ratio=expected_sent_ratio,
            target_limit_usage_ratio=target_limit_usage_ratio,
            use_manual_values=False,
        )

        plans_by_entity[entity_name] = plan_df
        summary_rows.append(summary)

    comparison_df = pd.DataFrame(summary_rows).sort_values(
        "score",
        ascending=False
    ).reset_index(drop=True)

    st.session_state["entity_comparison_df"] = comparison_df
    st.session_state["plans_by_entity"] = plans_by_entity

# --------------------------------------------------
# Display comparison if available
# --------------------------------------------------
if "entity_comparison_df" in st.session_state and "plans_by_entity" in st.session_state:

    comparison_df = st.session_state["entity_comparison_df"]
    plans_by_entity = st.session_state["plans_by_entity"]

    st.subheader("Entity Comparison Table")

    st.dataframe(comparison_df, use_container_width=True)

    best_entity = comparison_df.iloc[0]["entity"]

    st.success(
        f"Best entity for this scenario: {best_entity}. "
        "It has the best balance between target reaching, safe days, and low error probabilities."
    )

    selected_entity = st.selectbox(
        "Select entity to inspect detailed plan",
        comparison_df["entity"].tolist(),
        index=0
    )

    plan_df = plans_by_entity[selected_entity].copy()

    # If manual override is enabled, regenerate selected entity detail only
    if manual_override:
        entity_strategy = get_entity_strategy(entity_df, selected_entity)

        plan_df, manual_summary = simulate_entity_plan(
            entity_name=selected_entity,
            selected_ip=selected_ip,
            scenario_mode=scenario_mode,
            latest=latest,
            ip_strategy=ip_strategy,
            entity_strategy=entity_strategy,
            target_volume=target_volume,
            max_days=max_days,
            manual_initial_volume=manual_initial_volume,
            manual_growth_rate=manual_growth_rate,
            manual_max_daily_limit=manual_max_daily_limit,
            expected_sent_ratio=expected_sent_ratio,
            target_limit_usage_ratio=target_limit_usage_ratio,
            use_manual_values=True,
        )

        st.info("Manual override is active for the selected detailed entity.")

    final_volume = plan_df["cumulative_volume"].max()
    target_reached = final_volume >= target_volume
    dangerous_days = int((plan_df["risk_zone"] == "Dangerous").sum())
    risk_days = int((plan_df["risk_zone"] == "Risk").sum())
    safe_days = int((plan_df["risk_zone"] == "Safe").sum())

    st.subheader(f"Detailed Strategy for Entity: {selected_entity}")

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Final Cumulative Volume", f"{int(final_volume):,}")
    k2.metric("Target Reached", "Yes" if target_reached else "No")
    k3.metric("Safe Days", safe_days)
    k4.metric("Dangerous Days", dangerous_days)

    # Main plan table
    st.subheader("Adaptive Daily Warm-up Table")

    table_cols = [
        "day",
        "daily_volume",
        "estimated_r_sent",
        "drop_5",
        "drop_10",
        "drop_15",
        "drop_20",
        "recommended_drops_per_day",
        "growth_rate",
        "cumulative_volume",
        "remaining_to_target",
        "estimated_error_probability",
        "spf_probability",
        "dkim_probability",
        "netblock_probability",
        "risk_zone",
        "decision",
    ]

    table_cols = [c for c in table_cols if c in plan_df.columns]
    st.dataframe(plan_df[table_cols], use_container_width=True)

    # Day-by-day explanation
    st.subheader("Best Strategy Day-by-Day Summary")

    strategy_day_summary = plan_df[
        [
            "day",
            "daily_volume",
            "estimated_r_sent",
            "recommended_drops_per_day",
            "growth_rate",
            "cumulative_volume",
            "remaining_to_target",
            "risk_zone",
            "decision",
        ]
    ].copy()

    strategy_day_summary["strategy_explanation"] = strategy_day_summary.apply(
        lambda row: (
            f"Day {int(row['day'])}: send {int(row['daily_volume']):,}, "
            f"expected R_Sent {int(row['estimated_r_sent']):,}, "
            f"use {int(row['recommended_drops_per_day'])} drops/day, "
            f"growth {row['growth_rate']:.2f}, "
            f"cumulative {int(row['cumulative_volume']):,}. "
            f"Risk status: {row['risk_zone']}."
        ),
        axis=1
    )

    st.dataframe(strategy_day_summary, use_container_width=True)

    # Volume graphs
    st.subheader("Daily Volume and Cumulative Volume")
    chart_df = plan_df[["day", "daily_volume", "cumulative_volume"]].set_index("day")
    st.line_chart(chart_df)

    st.subheader("Growth Rate by Day")
    growth_chart = plan_df[["day", "growth_rate"]].set_index("day")
    st.line_chart(growth_chart)

    # Risk zone lifecycle graph
    st.subheader("IP Lifecycle Through Risk Zones")

    risk_visual = plan_df.copy()
    risk_visual["safe_zone"] = risk_visual["risk_zone"].apply(lambda x: 1 if x == "Safe" else 0)
    risk_visual["risk_zone_score"] = risk_visual["risk_zone"].apply(lambda x: 1 if x == "Risk" else 0)
    risk_visual["dangerous_zone"] = risk_visual["risk_zone"].apply(lambda x: 1 if x == "Dangerous" else 0)

    zone_chart = risk_visual[
        ["day", "safe_zone", "risk_zone_score", "dangerous_zone"]
    ].set_index("day")

    st.line_chart(zone_chart)
    st.caption("This graph shows the daily state of the IP: Safe, Risk, or Dangerous.")

    # Error type probability graph
    st.subheader("Error Type Probability Evolution")

    error_chart = plan_df[
        ["day", "spf_probability", "dkim_probability", "netblock_probability"]
    ].set_index("day")

    st.line_chart(error_chart)

    # AI error cause analysis
    st.subheader("AI Error Cause Analysis")

    analysis_df = build_error_cause_table(plan_df)
    st.dataframe(analysis_df, use_container_width=True)

    # Risk evolution graph
    st.subheader("Risk Evolution")

    risk_map = {"Safe": 0, "Risk": 1, "Dangerous": 2}
    plan_df["risk_code"] = plan_df["risk_zone"].map(risk_map)

    risk_chart = plan_df[
        ["day", "risk_code", "estimated_error_probability"]
    ].set_index("day")

    st.line_chart(risk_chart)
    st.caption("Risk code: 0 = Safe, 1 = Risk, 2 = Dangerous.")

    # Final recommendation
    st.subheader("Final Scenario Recommendation")

    if not target_reached:
        st.warning(
            "The plan does not reach the target within the selected duration. "
            "Increase max days, increase allowed growth rate, or increase max daily limit."
        )
    elif dangerous_days > 0:
        st.error(
            f"The target is reached, but the plan enters Dangerous zone in entity {selected_entity}. "
            "This entity/strategy is not recommended unless parameters are reduced."
        )
    elif risk_days > 0:
        st.warning(
            f"The target is reached in entity {selected_entity}, but with some Risk days. "
            "Use this strategy carefully and monitor SPF/DKIM/Netblock probabilities."
        )
    else:
        st.success(
            f"The target is reached safely in entity {selected_entity}. "
            "This is the safest recommended strategy for this scenario."
        )

else:
    st.info("Choose Existing IP or New IP, then click Compare Entities.")
