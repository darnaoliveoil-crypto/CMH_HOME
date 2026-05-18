# -*- coding: utf-8 -*-
"""
pfe_3_dataCleaning.py
Local VS Code version

Goal:
- Read multiple raw files from backend/data/raw/
    details_*.csv
    grid_*.csv
    drop*.json
- Clean Detail, Gride and Drop data
- Merge them at IP level
- Save outputs in backend/data/processed/

Outputs:
- detail_clean.csv
- gride_clean.csv
- final1_ready_V2.csv
- drop_for_merge.csv
- final_data.csv
"""

from pathlib import Path
import json
import re
import ast
import numpy as np
import pandas as pd

pd.set_option("future.no_silent_downcasting", True)

# ==========================================================
# 0. PATHS
# ==========================================================

# This file is expected inside: backend/Script/pfe_3_dataCleaning.py
BACKEND_DIR = Path(__file__).resolve().parent
RAW_DIR = BACKEND_DIR / "data" / "raw"
PROCESSED_DIR = BACKEND_DIR / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

DETAIL_PATTERN = "*details*.csv"
GRID_PATTERN = "*grid*.csv"
DROP_PATTERN = "*drop*.json"
DEFAULT_YEAR = 2026


# ==========================================================
# 1. HELPER FUNCTIONS
# ==========================================================

def print_step(title: str) -> None:
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def read_many_csv(pattern: str, label: str) -> pd.DataFrame:
    files = sorted(RAW_DIR.glob(pattern))
    if not files:
        raise FileNotFoundError(f"No {label} files found in {RAW_DIR} with pattern: {pattern}")

    dfs = []
    for file in files:
        print(f"Reading {label}: {file.name}")
        df = pd.read_csv(file)
        df["source_file"] = file.name
        dfs.append(df)

    result = pd.concat(dfs, ignore_index=True)
    print(f"Total {label} rows: {result.shape[0]} | columns: {result.shape[1]}")
    return result


def read_many_json(pattern: str, label: str) -> pd.DataFrame:
    files = sorted(RAW_DIR.glob(pattern))
    if not files:
        raise FileNotFoundError(f"No {label} files found in {RAW_DIR} with pattern: {pattern}")

    dfs = []
    for file in files:
        print(f"Reading {label}: {file.name}")
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, list):
            df = pd.DataFrame(data)
        elif isinstance(data, dict):
            # common case: json contains a root list under one key
            list_values = [v for v in data.values() if isinstance(v, list)]
            df = pd.DataFrame(list_values[0]) if list_values else pd.DataFrame([data])
        else:
            raise ValueError(f"Unsupported JSON structure in {file.name}")

        df["source_file"] = file.name
        dfs.append(df)

    result = pd.concat(dfs, ignore_index=True)
    print(f"Total {label} rows: {result.shape[0]} | columns: {result.shape[1]}")
    return result


def parse_detail_datetime(x, year: int = DEFAULT_YEAR):
    x = str(x).strip()
    date_match = re.search(r"(\d{2})/(\d{2})", x)
    time_match = re.search(r"(\d{2}:\d{2}:\d{2})", x)

    if not date_match:
        return pd.NaT

    day = date_match.group(1)
    month = date_match.group(2)
    time_part = time_match.group(1) if time_match else "00:00:00"

    # Original Colab logic used year-day-month
    full_str = f"{year}-{day}-{month} {time_part}"
    return pd.to_datetime(full_str, format="%Y-%d-%m %H:%M:%S", errors="coerce")


def parse_gride_datetime(x):
    x = str(x).strip()
    date_match = re.search(r"(\d{2}/\d{2}/\d{4})", x)
    time_match = re.search(r"(\d{2}:\d{2}:\d{2})", x)

    if not date_match:
        return pd.NaT

    date_part = date_match.group(1)
    time_part = time_match.group(1) if time_match else "00:00:00"
    full_str = f"{date_part} {time_part}"
    return pd.to_datetime(full_str, format="%d/%m/%Y %H:%M:%S", errors="coerce")


def parse_drop_datetime(x, year: int = DEFAULT_YEAR):
    x = str(x).strip()
    date_match = re.search(r"(\d{2})/(\d{2})", x)
    time_match = re.search(r"(\d{2}:\d{2}:\d{2})", x)

    if not date_match:
        return pd.NaT

    day = date_match.group(1)
    month = date_match.group(2)
    time_part = time_match.group(1) if time_match else "00:00:00"

    full_str = f"{year}-{month}-{day} {time_part}"
    return pd.to_datetime(full_str, format="%Y-%m-%d %H:%M:%S", errors="coerce")


def split_ips(val):
    val = str(val).strip()
    if val == "" or val.lower() == "nan":
        return []
    return [ip.strip() for ip in val.split(",") if ip.strip()]


def extract_servers(val):
    val = str(val)
    return re.findall(r"s_[^\s,]+", val)


def extract_servers_from_message(msg):
    msg = str(msg)
    servers = re.findall(r"s_[A-Za-z0-9_]+", msg)
    return list(dict.fromkeys(servers))

def extract_entity_from_server(server):
    server = str(server).lower().strip()
    match = re.search(r"s_(cmh\d+)", server)
    if match:
        return match.group(1)
    return "unknown"

def safe_parse_ip_map(ip_map_str):
    if ip_map_str is None:
        return {}

    text = str(ip_map_str).strip()
    if text == "" or text.lower() == "nan":
        return {}

    # Try JSON first
    try:
        return json.loads(text)
    except Exception:
        pass

    # Try Python dict format with single quotes
    try:
        parsed = ast.literal_eval(text)
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        return {}


def extract_ip_errors(ip_map_str):
    ip_map = safe_parse_ip_map(ip_map_str)
    ip_errors = []

    for ip, errors in ip_map.items():
        if isinstance(errors, list):
            for error in errors:
                ip_errors.append({"ip": ip, "error": str(error)})
        elif errors is not None:
            ip_errors.append({"ip": ip, "error": str(errors)})

    return ip_errors


# ==========================================================
# 2. CLEAN DETAIL DATA
# ==========================================================

def clean_detail(detail: pd.DataFrame) -> pd.DataFrame:
    required_cols = ["FK_ID", "Date", "Sent", "R.Sent", "Offset", "Limit", "Server", "Ips"]
    missing = [c for c in required_cols if c not in detail.columns]
    if missing:
        raise KeyError(f"Missing columns in Detail files: {missing}")

    detail_clean = detail[required_cols].copy()
    detail_clean = detail_clean.rename(columns={
        "FK_ID": "campaign_id",
        "Date": "raw_date",
        "Sent": "sent_detail",
        "R.Sent": "r_sent_detail",
        "Offset": "offset",
        "Limit": "limit",
        "Server": "server",
        "Ips": "ips_raw",
    })

    for col in ["server", "raw_date", "ips_raw"]:
        detail_clean[col] = detail_clean[col].astype(str).str.strip()

    detail_clean["datetime"] = detail_clean["raw_date"].apply(parse_detail_datetime)
    detail_clean["entity"] = detail_clean["server"].apply(extract_entity_from_server)
    detail_clean["ips_list"] = detail_clean["ips_raw"].apply(split_ips)
    detail_clean["nb_ips"] = detail_clean["ips_list"].apply(len)

    for col in ["campaign_id", "sent_detail", "r_sent_detail", "offset", "limit"]:
        detail_clean[col] = pd.to_numeric(detail_clean[col], errors="coerce")

    detail_clean = detail_clean.sort_values(
        by=["server", "datetime", "campaign_id"]
    ).reset_index(drop=True)

    detail_clean = detail_clean[[
    "campaign_id", "server", "entity", "datetime", "sent_detail", "r_sent_detail",
    "offset", "limit", "ips_list", "nb_ips"
]]

    return detail_clean


# ==========================================================
# 3. CLEAN GRIDE DATA
# ==========================================================

def clean_gride(gride: pd.DataFrame) -> pd.DataFrame:
    required_cols = ["Date", "ID", "Sent", "R.Sent", "Profile", "Server(s)"]
    missing = [c for c in required_cols if c not in gride.columns]
    if missing:
        raise KeyError(f"Missing columns in Gride files: {missing}")

    gride_clean = gride[required_cols].copy()
    gride_clean = gride_clean.rename(columns={
        "Date": "raw_gride_date",
        "ID": "campaign_id",
        "Sent": "sent_gride",
        "R.Sent": "r_sent_gride",
        "Profile": "profile",
        "Server(s)": "servers_raw",
    })

    for col in ["raw_gride_date", "profile", "servers_raw"]:
        gride_clean[col] = gride_clean[col].astype(str).str.strip()

    gride_clean["datetime_gride"] = gride_clean["raw_gride_date"].apply(parse_gride_datetime)

    for col in ["campaign_id", "sent_gride", "r_sent_gride"]:
        gride_clean[col] = pd.to_numeric(gride_clean[col], errors="coerce")

    gride_clean["servers_list"] = gride_clean["servers_raw"].apply(extract_servers)
    gride_clean["nb_servers"] = gride_clean["servers_list"].apply(len)

    gride_clean = gride_clean[[
        "campaign_id", "datetime_gride", "sent_gride", "r_sent_gride",
        "servers_list", "nb_servers"
    ]]

    # Keep one row per campaign_id to avoid accidental multiplication in merge
    gride_clean = gride_clean.sort_values("datetime_gride").drop_duplicates(
        subset=["campaign_id"], keep="first"
    )

    return gride_clean


# ==========================================================
# 4. CLEAN DROP DATA
# ==========================================================

def clean_drop(drop: pd.DataFrame) -> pd.DataFrame:
    required_cols = ["byIp", "fullMessage", "limit", "offset", "outSum", "totalIps", "reportTime", "ipMap"]
    missing = [c for c in required_cols if c not in drop.columns]
    if missing:
        raise KeyError(f"Missing columns in Drop JSON files: {missing}")

    drop_clean = drop[required_cols].copy()
    drop_clean = drop_clean.rename(columns={
        "byIp": "by_ip",
        "fullMessage": "full_message",
        "reportTime": "raw_report_time",
        "ipMap": "ip_map_raw",
    })

    for col in ["by_ip", "full_message", "raw_report_time", "ip_map_raw"]:
        drop_clean[col] = drop_clean[col].astype(str).str.strip()

    drop_clean["datetime_drop"] = drop_clean["raw_report_time"].apply(parse_drop_datetime)
    drop_clean["servers_drop_list"] = drop_clean["full_message"].apply(extract_servers_from_message)
    drop_clean["ip_errors"] = drop_clean["ip_map_raw"].apply(extract_ip_errors)

    for col in ["by_ip", "limit", "offset", "outSum", "totalIps"]:
        drop_clean[col] = pd.to_numeric(drop_clean[col], errors="coerce")

    drop_final = drop_clean.explode("ip_errors")
    drop_final["ip"] = drop_final["ip_errors"].apply(lambda x: x.get("ip") if isinstance(x, dict) else None)
    drop_final["error_type_from_error"] = drop_final["ip_errors"].apply(lambda x: x.get("error") if isinstance(x, dict) else None)
    drop_final["server"] = drop_final["servers_drop_list"].apply(
        lambda x: x[0] if isinstance(x, list) and len(x) > 0 else None
    )

    drop_for_merge = drop_final[[
        "datetime_drop", "server", "ip", "limit", "outSum", "by_ip", "totalIps", "error_type_from_error"
    ]].copy()

    drop_for_merge = drop_for_merge.dropna(subset=["datetime_drop", "server", "ip"])
    drop_for_merge = drop_for_merge.sort_values(["server", "ip", "datetime_drop"]).reset_index(drop=True)

    return drop_for_merge


# ==========================================================
# 5. MERGE DETAIL + GRIDE
# ==========================================================

def merge_detail_gride(detail_clean: pd.DataFrame, gride_clean: pd.DataFrame):
    final1 = detail_clean.merge(gride_clean, on="campaign_id", how="left")

    final1["server_in_gride_list"] = final1.apply(
        lambda row: row["server"] in row["servers_list"] if isinstance(row["servers_list"], list) else False,
        axis=1,
    )

    final1 = final1[[
    "campaign_id", "server", "entity", "datetime_gride", "sent_detail", "r_sent_detail",
    "offset", "limit", "ips_list", "nb_ips", "sent_gride", "r_sent_gride",
    "servers_list", "server_in_gride_list", "nb_servers"
    ]].copy()

    final1_ready_v2 = final1.copy().explode("ips_list")
    final1_ready_v2 = final1_ready_v2.rename(columns={"ips_list": "ip"})
    final1_ready_v2 = final1_ready_v2.drop(
        columns=["servers_list", "nb_servers", "nb_ips", "server_in_gride_list"],
        errors="ignore",
    )

    final1_ready_v2["ip"] = final1_ready_v2["ip"].astype(str).str.strip()
    final1_ready_v2 = final1_ready_v2[final1_ready_v2["ip"].ne("")]

    return final1, final1_ready_v2


# ==========================================================
# 6. MERGE FINAL1_READY_V2 + DROP
# ==========================================================

def merge_with_drop(final1_ready_v2: pd.DataFrame, drop_for_merge: pd.DataFrame) -> pd.DataFrame:
    final_clean = final1_ready_v2.dropna(subset=["server", "ip", "datetime_gride"]).copy()
    drop_clean = drop_for_merge.dropna(subset=["server", "ip", "datetime_drop"]).copy()

    final_clean["datetime_gride"] = pd.to_datetime(final_clean["datetime_gride"], errors="coerce")
    drop_clean["datetime_drop"] = pd.to_datetime(drop_clean["datetime_drop"], errors="coerce")

    final_clean = final_clean.dropna(subset=["datetime_gride"])
    drop_clean = drop_clean.dropna(subset=["datetime_drop"])

    merged_parts = []
    unique_pairs = final_clean[["server", "ip"]].drop_duplicates().values

    for server_name, ip_val in unique_pairs:
        left = final_clean[
            (final_clean["server"] == server_name) & (final_clean["ip"] == ip_val)
        ].sort_values("datetime_gride").reset_index(drop=True)

        right = drop_clean[
            (drop_clean["server"] == server_name) & (drop_clean["ip"] == ip_val)
        ].sort_values("datetime_drop").reset_index(drop=True)

        if left.empty:
            continue

        if right.empty:
            left = left.copy()
            left["datetime_drop"] = pd.NaT
            left["limit_drop"] = np.nan
            left["outSum"] = np.nan
            left["by_ip"] = np.nan
            left["totalIps"] = np.nan
            left["error_type_from_error"] = "No error"
            merged_parts.append(left)
        else:
            merged = pd.merge_asof(
                left,
                right,
                left_on="datetime_gride",
                right_on="datetime_drop",
                direction="nearest",
                tolerance=pd.Timedelta("20min"),
                suffixes=("", "_drop"),
            )
            merged_parts.append(merged)

    if not merged_parts:
        raise ValueError("No rows available after merge_with_drop(). Check server/IP/datetime columns.")

    final_merged = pd.concat(merged_parts, ignore_index=True)
    final_merged["error_type_from_error"] = final_merged["error_type_from_error"].fillna("No error")

    # If merge_asof created duplicated right keys, keep original names clean
    final_merged = final_merged.drop(columns=["datetime_drop", "server_drop", "ip_drop"], errors="ignore")

    return final_merged


# ==========================================================
# 7. IP DISTRIBUTION
# ==========================================================

def calculate_ip_distribution(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    group_cols = ["campaign_id", "server", "datetime_gride"]
    df["nb_ips_in_campaign"] = df.groupby(group_cols)["ip"].transform("count")
    df["ip_has_error"] = df["error_type_from_error"].notna() & (df["error_type_from_error"] != "No error")

    df["sent_per_ip"] = np.nan
    df["r_sent_per_ip"] = np.nan
    df["limit_per_ip"] = np.nan

    for _, group in df.groupby(group_cols, sort=False):
        total_sent = int(group["sent_detail"].iloc[0]) if pd.notna(group["sent_detail"].iloc[0]) else 0
        total_r_sent = int(group["r_sent_detail"].iloc[0]) if pd.notna(group["r_sent_detail"].iloc[0]) else 0
        total_limit = int(group["limit"].iloc[0]) if pd.notna(group["limit"].iloc[0]) else 0
        n = int(group["nb_ips_in_campaign"].iloc[0]) if pd.notna(group["nb_ips_in_campaign"].iloc[0]) else 0

        if n <= 0:
            df.loc[group.index, ["sent_per_ip", "r_sent_per_ip", "limit_per_ip"]] = 0
            continue

        def distribute(total, n):
            base = total // n
            rem = total % n
            values = [base] * n
            for i in range(rem):
                values[i] += 1
            return np.array(values, dtype=float)

        sent_values = distribute(total_sent, n)
        limit_values = distribute(total_limit, n)
        r_sent_values = sent_values.copy()

        if total_sent <= total_r_sent:
            r_sent_values = distribute(total_r_sent, n)
        else:
            lost = int(total_sent - total_r_sent)
            group_indices = group.index.to_numpy()
            error_indices = group[group["ip_has_error"]].index.to_numpy()
            safe_indices = group[~group["ip_has_error"]].index.to_numpy()

            def reduce_from(indices, lost_count, values):
                positions = [np.where(group_indices == idx)[0][0] for idx in indices]
                while lost_count > 0:
                    eligible = [pos for pos in positions if values[pos] > 0]
                    if not eligible:
                        break
                    pos = eligible[0]
                    values[pos] -= 1
                    lost_count -= 1
                return lost_count, values

            lost, r_sent_values = reduce_from(error_indices, lost, r_sent_values)
            if lost > 0:
                lost, r_sent_values = reduce_from(safe_indices, lost, r_sent_values)

        df.loc[group.index, "sent_per_ip"] = sent_values
        df.loc[group.index, "r_sent_per_ip"] = r_sent_values
        df.loc[group.index, "limit_per_ip"] = limit_values

    df["sent_per_ip"] = df["sent_per_ip"].astype(float).fillna(0)
    df["r_sent_per_ip"] = df["r_sent_per_ip"].astype(float).fillna(0)
    df["limit_per_ip"] = df["limit_per_ip"].astype(float).fillna(0)

    df["total_sent_calc_per_group"] = df.groupby(group_cols)["sent_per_ip"].transform("sum")
    df["total_r_sent_calc_per_group"] = df.groupby(group_cols)["r_sent_per_ip"].transform("sum")
    df["total_limit_calc_per_group"] = df.groupby(group_cols)["limit_per_ip"].transform("sum")

    df["sent_diff"] = df["total_sent_calc_per_group"] - df["sent_detail"]
    df["r_sent_diff"] = df["total_r_sent_calc_per_group"] - df["r_sent_detail"]
    df["limit_diff"] = df["total_limit_calc_per_group"] - df["limit"]

    return df


# ==========================================================
# 8. MAIN PIPELINE
# ==========================================================

def main():
    print_step("PFE 3 - DATA CLEANING PIPELINE STARTED")
    print(f"Raw folder      : {RAW_DIR}")
    print(f"Processed folder: {PROCESSED_DIR}")

    print_step("1. Reading raw files")
    detail_raw = read_many_csv(DETAIL_PATTERN, "Detail")
    gride_raw = read_many_csv(GRID_PATTERN, "Gride")
    drop_raw = read_many_json(DROP_PATTERN, "Drop")

    print_step("2. Cleaning Detail data")
    detail_clean = clean_detail(detail_raw)
    print(detail_clean.shape)
    detail_clean.to_csv(PROCESSED_DIR / "detail_clean.csv", index=False)

    print_step("3. Cleaning Gride data")
    gride_clean = clean_gride(gride_raw)
    print(gride_clean.shape)
    gride_clean.to_csv(PROCESSED_DIR / "gride_clean.csv", index=False)

    print_step("4. Merging Detail + Gride")
    final1, final1_ready_v2 = merge_detail_gride(detail_clean, gride_clean)
    print("final1:", final1.shape)
    print("final1_ready_V2:", final1_ready_v2.shape)
    final1_ready_v2.to_csv(PROCESSED_DIR / "final1_ready_V2.csv", index=False)

    print_step("5. Cleaning Drop data")
    drop_for_merge = clean_drop(drop_raw)
    print(drop_for_merge.shape)
    drop_for_merge.to_csv(PROCESSED_DIR / "drop_for_merge.csv", index=False)

    print_step("6. Merging with Drop data")
    final_merged = merge_with_drop(final1_ready_v2, drop_for_merge)
    print("final_merged:", final_merged.shape)

    print_step("7. Calculating IP distribution")
    final_merged_v2 = calculate_ip_distribution(final_merged)

    verification_df = final_merged_v2.groupby(["campaign_id", "server", "datetime_gride"]).agg(
        original_sent_detail=("sent_detail", "first"),
        original_r_sent_detail=("r_sent_detail", "first"),
        original_limit=("limit", "first"),
        sum_sent_per_ip=("sent_per_ip", "sum"),
        sum_r_sent_per_ip=("r_sent_per_ip", "sum"),
        sum_limit_per_ip=("limit_per_ip", "sum"),
    ).reset_index()

    verification_df["sent_deviation"] = verification_df["sum_sent_per_ip"] - verification_df["original_sent_detail"]
    verification_df["r_sent_deviation"] = verification_df["sum_r_sent_per_ip"] - verification_df["original_r_sent_detail"]
    verification_df["limit_deviation"] = verification_df["sum_limit_per_ip"] - verification_df["original_limit"]

    bad = verification_df[
        (verification_df["sent_deviation"].abs() > 0.001) |
        (verification_df["r_sent_deviation"].abs() > 0.001) |
        (verification_df["limit_deviation"].abs() > 0.001)
    ]

    if bad.empty:
        print("Distribution verification OK: no significant deviation.")
    else:
        print("WARNING: deviations found in IP distribution:")
        print(bad.head(20))
        bad.to_csv(PROCESSED_DIR / "distribution_deviations.csv", index=False)

    print_step("8. Creating final_data")
    final_data = final_merged_v2[[
    "campaign_id", "server", "entity", "ip", "datetime_gride",
    "sent_detail", "r_sent_detail", "sent_per_ip", "r_sent_per_ip",
    "offset", "limit", "limit_per_ip", "outSum", "error_type_from_error"
    ]].copy()

    for col in ["sent_per_ip", "r_sent_per_ip", "limit_per_ip"]:
        final_data[col] = final_data[col].round().astype("int64")

    final_data = final_data.sort_values(["ip", "datetime_gride", "campaign_id"]).reset_index(drop=True)
    final_data.to_csv(PROCESSED_DIR / "final_data.csv", index=False)

    print("Saved files:")
    for file in [
        "detail_clean.csv",
        "gride_clean.csv",
        "final1_ready_V2.csv",
        "drop_for_merge.csv",
        "final_data.csv",
    ]:
        print(f"- {PROCESSED_DIR / file}")

    print("\nfinal_data shape:", final_data.shape)
    print(final_data.head())

    detail_clean.to_json(
    PROCESSED_DIR / "detail_clean.json",
    orient="records",
    indent=4,
    date_format="iso"
)

    gride_clean.to_json(
    PROCESSED_DIR / "gride_clean.json",
    orient="records",
    indent=4,
    date_format="iso"
    )

    drop_for_merge.to_json(
    PROCESSED_DIR / "drop_for_merge.json",
    orient="records",
    indent=4,
    date_format="iso"
    )

    # Save JSON output
    final_data.to_json(
    PROCESSED_DIR / "final_data.json",
    orient="records",
    indent=4,
    date_format="iso"
    )

    print_step("PFE 3 - DATA CLEANING PIPELINE FINISHED SUCCESSFULLY")


if __name__ == "__main__":
    main()
