from cirada_senpy.core import variability_from_catalog
from unittest import TestCase

import pandas as pd


def make_catalog():
    # VAR: two epochs, peak 10 -> 20 (variable), plus a same-epoch overlapping
    # tile (max is taken). STEADY: two epochs, no change. ONE: a single epoch
    # (dropped). NONVLASS row must be ignored.
    return pd.DataFrame(
        [
            {"source": "VAR", "ra": 1.0, "dec": 2.0, "survey": "VLASS", "peak": 10.0, "snr": 100, "date": "2019-06-18T18:29:17"},
            {"source": "VAR", "ra": 1.0, "dec": 2.0, "survey": "VLASS", "peak": 9.5,  "snr": 90,  "date": "2019-06-18T18:31:02"},
            {"source": "VAR", "ra": 1.0, "dec": 2.0, "survey": "VLASS", "peak": 20.0, "snr": 100, "date": "2021-10-12T11:33:23"},
            {"source": "VAR", "ra": 1.0, "dec": 2.0, "survey": "NVSS",  "peak": 99.0, "snr": 100, "date": ""},
            {"source": "STEADY", "ra": 3.0, "dec": 4.0, "survey": "VLASS", "peak": 5.0, "snr": 50, "date": "2019-06-18T00:00:00"},
            {"source": "STEADY", "ra": 3.0, "dec": 4.0, "survey": "VLASS", "peak": 5.0, "snr": 50, "date": "2021-10-12T00:00:00"},
            {"source": "ONE", "ra": 5.0, "dec": 6.0, "survey": "VLASS", "peak": 7.0, "snr": 50, "date": "2020-01-01T00:00:00"},
        ]
    )


class VariabilityTestCase(TestCase):
    def test_flags_variable(self):
        result = variability_from_catalog(make_catalog())
        # ONE has a single epoch -> excluded.
        self.assertEqual(set(result["source"]), {"VAR", "STEADY"})
        var = result[result["source"] == "VAR"].iloc[0]
        steady = result[result["source"] == "STEADY"].iloc[0]
        self.assertEqual(var["n_epochs"], 2)  # same-day tiles collapsed
        self.assertTrue(var["variable"])
        self.assertFalse(steady["variable"])

    def test_frac_var_value(self):
        result = variability_from_catalog(make_catalog())
        var = result[result["source"] == "VAR"].iloc[0]
        # peaks 10 and 20 -> (20-10)/(20+10) = 0.333
        self.assertAlmostEqual(var["frac_var"], 1.0 / 3.0, places=3)

    def test_columns(self):
        result = variability_from_catalog(make_catalog())
        for column in ("source", "n_epochs", "flux_mean", "mod_index", "frac_var", "variable"):
            self.assertIn(column, result.columns)
