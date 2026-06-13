from cirada_senpy.core import (
    download_file,
    measure_catalog,
    spectral_index_from_catalog,
)
from cirada_senpy.core.surveys import AVAILABLE_SURVEYS, DEFAULT_SURVEYS

import click


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
def download(input_path: str, output_path: str, surveys: str, radius: float, overwrite: bool):
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


if __name__ == "__main__":
    cli()
