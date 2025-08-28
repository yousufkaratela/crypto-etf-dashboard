import re
import io
import requests
import pandas as pd
import altair as alt
import streamlit as st

# --------------------------------------------------------------------------------------
# CONFIG
# --------------------------------------------------------------------------------------
st.set_page_config(page_title="Crypto ETF Flows Dashboard", page_icon="📊", layout="wide")
st.title("📊 Crypto ETF Flows Dashboard (BlackRock, Grayscale, Fidelity, …)")

st.caption(
    "Live flows pulled from Farside. If the site layout changes, parsing may need a tweak."
)

# --------------------------------------------------------------------------------------
# HELPERS
# --------------------------------------------------------------------------------------
def _to_number(x: str) -> float | None:
    """Convert strings like '1,234', '- 56', '—' to float; return None if blank."""
    if x is None:
        return None
    s = str(x).strip()
    if s in {"", "–", "—", "-", "N/A"}:
        return None
    s = s.replace(",", "")
    # Remove leading currency symbols or plus signs
    s = re.sub(r"^[+$£€]", "", s)
    # Remove any stray spaces around minus signs
    s = s.replace("−", "-").replace("–", "-")
    try:
        return float(s)
    except Exception:
        return None


@st.cache_data(ttl=60 * 30, show_spinner="Fetching latest ETF flows…")  # refresh every 30 min
def fetch_farside_flows() -> pd.DataFrame:
    """
    Fetch the Farside Bitcoin ETF flows page via r.jina.ai (read-only proxy)
    and return a tidy DataFrame: columns = ['date', 'etf', 'flow'].
    """
    # Farside HTML is often blocked to bots; the r.jina.ai read proxy is stable & cacheable.
    src_url = "https://farside.co.uk/bitcoin-etf-flows"
    proxy_url = f"https://r.jina.ai/{src_url}"

    # 1) Get HTML
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(proxy_url, headers=headers, timeout=20)
    resp.raise_for_status()
    html = resp.text

    # 2) Parse all HTML tables and pick the primary flows table (has a 'Date' column)
    tables = pd.read_html(html, flavor="lxml", thousands=",")
    flows_df = None
    for tbl in tables:
        cols = [str(c).strip().lower() for c in tbl.columns]
        if "date" in cols and len(tbl.columns) > 3:  # should have many ETF columns + Date
            flows_df = tbl.copy()
            break

    if flows_df is None:
        raise RuntimeError("Could not locate the flows table on the page.")

    # 3) Clean column names
    flows_df.columns = [str(c).strip() for c in flows_df.columns]

    # 4) Some tables include 'Total'/'Totals' columns; drop them if present
    drop_like = {"total", "totals"}
    to_drop = [c for c in flows_df.columns if str(c).strip().lower() in drop_like]
    if to_drop:
        flows_df = flows_df.drop(columns=to_drop)

    # 5) Convert Date
    flows_df.rename(columns={flows_df.columns[0]: "date"}, inplace=True)
    flows_df["date"] = pd.to_datetime(flows_df["date"], errors="coerce")

    # 6) Melt to long format: date | etf | flow
    long_df = flows_df.melt(id_vars=["date"], var_name="etf", value_name="flow_raw")

    # 7) Clean numbers
    long_df["flow"] = long_df["flow_raw"].map(_to_number)

    # Only keep rows with a valid date and some numeric flow (NaN rows come from missing entries)
    long_df = long_df.dropna(subset=["date"]).copy()
    # Some rows might be NaN flow (table blanks) — keep them as 0 for chart continuity
    long_df["flow"] = long_df["flow"].fillna(0.0)

    # Normalize ETF tickers (strip notes like '(Millions USD)' if they appear)
    long_df["etf"] = (
        long_df["etf"]
        .astype(str)
        .str.replace(r"\(.*?\)", "", regex=True)
        .str.strip()
    )

    # Sort
    long_df = long_df.sort_values(["etf", "date"]).reset_index(drop=True)

    return long_df[["date", "etf", "flow"]]


def cumulative_flows(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.sort_values(["etf", "date"])
          .groupby("etf", as_index=False)
          .apply(lambda g: g.assign(cum_flow=g["flow"].cumsum()))
          .reset_index(drop=True)
    )


# --------------------------------------------------------------------------------------
# DATA
# --------------------------------------------------------------------------------------
try:
    df = fetch_farside_flows()
except Exception as e:
    st.error(f"Error fetching data: {e}")
    st.stop()

if df.empty:
    st.warning("No data available right now.")
    st.stop()

# --------------------------------------------------------------------------------------
# SIDEBAR FILTERS
# --------------------------------------------------------------------------------------
with st.sidebar:
    st.header("Filters")
    all_etfs = sorted(df["etf"].unique())
    default_selection = [t for t in all_etfs if t.upper() in {"IBIT", "FBTC", "GBTC"}] or all_etfs[:5]
    selected_etfs = st.multiselect("Select ETFs", options=all_etfs, default=default_selection)

    st.write("**Rows**")
    max_rows = st.slider("Table rows to show", 20, 500, 100, step=20)

df_sel = df[df["etf"].isin(selected_etfs)].copy()
if df_sel.empty:
    st.warning("No rows match your selection.")
    st.stop()

# --------------------------------------------------------------------------------------
# KPI SUMMARY
# --------------------------------------------------------------------------------------
latest_date = df_sel["date"].max()
latest = df_sel[df_sel["date"] == latest_date].groupby("etf", as_index=False)["flow"].sum()
total_today = latest["flow"].sum()

col1, col2, col3 = st.columns(3)
col1.metric("Latest date", latest_date.date())
col2.metric("Total daily flows (USD)", f"{total_today:,.0f}")
col3.metric("ETFs shown", len(selected_etfs))

st.divider()

# --------------------------------------------------------------------------------------
# CHARTS
# --------------------------------------------------------------------------------------
st.subheader("📉 Daily Net Flows")
daily_chart = (
    alt.Chart(df_sel)
    .mark_line(point=True)
    .encode(
        x=alt.X("date:T", title="Date"),
        y=alt.Y("flow:Q", title="Net Flow (USD)"),
        color=alt.Color("etf:N", title="ETF"),
        tooltip=["date:T", "etf:N", alt.Tooltip("flow:Q", format=",.0f")],
    )
    .properties(height=320)
)
st.altair_chart(daily_chart, use_container_width=True)

st.subheader("📈 Cumulative Net Flows")
cum_df = cumulative_flows(df_sel)
cum_chart = (
    alt.Chart(cum_df)
    .mark_line(point=True)
    .encode(
        x=alt.X("date:T", title="Date"),
        y=alt.Y("cum_flow:Q", title="Cumulative Flow (USD)"),
        color=alt.Color("etf:N", title="ETF"),
        tooltip=["date:T", "etf:N", alt.Tooltip("cum_flow:Q", format=",.0f")],
    )
    .properties(height=320)
)
st.altair_chart(cum_chart, use_container_width=True)

# --------------------------------------------------------------------------------------
# DATA TABLE + EXPORT
# --------------------------------------------------------------------------------------
st.subheader("🧾 Data")
st.dataframe(
    df_sel.sort_values(["date", "etf"], ascending=[False, True]).head(max_rows),
    use_container_width=True,
)

csv = df_sel.to_csv(index=False).encode("utf-8")
st.download_button(
    "💾 Download CSV",
    data=csv,
    file_name="bitcoin_etf_flows.csv",
    mime="text/csv",
)
