# crypto_etf_flows.py
import re
from io import StringIO
from typing import List

import altair as alt
import pandas as pd
import requests
import streamlit as st

# -------------------------------
# Page setup
# -------------------------------
st.set_page_config(page_title="Crypto ETF Flows Dashboard", page_icon="📊", layout="wide")
st.title("📊 Crypto ETF Flows Dashboard (BlackRock, Grayscale, Fidelity, …)")
st.caption("Live flows parsed from Farside via Jina reader (works around 403).")

JINA_URLS: List[str] = [
    # Try several variants to survive subtle redirects/caching differences
    "https://r.jina.ai/http://farside.co.uk/bitcoin-etf-flows",
    "https://r.jina.ai/https://farside.co.uk/bitcoin-etf-flows",
    "https://r.jina.ai/http://www.farside.co.uk/bitcoin-etf-flows",
    "https://r.jina.ai/https://www.farside.co.uk/bitcoin-etf-flows",
    "https://r.jina.ai/http://farside.co.uk/bitcoin-etf-flows/",
    "https://r.jina.ai/https://farside.co.uk/bitcoin-etf-flows/",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/124.0 Safari/537.36"
}

# -------------------------------
# Helpers
# -------------------------------
def _to_millions_number(x) -> float:
    """Convert values like '$123.4m', '+12.3m', '-3.2m', '—', '' to float (USD)."""
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return 0.0

    s = str(x).strip().lower()
    if s in {"—", "-", "--", "nan", ""}:
        return 0.0

    # Remove currency/grouping signs
    s = s.replace("$", "").replace(",", "").replace("usd", "").strip()

    # Match optional sign + number + optional scale (m/b)
    m = re.search(r"([+-]?\d+(?:\.\d+)?)(?:\s*([mb]))?", s)
    if not m:
        # Sometimes raw numbers with no suffix; treat as millions already or 0
        try:
            return float(s)
        except Exception:
            return 0.0

    val = float(m.group(1))
    scale = m.group(2)
    if scale == "b":
        val *= 1_000_000_000
    else:
        # default to millions
        val *= 1_000_000
    return val


def _pick_flows_table(tables: List[pd.DataFrame]) -> pd.DataFrame | None:
    """Pick the table that has a 'Date' column (case-insensitive)."""
    for t in tables:
        cols = [str(c).strip() for c in t.columns]
        if any(c.lower() == "date" for c in cols):
            t.columns = cols
            return t
    return None


@st.cache_data(ttl=30 * 60, show_spinner="Fetching live ETF flows…")  # 30 minutes
def fetch_farside_flows() -> pd.DataFrame:
    last_error = None

    for url in JINA_URLS:
        try:
            r = requests.get(url, headers=HEADERS, timeout=20)
            r.raise_for_status()
            html = r.text
            # Parse *HTML tables* with pandas (uses bs4 + lxml behind the scenes)
            tables = pd.read_html(StringIO(html))  # may raise if none
            if not tables:
                continue

            base = _pick_flows_table(tables)
            if base is None or base.empty:
                continue

            # Normalize 'Date'
            base["Date"] = pd.to_datetime(base["Date"], errors="coerce")
            base = base.dropna(subset=["Date"])

            # Drop obviously non-flow columns if present
            drop_like = {"total", "aum", "issuer", "inception", "fund", "cumulative"}
            keep_cols = ["Date"] + [
                c for c in base.columns
                if c != "Date" and all(k not in c.lower() for k in drop_like)
            ]
            base = base[keep_cols]

            # Clean all flow columns
            for c in base.columns:
                if c == "Date":
                    continue
                base[c] = base[c].apply(_to_millions_number)

            # Reshape to long
            long_df = base.melt(id_vars=["Date"], var_name="etf", value_name="flow_usd")
            long_df = long_df.sort_values("Date").reset_index(drop=True)
            return long_df
        except Exception as e:
            last_error = e
            continue

    # If we get here, everything failed
    msg = f"All sources failed. Last error: {last_error}"
    raise RuntimeError(msg)


# -------------------------------
# Controls
# -------------------------------
col_a, col_b = st.columns([1, 2])
with col_a:
    if st.button("🔁 Force refresh (clear cache)", use_container_width=True):
        fetch_farside_flows.clear()  # type: ignore[attr-defined]
        st.experimental_rerun()

# -------------------------------
# Load data
# -------------------------------
try:
    df = fetch_farside_flows()
except Exception as e:
    st.error(f"Error fetching data: {e}")
    st.stop()

if df.empty:
    st.warning("No flow data parsed from source.")
    st.stop()

# -------------------------------
# Sidebar filters
# -------------------------------
with st.sidebar:
    st.header("Filters")
    all_etfs = sorted(df["etf"].unique())
    default_pick = [e for e in all_etfs if e.upper() in {"IBIT", "GBTC", "FBTC"}]
    if not default_pick:
        default_pick = all_etfs[:5]
    chosen = st.multiselect("ETFs", all_etfs, default=default_pick)
    date_min = st.date_input("From date", value=pd.to_datetime(df["Date"]).min().date())
    date_max = st.date_input("To date", value=pd.to_datetime(df["Date"]).max().date())

mask = (
    df["etf"].isin(chosen) &
    (df["Date"].dt.date >= pd.to_datetime(date_min).date()) &
    (df["Date"].dt.date <= pd.to_datetime(date_max).date())
)
df_f = df.loc[mask].copy()

if df_f.empty:
    st.warning("No rows after filtering. Adjust your filters.")
    st.stop()

# -------------------------------
# Charts
# -------------------------------
st.subheader("📉 Daily Net Flows (USD)")
chart = (
    alt.Chart(df_f)
    .mark_line(point=True)
    .encode(
        x=alt.X("Date:T", title="Date"),
        y=alt.Y("flow_usd:Q", title="Flow (USD)", axis=alt.Axis(format="~s")),
        color=alt.Color("etf:N", title="ETF"),
        tooltip=[
            alt.Tooltip("Date:T", title="Date"),
            alt.Tooltip("etf:N", title="ETF"),
            alt.Tooltip("flow_usd:Q", title="Flow", format="$.3s"),
        ],
    )
    .interactive()
)
st.altair_chart(chart, use_container_width=True)

st.subheader("📈 Cumulative Net Flows (USD)")
cum = (
    df_f.sort_values(["etf", "Date"])
        .groupby("etf", as_index=False)
        .apply(lambda g: g.assign(cum_flow=g["flow_usd"].cumsum()))
        .reset_index(drop=True)
)
cum_chart = (
    alt.Chart(cum)
    .mark_line()
    .encode(
        x=alt.X("Date:T", title="Date"),
        y=alt.Y("cum_flow:Q", title="Cumulative Flow (USD)", axis=alt.Axis(format="~s")),
        color=alt.Color("etf:N", title="ETF"),
        tooltip=[
            alt.Tooltip("Date:T", title="Date"),
            alt.Tooltip("etf:N", title="ETF"),
            alt.Tooltip("cum_flow:Q", title="Cum Flow", format="$.3s"),
        ],
    )
    .interactive()
)
st.altair_chart(cum_chart, use_container_width=True)

# -------------------------------
# Table
# -------------------------------
st.subheader("🧾 Raw data")
st.dataframe(
    df_f.sort_values(["Date", "etf"], ascending=[False, True]),
    use_container_width=True,
    height=420,
)
st.download_button(
    "💾 Download CSV",
    data=df_f.to_csv(index=False).encode("utf-8"),
    file_name="bitcoin_etf_flows.csv",
    mime="text/csv",
)
