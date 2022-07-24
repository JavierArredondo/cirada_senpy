from .handler import Handler
from .query import Query
from typing import List

import astropy.io.fits as fio
import io
import tarfile


def download_file(input_path: str, output_path: str, force: bool = False):
    _handler = Handler(input_path, output_path, force)
    _handler.download()


def open_fits_tgz(input_file_path: str) -> List:
    fits_data = []
    with tarfile.open(input_file_path, "r") as f:
        for member in f.getmembers():
            data = f.extractfile(member)
            content = data.read()
            fits = io.BytesIO(content)
            opened_fits = fio.open(fits)[0]
            fits_data.append(opened_fits)
    return fits_data


__all__ = ["Handler", "download_file", "open_fits_tgz"]
