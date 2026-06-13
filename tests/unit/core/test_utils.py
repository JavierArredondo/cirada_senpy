from cirada_senpy.core import open_fits_tgz
from unittest import TestCase

import os
from astropy.io.fits.hdu.image import PrimaryHDU

FILE_PATH = os.path.dirname(__file__)


class UtilsTestCase(TestCase):
    def test_open_fits_tgz(self):
        data_fits = open_fits_tgz(os.path.join(FILE_PATH, "../data/Orion.tgz"))
        self.assertIsInstance(data_fits, list)
        self.assertEqual(2, len(data_fits))
        for hdu in data_fits:
            self.assertIsInstance(hdu, PrimaryHDU)
