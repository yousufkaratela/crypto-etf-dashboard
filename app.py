import streamlit as st
import pandas as pd
from crypto_etf_flows import get_etf_flows

st.set_page_config(page_title="Crypto ETF Flows Dashboard", layout="wide")

st.title("📊 Crypto ETF Flows Dashboard (BlackRock, Grayscale, Fidelity)")

try:
    df = get_etf_flows()
    if df is not None and not df.empty:
        st.success("Data fetched successfully ✅")
        st.dataframe(df)
    else:
        st.warning("⚠️ No data available.")
except Exception as e:
    st.error(f"Error fetching data: {e}")
