from typing import List, Optional

from .catalog import measure_catalog
from .handler import Handler
from .sed import spectral_index_from_catalog
from .surveys import AVAILABLE_SURVEYS, DEFAULT_SURVEYS
from .utils import open_fits_tgz


def download_file(
    input_path: str,
    output_path: str,
    surveys: Optional[List[str]] = None,
    radius_arcmin: float = 3.0,
    overwrite: bool = False,
) -> List[str]:
    handler = Handler(
        input_path,
        output_path,
        surveys=surveys,
        radius_arcmin=radius_arcmin,
        overwrite=overwrite,
    )
    return handler.download()


__all__ = [
    "Handler",
    "download_file",
    "measure_catalog",
    "spectral_index_from_catalog",
    "open_fits_tgz",
    "AVAILABLE_SURVEYS",
    "DEFAULT_SURVEYS",
]
