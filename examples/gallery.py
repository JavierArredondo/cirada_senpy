"""Regenerate the README science gallery from live survey data.

Run with the optional viz extra installed:

    uv run --extra viz python examples/gallery.py

Produces four figures under docs/images/, all from cutouts the package
fetches:

  1. cygA_multiwavelength.png  — Cygnus A radio -> infrared -> optical
  2. cygA_spectral_map.png     — per-pixel TGSS/NVSS spectral index
  3. spectral_index.png        — spectral index of bright calibrators
  4. flux_history.png          — VLASS flux vs epoch for variable sources

The spectral indices are *indicative*: peak flux on each survey's native beam
(TGSS ~25", NVSS ~45"), not beam-matched. The point is that the multi-survey
data and the feature drop straight out of the tool.
"""

import os
import warnings

import astropy.units as u
import numpy as np
import pandas as pd
from astropy.coordinates import SkyCoord
from astropy.visualization import (
    AsinhStretch,
    ImageNormalize,
    PercentileInterval,
    ZScaleInterval,
)

from cirada_senpy.core.flux_history import flux_history_from_catalog, plot_flux_history
from cirada_senpy.core.surveys import fetch_survey
from cirada_senpy.science import (
    SURVEY_BEAM_ARCSEC,
    SURVEY_FREQUENCY_MHZ,
    matched_cutouts,
    measure_cutout,
    peak_flux,
    spectral_index,
    spectral_index_map,
)

warnings.filterwarnings("ignore")

OUT = os.path.join(os.path.dirname(__file__), "..", "docs", "images")


def _squeeze(hdul):
    data = np.squeeze(hdul[0].data).astype(float)
    return np.nan_to_num(data, nan=np.nanmin(data))


def multiwavelength_montage(plt):
    """Cygnus A across surveys: radio -> infrared -> optical."""
    cygA = SkyCoord.from_name("Cygnus A")
    panels = [
        ("TGSS", "150 MHz", "inferno"),
        ("NVSS", "1.4 GHz", "inferno"),
        ("WISE", "3.4 um", "cividis"),
        ("DSS", "optical", "gray"),
    ]
    grabbed = []
    for name, band, cmap in panels:
        try:
            hduls = fetch_survey(cygA, name, 1.2 * u.arcmin)
            if hduls:
                grabbed.append((name, band, cmap, _squeeze(hduls[0])))
        except Exception as error:  # noqa: BLE001 - skip surveys without coverage
            print(f"  {name}: skip ({type(error).__name__})")

    fig, axes = plt.subplots(1, len(grabbed), figsize=(3.4 * len(grabbed), 3.9))
    for ax, (name, band, cmap, data) in zip(axes, grabbed):
        norm = ImageNormalize(data, interval=ZScaleInterval(), stretch=AsinhStretch())
        ax.imshow(data, origin="lower", cmap=cmap, norm=norm)
        ax.set_title(name, fontsize=14, fontweight="bold", pad=6)
        ax.text(
            0.5,
            -0.07,
            band,
            transform=ax.transAxes,
            ha="center",
            va="top",
            fontsize=9,
            color="#9aa0a6",
        )
        ax.set_xticks([])
        ax.set_yticks([])
    fig.suptitle(
        "Cygnus A  ·  one source across surveys: radio → infrared → optical",
        fontsize=13,
        color="#cfd2d6",
        y=1.04,
    )
    fig.tight_layout()
    path = os.path.join(OUT, "cygA_multiwavelength.png")
    fig.savefig(path, dpi=125, bbox_inches="tight", facecolor="#0d1117")
    print("wrote", path)


def spectral_map(plt):
    """Per-pixel TGSS/NVSS spectral index of Cygnus A on a matched grid."""
    cygA = SkyCoord.from_name("Cygnus A")
    tgss, nvss = matched_cutouts(
        cygA, ["TGSS", "NVSS"], pixels=300, radius=2.2 * u.arcmin
    )
    alpha = spectral_index_map(
        tgss, SURVEY_FREQUENCY_MHZ["TGSS"], nvss, SURVEY_FREQUENCY_MHZ["NVSS"]
    )
    print(
        f"  alpha map: median={np.nanmedian(alpha):+.2f}, "
        f"flattest={np.nanmax(alpha):+.2f}, steepest={np.nanmin(alpha):+.2f}"
    )

    fig, (axL, axR) = plt.subplots(1, 2, figsize=(11, 4.6))
    axL.imshow(
        nvss,
        origin="lower",
        cmap="inferno",
        norm=ImageNormalize(
            nvss, interval=PercentileInterval(99.5), stretch=AsinhStretch()
        ),
    )
    axL.set_title("Cygnus A — NVSS 1.4 GHz", fontsize=12)
    image = axR.imshow(alpha, origin="lower", cmap="Spectral_r", vmin=-1.3, vmax=0.1)
    axR.contour(
        nvss,
        levels=np.nanmax(nvss) * np.array([0.05, 0.2, 0.5, 0.85]),
        colors="k",
        linewidths=0.5,
        alpha=0.5,
    )
    axR.set_title("Spectral index map  α", fontsize=12)
    for ax in (axL, axR):
        ax.set_xticks([])
        ax.set_yticks([])
    cbar = fig.colorbar(image, ax=axR, fraction=0.046)
    cbar.set_label("α  (flat → steep)")
    fig.suptitle(
        "Same galaxy, pixel-by-pixel: flat hotspots vs steep lobes",
        fontsize=12,
        color="#cfd2d6",
        y=1.0,
    )
    fig.tight_layout()
    path = os.path.join(OUT, "cygA_spectral_map.png")
    fig.savefig(path, dpi=130, bbox_inches="tight", facecolor="#0d1117")
    print("wrote", path)


def calibrator_indices(plt):
    """Spectral index as one feature per source over bright calibrators."""
    sample = [
        "3C48",
        "3C147",
        "3C286",
        "3C295",
        "3C196",
        "3C273",
        "3C84",
        "M87",
        "3C348",
    ]
    nu_t, nu_n = SURVEY_FREQUENCY_MHZ["TGSS"], SURVEY_FREQUENCY_MHZ["NVSS"]
    fluxes_t, fluxes_n, alphas, names = [], [], [], []
    for name in sample:
        try:
            pos = SkyCoord.from_name(name)
            tg = fetch_survey(pos, "TGSS", 1.5 * u.arcmin)
            nv = fetch_survey(pos, "NVSS", 1.5 * u.arcmin)
            if not tg or not nv:
                continue
            st, sn = peak_flux(tg[0]), peak_flux(nv[0])
            if st <= 0 or sn <= 0:
                continue
            fluxes_t.append(st)
            fluxes_n.append(sn)
            alphas.append(spectral_index(st, nu_t, sn, nu_n))
            names.append(name)
        except Exception as error:  # noqa: BLE001
            print(f"  {name}: skip ({type(error).__name__})")
    fluxes_t = np.array(fluxes_t)
    fluxes_n = np.array(fluxes_n)
    alphas = np.array(alphas)
    print(f"  N={len(names)}  median alpha={np.median(alphas):+.2f}")

    fig, ax = plt.subplots(figsize=(6.2, 5))
    sc = ax.scatter(
        fluxes_n,
        fluxes_t,
        c=alphas,
        cmap="coolwarm_r",
        s=140,
        edgecolor="white",
        vmin=-1.2,
        vmax=0.2,
        zorder=3,
    )
    for name, sn, st in zip(names, fluxes_n, fluxes_t):
        ax.annotate(
            name,
            (sn, st),
            fontsize=8,
            color="#cfd2d6",
            xytext=(5, 4),
            textcoords="offset points",
        )
    lim = [
        min(fluxes_t.min(), fluxes_n.min()) * 0.6,
        max(fluxes_t.max(), fluxes_n.max()) * 1.6,
    ]
    ax.plot(lim, lim, "--", color="#666", lw=1, label="S150 = S1400 (α=0)")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(lim)
    ax.set_ylim(lim)
    ax.set_xlabel("NVSS  S$_{1.4\\,GHz}$  [Jy/beam]")
    ax.set_ylabel("TGSS  S$_{150\\,MHz}$  [Jy/beam]")
    ax.set_title(
        "Radio spectral index from two surveys\n(steep sources sit above the line)",
        fontsize=11,
    )
    cbar = fig.colorbar(sc)
    cbar.set_label("spectral index  α")
    ax.legend(loc="upper left", fontsize=8)
    fig.tight_layout()
    path = os.path.join(OUT, "spectral_index.png")
    fig.savefig(path, dpi=130, facecolor="#0d1117")
    print("wrote", path)


def flux_history_example(plt):
    """VLASS flux history (flux vs epoch) for bright, variable radio sources.

    VLASS images the same sky in several epochs years apart, so a single
    ``fetch_survey`` per source already returns one tile per epoch. We measure
    the peak flux of each, build the per-epoch history, and plot it.
    """
    sample = ["3C273", "3C279", "3C84", "M87"]
    beam = SURVEY_BEAM_ARCSEC.get("VLASS")
    rows = []
    for name in sample:
        try:
            pos = SkyCoord.from_name(name)
            hduls = fetch_survey(pos, "VLASS", 1.5 * u.arcmin)
            if not hduls:
                print(f"  {name}: skip (no VLASS coverage)")
                continue
            for hdul in hduls:
                measurement = measure_cutout(hdul, beam_fwhm_arcsec=beam)
                rows.append(
                    {
                        "source": name,
                        "ra": pos.ra.deg,
                        "dec": pos.dec.deg,
                        "survey": "VLASS",
                        **measurement,
                    }
                )
        except Exception as error:  # noqa: BLE001 - skip sources without coverage
            print(f"  {name}: skip ({type(error).__name__})")

    catalog = pd.DataFrame(rows)
    history = flux_history_from_catalog(catalog, survey="VLASS")
    kept = sorted(history["source"].unique())
    print(f"  sources with VLASS epochs: {', '.join(kept) or 'none'}")
    if history.empty:
        print("  no VLASS epochs measured — skipping flux-history figure")
        return

    path = os.path.join(OUT, "flux_history.png")
    plot_flux_history(history, path)
    print("wrote", path)


def main():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.style.use("dark_background")
    os.makedirs(OUT, exist_ok=True)
    print("1/4 multi-wavelength montage…")
    multiwavelength_montage(plt)
    print("2/4 spectral-index map…")
    spectral_map(plt)
    print("3/4 calibrator spectral indices…")
    calibrator_indices(plt)
    print("4/4 VLASS flux history…")
    flux_history_example(plt)
    print("done.")


if __name__ == "__main__":
    main()
