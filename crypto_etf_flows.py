import pandas as pd
import requests
from bs4 import BeautifulSoup
import streamlit as st

URL = "https://www.farside.co.uk/bitcoin-etf-flows"

@st.cache_data(ttl=3600)  # cache for 1h
def fetch_etf_flows() -> pd.DataFrame:
    """
    Fetches ETF flow data from Farside using BeautifulSoup.
    """

    try:
        response = requests.get(URL, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()

        # Parse HTML
        soup = BeautifulSoup(response.text, "html.parser")

        # Find all tables
        tables = pd.read_html(str(soup))
        if not tables:
            raise RuntimeError("No tables found on the ETF flows page")

        df = tables[0]
        df.columns = [col.strip() for col in df.columns]  # clean headers
        return df

    except Exception as e:
        raise RuntimeError(f"Failed to fetch ETF flows: {e}")
