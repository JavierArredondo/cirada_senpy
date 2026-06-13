from cirada_senpy.core import spectral_index_from_catalog
from unittest import TestCase

import numpy as np
import pandas as pd


def make_catalog():
    # Source A: steep (bright at 150, faint at 1400) + two VLASS tiles; one
    # NVSS integrated is NaN to exercise the peak fallback; a DSS row that must
    # be ignored (non-radio). Source B: flat.
    return pd.DataFrame(
        [
            {"source": "A", "ra": 1.0, "dec": 2.0, "survey": "TGSS",  "peak": 100.0, "integrated": 100.0},
            {"source": "A", "ra": 1.0, "dec": 2.0, "survey": "NVSS",  "peak": 10.0,  "integrated": np.nan},
            {"source": "A", "ra": 1.0, "dec": 2.0, "survey": "VLASS", "peak": 6.0,   "integrated": 4.0},
            {"source": "A", "ra": 1.0, "dec": 2.0, "survey": "VLASS", "peak": 7.0,   "integrated": 6.0},
            {"source": "A", "ra": 1.0, "dec": 2.0, "survey": "DSS",   "peak": 5.0,   "integrated": np.nan},
            {"source": "B", "ra": 3.0, "dec": 4.0, "survey": "TGSS",  "peak": 10.0,  "integrated": 10.0},
            {"source": "B", "ra": 3.0, "dec": 4.0, "survey": "NVSS",  "peak": 10.0,  "integrated": 10.0},
        ]
    )


class SpectralIndexFromCatalogTestCase(TestCase):
    def test_per_source_fit(self):
        result = spectral_index_from_catalog(make_catalog())
        self.assertEqual(set(result["source"]), {"A", "B"})
        a = result[result["source"] == "A"].iloc[0]
        b = result[result["source"] == "B"].iloc[0]
        # A is steep (negative); B is flat (~0).
        self.assertLess(a["alpha"], -0.5)
        self.assertAlmostEqual(b["alpha"], 0.0, places=6)

    def test_ignores_non_radio_and_counts_bands(self):
        result = spectral_index_from_catalog(make_catalog())
        a = result[result["source"] == "A"].iloc[0]
        # TGSS + NVSS + VLASS = 3 radio bands; DSS excluded.
        self.assertEqual(a["n_bands"], 3)

    def test_columns(self):
        result = spectral_index_from_catalog(make_catalog())
        for column in ("source", "ra", "dec", "n_bands", "alpha", "alpha_err"):
            self.assertIn(column, result.columns)
