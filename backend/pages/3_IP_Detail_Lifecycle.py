import streamlit as st
import pandas as pd
import numpy as np

from utils.data_loader import load_ip_analyse, load_inference_predictions, load_warmup_plan

st.set_page_config(page_title="IP Detail & Lifecycle", layout="wide")

st.title("IP Detail & Lifecycle Analysis")

ip_data = load_ip_analyse()
pred_data = load_inference_predictions()
warmup_plan = load_warmup_plan()

if ip_data is None or pred_data is None:
    st.warning("Missing data. Run Dashboard 1 pipeline first.")
    st.stop()

ip_data["datetime_gride"] = pd.to_datetime(ip_data["datetime_gride"], errors="coerce")
pred_data["datetime_gride"] = pd.to_datetime(pred_data["datetime_gride"], errors="coerce")

ip_data["entity"] = ip_data["server"].astype(str).str.extract(r"s_(cmh\d+)")
pred_data["entity"] = pred_data["server"].astype(str).str.extract(r"s_(cmh\d+)")

# -----------------------------
# Sidebar filters
# -----------------------------
st.sidebar.header("Filters")

entities = ["All"] + sorted(ip_data["entity"].dropna().unique().tolist())
selected_entity = st.sidebar.selectbox("Entity", entities)

filtered_data = ip_data.copy()

if selected_entity != "All":
    filtered_data = filtered_data[filtered_data["entity"] == selected_entity]

servers = ["All"] + sorted(filtered_data["server"].dropna().unique().tolist())
selected_server = st.sidebar.selectbox("Server", servers)

if selected_server != "All":
    filtered_data = filtered_data[filtered_data["server"] == selected_server]

years = sorted(filtered_data["datetime_gride"].dt.year.dropna().unique())
selected_year = st.sidebar.selectbox("Year", years)

filtered_data = filtered_data[filtered_data["datetime_gride"].dt.year == selected_year]

months = sorted(filtered_data["datetime_gride"].dt.month.dropna().unique())
selected_month = st.sidebar.selectbox("Month", months)

filtered_data = filtered_data[filtered_data["datetime_gride"].dt.month == selected_month]

days = sorted(filtered_data["datetime_gride"].dt.day.dropna().unique())
selected_day = st.sidebar.selectbox("Day", days)

filtered_data = filtered_data[filtered_data["datetime_gride"].dt.day == selected_day]

ips = sorted(filtered_data["ip"].dropna().unique())

if not ips:
    st.warning("No IP found for selected filters.")
    st.stop()

selected_ip = st.selectbox("Select IP", ips)

manual_ip = st.text_input("Or manually enter IP")
if manual_ip.strip():
    selected_ip = manual_ip.strip()

# Important: lifecycle should use full history of this IP, not only selected day
df_ip = ip_data[ip_data["ip"] == selected_ip].copy()
pred_ip = pred_data[pred_data["ip"] == selected_ip].copy()

if selected_server != "All":
    df_ip = df_ip[df_ip["server"] == selected_server]
    pred_ip = pred_ip[pred_ip["server"] == selected_server]

if df_ip.empty:
    st.error("IP not found.")
    st.stop()

df_ip = df_ip.sort_values("datetime_gride")
pred_ip = pred_ip.sort_values("datetime_gride")

# -----------------------------
# Clean / enrich features
# -----------------------------
df_ip["date"] = df_ip["datetime_gride"].dt.date
df_ip["time_gap_min_calc"] = df_ip["datetime_gride"].diff().dt.total_seconds().div(60)

if "time_gap_min" not in df_ip.columns:
    df_ip["time_gap_min"] = df_ip["time_gap_min_calc"]
else:
    df_ip["time_gap_min"] = pd.to_numeric(df_ip["time_gap_min"], errors="coerce").fillna(df_ip["time_gap_min_calc"])

df_ip["sent_per_ip"] = pd.to_numeric(df_ip["sent_per_ip"], errors="coerce").fillna(0)
df_ip["r_sent_per_ip"] = pd.to_numeric(df_ip["r_sent_per_ip"], errors="coerce").fillna(0)
df_ip["growth_rate"] = pd.to_numeric(df_ip["growth_rate"], errors="coerce").fillna(0)
df_ip["drops_per_day"] = pd.to_numeric(df_ip.get("drops_per_day", 0), errors="coerce").fillna(0)

if "predicted_risk_label_encoded" in pred_ip.columns:
    pred_ip["predicted_risk_label_encoded"] = pd.to_numeric(
        pred_ip["predicted_risk_label_encoded"], errors="coerce"
    ).fillna(0)

# Remove useless close connection errors
noise_patterns = ["close connection", "closed connection", "connection closed"]
error_mask = df_ip["error_type_from_error"].astype(str).str.lower().apply(
    lambda x: x != "no error" and not any(p in x for p in noise_patterns)
)
errors = df_ip[error_mask][
    ["datetime_gride", "error_type_from_error", "sent_per_ip", "r_sent_per_ip"]
].copy()

first_row = df_ip.iloc[0]
latest_row = df_ip.iloc[-1]
latest_pred = pred_ip.iloc[-1] if not pred_ip.empty else None

active_days = df_ip["datetime_gride"].dt.date.nunique()
total_rsent_volume = df_ip["r_sent_per_ip"].sum()
total_sent_volume = df_ip["sent_per_ip"].sum()

avg_sent_ratio = total_rsent_volume / total_sent_volume if total_sent_volume > 0 else 0
avg_growth = df_ip["growth_rate"].mean()
avg_rsent = df_ip["r_sent_per_ip"].mean()
avg_time_gap = df_ip["time_gap_min"].mean()
avg_drops = df_ip["drops_per_day"].mean()
max_drops = df_ip["drops_per_day"].max()

max_sent_idx = df_ip["sent_per_ip"].idxmax()
min_sent_idx = df_ip["sent_per_ip"].idxmin()

max_sent_row = df_ip.loc[max_sent_idx]
min_sent_row = df_ip.loc[min_sent_idx]

max_volume = max_sent_row["sent_per_ip"]
max_volume_rsent = max_sent_row["r_sent_per_ip"]

min_volume = min_sent_row["sent_per_ip"]
min_volume_rsent = min_sent_row["r_sent_per_ip"]

last_sent = latest_row["sent_per_ip"]
last_rsent = latest_row["r_sent_per_ip"]

netblock_count = (df_ip["error_type_from_error"] == "Rate limit IP Netblock").sum()
error_count = len(errors)

risk_periods = 0
dangerous_periods = 0

if not pred_ip.empty and "predicted_risk_label" in pred_ip.columns:
    risk_periods = (pred_ip["predicted_risk_label"] == "Risk").sum()
    dangerous_periods = (pred_ip["predicted_risk_label"] == "Dangerous").sum()

def classify_lifecycle(active_days, error_count, netblock_count, avg_sent_ratio, avg_growth, dangerous_periods):
    if netblock_count > 0 or dangerous_periods > 0:
        return "Blocked/Risky IP"
    if active_days <= 1:
        return "New IP"
    if error_count > 5:
        return "Risky IP"
    if active_days <= 15 and avg_sent_ratio >= 0.7:
        return "Warming IP"
    if avg_sent_ratio >= 0.85 and avg_growth < 0.4:
        return "Stable IP"
    if avg_growth < 0:
        return "Cooling IP"
    return "Warming IP"

lifecycle_status = classify_lifecycle(
    active_days, error_count, netblock_count, avg_sent_ratio, avg_growth, dangerous_periods
)

# -----------------------------
# Information
# -----------------------------
st.subheader("IP Information")

server_list = ", ".join(sorted(df_ip["server"].dropna().unique()))
entity_list = ", ".join(sorted(df_ip["entity"].dropna().unique()))

st.markdown(f"**Server(s):** {server_list}")
st.markdown(f"**Entity:** {entity_list}")

st.caption("Risk prediction key: 0 = Safe | 1 = Risk | 2 = Dangerous")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Lifecycle Status", lifecycle_status)
c2.metric("Active Days", active_days)
c3.metric("Total Cumulative R_Sent", f"{int(total_rsent_volume):,}")
c4.metric("Avg R_Sent", f"{int(avg_rsent):,}")

c5, c6, c7, c8 = st.columns(4)
c5.metric("Avg Sent Ratio", round(avg_sent_ratio, 3))
c6.metric("Avg Growth Rate", round(avg_growth, 3))
c7.metric("Risk Periods", int(risk_periods))
c8.metric("Dangerous Periods", int(dangerous_periods))

c9, c10, c11, c12 = st.columns(4)
c9.metric("Avg Time Gap (min)", round(avg_time_gap, 2) if pd.notna(avg_time_gap) else 0)
c10.metric("Avg Drops/Day", round(avg_drops, 2))
c11.metric("Max Drops/Day", int(max_drops))
c12.metric("Errors Count", int(error_count))

st.divider()

# -----------------------------
# Max / Min / Latest volume quality
# -----------------------------
st.subheader("Volume Quality Check")

v1, v2, v3 = st.columns(3)

with v1:
    st.markdown("### Max Sent Volume")
    st.write("Sent:", int(max_volume))
    st.write("R_Sent:", int(max_volume_rsent))
    ratio = max_volume_rsent / max_volume if max_volume > 0 else 0
    st.write("Success Ratio:", round(ratio, 3))

with v2:
    st.markdown("### Min Sent Volume")
    st.write("Sent:", int(min_volume))
    st.write("R_Sent:", int(min_volume_rsent))
    ratio = min_volume_rsent / min_volume if min_volume > 0 else 0
    st.write("Success Ratio:", round(ratio, 3))

with v3:
    st.markdown("### Latest Sent Volume")
    st.write("Sent:", int(last_sent))
    st.write("R_Sent:", int(last_rsent))
    ratio = last_rsent / last_sent if last_sent > 0 else 0
    st.write("Success Ratio:", round(ratio, 3))

st.divider()

# -----------------------------
# First / latest launch
# -----------------------------
st.subheader("First & Latest Launch Information")

info_col1, info_col2 = st.columns(2)

with info_col1:
    st.markdown("### First Launch")
    st.write("First Date:", first_row["datetime_gride"])
    st.write("First Sent:", int(first_row["sent_per_ip"]))
    st.write("First R_Sent:", int(first_row["r_sent_per_ip"]))
    st.write("First Error:", first_row["error_type_from_error"])

with info_col2:
    st.markdown("### Latest Launch")
    st.write("Latest Date:", latest_row["datetime_gride"])
    st.write("Latest Sent:", int(latest_row["sent_per_ip"]))
    st.write("Latest R_Sent:", int(latest_row["r_sent_per_ip"]))
    st.write("Latest Error:", latest_row["error_type_from_error"])

    if latest_pred is not None:
        st.write("Predicted Risk:", latest_pred.get("predicted_risk_label", "N/A"))
        st.write("Risk Code:", latest_pred.get("predicted_risk_label_encoded", "N/A"))
        st.write("Netblock Probability:", latest_pred.get("netblock_error_probability", 0))

st.divider()

# -----------------------------
# Graphs
# -----------------------------
st.subheader("Sent vs Successful Sent")
sent_chart = df_ip[["datetime_gride", "sent_per_ip", "r_sent_per_ip"]].set_index("datetime_gride")
st.line_chart(sent_chart)

st.subheader("Cumulative R_Sent Volume Evolution")
df_ip["cumulative_r_sent_per_ip"] = df_ip["r_sent_per_ip"].cumsum()
cum_df = df_ip[["datetime_gride", "cumulative_r_sent_per_ip"]].set_index("datetime_gride")
st.line_chart(cum_df)

st.subheader("Growth Rate Evolution")
growth_chart = df_ip[["datetime_gride", "growth_rate"]].set_index("datetime_gride")
st.line_chart(growth_chart)

st.subheader("Time Gap Evolution")
time_gap_chart = df_ip[["datetime_gride", "time_gap_min"]].set_index("datetime_gride")
st.line_chart(time_gap_chart)

st.subheader("Drop Activity")
drop_activity = (
    df_ip.groupby("date")
    .agg(
        drops=("campaign_id", "count"),
        daily_r_sent=("r_sent_per_ip", "sum"),
        max_growth_rate=("growth_rate", "max"),
        cumulative_r_sent=("r_sent_per_ip", "sum"),
    )
    .reset_index()
)

drop_activity["cumulative_r_sent"] = drop_activity["daily_r_sent"].cumsum()

st.dataframe(drop_activity, use_container_width=True)
st.line_chart(drop_activity.set_index("date")[["drops", "daily_r_sent"]])

st.subheader("Error Timeline")

if errors.empty:
    st.success("No relevant errors found for this IP after excluding close connection noise.")
else:
    st.dataframe(errors, use_container_width=True)

st.subheader("Risk Zone Evolution")

if pred_ip.empty:
    st.warning("No prediction data found for this IP.")
else:
    risk_timeline = pred_ip[["datetime_gride", "predicted_risk_label_encoded"]].copy()
    risk_timeline = risk_timeline.set_index("datetime_gride")
    st.line_chart(risk_timeline)

    st.caption("0 = Safe, 1 = Risk, 2 = Dangerous")

st.subheader("Actual Path vs Ideal Path")

actual_path = df_ip[["datetime_gride", "r_sent_per_ip", "growth_rate", "time_gap_min", "drops_per_day"]].copy()
actual_path = actual_path.sort_values("datetime_gride")
actual_path["step"] = range(1, len(actual_path) + 1)

actual_path["Actual Path"] = actual_path["r_sent_per_ip"].cumsum()

target_final = actual_path["Actual Path"].iloc[-1]
start_value = actual_path["Actual Path"].iloc[0]

ideal_values = np.linspace(start_value, target_final, len(actual_path))
actual_path["Ideal Path"] = ideal_values

actual_path["gap"] = actual_path["Actual Path"] - actual_path["Ideal Path"]
actual_path["gap_abs"] = actual_path["gap"].abs()

path_chart = actual_path[["step", "Actual Path", "Ideal Path"]].set_index("step")
st.line_chart(path_chart)

avg_growth_ip = actual_path["growth_rate"].mean()
max_growth_ip = actual_path["growth_rate"].max()
avg_time_gap_ip = actual_path["time_gap_min"].mean()
avg_drops_ip = actual_path["drops_per_day"].mean()

actual_path["gap_ratio"] = actual_path["gap"] / target_final if target_final > 0 else 0

max_positive_gap = actual_path["gap_ratio"].max()
max_negative_gap = actual_path["gap_ratio"].min()
avg_abs_gap = actual_path["gap_ratio"].abs().mean()

biggest_gap_row = actual_path.loc[actual_path["gap_abs"].idxmax()]
biggest_gap_step = int(biggest_gap_row["step"])
biggest_gap_value = int(biggest_gap_row["gap"])

if avg_abs_gap > 0.25:
    stability_level = "far from the ideal path"
elif avg_abs_gap > 0.10:
    stability_level = "moderately different from the ideal path"
else:
    stability_level = "close to the ideal path"

if max_positive_gap > 0.15:
    path_behavior = (
        "The actual path is above the ideal path during part of the lifecycle. "
        "This means the IP sent volume faster than the smooth recommended rhythm."
    )
elif max_negative_gap < -0.15:
    path_behavior = (
        "The actual path is below the ideal path during part of the lifecycle. "
        "This means the IP progressed slower than the recommended rhythm."
    )
else:
    path_behavior = (
        "The actual path stays relatively close to the ideal curve, "
        "but small differences still exist during the lifecycle."
    )

specific_causes = []

if max_growth_ip > 0.5:
    specific_causes.append("strong growth spikes")

if avg_growth_ip < 0.05:
    specific_causes.append("low average growth")

if avg_time_gap_ip < 30:
    specific_causes.append("short time gaps between drops")

if avg_drops_ip > 15:
    specific_causes.append("high drop frequency")

if avg_sent_ratio < 0.7:
    specific_causes.append("weak sent ratio")

if risk_periods > 0:
    specific_causes.append("risk periods detected")

if dangerous_periods > 0:
    specific_causes.append("dangerous periods detected")

if not specific_causes:
    specific_causes.append("minor natural variation in sending behavior")

global_interpretation = (
    f"For IP {selected_ip}, the actual path is {stability_level}. "
    f"{path_behavior} "
    f"The biggest deviation appears around step {biggest_gap_step}, "
    f"with a gap of {biggest_gap_value:,} R_Sent compared to the ideal path. "
    f"Main detected causes: {', '.join(specific_causes)}."
)

st.info(global_interpretation)
st.subheader("Why Actual Path Is Different From Ideal Path")

explanation_df = pd.DataFrame({
    "Indicator": [
        "Average Growth Rate",
        "Maximum Growth Rate",
        "Average Time Gap",
        "Average Drops/Day",
        "Average Sent Ratio",
        "Risk Periods",
        "Dangerous Periods",
    ],
    "Value": [
        round(avg_growth_ip, 4),
        round(max_growth_ip, 4),
        round(avg_time_gap_ip, 2),
        round(avg_drops_ip, 2),
        round(avg_sent_ratio, 3),
        int(risk_periods),
        int(dangerous_periods),
    ],
    "Interpretation": [
        "Shows general speed of volume increase",
        "Detects sudden aggressive jumps",
        "Shows spacing between drops",
        "Shows sending pressure per day",
        "Measures successful delivery quality",
        "Periods where AI detected instability",
        "Periods where AI detected high blocking risk",
    ]
})

st.dataframe(explanation_df, use_container_width=True)

st.subheader("AI Path Recommendation")

recommendation_text = (
    "Main causes detected: " + ", ".join(specific_causes) + ". "
    "To move closer to the ideal path, the IP should increase volume progressively, "
    "avoid sudden growth jumps, keep enough time between drops, maintain a strong sent ratio, "
    "and reduce pressure when Risk or Dangerous periods appear."
)
st.warning(recommendation_text)

useful_cols = [
    "datetime_gride",
    "server",
    "entity",
    "sent_per_ip",
    "r_sent_per_ip",
    "growth_rate",
    "time_gap_min",
    "drops_per_day",
    "error_type_from_error",
    "cumulative_r_sent_per_ip",
]

useful_cols = [c for c in useful_cols if c in df_ip.columns]

st.dataframe(df_ip[useful_cols], use_container_width=True)