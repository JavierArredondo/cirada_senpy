from cirada_senpy.core import measure_catalog
from unittest import TestCase, mock

import numpy as np
import os
import tempfile
from astropy.io import fits

FILE_PATH = os.path.dirname(__file__)
INPUT = os.path.join(FILE_PATH, "../data/targets_coords.csv")


def beamed_hdul():
    data = np.zeros((20, 20), dtype=np.float32)
    data[10, 10] = 5.0
    header = fits.Header()
    header["BUNIT"] = "JY/BEAM"
    header["BMAJ"] = header["BMIN"] = 0.01
    header["CDELT2"] = 0.001
    return fits.HDUList([fits.PrimaryHDU(data=data, header=header)])


class MeasureCatalogTestCase(TestCase):
    @mock.patch("cirada_senpy.core.catalog.fetch_survey", return_value=[beamed_hdul()])
    def test_builds_catalog(self, _mock):
        catalog = measure_catalog(INPUT, None, surveys=["NVSS"])
        # 2 sources x 1 survey x 1 tile.
        self.assertEqual(len(catalog), 2)
        for column in ("source", "ra", "dec", "survey", "peak", "snr", "integrated"):
            self.assertIn(column, catalog.columns)
        self.assertTrue((catalog["survey"] == "NVSS").all())
        self.assertTrue((catalog["peak"] == 5.0).all())

    @mock.patch("cirada_senpy.core.catalog.fetch_survey", return_value=[beamed_hdul()])
    def test_writes_csv(self, _mock):
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "catalog.csv")
            measure_catalog(INPUT, out, surveys=["NVSS"])
            self.assertTrue(os.path.exists(out))

    @mock.patch("cirada_senpy.core.catalog.fetch_survey", return_value=[])
    def test_no_coverage_empty_catalog(self, _mock):
        catalog = measure_catalog(INPUT, None, surveys=["NVSS"])
        self.assertEqual(len(catalog), 0)
        self.assertIn("peak", catalog.columns)  # schema preserved
