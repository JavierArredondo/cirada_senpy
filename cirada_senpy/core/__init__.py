from .handler import Handler
from .query import Query
from .utils import open_fits_tgz


def download_file(input_path: str, output_path: str, force: bool = False):
    _handler = Handler(input_path, output_path, force)
    _handler.download()


__all__ = ["Handler", "download_file", "open_fits_tgz"]
