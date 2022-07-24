from cirada_senpy.core import Handler
from unittest import mock, TestCase
from unittest.mock import MagicMock

import os
import shutil
import tempfile

FILE_PATH = os.path.dirname(__file__)


class HandlerTestCase(TestCase):
    def setUp(self):
        self.input_path_file = os.path.join(FILE_PATH, "../data/input_example.csv")
        self.output_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.output_dir)

    def test_verify_io(self):
        # A valid handler: the file and the output dir exists
        hndlr = Handler(
            input_path_file=self.input_path_file, output_dir=self.output_dir
        )
        valid = hndlr._verify_io()
        self.assertTrue(valid)

        # An invalid handler: the file doest not exists
        with self.assertRaises(Exception) as context:
            hndlr = Handler(input_path_file="thi_files.csv", output_dir=self.output_dir)
            valid = hndlr._verify_io()
        self.assertIsInstance(context.exception, Exception)
