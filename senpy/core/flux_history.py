"""Per-source flux history (flux vs. epoch) from a ``senpy measure`` catalog.

A survey like VLASS images each source in several epochs years apart; collecting
the per-epoch flux gives a sparse "light curve". The name is intentionally
generic (``flux_history`` rather than ``light_curve``) since this works for any
survey/band, not just radio. This is pure post-processing over a ``senpy
measure`` catalog (which carries each cutout's ``date`` from DATE-OBS).

See :mod:`senpy.core.variability` for the summary-statistics counterpart.
"""

from typing import Optional, Union

import pandas as pd

from ..io.data_file import read_file, write_file


def flux_history_from_catalog(
    catalog: Union[str, pd.DataFrame],
    output_path: Optional[str] = None,
    survey: str = "VLASS",
    flux_column: str = "peak",
) -> pd.DataFrame:
    """Build a per-source, per-epoch flux time series for one survey.

    Cutouts are grouped into epochs by observation day (DATE-OBS), taking the
    brightest tile per epoch. Returns a long-format DataFrame with one row per
    ``(source, epoch)``: ``source, ra, dec, survey, epoch, flux, snr,
    n_epochs``, sorted by source then epoch. Unlike
    :func:`variability_from_catalog`, single-epoch sources are kept (a one-point
    history is still a valid history).
    """
    data = read_file(catalog) if isinstance(catalog, str) else catalog.copy()
    data = data[data["survey"] == survey].copy()
    data["day"] = data["date"].astype(str).str.slice(0, 10)
    data = data[data["day"].str.len() == 10]  # require a real DATE-OBS

    rows = []
    for source, group in data.groupby("source"):
        per_epoch = group.groupby("day").agg(
            flux=(flux_column, "max"),
            snr=("snr", "max"),
        )
        n_epochs = int(per_epoch.shape[0])
        for day, epoch in per_epoch.iterrows():
            rows.append(
                {
                    "source": source,
                    "ra": group["ra"].iloc[0],
                    "dec": group["dec"].iloc[0],
                    "survey": survey,
                    "epoch": day,
                    "flux": float(epoch["flux"]),
                    "snr": float(epoch["snr"]),
                    "n_epochs": n_epochs,
                }
            )

    result = pd.DataFrame(
        rows,
        columns=["source", "ra", "dec", "survey", "epoch", "flux", "snr", "n_epochs"],
    ).sort_values(["source", "epoch"], ignore_index=True)

    if output_path:
        write_file(result, output_path)
    n_sources = result["source"].nunique()
    print(
        f"\nFlux history: {len(result)} epoch(s) across {n_sources} {survey} source(s)"
        + (f" -> {output_path}" if output_path else "")
    )
    return result


def plot_flux_history(history: pd.DataFrame, output_path: str) -> str:
    """Plot flux vs. epoch (one line per source) to ``output_path`` as an image.

    Requires the optional ``viz`` extra (``pip install senpy[viz]``).
    Returns the path written.
    """
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.dates as mdates
        import matplotlib.pyplot as plt
    except ImportError as exc:  # pragma: no cover - depends on optional extra
        raise ImportError(
            "Plotting requires matplotlib. Install with: pip install 'senpy[viz]'"
        ) from exc

    fig, ax = plt.subplots(figsize=(8, 5))
    for source, group in history.groupby("source"):
        group = group.sort_values("epoch")
        epochs = pd.to_datetime(group["epoch"])
        ax.plot(epochs, group["flux"], marker="o", label=str(source))

    survey = history["survey"].iloc[0] if len(history) else ""
    ax.set_xlabel("Epoch (DATE-OBS)")
    ax.set_ylabel("Peak flux")
    ax.set_title(f"{survey} flux history")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    fig.autofmt_xdate()
    if history["source"].nunique() <= 12:
        ax.legend(fontsize="small")
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    return output_path
