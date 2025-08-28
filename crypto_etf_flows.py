import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import altair as alt

# -------------------------------
# 1. Data Fetching (Scraping Farside ETF flows)
# -------------------------------
@st.cache_data
def get_farside_data():
    url = "https://farside.co.uk/bitcoin-etf-flows"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/116.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        # Parse the HTML page
        soup = BeautifulSoup(response.text, "html.parser")
        table = soup.find("table")

        # Convert table to DataFrame
        df = pd.read_html(str(table))[0]

        # Ensure date is parsed correctly
        if "Date" in df.columns:
            df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

        return df
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame()

# -------------------------------
# 2. Streamlit App Layout
# -------------------------------
st.set_page_config(page_title="Crypto ETF Flows Dashboard", layout="wide")

st.title("📊 Crypto ETF Flows Dashboard (BlackRock, Grayscale, Fidelity)")

df = get_farside_data()

if df.empty:
    st.warning("⚠️ No data available.")
else:
    st.success("✅ Data loaded successfully!")

    st.dataframe(df)

    # Example chart (Net Flows over time if column exists)
    if "Net Flows" in df.columns:
        chart = (
            alt.Chart(df)
            .mark_bar()
            .encode(
                x="Date:T",
                y="Net Flows:Q",
                tooltip=list(df.columns)
            )
            .properties(width=800, height=400)
        )
        st.altair_chart(chart, use_container_width=True)
