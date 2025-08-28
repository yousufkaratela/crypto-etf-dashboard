import pandas as pd
import requests
from requests_html import HTMLSession
import streamlit as st

URL = "https://www.farside.co.uk/bitcoin-etf-flows"

@st.cache_data(ttl=3600)  # cache for 1h
def fetch_etf_flows() -> pd.DataFrame:
    """
    Fetches ETF flow data from Farside.
    Tries requests first, then falls back to requests_html.
    """

    # --- Method 1: Simple requests ---
    try:
        response = requests.get(URL, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
        tables = pd.read_html(response.text)
        if tables:
            df = tables[0]
            df.columns = [col.strip() for col in df.columns]
            return df
    except Exception as e:
        print(f"⚠️ requests failed: {e}")

    # --- Method 2: requests_html with JS rendering ---
    try:
        session = HTMLSession()
        r = session.get(URL, headers={"User-Agent": "Mozilla/5.0"})
        r.html.render(timeout=30, sleep=2)
        tables = pd.read_html(r.html.html)
        if tables:
            df = tables[0]
            df.columns = [col.strip() for col in df.columns]
            return df
    except Exception as e:
        print(f"❌ requests_html failed: {e}")

    raise RuntimeError("No tables found in the ETF flows page.")
