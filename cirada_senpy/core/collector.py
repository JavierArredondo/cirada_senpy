import pandas as pd
import requests
from typing import List


class Collector:
    def __init__(self, data: pd.DataFrame):
        self.data = data
        self.headers = {"Content-Type": "application/json"}
        self.url = "http://cutouts.cirada.ca/download_fits_batch/"
        pass

    def create_payloads(self) -> List[dict]:
        payloads = []
        for index, source in self.data.groupby("source_name"):
            source_payload = []
            for j, row in source.iterrows():
                payload = {
                    "filepath": f"/tmp/{row['filename']}",
                    "filename": row["filename"],
                    "row": index,
                    "RA": row["ra"],
                    "DEC": row["dec"],
                    "only_mosaic": False
                }
                source_payload.append(payload)
            payloads.append({index: source_payload})
        return payloads

    def download(self):
        payloads = self.create_payloads()
        for payload in payloads:
            response = requests.request("POST", self.url, json=payload, headers=self.headers)
            output_name = list(payload.keys())[0]
            with open(f"{output_name}.tgz", "wb") as f:
                f.write(response.content)
