from unittest import TestCase

import pandas as pd

from senpy.core import flux_history_from_catalog


def make_catalog():
    # VAR: two epochs (peaks 10 -> 20), with a same-day overlapping tile that
    # must collapse to the max (10, not 9.5). NVSS row must be ignored. ONE has
    # a single epoch and IS kept (a one-point history is still valid).
    return pd.DataFrame(
        [
            {
                "source": "VAR",
                "ra": 1.0,
                "dec": 2.0,
                "survey": "VLASS",
                "peak": 10.0,
                "integrated": 11.0,
                "snr": 100,
                "date": "2019-06-18T18:29:17",
            },
            {
                "source": "VAR",
                "ra": 1.0,
                "dec": 2.0,
                "survey": "VLASS",
                "peak": 9.5,
                "integrated": 9.9,
                "snr": 90,
                "date": "2019-06-18T18:31:02",
            },
            {
                "source": "VAR",
                "ra": 1.0,
                "dec": 2.0,
                "survey": "VLASS",
                "peak": 20.0,
                "integrated": 22.0,
                "snr": 100,
                "date": "2021-10-12T11:33:23",
            },
            {
                "source": "VAR",
                "ra": 1.0,
                "dec": 2.0,
                "survey": "NVSS",
                "peak": 99.0,
                "integrated": 99.0,
                "snr": 100,
                "date": "",
            },
            {
                "source": "ONE",
                "ra": 5.0,
                "dec": 6.0,
                "survey": "VLASS",
                "peak": 7.0,
                "integrated": 7.5,
                "snr": 50,
                "date": "2020-01-01T00:00:00",
            },
        ]
    )


class FluxHistoryTestCase(TestCase):
    def test_long_format_and_collapse(self):
        result = flux_history_from_catalog(make_catalog())
        var = result[result["source"] == "VAR"].sort_values("epoch")
        # Two epochs, same-day tiles collapsed to the max (10, not 9.5).
        self.assertEqual(list(var["epoch"]), ["2019-06-18", "2021-10-12"])
        self.assertEqual(list(var["flux"]), [10.0, 20.0])
        self.assertTrue((var["n_epochs"] == 2).all())

    def test_keeps_single_epoch_source(self):
        result = flux_history_from_catalog(make_catalog())
        one = result[result["source"] == "ONE"]
        self.assertEqual(len(one), 1)
        self.assertEqual(int(one["n_epochs"].iloc[0]), 1)

    def test_excludes_other_surveys_and_undated(self):
        result = flux_history_from_catalog(make_catalog())
        # NVSS row (and its empty date) never appears.
        self.assertEqual(set(result["survey"]), {"VLASS"})
        self.assertNotIn(99.0, set(result["flux"]))

    def test_integrated_flux_column(self):
        result = flux_history_from_catalog(make_catalog(), flux_column="integrated")
        var = result[result["source"] == "VAR"].sort_values("epoch")
        self.assertEqual(list(var["flux"]), [11.0, 22.0])

    def test_columns(self):
        result = flux_history_from_catalog(make_catalog())
        for column in (
            "source",
            "ra",
            "dec",
            "survey",
            "epoch",
            "flux",
            "snr",
            "n_epochs",
        ):
            self.assertIn(column, result.columns)
