from astropy.io.fits.hdu.image import PrimaryHDU
from cirada_senpy.core import download_file, Handler, open_fits_tgz
from unittest import mock, TestCase

import os
import pandas as pd
import shutil
import tempfile

fake_submitted = pd.DataFrame(
    {"source_name": ["a"], "filename": "a", "ra": [0], "dec": [0]}
)

FILE_PATH = os.path.dirname(__file__)


class HandlerTestCase(TestCase):
    def setUp(self):
        self.input_path_file = os.path.join(FILE_PATH, "../data/input_example.csv")
        self.output_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.output_dir)

    def test_verify_io(self):
        # A valid handler: the file and the output dir exists
        handler = Handler(
            input_path_file=self.input_path_file, output_dir=self.output_dir
        )
        valid = handler._verify_io()
        self.assertTrue(valid)

        # An invalid handler: the file doest not exists
        with self.assertRaises(Exception) as context:
            handler = Handler(
                input_path_file="thi_files.csv", output_dir=self.output_dir
            )
            valid = handler._verify_io()
        self.assertIsInstance(context.exception, Exception)

    @mock.patch("cirada_senpy.core.query.Query.submit", return_value=fake_submitted)
    def test_download(self, mock_query: mock.Mock):
        # Exists the output folder
        handler = Handler(
            input_path_file=self.input_path_file, output_dir=self.output_dir, force=True
        )
        handler.download()

        # Does not exist the output folder
        handler = Handler(
            input_path_file=self.input_path_file,
            output_dir=os.path.join(self.output_dir, "data/"),
            force=True,
        )
        handler.download()

        # Does not force
        handler = Handler(
            input_path_file=self.input_path_file,
            output_dir=self.output_dir,
            force=False,
        )
        handler.download()

    @mock.patch("cirada_senpy.core.query.Query.submit", return_value=pd.DataFrame())
    def test_direct_download(self, mock_query: mock.Mock):
        download_file(self.input_path_file, self.output_dir, force=True)
        self.assertListEqual(os.listdir(self.output_dir), [])

    def test_open_fits_tgz(self):
        data_fits = open_fits_tgz(os.path.join(FILE_PATH, "../data/Orion.tgz"))
        self.assertIsInstance(data_fits, list)
        self.assertEqual(2, len(data_fits))

        for f in data_fits:
            self.assertIsInstance(f, PrimaryHDU)
