import streamlit as st
from crypto_etf_flows import fetch_etf_flows

st.set_page_config(page_title="Crypto ETF Flows Dashboard", layout="wide")

st.title("📊 Crypto ETF Flows Dashboard (BlackRock, Grayscale, Fidelity, …)")
st.caption("Live flows parsed from Farside using BeautifulSoup.")

# Refresh button
if st.button("🔄 Force refresh (clear cache)"):
    st.cache_data.clear()
    st.rerun()

# Fetch ETF data
try:
    df = fetch_etf_flows()
    st.success("✅ Data fetched successfully!")
    st.dataframe(df, use_container_width=True)
except Exception as e:
    st.error(f"Error fetching data: {e}")
