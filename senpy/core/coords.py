"""Parse heterogeneous target rows into astropy SkyCoord positions."""
import astropy.units as u
import pandas as pd
from astropy.coordinates import SkyCoord


def _blank(value) -> bool:
    """True for None, NaN, or whitespace-only / 'nan' strings."""
    if value is None:
        return True
    if isinstance(value, float) and pd.isna(value):
        return True
    return str(value).strip().lower() in ("", "nan")


def parse_position(ra, dec, name) -> SkyCoord:
    """Resolve a target row to a SkyCoord.

    Prefers explicit ``ra``/``dec`` (decimal degrees, else sexagesimal); falls
    back to resolving ``name`` via Sesame. Raises ValueError if the row has
    neither usable coordinates nor a name.
    """
    if not _blank(ra) and not _blank(dec):
        ra_s = str(ra).strip().strip("'\"")
        dec_s = str(dec).strip().strip("'\"")
        try:
            return SkyCoord(float(ra_s), float(dec_s), unit="deg")
        except ValueError:
            return SkyCoord(ra_s, dec_s, unit=(u.hourangle, u.deg))
    if not _blank(name):
        return SkyCoord.from_name(str(name).strip())
    raise ValueError("row has neither coordinates nor a resolvable name")


def source_label(ra, dec, name, position: SkyCoord) -> str:
    """A filesystem-safe label for a target: its name if given, else its
    decimal-degree coordinates."""
    if not _blank(name):
        return "".join(
            c if (c.isalnum() or c in "-_.") else "_" for c in str(name).strip()
        )
    return f"{position.ra.deg:.4f}{position.dec.deg:+.4f}"
