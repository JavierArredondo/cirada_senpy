"""Per-source spectral index from a measurement catalog (S ∝ ν**α)."""
from typing import Optional, Union

import pandas as pd

from ..io.data_file import read_file, write_file
from ..science import SURVEY_FREQUENCY_MHZ, fit_spectral_index


def spectral_index_from_catalog(
    catalog: Union[str, pd.DataFrame],
    output_path: Optional[str] = None,
    flux_column: str = "integrated",
) -> pd.DataFrame:
    """Fit a power-law spectral index per source from a ``senpy measure`` catalog.

    Uses ``flux_column`` (default ``integrated``), falling back to ``peak`` where
    it is missing. Only radio surveys with a known frequency contribute; VLASS
    tiles are collapsed to one flux per survey (the brightest). Returns a
    per-source DataFrame: ``source, ra, dec, n_bands, alpha, alpha_err``.
    """
    data = read_file(catalog) if isinstance(catalog, str) else catalog.copy()
    data = data[data["survey"].isin(SURVEY_FREQUENCY_MHZ)].copy()
    data["freq"] = data["survey"].map(SURVEY_FREQUENCY_MHZ)
    data["flux"] = data[flux_column].where(data[flux_column].notna(), data["peak"])

    # One flux per (source, survey): the brightest tile.
    per_band = (
        data.groupby(["source", "survey"])
        .agg(ra=("ra", "first"), dec=("dec", "first"),
             freq=("freq", "first"), flux=("flux", "max"))
        .reset_index()
    )

    rows = []
    for source, group in per_band.groupby("source"):
        alpha, alpha_err = fit_spectral_index(group["freq"].values, group["flux"].values)
        rows.append(
            {
                "source": source,
                "ra": group["ra"].iloc[0],
                "dec": group["dec"].iloc[0],
                "n_bands": int((group["flux"] > 0).sum()),
                "alpha": alpha,
                "alpha_err": alpha_err,
            }
        )
    result = pd.DataFrame(
        rows, columns=["source", "ra", "dec", "n_bands", "alpha", "alpha_err"]
    )
    if output_path:
        write_file(result, output_path)
    print(f"\nFitted spectral index for {len(result)} source(s)"
          + (f" -> {output_path}" if output_path else ""))
    return result
