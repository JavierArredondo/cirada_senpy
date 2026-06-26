"""Survey registry and cutout fetching, backed by astroquery.

SkyView (HEASARC) serves most radio/IR/optical surveys through a single
interface; VLASS is not in SkyView, so it is fetched from the CADC data
service directly.
"""
import warnings
from io import BytesIO
from typing import List

import astropy.units as u
import requests
from astropy.coordinates import SkyCoord
from astropy.io import fits

# Friendly survey key -> exact SkyView survey name.
SKYVIEW_SURVEYS = {
    "NVSS": "NVSS",
    "FIRST": "VLA FIRST (1.4 GHz)",
    "TGSS": "TGSS ADR1",
    "SUMSS": "SUMSS 843 MHz",
    "GLEAM": "GLEAM 170-231 MHz",
    "WISE": "WISE 3.4",
    "SDSS": "SDSSr",
    "DSS": "DSS",
}

# VLASS is served by the CADC data service, not SkyView.
VLASS = "VLASS"

AVAILABLE_SURVEYS = [VLASS] + list(SKYVIEW_SURVEYS)
DEFAULT_SURVEYS = ["VLASS", "NVSS", "FIRST"]

# Generous timeout: CADC cutout sync calls can be slow.
CADC_TIMEOUT = 120


def normalize_survey(key: str) -> str:
    """Validate and canonicalize a survey key (case-insensitive)."""
    canonical = key.strip().upper()
    if canonical not in AVAILABLE_SURVEYS:
        raise ValueError(
            f"Unknown survey '{key}'. Available: {', '.join(AVAILABLE_SURVEYS)}"
        )
    return canonical


def fetch_survey(
    position: SkyCoord, survey: str, radius: u.Quantity
) -> List[fits.HDUList]:
    """Fetch every cutout for one survey at one position.

    Returns a (possibly empty) list of HDULists; empty means the survey has
    no coverage at that position.
    """
    survey = normalize_survey(survey)
    if survey == VLASS:
        return _fetch_vlass(position, radius)
    return _fetch_skyview(position, survey, radius)


def _fetch_skyview(
    position: SkyCoord, survey: str, radius: u.Quantity
) -> List[fits.HDUList]:
    from astroquery.skyview import SkyView

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        images = SkyView.get_images(
            position=position, survey=[SKYVIEW_SURVEYS[survey]], radius=radius
        )
    return [img for img in images if img is not None]


def _fetch_vlass(position: SkyCoord, radius: u.Quantity) -> List[fits.HDUList]:
    from astroquery.cadc import Cadc

    cadc = Cadc()
    results = cadc.query_region(position, radius=radius, collection="VLASS")
    if len(results) == 0:
        return []
    urls = cadc.get_image_list(results, position, radius)
    hduls = []
    for url in urls:
        response = requests.get(url, timeout=CADC_TIMEOUT)
        response.raise_for_status()
        hduls.append(fits.open(BytesIO(response.content)))
    return hduls
