import streamlit as st
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

st.set_page_config(
    page_title="IP Optimization Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("Email Sending IP Optimization System")

st.markdown("""
This platform helps analyze, predict, simulate, and optimize email sending IP behavior.

### Platform Modules

1. **Data Upload & Pipeline**
   - Upload raw Detail, Gride, and Drop files
   - Run cleaning, merging, feature engineering, and inference

2. **Global Overview**
   - Monitor global IP health, risk levels, errors, and stability

3. **IP Detail & Lifecycle**
   - Analyze one selected IP across its full lifecycle

4. **Prediction, Simulation & Scenario Comparison**
   - Test strategies, compare scenarios, and generate warm-up plans

5. **Final Decision & Explainable AI**
   - Get final operational decisions and model explanations
""")

st.info("Use the sidebar to navigate between dashboards.")

st.success("Dashboard structure initialized successfully.")