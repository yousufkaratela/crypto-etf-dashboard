import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

# -------------------------------
# Basic Streamlit App Setup
# -------------------------------
st.set_page_config(page_title="Crypto ETF Dashboard", layout="wide")

st.title("🚀 Crypto ETF Dashboard")
st.write("✅ This is a minimal working version of the app. If you can see this, the deployment works fine.")

# -------------------------------
# Create Dummy Data
# -------------------------------
np.random.seed(42)
dates = pd.date_range("2025-01-01", periods=30)
data = pd.DataFrame({
    "Date": dates,
    "BTC_ETF_Flows": np.random.randint(-50, 100, size=30),
    "ETH_ETF_Flows": np.random.randint(-30, 80, size=30)
})

# -------------------------------
# Show Data Table
# -------------------------------
st.subheader("📊 Sample ETF Flows Data")
st.dataframe(data)

# -------------------------------
# Line Chart
# -------------------------------
st.subheader("📈 ETF Flows Over Time")
chart = alt.Chart(data).transform_fold(
    ["BTC_ETF_Flows", "ETH_ETF_Flows"],
    as_=["ETF", "Flows"]
).mark_line().encode(
    x="Date:T",
    y="Flows:Q",
    color="ETF:N"
).properties(width=700, height=400)

st.altair_chart(chart, use_container_width=True)

# -------------------------------
# Summary Stats
# -------------------------------
st.subheader("📌 Summary")
st.metric("Total BTC ETF Flows", f"{data['BTC_ETF_Flows'].sum()} M")
st.metric("Total ETH ETF Flows", f"{data['ETH_ETF_Flows'].sum()} M")
