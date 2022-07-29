from cirada_senpy.core.collector import Collector
from io import StringIO
from unittest import mock, TestCase

import os
import pandas as pd

STRING_GOOD_DATA = StringIO(
    """ra,dec,source_name,filename
162.338077,-0.66805,example,example.tgz"""
)

STRING_BAD_DATA = StringIO(
    """ra,dec,any,filename_
162.338077,-0.66805,example,example.tgz"""
)


class FakeRequest:
    def __init__(self, status_code=200, content=b""):
        self.status_code = status_code
        self.content = content


class CollectorTestCase(TestCase):
    good_data = pd.read_csv(STRING_GOOD_DATA, sep=",")
    bad_data = pd.read_csv(STRING_BAD_DATA, sep=",")

    def setUp(self) -> None:
        pass

    def test_init(self):
        collector = Collector(self.good_data)
        self.assertIsInstance(collector, Collector)
        self.assertIsInstance(collector.data, pd.DataFrame)
        self.assertIsInstance(collector.headers, dict)

    def test_create_payload(self):
        expected_response = [
            {
                "example": [
                    {
                        "filepath": "/tmp/example.tgz",
                        "filename": "example.tgz",
                        "row": "example",
                        "RA": 162.338077,
                        "DEC": -0.66805,
                        "only_mosaic": False,
                    }
                ]
            }
        ]
        collector = Collector(self.good_data)
        payload = collector.create_payloads()
        self.assertIsInstance(payload, list)
        self.assertIsInstance(payload[0], dict)
        self.assertListEqual(expected_response, payload)

    def test_create_payload_bad_input(self):
        collector = Collector(self.bad_data)
        with self.assertRaises(KeyError) as context:
            collector.create_payloads()
        self.assertIsInstance(context.exception, KeyError)
        self.assertTrue("source_name" in str(context.exception))

    @mock.patch("requests.request", return_value=FakeRequest(200, b"binary_content"))
    def test_download(self, mock_request: mock.Mock):
        collector = Collector(self.good_data, output_path="/tmp")
        collector.download()
        exists_output = "example.tgz" in os.listdir("/tmp")
        self.assertTrue(exists_output)
