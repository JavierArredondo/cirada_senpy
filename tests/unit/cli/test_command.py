from cirada_senpy.cli import commands
from click.testing import CliRunner
from unittest import mock

import pandas as pd
import unittest

fake_submitted = pd.DataFrame(
    {"source_name": ["a"], "filename": "a", "ra": [0], "dec": [0]}
)


class TestManage(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()

    @mock.patch("cirada_senpy.core.query.Query.submit", return_value=fake_submitted)
    def test_download(self, mock_query: mock.Mock):
        with self.runner.isolated_filesystem(temp_dir="/tmp") as td:
            with open("input.csv", "w") as f:
                f.write("ra,dec,name\n05h 35m 18s, -05d 23m 0s,Orion")
        result = self.runner.invoke(commands.download, [f"{td}/input.csv", td])
        self.assertEqual(result.exit_code, 0)
