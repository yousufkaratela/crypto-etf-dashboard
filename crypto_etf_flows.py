import re
import requests
import pandas as pd
import altair as alt
import streamlit as st
from io import StringIO

st.set_page_config(page_title="Crypto ETF Flows Dashboard", page_icon="📊", layout="wide")
st.title("📊 Crypto ETF Flows Dashboard (BlackRock, Grayscale, Fidelity, …)")
st.caption("Live ETF flows pulled from Farside (parsed from text, no HTML table needed).")

# -------------------------------
# Fetch & parse
# -------------------------------
@st.cache_data(ttl=1800, show_spinner="Fetching live ETF flows…")
def fetch_flows():
    url = "https://r.jina.ai/http://farside.co.uk/bitcoin-etf-flows"
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers, timeout=20)
    r.raise_for_status()
    text = r.text

    # Extract lines like: 2025-08-27 | IBIT | +$155.3m
    pattern = re.compile(r"(\d{4}-\d{2}-\d{2}).*?([A-Z]{3,5}).*?([-+]?\$?\d[\d,.]*)m", re.I)
    rows = []
    for date, etf, val in pattern.findall(text):
        # Clean value
        val = val.replace("$", "").replace(",", "")
        try:
            flow = float(val) * 1_000_000
        except:
            continue
        rows.append((pd.to_datetime(date), etf.upper(), flow))

    df = pd.DataFrame(rows, columns=["date", "etf", "flow"])
    return df.sort_values(["etf", "date"])


def cumulative(df):
    return df.groupby("etf", group_keys=False).apply(
        lambda g: g.assign(cum_flow=g["flow"].cumsum())
    )

# -------------------------------
# Load
# -------------------------------
try:
    df = fetch_flows()
except Exception as e:
    st.error(f"Failed to fetch flows: {e}")
    st.stop()

if df.empty:
    st.warning("No flow data parsed from source.")
    st.stop()

# -------------------------------
# Sidebar filters
# -------------------------------
with st.sidebar:
    st.header("Filters")
    etfs = sorted(df["etf"].unique())
    selected = st.multiselect("Select ETFs", etfs, default=etfs[:5])
    rows = st.slider("Rows to show", 20, 300, 100)

df = df[df["etf"].isin(selected)]

# -------------------------------
# Charts
# -------------------------------
st.subheader("📉 Daily Flows (USD)")
daily_chart = alt.Chart(df).mark_line(point=True).encode(
    x="date:T", y="flow:Q", color="etf:N",
    tooltip=["date:T", "etf:N", alt.Tooltip("flow:Q", format=",.0f")]
)
st.altair_chart(daily_chart, use_container_width=True)

st.subheader("📈 Cumulative Flows (USD)")
cum_df = cumulative(df)
cum_chart = alt.Chart(cum_df).mark_line(point=True).encode(
    x="date:T", y="cum_flow:Q", color="etf:N",
    tooltip=["date:T", "etf:N", alt.Tooltip("cum_flow:Q", format=",.0f")]
)
st.altair_chart(cum_chart, use_container_width=True)

# -------------------------------
# Data table
# -------------------------------
st.subheader("🧾 Data")
st.dataframe(df.sort_values(["date", "etf"], ascending=[False, True]).head(rows))

csv = df.to_csv(index=False).encode("utf-8")
st.download_button("💾 Download CSV", csv, "etf_flows.csv", "text/csv")
