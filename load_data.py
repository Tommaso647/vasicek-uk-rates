"""
Download the Bank of England's month-end UK nominal gilt spot curve and save it as one CSV.

Source: Bank of England yield curve data (the "GLC" nominal curves, month-end).
The zip holds three Excel files (1970-2015, 2016-2024, 2025-present). Each has a sheet
"4. spot curve": one row per month-end, one column per maturity (0.5y, 1y, ... 40y),
values are continuously compounded zero-coupon yields in percent.

Output: data/uk_gilt_spot_monthly.csv  (index = month-end date, columns = maturity in years, values in %)

Run once:  python load_data.py
"""

import io
import zipfile
from pathlib import Path
from urllib.request import urlopen

import pandas as pd

URL = "https://www.bankofengland.co.uk/-/media/boe/files/statistics/yield-curves/glcnominalmonthedata.zip"
RAW = Path("data/raw/glcnominalmonthedata.zip")
OUT = Path("data/uk_gilt_spot_monthly.csv")


def download():
    if not RAW.exists():
        RAW.parent.mkdir(parents=True, exist_ok=True)
        RAW.write_bytes(urlopen(URL).read())


def read_spot_sheet(xlsx_bytes):
    sheet = pd.read_excel(io.BytesIO(xlsx_bytes), sheet_name="4. spot curve", header=None)
    maturities = sheet.iloc[3, 1:].astype(float).values        # row 4 of the sheet holds "years: 0.5, 1.0, ..."
    rows = sheet.iloc[4:]
    dates = pd.to_datetime(rows[0], errors="coerce")
    rows = rows[dates.notna()]                                  # drop any footer rows that aren't dates
    curve = rows.iloc[:, 1:].astype(float)
    curve.index = pd.to_datetime(rows[0])
    curve.columns = maturities
    return curve


def main():
    download()
    with zipfile.ZipFile(RAW) as z:
        parts = [read_spot_sheet(z.read(name)) for name in sorted(z.namelist()) if name.endswith(".xlsx")]
    curve = pd.concat(parts).sort_index()
    curve = curve[~curve.index.duplicated(keep="last")]
    curve.index.name = "date"
    curve.to_csv(OUT)
    print(f"Saved {OUT}: {curve.shape[0]} month-ends, {curve.index.min():%b %Y} to {curve.index.max():%b %Y}, "
          f"maturities {curve.columns.min()}y to {curve.columns.max()}y")


if __name__ == "__main__":
    main()
