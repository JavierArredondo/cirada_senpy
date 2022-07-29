from cirada_senpy.core.query import Query
from unittest import mock, TestCase


class FakeRequest:
    def __init__(self, status_code=200, content=""):
        self.status_code = status_code
        starts_with = '{"total": 1, "error_message": "", "upload_name": ""}?END?'
        content = {
            "result": {
                "1": {
                    "source_name": "Orion",
                    "location": [83.82208, -5.39111],
                    "radius": 20.0,
                    "fits_data": [
                        {
                            "epoch": "a",
                            "filename": "mean-83.8220_8.fits",
                            "originals": {},
                            "out_dir": "",
                            "overwrite": "True",
                            "group": "None",
                            "survey": "RM_mean",
                            "position": [83.82208, -5.39111],
                            "radius": 20.0,
                            "thumbnail": "a",
                        }
                    ],
                }
            }
        }
        ends_with = "?END?"
        self.text = starts_with + str(content) + ends_with
        self.text = self.text.replace("'", '"')


class QueryTestCase(TestCase):
    def setUp(self) -> None:
        pass

    def test_init(self):
        query = Query(20, 20, source_name="Orion")
        self.assertEqual(query.source_name, "Orion")
        self.assertEqual(query.ra, None)
        self.assertEqual(query.dec, None)
        self.assertEqual(query.x_size, 20)
        self.assertEqual(query.y_size, 20)

    def test_create_payload(self):
        query = Query(20, 20, source_name="Orion")
        payload = query.create_payload()

        self.assertIsInstance(payload, str)
        self.assertIn("source_name", payload)
        self.assertIn("x_size", payload)
        self.assertIn("y_size", payload)
        self.assertNotIn("location", payload)

    @mock.patch("requests.request", return_value=FakeRequest(200))
    def test_submit(self, mock_request: mock.Mock):
        query = Query(20, 20, source_name="Orion")
        response = query.submit()
