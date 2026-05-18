from fastapi import APIRouter
from api.data_service import get_df_ml

router = APIRouter()


@router.get("/kpis")
def get_overview_kpis():

    df = get_df_ml()

    if not df:
        return {"error": "No data found"}

    total_ips = len(set(row["ip"] for row in df))

    safe_ips = len(set(
        row["ip"]
        for row in df
        if row["risk_label"] == "Safe"
    ))

    risk_ips = len(set(
        row["ip"]
        for row in df
        if row["risk_label"] == "Risk"
    ))

    dangerous_ips = len(set(
        row["ip"]
        for row in df
        if row["risk_label"] == "Dangerous"
    ))

    blocked_ips = len(set(
        row["ip"]
        for row in df
        if row["blocked_before"] == 1
    ))

    avg_r_sent = round(
        sum(row["r_sent_per_ip"] for row in df) / len(df),
        2
    )

    avg_sent_ratio = round(
        sum(row["sent_ratio"] for row in df) / len(df),
        3
    )

    global_error_rate = round(
        1 - avg_sent_ratio,
        3
    )

    return {
        "total_ips": total_ips,
        "safe_ips": safe_ips,
        "risk_ips": risk_ips,
        "dangerous_ips": dangerous_ips,
        "blocked_ips": blocked_ips,
        "avg_r_sent": avg_r_sent,
        "avg_sent_ratio": avg_sent_ratio,
        "global_error_rate": global_error_rate
    }