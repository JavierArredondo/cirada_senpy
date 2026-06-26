"""Per-source radio variability across observation epochs (e.g. VLASS).

VLASS images a source in several epochs years apart; comparing the peak flux
between epochs flags variable sources and transient candidates. This is pure
post-processing over a ``senpy measure`` catalog (which carries each cutout's
``date`` from DATE-OBS).
"""
from typing import Optional, Union

import numpy as np
import pandas as pd

from ..io.data_file import read_file, write_file


def variability_from_catalog(
    catalog: Union[str, pd.DataFrame],
    output_path: Optional[str] = None,
    survey: str = "VLASS",
    min_snr: float = 5.0,
    mod_index_threshold: float = 0.1,
) -> pd.DataFrame:
    """Flag variable sources from multi-epoch measurements of one survey.

    Cutouts are grouped into epochs by observation day (DATE-OBS), taking the
    brightest tile per epoch. For sources with >=2 epochs, computes:
    ``flux_mean``, ``mod_index`` (std/mean), ``frac_var`` ((max-min)/(max+min)),
    and a boolean ``variable`` (modulation above threshold and well detected).
    Returns a per-source DataFrame.
    """
    data = read_file(catalog) if isinstance(catalog, str) else catalog.copy()
    data = data[data["survey"] == survey].copy()
    data["day"] = data["date"].astype(str).str.slice(0, 10)
    data = data[data["day"].str.len() == 10]  # require a real DATE-OBS

    rows = []
    for source, group in data.groupby("source"):
        per_epoch = group.groupby("day")["peak"].max().to_numpy(dtype=float)
        if per_epoch.size < 2:
            continue
        mean = float(np.mean(per_epoch))
        mod_index = float(np.std(per_epoch, ddof=1) / mean) if mean > 0 else float("nan")
        frac_var = float(
            (per_epoch.max() - per_epoch.min()) / (per_epoch.max() + per_epoch.min())
        )
        rows.append(
            {
                "source": source,
                "ra": group["ra"].iloc[0],
                "dec": group["dec"].iloc[0],
                "n_epochs": int(per_epoch.size),
                "flux_mean": mean,
                "mod_index": mod_index,
                "frac_var": frac_var,
                "variable": bool(
                    mod_index > mod_index_threshold and group["snr"].max() > min_snr
                ),
            }
        )

    result = pd.DataFrame(
        rows,
        columns=["source", "ra", "dec", "n_epochs", "flux_mean",
                 "mod_index", "frac_var", "variable"],
    )
    if output_path:
        write_file(result, output_path)
    print(f"\nVariability for {len(result)} source(s) with >=2 {survey} epochs"
          + (f" -> {output_path}" if output_path else ""))
    return result
