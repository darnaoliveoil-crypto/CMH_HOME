# -*- coding: utf-8 -*-
"""
PFE 10 - Time Series Forecasting (VS Code version)
Reads:  backend/data/processed/df_ml.csv
Saves:  backend/data/processed/time_series_daily_ip.csv
        backend/data/processed/forecast_all_ips_7_days.csv
        backend/outputs/forecast_selected_ip_7_days.csv
        backend/outputs/forecast_summary.csv

This version is adapted from the Colab notebook for local execution.
It uses Prophet if installed; otherwise it falls back to a simple rolling/trend forecast.
"""

from pathlib import Path
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
PROCESSED_DIR = DATA_DIR / "processed"
OUTPUTS_DIR = BASE_DIR / "outputs"
MODELS_DIR = BASE_DIR / "models"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)

DF_ML_PATH = PROCESSED_DIR / "df_ml.csv"
DAILY_TS_PATH = PROCESSED_DIR / "time_series_daily_ip.csv"
FORECAST_ALL_PATH = PROCESSED_DIR / "forecast_all_ips_7_days.csv"
FORECAST_SELECTED_PATH = OUTPUTS_DIR / "forecast_selected_ip_7_days.csv"
FORECAST_SUMMARY_PATH = OUTPUTS_DIR / "forecast_summary.csv"

FORECAST_DAYS = 7

# ---------------------------------------------------------------------
# Optional Prophet import
# ---------------------------------------------------------------------
try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except Exception:
    Prophet = None
    PROPHET_AVAILABLE = False


# ---------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------
def read_csv_required(path: Path, name: str) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing {name}: {path}")
    return pd.read_csv(path)


def clean_numeric(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    for col in cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def aggregate_daily_ip(df: pd.DataFrame) -> pd.DataFrame:
    required = ["ip", "datetime_gride", "daily_volume", "sent_ratio", "risk_label_encoded"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in df_ml.csv: {missing}")

    df = df.copy()
    df["datetime_gride"] = pd.to_datetime(df["datetime_gride"], errors="coerce")
    df = df.dropna(subset=["ip", "datetime_gride"])
    df["date"] = df["datetime_gride"].dt.normalize()

    df = clean_numeric(df, ["daily_volume", "sent_ratio", "risk_label_encoded"])

    daily = (
        df.groupby(["ip", "date"], as_index=False)
        .agg(
            daily_volume=("daily_volume", "sum"),
            sent_ratio=("sent_ratio", "mean"),
            risk_label_encoded=("risk_label_encoded", "mean"),
        )
    )

    # Complete missing dates per IP
    completed_parts = []
    for ip, group in daily.groupby("ip"):
        group = group.sort_values("date").copy()
        full_dates = pd.date_range(group["date"].min(), group["date"].max(), freq="D")
        group = group.set_index("date").reindex(full_dates)
        group.index.name = "date"
        group["ip"] = ip
        group["daily_volume"] = group["daily_volume"].fillna(0)
        group["sent_ratio"] = group["sent_ratio"].ffill().bfill().fillna(0)
        group["risk_label_encoded"] = group["risk_label_encoded"].ffill().bfill().fillna(0)
        completed_parts.append(group.reset_index())

    if completed_parts:
        daily_full = pd.concat(completed_parts, ignore_index=True)
    else:
        daily_full = pd.DataFrame(columns=["date", "ip", "daily_volume", "sent_ratio", "risk_label_encoded"])

    return daily_full[["ip", "date", "daily_volume", "sent_ratio", "risk_label_encoded"]]


def simple_forecast(series_df: pd.DataFrame, metric: str, periods: int = 7) -> pd.DataFrame:
    """Fallback forecast using recent mean + simple linear trend."""
    data = series_df[["date", metric]].dropna().sort_values("date").copy()
    if data.empty:
        last_date = pd.Timestamp.today().normalize()
        future_dates = pd.date_range(last_date + pd.Timedelta(days=1), periods=periods, freq="D")
        return pd.DataFrame({"ds": future_dates, f"forecast_{metric}": 0.0})

    last_date = data["date"].max()
    future_dates = pd.date_range(last_date + pd.Timedelta(days=1), periods=periods, freq="D")

    y = pd.to_numeric(data[metric], errors="coerce").fillna(0).to_numpy(dtype=float)
    if len(y) >= 2:
        recent = y[-min(7, len(y)):]
        base = float(np.mean(recent))
        trend = float((recent[-1] - recent[0]) / max(len(recent) - 1, 1))
        preds = [max(base + trend * (i + 1), 0) for i in range(periods)]
    else:
        preds = [max(float(y[-1]), 0)] * periods

    # Bound ratio/risk values to logical intervals
    if metric == "sent_ratio":
        preds = [min(max(p, 0), 1.5) for p in preds]
    if metric == "risk_label_encoded":
        preds = [min(max(p, 0), 2) for p in preds]

    return pd.DataFrame({"ds": future_dates, f"forecast_{metric}": preds})


def prophet_forecast(series_df: pd.DataFrame, metric: str, periods: int = 7) -> pd.DataFrame:
    """Forecast one metric with Prophet. Falls back to simple forecast when data is too small or Prophet fails."""
    if not PROPHET_AVAILABLE:
        return simple_forecast(series_df, metric, periods)

    data = series_df[["date", metric]].dropna().sort_values("date").copy()
    data = data.rename(columns={"date": "ds", metric: "y"})
    data["y"] = pd.to_numeric(data["y"], errors="coerce").fillna(0)

    # Prophet needs at least 2 non-NaN points; very short series can still fail, so fallback is kept.
    if len(data) < 3 or data["y"].nunique() <= 1:
        return simple_forecast(series_df, metric, periods)

    try:
        model = Prophet(
            daily_seasonality=False,
            weekly_seasonality=False,
            yearly_seasonality=False,
            interval_width=0.8,
        )
        model.fit(data)
        future = model.make_future_dataframe(periods=periods, freq="D")
        forecast = model.predict(future)
        out = forecast[["ds", "yhat"]].tail(periods).copy()
        out = out.rename(columns={"yhat": f"forecast_{metric}"})
        out[f"forecast_{metric}"] = out[f"forecast_{metric}"].clip(lower=0)
        if metric == "sent_ratio":
            out[f"forecast_{metric}"] = out[f"forecast_{metric}"].clip(lower=0, upper=1.5)
        if metric == "risk_label_encoded":
            out[f"forecast_{metric}"] = out[f"forecast_{metric}"].clip(lower=0, upper=2)
        return out
    except Exception as exc:
        print(f"Prophet failed for metric={metric}. Using simple fallback. Reason: {exc}")
        return simple_forecast(series_df, metric, periods)


def forecast_one_ip(daily_full: pd.DataFrame, ip: str, periods: int = 7) -> pd.DataFrame:
    ip_df = daily_full[daily_full["ip"] == ip].copy().sort_values("date")
    if ip_df.empty:
        raise ValueError(f"No daily data found for IP: {ip}")

    volume_fc = prophet_forecast(ip_df, "daily_volume", periods)
    ratio_fc = prophet_forecast(ip_df, "sent_ratio", periods)
    risk_fc = prophet_forecast(ip_df, "risk_label_encoded", periods)

    final = volume_fc.merge(ratio_fc, on="ds", how="outer")
    final = final.merge(risk_fc, on="ds", how="outer")
    final.insert(0, "ip", ip)
    final = final.rename(columns={"ds": "forecast_date"})

    # Clean types and add cumulative forecast volume
    final["forecast_daily_volume"] = pd.to_numeric(final["forecast_daily_volume"], errors="coerce").fillna(0).round(0).astype(int)
    final["forecast_sent_ratio"] = pd.to_numeric(final["forecast_sent_ratio"], errors="coerce").fillna(0).round(3)
    final["forecast_risk_label_encoded"] = pd.to_numeric(final["forecast_risk_label_encoded"], errors="coerce").fillna(0).round(3)
    final["forecast_cumulative_volume"] = final["forecast_daily_volume"].cumsum()

    return final


def choose_selected_ip(daily_full: pd.DataFrame) -> str:
    # Select IP with most non-zero volume days; if tie, highest total volume.
    stats = (
        daily_full.assign(nonzero_day=(daily_full["daily_volume"] > 0).astype(int))
        .groupby("ip", as_index=False)
        .agg(nonzero_days=("nonzero_day", "sum"), total_volume=("daily_volume", "sum"), rows=("date", "count"))
        .sort_values(["nonzero_days", "total_volume", "rows"], ascending=False)
    )
    if stats.empty:
        raise ValueError("No IPs found in time-series data.")
    return str(stats.iloc[0]["ip"])



# ---------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------
def main():
    print("=" * 70)
    print("PFE 10 - Time Series Forecasting")
    print("=" * 70)

    print(f"Reading df_ml from: {DF_ML_PATH}")
    df_ml = read_csv_required(DF_ML_PATH, "df_ml.csv")
    print(f"Loaded df_ml shape: {df_ml.shape}")

    daily_full = aggregate_daily_ip(df_ml)
    daily_full.to_csv(DAILY_TS_PATH, index=False)
    print(f"Saved daily time-series dataset: {DAILY_TS_PATH}")
    print(f"Daily time-series shape: {daily_full.shape}")

    selected_ip = choose_selected_ip(daily_full)
    print(f"Selected IP for detailed forecast: {selected_ip}")
    print(f"Forecast engine: {'Prophet' if PROPHET_AVAILABLE else 'Simple fallback (Prophet not installed)'}")

    import joblib

    forecast_config = {
      "forecast_days": FORECAST_DAYS,
        "engine": "Prophet" if PROPHET_AVAILABLE else "Simple fallback",
      "input_file": str(DF_ML_PATH),
     "output_all_ips": str(FORECAST_ALL_PATH),
     "output_selected_ip": str(FORECAST_SELECTED_PATH),
     "metrics": ["daily_volume", "sent_ratio", "risk_label_encoded"]
    }

    joblib.dump(forecast_config, MODELS_DIR / "forecasting_config.pkl")
    print("Saved forecasting config.")

    selected_forecast = forecast_one_ip(daily_full, selected_ip, periods=FORECAST_DAYS)
    selected_forecast.to_csv(FORECAST_SELECTED_PATH, index=False)
    print(f"Saved selected IP forecast: {FORECAST_SELECTED_PATH}")

    # Forecast all IPs for dashboard usage
    all_forecasts = []
    for ip in daily_full["ip"].dropna().unique():
        try:
            fc = forecast_one_ip(daily_full, str(ip), periods=FORECAST_DAYS)
            all_forecasts.append(fc)
        except Exception as exc:
            print(f"Skipping IP {ip}: {exc}")

    if all_forecasts:
        forecast_all = pd.concat(all_forecasts, ignore_index=True)
    else:
        forecast_all = pd.DataFrame()

    forecast_all.to_csv(FORECAST_ALL_PATH, index=False)
    print(f"Saved all IP forecasts: {FORECAST_ALL_PATH}")

    # Summary file
    if not forecast_all.empty:
        summary = (
            forecast_all.groupby("ip", as_index=False)
            .agg(
                forecast_7d_total_volume=("forecast_daily_volume", "sum"),
                forecast_avg_sent_ratio=("forecast_sent_ratio", "mean"),
                forecast_avg_risk=("forecast_risk_label_encoded", "mean"),
                forecast_max_daily_volume=("forecast_daily_volume", "max"),
            )
            .sort_values("forecast_7d_total_volume", ascending=False)
        )
    else:
        summary = pd.DataFrame()

    summary.to_csv(FORECAST_SUMMARY_PATH, index=False)
    print(f"Saved forecast summary: {FORECAST_SUMMARY_PATH}")

    print("\nPreview selected forecast:")
    print(selected_forecast.head(10).to_string(index=False))
    print("\nPFE 10 completed successfully.")


if __name__ == "__main__":
    main()
