from cirada_senpy.science import (
    SURVEY_FREQUENCY_MHZ,
    peak_flux,
    spectral_index,
    spectral_index_map,
)
from unittest import TestCase

import numpy as np
from astropy.io import fits


class SpectralIndexTestCase(TestCase):
    def test_flat_spectrum(self):
        # Equal flux at both frequencies -> alpha = 0.
        self.assertAlmostEqual(spectral_index(10.0, 150.0, 10.0, 1400.0), 0.0)

    def test_power_law_recovered(self):
        # S = nu**alpha with alpha = -0.7 -> recover -0.7 exactly.
        nu_low, nu_high = 150.0, 1400.0
        alpha_true = -0.7
        s_low, s_high = nu_low**alpha_true, nu_high**alpha_true
        self.assertAlmostEqual(
            spectral_index(s_low, nu_low, s_high, nu_high), alpha_true, places=6
        )

    def test_steep_source_is_negative(self):
        # Brighter at low frequency -> negative (steep) index.
        self.assertLess(spectral_index(50.0, 150.0, 10.0, 1400.0), 0)

    def test_array_input(self):
        result = spectral_index(np.array([10.0, 20.0]), 150.0, np.array([10.0, 10.0]), 1400.0)
        self.assertEqual(result.shape, (2,))
        self.assertAlmostEqual(result[0], 0.0)
        self.assertLess(result[1], 0.0)


class PeakFluxTestCase(TestCase):
    def test_peak_ignores_nan(self):
        data = np.array([[1.0, 2.0], [np.nan, 5.0]], dtype=np.float32)
        hdul = fits.HDUList([fits.PrimaryHDU(data=data)])
        self.assertEqual(peak_flux(hdul), 5.0)


class SpectralIndexMapTestCase(TestCase):
    def test_shape_and_masking(self):
        low = np.array([[100.0, 0.0], [50.0, 1.0]])
        high = np.array([[10.0, 0.0], [50.0, 1.0]])
        alpha = spectral_index_map(low, 150.0, high, 1400.0, threshold=0.1)
        self.assertEqual(alpha.shape, (2, 2))
        # Bright pixel [0,0]: defined and steep.
        self.assertFalse(np.isnan(alpha[0, 0]))
        self.assertLess(alpha[0, 0], 0)
        # Faint pixels masked to NaN.
        self.assertTrue(np.isnan(alpha[0, 1]))
        self.assertTrue(np.isnan(alpha[1, 1]))

    def test_mismatched_grids_raise(self):
        with self.assertRaises(ValueError):
            spectral_index_map(np.zeros((4, 4)), 150.0, np.zeros((4, 5)), 1400.0)


class FrequencyTableTestCase(TestCase):
    def test_known_frequencies(self):
        self.assertEqual(SURVEY_FREQUENCY_MHZ["TGSS"], 150.0)
        self.assertEqual(SURVEY_FREQUENCY_MHZ["NVSS"], 1400.0)
        self.assertEqual(SURVEY_FREQUENCY_MHZ["VLASS"], 3000.0)
