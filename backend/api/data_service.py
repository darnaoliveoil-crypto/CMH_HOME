from pathlib import Path
import json

BASE_DIR = Path(__file__).resolve().parents[1]
PROCESSED_DIR = BASE_DIR / "data" / "processed"

def load_json(filename: str):
    path = PROCESSED_DIR / filename
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def get_df_ml():
    return load_json("df_ml.json")

def get_ip_analyse():
    return load_json("IP_Analyse.json")

def get_first_ip_summary():
    return load_json("first_ip_summary.json")