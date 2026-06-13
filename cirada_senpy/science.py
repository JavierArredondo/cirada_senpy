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


def peak_flux(hdul) -> float:
    """Peak pixel value (Jy/beam) of a cutout HDUList, ignoring NaNs."""
    data = np.squeeze(hdul[0].data).astype(float)
    return float(np.nanmax(data))


def spectral_index(flux_low, freq_low_mhz, flux_high, freq_high_mhz):
    """Spectral index ``α`` from two flux/frequency points (``S ∝ ν**α``).

    Works on scalars or numpy arrays. ``freq_*`` are in MHz; the unit cancels.
    """
    return np.log10(flux_high / flux_low) / np.log10(freq_high_mhz / freq_low_mhz)


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
