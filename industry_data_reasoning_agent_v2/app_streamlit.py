from __future__ import annotations

import os
import tempfile
import time
from pathlib import Path

import pandas as pd
import streamlit as st

# Ensure these imports match your actual local file structure
from src.pipeline import IndustryDataReasoningPipeline
from src.utils import safe_json

# 1. Page Config
st.set_page_config(page_title="Industry Data Reasoning Agent", layout="wide")

# 2. Custom CSS for Visual Effects & Animations
st.markdown(
    """
    <style>
    /* Add a pulsing, glowing drag-and-drop animation to the file uploader */
    [data-testid="stFileUploader"] {
        transition: transform 0.3s ease, box-shadow 0.3s ease, border 0.3s ease;
        border-radius: 12px;
        border: 2px dashed #4CAF50;
        background-color: rgba(76, 175, 80, 0.05);
        padding: 10px;
    }
    [data-testid="stFileUploader"]:hover {
        transform: scale(1.02);
        box-shadow: 0 8px 20px rgba(76, 175, 80, 0.3);
        border-color: #45a049;
        background-color: rgba(76, 175, 80, 0.1);
    }
    
    /* Button click animation */
    [data-testid="baseButton-primary"] {
        transition: transform 0.1s ease;
    }
    [data-testid="baseButton-primary"]:active {
        transform: scale(0.95);
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("Industry Data Reasoning Agent")
st.caption("Multi-agent analytics: ingestion → privacy → profiling → quality → planning → execution → visualization → verification → report → audit")

with st.sidebar:
    st.header("API Settings")
    api_key = st.text_input("OPENAI_API_KEY", type="password")
    model = st.text_input("Model", value=os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
    st.warning("API mode me schema, samples, question aur result preview LLM ko ja sakte hain. PII columns redacted samples ke saath bheje jaate hain.")

    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key
    if model:
        os.environ["OPENAI_MODEL"] = model

uploaded = st.file_uploader("Dataset upload karo", type=["csv", "xlsx", "xls", "json", "parquet"])
query = st.text_input("Question", value="top products by revenue")

if uploaded and st.button("Run Agent", type="primary"):
    suffix = Path(uploaded.name).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded.read())
        tmp_path = tmp.name

    # 3. Animated Step-by-Step Live Status Tracker
    with st.status("🚀 Initializing Agent Pipeline...", expanded=True) as status:
        st.write("📥 **Step 1:** Ingesting dataset into temporary storage...")
        time.sleep(0.8) # Visual delay for UI effect
        
        st.write("🕵️‍♂️ **Step 2:** Profiling schema and scanning for PII...")
        time.sleep(0.8)
        
        st.write("📊 **Step 3:** Analyzing data quality and drift...")
        time.sleep(0.8)
        
        st.write("🧠 **Step 4:** Planning and executing reasoning tasks (LLM running)...")
        
        # --- Actual Pipeline Execution ---
        pipeline = IndustryDataReasoningPipeline(model=model, runs_dir="runs")
        output = pipeline.run(tmp_path, query)
        # ---------------------------------
        
        st.write("✅ **Step 5:** Verifying results, generating charts, and compiling report...")
        time.sleep(0.5)
        
        # Mark status as complete and collapse the box
        status.update(label="🎉 Pipeline Complete!", state="complete", expanded=False)

    # Trigger a celebration animation
    st.balloons()

    # Display run stats
    st.subheader("Run Status")
    st.json({
        "run_id": output.get("run_id"),
        "llm_enabled": output.get("llm_enabled"),
        "model": output.get("model"),
        "raw_shape": output.get("raw_df_shape"),
        "clean_shape": output.get("clean_df_shape"),
    })

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Plan", "Result", "Insight & Verification", "Quality/Privacy", "Artifacts"])

    with tab1:
        st.json(output.get("plan", {}))
        st.subheader("Agent Timeline")
        st.json(output.get("messages", []))

    with tab2:
        if isinstance(output.get("result"), list):
            st.dataframe(pd.DataFrame(output["result"]))
        else:
            st.json(output.get("result", {}))
            
        if output.get("chart_path"):
            st.image(output["chart_path"])

    with tab3:
        st.success(output.get("insight", "No insights generated."))
        st.json(output.get("verification", {}))
        if output.get("fallback"):
            st.subheader("General Problem Solver")
            st.json(output["fallback"])

    with tab4:
        st.subheader("Data Quality")
        st.json(output.get("quality_report", {}))
        st.subheader("PII Report")
        st.json(output.get("pii_report", {}))
        st.subheader("Drift Report")
        st.json(output.get("drift_report", {}))

    with tab5:
        st.write(f"Report: `{output.get('report_path')}`")
        st.write(f"Chart: `{output.get('chart_path')}`")
        audit_json = safe_json(output, 100000)
        st.download_button("Download audit JSON", data=audit_json, file_name=f"audit_{output.get('run_id', 'log')}.json", mime="application/json")
else:
    st.info("Dataset upload karo, question likho, phir Run Agent dabao.")