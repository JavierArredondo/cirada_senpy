from senpy.cli import commands
from click.testing import CliRunner
from unittest import mock

import numpy as np
import os
import unittest
from astropy.io import fits


def fake_hdul():
    return fits.HDUList([fits.PrimaryHDU(data=np.zeros((4, 4), dtype=np.float32))])


class TestManage(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()

    @mock.patch("senpy.core.handler.fetch_survey", return_value=[fake_hdul()])
    def test_download(self, _mock):
        with self.runner.isolated_filesystem() as td:
            with open("input.csv", "w") as f:
                f.write("ra,dec,name\n187.7059,12.3911,M87\n")
            result = self.runner.invoke(
                commands.download, ["input.csv", td, "-s", "NVSS"]
            )
            self.assertEqual(result.exit_code, 0, result.output)
            self.assertTrue(any(n.endswith("_NVSS.fits") for n in os.listdir(td)))
