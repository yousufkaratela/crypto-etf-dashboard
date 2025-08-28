import requests
import pandas as pd
from bs4 import BeautifulSoup
import streamlit as st

st.set_page_config(page_title="Crypto ETF Flows Dashboard", layout="wide")

URL = "https://r.jina.ai/https://www.farside.co.uk/bitcoin-etf-flows"

@st.cache_data(ttl=600)
def fetch_farside_flows():
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(URL, headers=headers, timeout=10)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "lxml")
        table = soup.find("table")
        if not table:
            return None

        df = pd.read_html(str(table))[0]
        return df

    except Exception as e:
        st.error(f"❌ Error fetching data: {e}")
        return None


# --- Streamlit App ---
st.title("📊 Crypto ETF Flows Dashboard")

st.button("🔄 Force refresh (clear cache)", on_click=fetch_farside_flows.clear)

df = fetch_farside_flows()

if df is not None:
    st.success("✅ Data loaded successfully")
    st.dataframe(df, use_container_width=True)
else:
    st.warning("⚠️ Could not load ETF data. Please try again later.")
