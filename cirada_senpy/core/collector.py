from tqdm import tqdm
from typing import List

import os.path
import pandas as pd
import requests


class Collector:
    def __init__(self, data: pd.DataFrame, output_path="."):
        self.data = data
        self.headers = {"Content-Type": "application/json"}
        self.url = "http://cutouts.cirada.ca/download_fits_batch/"
        self.output_path = output_path

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
                    "only_mosaic": False,
                }
                source_payload.append(payload)
            payloads.append({index: source_payload})
        return payloads

    def download(self):
        payloads = self.create_payloads()
        progress_bar = tqdm(payloads)
        for payload in progress_bar:
            output_name = list(payload.keys())[0]
            progress_bar.set_description(f"Downloading {output_name}")
            response = requests.request(
                "POST", self.url, json=payload, headers=self.headers
            )
            output_path = os.path.join(self.output_path, f"{output_name}.tgz")
            with open(output_path, "wb") as f:
                f.write(response.content)
