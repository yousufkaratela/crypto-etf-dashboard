import requests
import pandas as pd
from bs4 import BeautifulSoup

# -----------------------------
# Fetch ETF Flows Data
# -----------------------------
def get_etf_flows():
    url = "https://farside.co.uk/bitcoin-etf-flows"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/115.0 Safari/537.36"
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # Locate the table
    table = soup.find("table")
    if table is None:
        raise ValueError("No table found on page")

    # Extract headers
    headers = [th.get_text(strip=True) for th in table.find("tr").find_all("th")]

    # Extract rows
    rows = []
    for tr in table.find_all("tr")[1:]:
        cells = [td.get_text(strip=True) for td in tr.find_all("td")]
        if cells:
            rows.append(cells)

    # Convert to DataFrame
    df = pd.DataFrame(rows, columns=headers)
    return df


# -----------------------------
# Main function for Streamlit
# -----------------------------
if __name__ == "__main__":
    try:
        df = get_etf_flows()
        print(df.head())
    except Exception as e:
        print("Error fetching ETF flows:", e)
