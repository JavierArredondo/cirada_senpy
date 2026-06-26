import click

from cirada_senpy.core import (
    download_file,
    flux_history_from_catalog,
    measure_catalog,
    plot_flux_history,
    spectral_index_from_catalog,
    variability_from_catalog,
)
from cirada_senpy.core.surveys import AVAILABLE_SURVEYS, DEFAULT_SURVEYS


@click.group()
def cli():
    pass


@cli.command()
@click.argument("input_path", type=str)
@click.argument("output_path", type=str)
@click.option(
    "--surveys",
    "-s",
    default=",".join(DEFAULT_SURVEYS),
    help=f"Comma-separated surveys. Available: {', '.join(AVAILABLE_SURVEYS)}",
)
@click.option(
    "--radius",
    "-r",
    default=3.0,
    type=float,
    help="Cutout radius in arcminutes.",
)
@click.option(
    "--overwrite",
    is_flag=True,
    default=False,
    help="Re-fetch and overwrite cutouts that already exist (default: skip).",
)
def download(
    input_path: str, output_path: str, surveys: str, radius: float, overwrite: bool
):
    survey_list = [s for s in surveys.split(",") if s.strip()]
    download_file(
        input_path,
        output_path,
        surveys=survey_list,
        radius_arcmin=radius,
        overwrite=overwrite,
    )


@cli.command()
@click.argument("input_path", type=str)
@click.argument("output_path", type=str)
@click.option(
    "--surveys",
    "-s",
    default=",".join(DEFAULT_SURVEYS),
    help=f"Comma-separated surveys. Available: {', '.join(AVAILABLE_SURVEYS)}",
)
@click.option(
    "--radius",
    "-r",
    default=3.0,
    type=float,
    help="Cutout radius in arcminutes.",
)
def measure(input_path: str, output_path: str, surveys: str, radius: float):
    """Measure cutouts (peak, integrated flux, rms, snr) into a feature catalog."""
    survey_list = [s for s in surveys.split(",") if s.strip()]
    measure_catalog(
        input_path,
        output_path,
        surveys=survey_list,
        radius_arcmin=radius,
    )


@cli.command("spectral-index")
@click.argument("catalog_path", type=str)
@click.argument("output_path", type=str)
@click.option(
    "--flux",
    "-f",
    "flux_column",
    default="integrated",
    type=click.Choice(["integrated", "peak"]),
    help="Flux measure to fit (falls back to peak where missing).",
)
def spectral_index_cmd(catalog_path: str, output_path: str, flux_column: str):
    """Fit a per-source radio spectral index from a `senpy measure` catalog."""
    spectral_index_from_catalog(catalog_path, output_path, flux_column=flux_column)


@cli.command()
@click.argument("catalog_path", type=str)
@click.argument("output_path", type=str)
@click.option(
    "--survey",
    "-s",
    default="VLASS",
    help="Multi-epoch survey to assess (default: VLASS).",
)
def variability(catalog_path: str, output_path: str, survey: str):
    """Flag variable sources across epochs from a `senpy measure` catalog."""
    variability_from_catalog(catalog_path, output_path, survey=survey)


@cli.command("flux-history")
@click.argument("catalog_path", type=str)
@click.argument("output_path", type=str)
@click.option(
    "--survey",
    "-s",
    default="VLASS",
    help="Multi-epoch survey to build the history for (default: VLASS).",
)
@click.option(
    "--flux",
    "-f",
    "flux_column",
    default="peak",
    type=click.Choice(["peak", "integrated"]),
    help="Flux measure per epoch (default: peak).",
)
@click.option(
    "--plot",
    "plot_path",
    default=None,
    type=str,
    help="Also save a flux-vs-epoch plot to this image path (needs the 'viz' extra).",
)
def flux_history(
    catalog_path: str, output_path: str, survey: str, flux_column: str, plot_path: str
):
    """Build a per-source flux time series (flux vs epoch) from a `senpy measure` catalog."""
    history = flux_history_from_catalog(
        catalog_path, output_path, survey=survey, flux_column=flux_column
    )
    if plot_path:
        plot_flux_history(history, plot_path)
        print(f"Flux-history plot -> {plot_path}")


if __name__ == "__main__":
    cli()
