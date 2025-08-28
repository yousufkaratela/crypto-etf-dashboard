import requests
import pandas as pd
from bs4 import BeautifulSoup
import streamlit as st

URL = "https://r.jina.ai/https://www.farside.co.uk/bitcoin-etf-flows"

@st.cache_data(ttl=600)
def fetch_farside_flows():
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(URL, headers=headers, timeout=10)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "lxml")
    table = soup.find("table")
    if not table:
        raise ValueError("No table found on Farside (via Jina proxy)")

    df = pd.read_html(str(table))[0]
    return df
