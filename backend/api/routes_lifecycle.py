from fastapi import APIRouter
from api.data_service import get_df_ml

router = APIRouter()


# =========================================================
# 1. Get all IPs
# =========================================================
@router.get("/ips")
def get_all_ips():

    df = get_df_ml()

    ips = sorted(list(set(row["ip"] for row in df)))

    return {
        "total_ips": len(ips),
        "ips": ips
    }


# =========================================================
# 2. Lifecycle KPIs for one IP
# =========================================================
@router.get("/{ip}/kpis")
def get_ip_kpis(ip: str):

    df = get_df_ml()

    ip_data = [row for row in df if row["ip"] == ip]

    if not ip_data:
        return {"error": "IP not found"}

    latest = ip_data[-1]

    total_cumulative_rsent = max(
        row["cumulative_r_sent_per_ip"]
        for row in ip_data
    )

    avg_r_sent = round(
        sum(row["r_sent_per_ip"] for row in ip_data) / len(ip_data),
        2
    )

    avg_sent_ratio = round(
        sum(row["sent_ratio"] for row in ip_data) / len(ip_data),
        3
    )

    avg_growth_rate = round(
        sum(row["growth_rate"] for row in ip_data) / len(ip_data),
        3
    )

    avg_drops_per_day = round(
        sum(row["drops_per_day"] for row in ip_data) / len(ip_data),
        2
    )

    max_drops_per_day = max(
        row["drops_per_day"]
        for row in ip_data
    )

    active_days = max(
        row["days_since_launch"]
        for row in ip_data
    )

    return {

        "ip": ip,

        "server": latest["server"],
        "entity": latest["entity"],

        "lifecycle_status": latest["risk_label"],

        "active_days": active_days,

        "total_cumulative_r_sent": total_cumulative_rsent,

        "avg_r_sent": avg_r_sent,

        "avg_sent_ratio": avg_sent_ratio,

        "avg_growth_rate": avg_growth_rate,

        "avg_drops_per_day": avg_drops_per_day,

        "max_drops_per_day": max_drops_per_day
    }


# =========================================================
# 3. Error timeline
# =========================================================
@router.get("/{ip}/errors")
def get_ip_errors(ip: str):

    df = get_df_ml()

    ip_errors = [
        {
            "datetime": row["datetime_gride"],
            "error_type": (
                "SPF" if row["spf_error"] == 1 else
                "DKIM" if row["dkim_error"] == 1 else
                "Netblock" if row["netblock_error"] == 1 else
                "No error"
            ),
            "sent_per_ip": row["sent_per_ip"],
            "r_sent_per_ip": row["r_sent_per_ip"],
            "sent_ratio": row["sent_ratio"],
            "risk_label": row["risk_label"]
        }
        for row in df
        if row["ip"] == ip and row["error_flag"] == 1
    ]

    return {
        "ip": ip,
        "total_errors": len(ip_errors),
        "errors": ip_errors
    }


# =========================================================
# 4. Full IP history
# =========================================================
@router.get("/{ip}/history")
def get_ip_history(ip: str):

    df = get_df_ml()

    history = [
        row
        for row in df
        if row["ip"] == ip
    ]

    return {
        "ip": ip,
        "total_events": len(history),
        "history": history
    }