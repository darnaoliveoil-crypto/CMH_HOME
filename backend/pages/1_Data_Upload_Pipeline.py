import streamlit as st
from pathlib import Path
import subprocess
import sys
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"

RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

st.set_page_config(page_title="Data Upload & Pipeline", layout="wide")

st.title("Data Upload & Pipeline Dashboard")

st.write("Upload raw Detail, Gride, and Drop files, then run the full processing pipeline.")

detail_files = st.file_uploader("Upload DataDetail CSV files", type=["csv"], accept_multiple_files=True)
gride_files = st.file_uploader("Upload DataGride CSV files", type=["csv"], accept_multiple_files=True)
drop_files = st.file_uploader("Upload DataDrop JSON files", type=["json"], accept_multiple_files=True)

def clear_raw_folder():
    for file in RAW_DIR.glob("*"):
        if file.is_file():
            file.unlink()

def save_uploaded_files(files, prefix):
    saved = []
    for i, file in enumerate(files, start=1):
        ext = Path(file.name).suffix
        path = RAW_DIR / f"{prefix}_{i}{ext}"
        with open(path, "wb") as f:
            f.write(file.getbuffer())
        saved.append(path.name)
    return saved

if st.button("Save Uploaded Files"):
    saved = []

    clear_raw_folder()

    if detail_files:
        saved += save_uploaded_files(detail_files, "details_data")
    if gride_files:
        saved += save_uploaded_files(gride_files, "grid_data")
    if drop_files:
        saved += save_uploaded_files(drop_files, "drop")

    if saved:
        st.success("Old raw files deleted. New files saved successfully.")
        st.write(saved)
    else:
        st.warning("Please upload files first.")

pipeline_scripts = [
    "pfe_3_dataCleaning_UPDATED.py",
    "pfe_4_ip_lifecycle_analysis_UPDATED.py",
    "pfe_5_feature_engineering_labels_UPDATED.py",
    "inference_pipeline_SAFE_COPY_v2.py",
    "warmup_strategy_engine.py",
]

if st.button("Run Full Pipeline"):
    logs = []

    for script in pipeline_scripts:
        script_path = BASE_DIR / script

        if not script_path.exists():
            logs.append(f"Missing script: {script}")
            continue

        st.write(f"Running {script} ...")

        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True,
        )

        logs.append(f"\n===== {script} =====")
        logs.append(result.stdout)

        if result.stderr:
            logs.append("ERROR:")
            logs.append(result.stderr)

        if result.returncode != 0:
            st.error(f"Pipeline stopped at {script}")
            st.code("\n".join(logs))
            st.stop()

    st.success("Full pipeline completed successfully.")
    st.code("\n".join(logs))

st.divider()

st.subheader("Processed Files Preview")

preview_files = {
    "Final Data": PROCESSED_DIR / "final_data.csv",
    "IP Analyse": PROCESSED_DIR / "IP_Analyse.csv",
    "ML Dataset": PROCESSED_DIR / "df_ml.csv",
    "Inference Predictions": PROCESSED_DIR / "inference_predictions.csv",
    "Warm-up Strategy Plan": PROCESSED_DIR / "warmup_strategy_plan.csv",
}

for name, path in preview_files.items():
    with st.expander(name):
        if path.exists():
            df = pd.read_csv(path)
            st.write(f"Shape: {df.shape}")
            st.dataframe(df.head(50), use_container_width=True)
        else:
            st.warning(f"{path.name} not found yet.")