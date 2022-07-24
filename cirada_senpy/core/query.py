import json
import pandas as pd
import requests


class Query:
    def __init__(
        self,
        x_size: int,
        y_size: int,
        source_name: str or None = None,
        ra: float or str or None = None,
        dec: float or str or None = None,
        coord_system: str = "Equatorial",
        thumbnail: bool = True,
    ):
        self.source_name = source_name
        self.ra = ra
        self.dec = dec
        self.x_size = x_size
        self.y_size = y_size
        self.coord_system = coord_system

        self.thumbnail = thumbnail
        self.boundary = "---011000010111000001101001"
        self.url = "http://cutouts.cirada.ca/rmcutout/rm_get_cutout/"
        self.headers = {
            "Content-Type": f"multipart/form-data; boundary={self.boundary}"
        }

    def create_payload(self) -> str:
        payload = f"-----011000010111000001101001\r\nContent-Disposition: form-data; "
        form_data = "Content-Disposition: form-data; "
        if self.x_size:
            payload += f'name="x_size"\r\n\r\n{self.x_size}\r\n--{self.boundary}\r\n{form_data}'
        if self.y_size:
            payload += f'name="y_size"\r\n\r\n{self.y_size}\r\n--{self.boundary}\r\n{form_data}'
        if self.source_name:
            payload += f'name="source_name"\r\n\r\n{self.source_name}\r\n--{self.boundary}\r\n{form_data}'
        if self.coord_system:
            payload += f'name="typeOfLoc"\r\n\r\n{self.coord_system}\r\n--{self.boundary}\r\n{form_data}'
        if self.ra and self.dec:
            payload += f'name="location"\r\n\r\n{self.ra} {self.dec}\r\n--{self.boundary}\r\n{form_data}'
        return payload

    def create_response(self, response: str) -> pd.DataFrame:
        response = json.loads(
            response[57:-5]
        )  # the string response has weird content like ?END?
        response = response["result"]
        cutouts_rows = []
        for key, value in response.items():
            main_data = {
                "source_name": value["source_name"],
                "ra": value["location"][0],
                "dec": value["location"][1],
                "radius": value["radius"],
            }
            for element in value["fits_data"]:
                if not self.thumbnail:
                    del element["thumbnail"]
                element.update(main_data)
                cutouts_rows.append(element)
        cutouts_rows = pd.DataFrame(cutouts_rows)
        return cutouts_rows

    def submit(self) -> pd.DataFrame:
        payload = self.create_payload()
        response = requests.request(
            "POST", self.url, data=payload, headers=self.headers
        )
        response = self.create_response(response.text)
        return response
