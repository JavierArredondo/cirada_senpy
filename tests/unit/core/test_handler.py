from senpy.core import Handler, download_file
from unittest import TestCase, mock

import numpy as np
import os
import shutil
import tempfile
from astropy.io import fits

FILE_PATH = os.path.dirname(__file__)
INPUT = os.path.join(FILE_PATH, "../data/targets_coords.csv")


def fake_hdul():
    return fits.HDUList([fits.PrimaryHDU(data=np.zeros((4, 4), dtype=np.float32))])


class HandlerTestCase(TestCase):
    def setUp(self):
        self.output_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.output_dir, ignore_errors=True)

    def test_missing_input_raises(self):
        with self.assertRaises(FileNotFoundError):
            Handler("does_not_exist.csv", self.output_dir)

    def test_creates_output_dir(self):
        nested = os.path.join(self.output_dir, "sub")
        Handler(INPUT, nested, surveys=["NVSS"])
        self.assertTrue(os.path.isdir(nested))

    def test_unknown_survey_raises(self):
        with self.assertRaises(ValueError):
            Handler(INPUT, self.output_dir, surveys=["BOGUS"])

    @mock.patch("senpy.core.handler.fetch_survey", return_value=[fake_hdul()])
    def test_download_writes_fits(self, _mock):
        written = Handler(INPUT, self.output_dir, surveys=["NVSS"]).download()
        self.assertEqual(len(written), 2)
        for path in written:
            self.assertTrue(path.endswith("_NVSS.fits"))
            self.assertTrue(os.path.exists(path))

    @mock.patch("senpy.core.handler.fetch_survey", return_value=[fake_hdul()])
    def test_skip_existing(self, mock_fetch):
        Handler(INPUT, self.output_dir, surveys=["NVSS"]).download()
        calls_after_first = mock_fetch.call_count
        # Second run: all outputs exist, so nothing is re-fetched.
        Handler(INPUT, self.output_dir, surveys=["NVSS"]).download()
        self.assertEqual(mock_fetch.call_count, calls_after_first)

    @mock.patch("senpy.core.handler.fetch_survey", return_value=[fake_hdul()])
    def test_overwrite_refetches(self, mock_fetch):
        Handler(INPUT, self.output_dir, surveys=["NVSS"]).download()
        calls_after_first = mock_fetch.call_count
        Handler(INPUT, self.output_dir, surveys=["NVSS"], overwrite=True).download()
        self.assertEqual(mock_fetch.call_count, 2 * calls_after_first)

    @mock.patch("senpy.core.handler.fetch_survey", return_value=[])
    def test_no_coverage_writes_nothing(self, _mock):
        written = Handler(INPUT, self.output_dir, surveys=["NVSS"]).download()
        self.assertEqual(written, [])

    @mock.patch("senpy.core.handler.fetch_survey", return_value=[fake_hdul()])
    def test_download_file_helper(self, _mock):
        written = download_file(INPUT, self.output_dir, surveys=["NVSS"])
        self.assertEqual(len(written), 2)
