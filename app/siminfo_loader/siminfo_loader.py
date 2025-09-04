import os
import re
import time
import logging
import requests
import pandas as pd
from postgres.postgres import DbWriter

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

class SimInfoLoader:
    def __init__(self, sheet_url: str, shared_dir: str, db_writer: DbWriter):
        self.sheet_url = sheet_url
        self.shared_dir = shared_dir
        self.db = db_writer
        os.makedirs(self.shared_dir, exist_ok=True)

    def _extract_sheet_id(self) -> str:
        m = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", self.sheet_url)
        if not m:
            raise ValueError("Could not fetch ID Google Sheet from URL")
        return m.group(1)

    def download_excel(self, filename_prefix: str = "world_output") -> str:
        sheet_id = self._extract_sheet_id()
        export_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"
        logging.info(f"Downloading Excel: {export_url}")
        resp = requests.get(export_url, timeout=60)
        resp.raise_for_status()
        ts = time.strftime("%Y%m%d_%H%M%S")
        dest_path = os.path.join(self.shared_dir, f"{filename_prefix}_{ts}.xlsx")
        with open(dest_path, "wb") as f:
            f.write(resp.content)
        logging.info(f"Saved: {dest_path}")
        return dest_path

    def parse_excel(self, xlsx_path: str) -> pd.DataFrame:
        logging.info(f"Read Excel (header=1): {xlsx_path}")
        df = pd.read_excel(xlsx_path, header=1, engine="openpyxl")
        print(df)
        df.columns = [str(c).strip() for c in df.columns]

        colmap = {
            "Slot / Channel": "channel_id",
            "Mpesa/Airtel": "operator",
            "phone number": "phone",
            "full name": "name",
            "Password": "pin",
            "IMSI": "imsi",
            "4 Last digits": "last_digits",
        }
        missing = [k for k in colmap if k not in df.columns]
        if missing:
            raise ValueError(f"Columns were not found: {missing}. There are: {list(df.columns)}")

        out = pd.DataFrame()
        out["channel_id"] = df["Slot / Channel"]
        out["operator"]   = df["Mpesa/Airtel"]
        out["phone"]      = df["phone number"]
        out["name"]       = df["full name"]

        def to_int_or_none(x):
            try:
                if pd.isna(x) or x == "":
                    return None
                return int(str(x).strip())
            except Exception:
                return None

        def digits_or_none(x):
            if pd.isna(x):
                return None
            s = str(x).strip()
            s = re.sub(r'\D', '', s)
            return s or None

        out["pin"]         = df["Password"].apply(to_int_or_none)
        out["imsi"]        = df["IMSI"].apply(digits_or_none)
        out["last_digits"] = df["4 Last digits"].apply(to_int_or_none)

        out["channel_id"] = out["channel_id"].apply(to_int_or_none)
        out = out[out["channel_id"].between(1, 32, inclusive="both")]

        return out.where(pd.notnull(out), None)

    def run(self):
        xlsx_path = self.download_excel()
        df = self.parse_excel(xlsx_path)
        self.db.upsert_sim_info_rows(df.to_dict(orient="records"))
        return xlsx_path, len(df)
