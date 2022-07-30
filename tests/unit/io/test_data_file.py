from cirada_senpy.io.data_file import get_format, read_file, write_file
from unittest import TestCase

import os
import pandas as pd

FILE_PATH = os.path.dirname(__file__)


class DataFileTestCase(TestCase):
    def setUp(self) -> None:
        pass

    def test_get_format(self):
        self.assertEqual("csv", get_format("csv"))
        self.assertEqual("csv", get_format("txt"))
        self.assertEqual("parquet", get_format("parquet"))
        self.assertEqual("pickle", get_format("pickle"))
        self.assertEqual("pickle", get_format("pkl"))

        with self.assertRaises(Exception) as context:
            get_format("xls")
        self.assertIsInstance(context.exception, Exception)
        self.assertEqual("*.xls extension not supported", str(context.exception))

    def test_read_file(self):
        file_path = os.path.join(FILE_PATH, "../data/input_example.csv")
        data = read_file(file_path)
        self.assertIsInstance(data, pd.DataFrame)

        data = read_file(file_path, file_format="csv")
        self.assertIsInstance(data, pd.DataFrame)

        with self.assertRaises(FileNotFoundError) as context:
            read_file("/this_path_does_not_exists/data.csv")
        self.assertIsInstance(context.exception, FileNotFoundError)

    def test_write_file(self):
        data = pd.DataFrame()

        write_file(data, "/tmp/data.csv")
        exists_file = "data.csv" in os.listdir("/tmp")
        self.assertTrue(exists_file)

        write_file(data, "/tmp/data.pickle")
        exists_file = "data.pickle" in os.listdir("/tmp")
        self.assertTrue(exists_file)
