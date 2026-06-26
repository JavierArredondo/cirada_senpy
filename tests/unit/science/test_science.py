from senpy.science import (
    SURVEY_FREQUENCY_MHZ,
    fit_spectral_index,
    measure_cutout,
    peak_flux,
    spectral_index,
    spectral_index_map,
)
from unittest import TestCase

import numpy as np
from astropy.io import fits


def gaussian_cutout(with_beam=True):
    y, x = np.mgrid[0:50, 0:50]
    source = 10.0 * np.exp(-((x - 25) ** 2 + (y - 25) ** 2) / (2 * 3.0**2))
    rng = np.random.default_rng(0)
    data = (source + rng.normal(0, 0.05, (50, 50))).astype(np.float32)
    header = fits.Header()
    header["BUNIT"] = "JY/BEAM" if with_beam else "counts"
    if with_beam:
        header["BMAJ"] = header["BMIN"] = 0.01  # deg
        header["CDELT2"] = 0.001  # deg/pixel
    return fits.HDUList([fits.PrimaryHDU(data=data, header=header)])


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


class FitSpectralIndexTestCase(TestCase):
    def test_two_points_exact(self):
        nu = [150.0, 1400.0]
        flux = [150.0**-0.7, 1400.0**-0.7]
        alpha, err = fit_spectral_index(nu, flux)
        self.assertAlmostEqual(alpha, -0.7, places=6)
        self.assertTrue(np.isnan(err))

    def test_multi_band_fit_recovers_slope(self):
        nu = np.array([150.0, 843.0, 1400.0, 3000.0])
        flux = nu**-0.8
        alpha, err = fit_spectral_index(nu, flux)
        self.assertAlmostEqual(alpha, -0.8, places=4)
        self.assertLess(err, 0.01)

    def test_insufficient_points(self):
        alpha, err = fit_spectral_index([1400.0], [10.0])
        self.assertTrue(np.isnan(alpha) and np.isnan(err))

    def test_ignores_nonpositive(self):
        alpha, _ = fit_spectral_index([150.0, 1400.0, 3000.0], [100.0, 10.0, np.nan])
        self.assertLess(alpha, 0)


class MeasureCutoutTestCase(TestCase):
    def test_beamed_map_measures_all(self):
        m = measure_cutout(gaussian_cutout(with_beam=True))
        self.assertAlmostEqual(m["peak"], 10.0, delta=0.5)
        self.assertGreater(m["snr"], 5)
        self.assertTrue(np.isfinite(m["integrated"]) and m["integrated"] > 0)
        self.assertGreater(m["npix"], 0)
        self.assertEqual(m["bunit"], "JY/BEAM")

    def test_no_beam_leaves_integrated_nan(self):
        m = measure_cutout(gaussian_cutout(with_beam=False))
        self.assertTrue(np.isnan(m["integrated"]))
        self.assertGreater(m["snr"], 5)  # peak/rms still well-defined

    def test_fallback_beam_enables_integrated(self):
        # No BMAJ/BMIN in header (like SkyView), but a survey beam is supplied
        # and the header still carries a pixel scale.
        hdul = gaussian_cutout(with_beam=False)
        hdul[0].header["CDELT2"] = 0.001
        m = measure_cutout(hdul, beam_fwhm_arcsec=3.6)
        self.assertTrue(np.isfinite(m["integrated"]) and m["integrated"] > 0)
