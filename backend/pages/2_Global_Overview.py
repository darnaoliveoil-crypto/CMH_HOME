import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from utils.data_loader import load_inference_predictions

st.set_page_config(page_title="Global Overview", layout="wide")

st.title("Global Overview Dashboard")

if st.button("Refresh data"):
    st.cache_data.clear()
    st.rerun()

df = load_inference_predictions()

if df is None:
    st.warning("No inference predictions found. Run Dashboard 1 pipeline first.")
    st.stop()

df["datetime_gride"] = pd.to_datetime(df["datetime_gride"], errors="coerce")
df = df.dropna(subset=["ip", "datetime_gride"])

# ----------------------------
# Filters
# ----------------------------
st.sidebar.header("Filters")

server_options = ["All"] + sorted(df["server"].dropna().unique().tolist())
selected_server = st.sidebar.selectbox("Filter by Server", server_options)

error_options = ["All", "SPF", "DKIM", "Netblock"]
selected_error = st.sidebar.selectbox("Filter by Error Type", error_options)

if selected_server != "All":
    df = df[df["server"] == selected_server]

# Create error type from highest probability
def detect_error_type(row):
    probs = {
        "SPF": row.get("spf_error_probability", 0),
        "DKIM": row.get("dkim_error_probability", 0),
        "Netblock": row.get("netblock_error_probability", 0),
    }
    best_error = max(probs, key=probs.get)
    if probs[best_error] <= 0:
        return "No Error"
    return best_error

df["predicted_error_type"] = df.apply(detect_error_type, axis=1)

if selected_error != "All":
    df = df[df["predicted_error_type"] == selected_error]

latest_ip = (
    df.sort_values("datetime_gride")
    .groupby("ip", as_index=False)
    .tail(1)
)

# ----------------------------
# KPIs
# ----------------------------
total_ips = latest_ip["ip"].nunique()
safe_ips = (latest_ip["predicted_risk_label"] == "Safe").sum()
risk_ips = (latest_ip["predicted_risk_label"] == "Risk").sum()
dangerous_ips = (latest_ip["predicted_risk_label"] == "Dangerous").sum()

blocked_ips = (
    (latest_ip["netblock_error_probability"] > 0.5)
    | (latest_ip.get("predicted_netblock_error", 0) == 1)
).sum()

avg_sent_ratio = round(latest_ip["sent_ratio"].mean(), 3)
avg_rsent = int(latest_ip["r_sent_per_ip"].mean()) if "r_sent_per_ip" in latest_ip.columns else 0
avg_growth = round(latest_ip["growth_rate"].mean(), 3)

global_error_rate = round(
    (
        (df["spf_error_probability"] > 0.1)
        | (df["dkim_error_probability"] > 0.1)
        | (df["netblock_error_probability"] > 0.1)
    ).mean(),
    3
)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total IPs", total_ips)
c2.metric("Safe IPs", safe_ips)
c3.metric("Risk IPs", risk_ips)
c4.metric("Dangerous IPs", dangerous_ips)

c5, c6, c7, c8 = st.columns(4)
c5.metric("Blocked IPs", int(blocked_ips))
c6.metric("Avg R_Sent", f"{avg_rsent:,}")
c7.metric("Avg Sent Ratio", avg_sent_ratio)
c8.metric("Global Error Rate", global_error_rate)

st.divider()

# ----------------------------
# Risk distribution
# ----------------------------
st.subheader("Risk Distribution by Latest IP Status")

risk_dist = latest_ip["predicted_risk_label"].value_counts().reset_index()
risk_dist.columns = ["Risk Label", "Count"]
st.bar_chart(risk_dist.set_index("Risk Label"))

# ----------------------------
# Daily Global R_Sent Volume
# ----------------------------
st.subheader("Daily Global R_Sent Volume")

daily_rsent = (
    df.groupby(df["datetime_gride"].dt.date)["r_sent_per_ip"]
    .sum()
    .reset_index()
)
daily_rsent.columns = ["Date", "Total R_Sent"]
st.line_chart(daily_rsent.set_index("Date"))

# ----------------------------
# Most frequent errors
# ----------------------------
st.subheader("Most Frequent Errors")

error_freq = pd.DataFrame({
    "Error Type": ["SPF", "DKIM", "Netblock"],
    "Frequency": [
        (df["spf_error_probability"] > 0.1).sum(),
        (df["dkim_error_probability"] > 0.1).sum(),
        (df["netblock_error_probability"] > 0.1).sum(),
    ]
})

st.bar_chart(error_freq.set_index("Error Type"))

# ----------------------------
# Error frequency vs R_Sent
# ----------------------------
st.subheader("Error Frequency vs R_Sent")

scatter_df = df.copy()
scatter_df["error_frequency"] = (
    (scatter_df["spf_error_probability"] > 0.1).astype(int)
    + (scatter_df["dkim_error_probability"] > 0.1).astype(int)
    + (scatter_df["netblock_error_probability"] > 0.1).astype(int)
)

scatter_df = scatter_df[["r_sent_per_ip", "error_frequency", "predicted_error_type"]].copy()
scatter_df["r_sent_per_ip"] = pd.to_numeric(scatter_df["r_sent_per_ip"], errors="coerce")
scatter_df["error_frequency"] = pd.to_numeric(scatter_df["error_frequency"], errors="coerce")

st.scatter_chart(
    scatter_df,
    x="r_sent_per_ip",
    y="error_frequency",
    color="predicted_error_type"
)

# ----------------------------
# Error activity heatmap by hour
# ----------------------------
st.subheader("Error Activity Heatmap by Hour of Day")

df["hour"] = df["datetime_gride"].dt.hour
df["date"] = df["datetime_gride"].dt.date

df["has_error"] = (
    (df["spf_error_probability"] > 0.1)
    | (df["dkim_error_probability"] > 0.1)
    | (df["netblock_error_probability"] > 0.1)
).astype(int)

heatmap_data = (
    df.groupby(["date", "hour"])["has_error"]
    .sum()
    .reset_index()
)

heatmap_pivot = heatmap_data.pivot(index="date", columns="hour", values="has_error").fillna(0)

st.dataframe(
    heatmap_pivot.style.background_gradient(cmap="Reds"),
    use_container_width=True
)

# ----------------------------
# Risk transition analysis
# ----------------------------
st.subheader("Risk Transition Analysis")

transition_df = df.sort_values(["ip", "datetime_gride"]).copy()
transition_df["previous_risk"] = transition_df.groupby("ip")["predicted_risk_label"].shift(1)
transition_df["current_risk"] = transition_df["predicted_risk_label"]

transitions = transition_df.dropna(subset=["previous_risk"])

transition_table = (
    transitions.groupby(["previous_risk", "current_risk"])
    .size()
    .reset_index(name="Count")
)

labels = sorted(
    list(set(transition_table["previous_risk"].tolist() + transition_table["current_risk"].tolist()))
)

label_index = {label: i for i, label in enumerate(labels)}

fig = go.Figure(data=[go.Sankey(
    node=dict(
        pad=20,
        thickness=20,
        label=labels,
    ),
    link=dict(
        source=transition_table["previous_risk"].map(label_index),
        target=transition_table["current_risk"].map(label_index),
        value=transition_table["Count"],
    )
)])

fig.update_layout(
    title_text="Risk Status Transitions Between Consecutive IP Events",
    height=500
)

st.plotly_chart(fig, use_container_width=True)

with st.expander("Transition Table"):
    st.dataframe(transition_table, use_container_width=True)

# ----------------------------
# Top dangerous / blocked IPs
# ----------------------------
st.subheader("Top Dangerous or Blocked IPs")

top_dangerous = latest_ip[
    (latest_ip["predicted_risk_label"] == "Dangerous")
    | (latest_ip["netblock_error_probability"] > 0.5)
].copy()

if top_dangerous.empty:
    st.success("No dangerous or blocked IPs detected in the latest status.")
else:
    top_dangerous = top_dangerous.sort_values(
        ["netblock_error_probability", "r_sent_per_ip"],
        ascending=False
    )

    cols = [
        "ip",
        "server",
        "datetime_gride",
        "predicted_risk_label",
        "predicted_error_type",
        "r_sent_per_ip",
        "sent_ratio",
        "growth_rate",
        "spf_error_probability",
        "dkim_error_probability",
        "netblock_error_probability",
    ]

    cols = [c for c in cols if c in top_dangerous.columns]

    st.dataframe(top_dangerous[cols].head(20), use_container_width=True)

# ----------------------------
# Latest IP status
# ----------------------------
st.subheader("Latest IP Status Table")

cols = [
    "ip",
    "server",
    "datetime_gride",
    "predicted_risk_label",
    "predicted_error_type",
    "r_sent_per_ip",
    "sent_ratio",
    "growth_rate",
    "netblock_error_probability",
]

cols = [c for c in cols if c in latest_ip.columns]

st.dataframe(latest_ip[cols], use_container_width=True)