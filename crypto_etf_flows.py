# crypto_etf_flows.py
import pandas as pd
import requests
from bs4 import BeautifulSoup
import streamlit as st

URL = "https://www.farside.co.uk/bitcoin-etf-flows"

@st.cache_data(ttl=600)
def fetch_farside_flows():
    """Fetch ETF flow data from Farside and return as DataFrame."""
    resp = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")

    table = soup.find("table")
    if not table:
        raise ValueError("No table found on Farside page")

    df = pd.read_html(str(table))[0]
    return df

# ---------------- Streamlit UI ----------------
st.set_page_config(page_title="Crypto ETF Flows Dashboard", layout="wide")
st.title("📊 Crypto ETF Flows Dashboard")

col1, col2 = st.columns([1,4])

with col1:
    if st.button("🔁 Force refresh (clear cache)", use_container_width=True):
        fetch_farside_flows.clear()  # clear cached data
        st.rerun()  # ✅ modern replacement for st.experimental_rerun()

try:
    df = fetch_farside_flows()
    st.success("✅ Data fetched successfully!")
    st.dataframe(df, use_container_width=True)
except Exception as e:
    st.error(f"❌ Error fetching data: {e}")
