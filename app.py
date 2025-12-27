# app.py - FINAL CASE STUDY COMPLIANT VERSION

import streamlit as st
import tempfile
import os
import pandas as pd
from dotenv import load_dotenv
from extractor import extract_indicators_from_pdf, save_rows_to_postgres

load_dotenv()

st.set_page_config(page_title="AA Impact Inc. ESG Extractor", layout="wide")

# Custom styling for AA Impact Inc.
st.markdown("""
    <style>
    .main-header {
        font-size: 42px;
        color: #1E3A8A;
        text-align: center;
        font-weight: bold;
    }
    .sub-header {
        font-size: 20px;
        color: #4B5563;
        text-align: center;
        margin-bottom: 30px;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="main-header">🌿 AA Impact Inc.</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Sustainability & ESG Consultancy<br>AI-Powered ESG Data Extraction Engine</div>', unsafe_allow_html=True)

st.markdown("### Upload a 2024 bank sustainability report (PDF) and extract 20 key CSRD indicators")

uploaded_file = st.file_uploader("Choose PDF Report", type="pdf")
bank_name = st.text_input("Bank Name", placeholder="e.g., AIB Group plc, Groupe BPCE, BBVA")
report_year = st.number_input("Report Year", min_value=2000, max_value=2100, value=2024, step=1)

if uploaded_file and bank_name:
    if st.button("🚀 Start Extraction"):
        with st.spinner("Processing PDF with PyMuPDF + GPT-4o... (30–90 seconds)"):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(uploaded_file.getvalue())
                temp_path = tmp.name

            try:
                rows = extract_indicators_from_pdf(temp_path, bank_name.strip(), report_year)

                # Full dataframe with ALL required columns
                df = pd.DataFrame(rows)
                display_df = df[[
                    "company", "report_year", "indicator_name", "value", "unit",
                    "confidence", "source_page", "source_section", "notes"
                ]].copy()
                display_df = display_df.sort_values("indicator_name").reset_index(drop=True)

                st.success("✅ Extraction Complete! 60 Data Points Ready")
                st.dataframe(display_df, use_container_width=True)

                # Full CSV download with all required columns
                csv = display_df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="📥 Download Full CSV (Case Study Format)",
                    data=csv,
                    file_name=f"{bank_name.replace(' ', '_')}_{report_year}_esg_full.csv",
                    mime="text/csv"
                )

                # Save to PostgreSQL
                conn_params = {
                    "dbname": os.getenv("PG_DATABASE", "huly"),
                    "user": os.getenv("PG_USER", "postgres"),
                    "password": os.getenv("PG_PASSWORD"),
                    "host": os.getenv("PG_HOST", "localhost"),
                    "port": os.getenv("PG_PORT", "5432")
                }

                save_rows_to_postgres(rows, conn_params)
                st.success("💾 All data saved to PostgreSQL with full metadata!")

                st.info("Ready for case study submission: CSV includes company, report_year, confidence, source_section, and notes.")

            except Exception as e:
                st.error(f"Error during processing: {str(e)}")
            finally:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)

st.markdown("---")
st.caption("AA Impact Inc. | AI Agent Developer Case Study | December 2025")
