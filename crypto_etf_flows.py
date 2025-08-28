import requests
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

# --------------------
# 1. Data Fetching (Scraping Farside ETF flows)
# --------------------
@st.cache_data
def get_farside_data():
    url = "https://farside.co.uk/bitcoin-etf-flows"
    try:
        # Read HTML tables directly
        tables = pd.read_html(url)
        df = tables[0]  # First table is the ETF flows table

        # Standardize column names
        df.columns = [c.strip().lower() for c in df.columns]

        # Rename if needed
        if "fund" in df.columns:
            df = df.rename(columns={"fund": "etf"})
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")

        # Convert numeric columns
        if "flow ($m)" in df.columns:
            df["flow"] = pd.to_numeric(df["flow ($m)"], errors="coerce") * 1_000_000
            df = df.drop(columns=["flow ($m)"])

        return df.dropna(subset=["date"])
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame()

# --------------------
# 2. Streamlit Dashboard
# --------------------
st.set_page_config(page_title="ETF Flow Dashboard", layout="wide")
st.title("📊 Crypto ETF Flows Dashboard (BlackRock, Grayscale, Fidelity)")

# Load data
df = get_farside_data()
if df.empty:
    st.warning("No data available.")
    st.stop()

# ETF Selector
etfs = sorted(df["etf"].unique())
selected_etfs = st.multiselect(
    "Select ETFs to Display", etfs, default=etfs[:3]
)

# Filter data
df_filtered = df[df["etf"].isin(selected_etfs)]

# --------------------
# 3. Charts
# --------------------

st.subheader("Daily Net Flows")
fig, ax = plt.subplots(figsize=(10, 5))
for etf in selected_etfs:
    etf_data = df_filtered[df_filtered["etf"] == etf]
    ax.plot(etf_data["date"], etf_data["flow"], label=etf)

ax.set_title("Daily ETF Net Flows")
ax.set_xlabel("Date")
ax.set_ylabel("Net Flow (USD)")
ax.legend()
st.pyplot(fig)

# Cumulative flows
st.subheader("Cumulative Net Flows")
cum_df = (
    df_filtered.groupby(["date", "etf"])["flow"]
    .sum()
    .groupby(level=1)
    .cumsum()
    .reset_index()
)
fig2, ax2 = plt.subplots(figsize=(10, 5))
for etf in selected_etfs:
    etf_data = cum_df[cum_df["etf"] == etf]
    ax2.plot(etf_data["date"], etf_data["flow"], label=etf)

ax2.set_title("Cumulative ETF Net Flows")
ax2.set_xlabel("Date")
ax2.set_ylabel("Cumulative Flow (USD)")
ax2.legend()
st.pyplot(fig2)

# --------------------
# 4. Data Table + Export
# --------------------
st.subheader("Raw Data")
st.dataframe(df_filtered.sort_values("date", ascending=False))

st.download_button(
    label="💾 Download Data as CSV",
    data=df_filtered.to_csv(index=False).encode("utf-8"),
    file_name="etf_flows.csv",
    mime="text/csv",
)
