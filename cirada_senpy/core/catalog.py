"""Measure cutouts into a feature catalog: targets x surveys -> a table of fluxes."""
from typing import List, Optional

import astropy.units as u
import pandas as pd
from tqdm import tqdm

from ..io.data_file import read_file, write_file
from ..science import SURVEY_BEAM_ARCSEC, measure_cutout
from .coords import parse_position, source_label
from .surveys import DEFAULT_SURVEYS, fetch_survey, normalize_survey


def measure_catalog(
    input_path: str,
    output_path: Optional[str] = None,
    surveys: Optional[List[str]] = None,
    radius_arcmin: float = 3.0,
) -> pd.DataFrame:
    """Fetch each target in each survey and measure it into one tidy catalog.

    Returns a DataFrame (one row per source x survey x tile) and, if
    ``output_path`` is given, writes it via the IO layer (csv/parquet/pickle).
    """
    survey_keys = [normalize_survey(s) for s in (surveys or DEFAULT_SURVEYS)]
    radius = radius_arcmin * u.arcmin

    data = read_file(input_path)
    for column in ("ra", "dec", "name"):
        if column not in data.columns:
            data[column] = None
    data = data.where(pd.notnull(data), None)

    rows: List[dict] = []
    failed: List[tuple] = []
    progress_bar = tqdm(data.iterrows(), total=len(data))
    for _, row in progress_bar:
        try:
            position = parse_position(row["ra"], row["dec"], row["name"])
        except Exception as error:
            failed.append((row["name"] or f"{row['ra']},{row['dec']}", "parse", str(error)))
            continue
        label = source_label(row["ra"], row["dec"], row["name"], position)
        for survey in survey_keys:
            progress_bar.set_description(f"{label} / {survey}")
            try:
                hduls = fetch_survey(position, survey, radius)
                if not hduls:
                    failed.append((label, survey, "no coverage"))
                    continue
                beam = SURVEY_BEAM_ARCSEC.get(survey)
                for index, hdul in enumerate(hduls):
                    measurement = measure_cutout(hdul, beam_fwhm_arcsec=beam)
                    rows.append(
                        {
                            "source": label,
                            "ra": position.ra.deg,
                            "dec": position.dec.deg,
                            "survey": survey,
                            "tile": index + 1,
                            **measurement,
                        }
                    )
            except Exception as error:
                failed.append((label, survey, str(error)))

    catalog = pd.DataFrame(
        rows,
        columns=["source", "ra", "dec", "survey", "tile",
                 "peak", "rms", "snr", "integrated", "npix", "bunit"],
    )
    if output_path:
        write_file(catalog, output_path)

    if failed:
        print(f"\n{len(failed)} measurement(s) failed or had no coverage:")
        for target, survey, message in failed:
            print(f"  - {target} [{survey}]: {message}")
    print(f"\nMeasured {len(catalog)} cutout(s)" + (f" -> {output_path}" if output_path else ""))
    return catalog
