import requests
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

# --------------------
# 1. Data Fetching
# --------------------
@st.cache_data
def get_farside_data():
    url = "https://farside.co.uk/bitcoin-etf-flows"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/115.0 Safari/537.36"
    }
    try:
        # Fetch page with browser-like headers
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        # Extract tables
        dfs = pd.read_html(response.text)
        df = dfs[0]  # ETF flows table is the first one

        # Clean columns
        df.columns = [c.lower().strip().replace(" ", "_") for c in df.columns]

        # Ensure consistent column names
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")

        # Rename flow column if needed
        if "net_flow_$m" in df.columns:
            df = df.rename(columns={"net_flow_$m": "flow"})

        return df

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
selected_etfs = st.multiselect("Select ETFs to Display", etfs, default=etfs[:3])

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
ax.set_ylabel("Net Flow (USD Millions)")
ax.legend()
st.pyplot(fig)

# Cumulative flows
st.subheader("Cumulative Net Flows")
cum_df = df_filtered.groupby(["date", "etf"])["flow"].sum().groupby(level=1).cumsum().reset_index()
fig2, ax2 = plt.subplots(figsize=(10, 5))
for etf in selected_etfs:
    etf_data = cum_df[cum_df["etf"] == etf]
    ax2.plot(etf_data["date"], etf_data["flow"], label=etf)

ax2.set_title("Cumulative ETF Net Flows")
ax2.set_xlabel("Date")
ax2.set_ylabel("Cumulative Flow (USD Millions)")
ax2.legend()
st.pyplot(fig2)

# --------------------
# 4. Data Table + Export
# --------------------
st.subheader("Raw Data")
st.dataframe(df_filtered.sort_values("date", ascending=False))

st.download_button(
    label="💾 Download Data as CSV",
    data=df_filtered.to_csv(index=False).encode('utf-8'),
    file_name="etf_flows.csv",
    mime="text/csv",
)
