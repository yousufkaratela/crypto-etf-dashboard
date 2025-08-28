import requests
import pandas as pd
import streamlit as st
import altair as alt
from io import StringIO

# -------------------------------
# Page setup
# -------------------------------
st.set_page_config(page_title="Crypto ETF Flows Dashboard", page_icon="📊", layout="wide")
st.title("📊 Crypto ETF Flows Dashboard (BlackRock, Grayscale, Fidelity, …)")
st.caption("Live ETF flows pulled from Farside (parsed from markdown table).")

# -------------------------------
# Data fetcher
# -------------------------------
@st.cache_data(ttl=1800, show_spinner="Fetching live ETF flows…")
def fetch_flows():
    url = "https://r.jina.ai/http://farside.co.uk/bitcoin-etf-flows"
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers, timeout=20)
    r.raise_for_status()
    text = r.text

    # Keep only markdown table rows
    lines = [l for l in text.splitlines() if "|" in l]
    if not lines:
        return pd.DataFrame()

    md_table = "\n".join(lines)

    # Parse with pandas
    try:
        df = pd.read_csv(StringIO(md_table), sep="|").dropna(axis=1, how="all")
    except Exception:
        return pd.DataFrame()

    # Clean headers
    df.columns = [c.strip() for c in df.columns]

    if "Date" not in df.columns:
        return pd.DataFrame()

    # Melt into long form: date | etf | flow
    df = df.melt(id_vars=["Date"], var_name="etf", value_name="flow")
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

    # Clean flows
    def parse_flow(x):
        if not isinstance(x, str):
            return 0
        x = x.replace("$", "").replace("m", "").replace("+", "").replace(",", "").strip()
        try:
            return float(x) * 1_000_000
        except:
            return 0

    df["flow"] = df["flow"].apply(parse_flow)
    return df.dropna()

# -------------------------------
# Load data
# -------------------------------
df = fetch_flows()
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
st.subheader("📉 Daily Flows")
flow_chart = alt.Chart(df).mark_line(point=True).encode(
    x="Date:T",
    y="flow:Q",
    color="etf:N",
    tooltip=["Date:T", "etf:N", alt.Tooltip("flow:Q", format=",.0f")]
)
st.altair_chart(flow_chart, use_container_width=True)

# -------------------------------
# Table
# -------------------------------
st.subheader("🧾 Data")
st.dataframe(df.sort_values(["Date", "etf"], ascending=[False, True]).head(rows))
