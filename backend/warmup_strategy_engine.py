from pathlib import Path
import pandas as pd
import numpy as np

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
PROCESSED_DIR = DATA_DIR / "processed"
OUTPUTS_DIR = BASE_DIR / "outputs"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_TARGET_VOLUME = 1_000_000
DEFAULT_MAX_DAYS = 15

OUTPUT_PLAN_PATH = PROCESSED_DIR / "warmup_strategy_plan.csv"
OUTPUT_SUMMARY_PATH = OUTPUTS_DIR / "warmup_strategy_summary.csv"


def classify_zone(limit_usage_ratio, growth_rate, volume_per_drop, error_probability):
    if error_probability >= 0.50 or limit_usage_ratio > 1.00 or growth_rate > 0.60:
        return "Dangerous"
    if error_probability >= 0.20 or limit_usage_ratio > 0.90 or growth_rate > 0.35:
        return "Risk"
    if volume_per_drop > 10000:
        return "Risk"
    return "Safe"


def generate_daily_plan(
    initial_volume,
    growth_rate,
    drops_per_day=20,
    target_volume=DEFAULT_TARGET_VOLUME,
    max_days=DEFAULT_MAX_DAYS,
    max_daily_limit=None,
    expected_sent_ratio=0.90,
    target_limit_usage_ratio=0.85,
    plan_type="Adaptive Safe AI",
):
    rows = []

    if max_daily_limit is None:
        max_daily_limit = max(target_volume / max_days * 2, initial_volume * 10, 1)

    safe_daily_limit = int(max_daily_limit * target_limit_usage_ratio)

    # Build smooth progressive volumes over all days
    raw_volumes = []
    current_volume = initial_volume

    for day in range(1, int(max_days) + 1):
        if day == 1:
            daily_volume = int(initial_volume)
            real_growth = 0
        else:
            # progressive but controlled growth
            real_growth = min(0.20 + (day / max_days) * 0.10, growth_rate)
            daily_volume = int(current_volume * (1 + real_growth))

        daily_volume = min(daily_volume, safe_daily_limit)
        raw_volumes.append(max(daily_volume, 1))
        current_volume = daily_volume

    # Rescale volumes so cumulative reaches target on final day
    total_raw = sum(raw_volumes)
    scale_factor = target_volume / total_raw if total_raw > 0 else 1

    daily_volumes = [int(v * scale_factor) for v in raw_volumes]

    # Adjust last day to reach exactly target
    diff = target_volume - sum(daily_volumes)
    daily_volumes[-1] += diff

    cumulative_volume = 0
    previous_volume = None

    for day, daily_volume in enumerate(daily_volumes, start=1):

        daily_volume = max(int(daily_volume), 0)

        if previous_volume is None or previous_volume == 0:
            real_growth = 0
        else:
            real_growth = (daily_volume - previous_volume) / previous_volume

        cumulative_volume += daily_volume

        # Choose safe drops dynamically
        if daily_volume <= 10000:
            adaptive_drops = 5
        elif daily_volume <= 30000:
            adaptive_drops = 10
        elif daily_volume <= 70000:
            adaptive_drops = 15
        else:
            adaptive_drops = 20

        volume_per_drop = daily_volume / adaptive_drops if adaptive_drops > 0 else daily_volume
        limit_usage_ratio = daily_volume / max_daily_limit if max_daily_limit > 0 else 0

        estimated_error_probability = min(
            0.02
            + max(real_growth, 0) * 0.25
            + max(limit_usage_ratio - target_limit_usage_ratio, 0) * 0.70
            + max(volume_per_drop - 10000, 0) / 80000
            + max(0.85 - expected_sent_ratio, 0) * 0.60,
            0.99,
        )

        risk_zone = classify_zone(
            limit_usage_ratio=limit_usage_ratio,
            growth_rate=real_growth,
            volume_per_drop=volume_per_drop,
            error_probability=estimated_error_probability,
        )

        if risk_zone == "Dangerous":
            decision = "Unsafe. Increase max days or reduce target volume."
        elif risk_zone == "Risk":
            decision = "Monitor carefully. Keep 20 drops/day and avoid faster growth."
        elif cumulative_volume >= target_volume:
            decision = "Target reached on final warm-up path. Stabilize volume."
        else:
            decision = "Continue safe progressive warm-up."

        rows.append({
            "plan_type": plan_type,
            "day": day,
            "daily_volume": daily_volume,
            "estimated_r_sent": int(round(daily_volume * expected_sent_ratio)),
            "cumulative_volume": int(cumulative_volume),
            "remaining_to_target": int(max(target_volume - cumulative_volume, 0)),

            "drop_5": round(daily_volume / 5, 2),
            "drop_10": round(daily_volume / 10, 2),
            "drop_15": round(daily_volume / 15, 2),
            "drop_20": round(daily_volume / 20, 2),

            "recommended_drops_per_day": adaptive_drops,
            "drops_per_day": adaptive_drops,
            "volume_per_drop": round(volume_per_drop, 2),
            "growth_rate": round(real_growth, 4),
            "limit_usage_ratio": round(limit_usage_ratio, 4),
            "estimated_sent_ratio": round(expected_sent_ratio, 3),
            "estimated_error_probability": round(estimated_error_probability, 4),
            "risk_zone": risk_zone,
            "decision": decision,
            "target_reached": cumulative_volume >= target_volume,
            "spf_probability": round(
    min(estimated_error_probability * (0.4 + real_growth), 1),
    4
),

"dkim_probability": round(
    min(estimated_error_probability * (0.3 + limit_usage_ratio), 1),
    4
),

"netblock_probability": round(
    min(
        estimated_error_probability
        * (0.5 + volume_per_drop / 15000),
        1
    ),
    4
),
        })

        previous_volume = daily_volume

    return pd.DataFrame(rows)


def run_warmup_strategy(
    target_volume=DEFAULT_TARGET_VOLUME,
    max_days=DEFAULT_MAX_DAYS,
    initial_volume=3000,
    growth_rate=0.30,
    max_daily_limit=100000,
    expected_sent_ratio=0.90,
    target_limit_usage_ratio=0.85,
    selected_ip=None,
    save_outputs=True,
):
    plan_df = generate_daily_plan(
        initial_volume=initial_volume,
        growth_rate=growth_rate,
        target_volume=target_volume,
        max_days=max_days,
        max_daily_limit=max_daily_limit,
        expected_sent_ratio=expected_sent_ratio,
        target_limit_usage_ratio=target_limit_usage_ratio,
        plan_type="Adaptive AI",
    )

    plan_df["selected_ip"] = selected_ip

    summary = pd.DataFrame([{
        "selected_ip": selected_ip,
        "final_cumulative_volume": int(plan_df["cumulative_volume"].max()),
        "target_volume": int(target_volume),
        "target_reached": bool(plan_df["target_reached"].max()),
        "risk_days": int((plan_df["risk_zone"] == "Risk").sum()),
        "dangerous_days": int((plan_df["risk_zone"] == "Dangerous").sum()),
        "max_error_probability": float(plan_df["estimated_error_probability"].max()),
        "avg_error_probability": float(plan_df["estimated_error_probability"].mean()),
        "recommended_status": (
            "Safe plan"
            if ((plan_df["risk_zone"] == "Risk").sum() == 0 and (plan_df["risk_zone"] == "Dangerous").sum() == 0 and plan_df["target_reached"].max())
            else "Needs monitoring"
        )
    }])

    if save_outputs:
        plan_df.to_csv(OUTPUT_PLAN_PATH, index=False)
        summary.to_csv(OUTPUT_SUMMARY_PATH, index=False)

    return plan_df, summary


def main():
    print("=" * 70)
    print("Adaptive AI Warm-up Strategy Engine")
    print("=" * 70)

    plan_df, summary = run_warmup_strategy(save_outputs=True)

    print(f"Saved plan: {OUTPUT_PLAN_PATH}")
    print(f"Saved summary: {OUTPUT_SUMMARY_PATH}")
    print("\nSummary:")
    print(summary.to_string(index=False))
    print("\nDaily plan:")
    print(plan_df.to_string(index=False))
    print("\nWarm-up strategy engine completed successfully.")


if __name__ == "__main__":
    main()