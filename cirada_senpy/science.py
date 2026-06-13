"""Spectral-index helpers — turn multi-survey cutouts into a physical feature.

Source brightness follows ``S ∝ ν**α``, so two surveys at different
frequencies give the spectral index ``α``, which separates source physics
(flat ``α ≈ 0`` for AGN cores/hotspots, steep ``α ≈ -0.7`` for aged lobes).

These functions are pure (numpy only). Rendering lives in ``examples/gallery.py``
behind the optional ``[viz]`` extra; the CLI command that will wrap these is a
planned follow-up.
"""
import numpy as np

# Representative central frequency (MHz) per survey key, for spectral indices.
SURVEY_FREQUENCY_MHZ = {
    "TGSS": 150.0,
    "GLEAM": 200.0,
    "SUMSS": 843.0,
    "NVSS": 1400.0,
    "FIRST": 1400.0,
    "VLASS": 3000.0,
}

# Published restoring-beam FWHM (arcsec) per radio survey, used for integrated
# flux when SkyView strips BMAJ/BMIN from the header. Optical/IR surveys have
# no beam and are intentionally absent.
SURVEY_BEAM_ARCSEC = {
    "TGSS": 25.0,
    "GLEAM": 120.0,
    "SUMSS": 45.0,
    "NVSS": 45.0,
    "FIRST": 5.4,
    "VLASS": 2.5,
}


def peak_flux(hdul) -> float:
    """Peak pixel value (Jy/beam) of a cutout HDUList, ignoring NaNs."""
    data = np.squeeze(hdul[0].data).astype(float)
    return float(np.nanmax(data))


def spectral_index(flux_low, freq_low_mhz, flux_high, freq_high_mhz):
    """Spectral index ``α`` from two flux/frequency points (``S ∝ ν**α``).

    Works on scalars or numpy arrays. ``freq_*`` are in MHz; the unit cancels.
    """
    return np.log10(flux_high / flux_low) / np.log10(freq_high_mhz / freq_low_mhz)


def fit_spectral_index(freqs_mhz, fluxes):
    """Power-law spectral index ``α`` (``S ∝ ν**α``) across two or more bands.

    Fits ``log10(S) = α·log10(ν) + c`` by least squares over the positive,
    finite points. Returns ``(alpha, alpha_err)``: for exactly two points the
    index is exact and the error is NaN; with fewer than two usable points both
    are NaN.
    """
    freqs = np.asarray(freqs_mhz, dtype=float)
    fluxes = np.asarray(fluxes, dtype=float)
    good = (freqs > 0) & (fluxes > 0) & np.isfinite(freqs) & np.isfinite(fluxes)
    x, y = np.log10(freqs[good]), np.log10(fluxes[good])
    if x.size < 2:
        return float("nan"), float("nan")
    if x.size == 2:
        return float((y[1] - y[0]) / (x[1] - x[0])), float("nan")
    design = np.vstack([x, np.ones_like(x)]).T
    coeffs, *_ = np.linalg.lstsq(design, y, rcond=None)
    residual_var = np.sum((y - design @ coeffs) ** 2) / (x.size - 2)
    covariance = residual_var * np.linalg.inv(design.T @ design)
    return float(coeffs[0]), float(np.sqrt(covariance[0, 0]))


def spectral_index_map(low, freq_low_mhz, high, freq_high_mhz, threshold=0.05):
    """Per-pixel ``α`` between two co-gridded maps.

    ``low`` and ``high`` are 2D arrays on the **same** pixel grid (see
    :func:`matched_cutouts`). Pixels below ``threshold`` times the peak in either
    map are masked to NaN so noise is not turned into spurious indices.
    """
    low = np.asarray(low, dtype=float)
    high = np.asarray(high, dtype=float)
    if low.shape != high.shape:
        raise ValueError(f"maps must share a grid: {low.shape} vs {high.shape}")
    mask = (
        (low > threshold * np.nanmax(low))
        & (high > threshold * np.nanmax(high))
        & (low > 0)
        & (high > 0)
    )
    alpha = np.full(low.shape, np.nan)
    alpha[mask] = spectral_index(low[mask], freq_low_mhz, high[mask], freq_high_mhz)
    return alpha


def matched_cutouts(position, surveys, pixels=300, radius=None):
    """Fetch several SkyView surveys onto ONE shared pixel grid.

    Returns a list of 2D arrays aligned pixel-for-pixel (a single SkyView call),
    which is what makes a per-pixel :func:`spectral_index_map` valid. Only
    SkyView-backed surveys are supported (VLASS, served by CADC, cannot be
    co-gridded this way).
    """
    import astropy.units as u
    from astroquery.skyview import SkyView

    from .core.surveys import SKYVIEW_SURVEYS, normalize_survey

    if radius is None:
        radius = 2.0 * u.arcmin
    names = []
    for survey in surveys:
        key = normalize_survey(survey)
        if key not in SKYVIEW_SURVEYS:
            raise ValueError(
                f"matched_cutouts supports only SkyView surveys "
                f"({', '.join(SKYVIEW_SURVEYS)}); got '{survey}'."
            )
        names.append(SKYVIEW_SURVEYS[key])
    images = SkyView.get_images(
        position=position, survey=names, pixels=pixels, radius=radius
    )
    return [np.squeeze(image[0].data).astype(float) for image in images]


def _beam_area_pixels(header, beam_fwhm_deg=None):
    """Gaussian beam area in pixels from BMAJ/BMIN (or a fallback FWHM), or None.

    Prefers the header's BMAJ/BMIN; if those are absent (e.g. SkyView strips
    them), falls back to a circular beam of ``beam_fwhm_deg``. Returns None when
    no beam is known or the pixel scale is missing.
    """
    bmaj, bmin = header.get("BMAJ"), header.get("BMIN")  # FWHM in degrees
    if (not bmaj or not bmin) and beam_fwhm_deg:
        bmaj = bmin = beam_fwhm_deg
    scale = header.get("CDELT2") or header.get("CD2_2")  # degrees/pixel
    if not bmaj or not bmin or not scale:
        return None
    beam_area_deg2 = (np.pi * bmaj * bmin) / (4.0 * np.log(2.0))
    return beam_area_deg2 / (abs(scale) ** 2)


def measure_cutout(hdul, threshold_sigma=3.0, beam_fwhm_arcsec=None):
    """Photometric measurements from a single cutout HDUList.

    Returns a dict with:
      ``peak``       peak pixel value (map units, e.g. Jy/beam),
      ``rms``        robust background noise (sigma-clipped std),
      ``snr``        (peak - background) / rms,
      ``integrated`` beam-corrected integrated flux above ``threshold_sigma``,
                     for radio maps with a beam (BMAJ/BMIN); NaN otherwise,
      ``npix``       number of pixels above the detection threshold,
      ``bunit``      the map's BUNIT, so ``peak`` is interpretable.

    Integrated flux is only well-defined for beamed (radio) maps; for optical/IR
    surveys with no beam it is left NaN by design.
    """
    from astropy.stats import sigma_clipped_stats

    hdu = hdul[0]
    data = np.squeeze(hdu.data).astype(float)
    finite = data[np.isfinite(data)]
    _, median, std = sigma_clipped_stats(finite, sigma=3.0, maxiters=5)
    peak = float(np.nanmax(data))
    rms = float(std)
    detection = data > (median + threshold_sigma * std)

    result = {
        "peak": peak,
        "rms": rms,
        "snr": float((peak - median) / rms) if rms > 0 else float("nan"),
        "integrated": float("nan"),
        "npix": int(np.sum(detection)),
        "bunit": str(hdu.header.get("BUNIT", "")).strip(),
        "date": str(hdu.header.get("DATE-OBS", "")).strip(),
    }
    beam_fwhm_deg = (beam_fwhm_arcsec / 3600.0) if beam_fwhm_arcsec else None
    beam_px = _beam_area_pixels(hdu.header, beam_fwhm_deg)
    if beam_px:
        result["integrated"] = float(np.sum(data[detection] - median) / beam_px)
    return result
