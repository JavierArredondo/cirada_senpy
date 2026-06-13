from cirada_senpy.core.surveys import (
    AVAILABLE_SURVEYS,
    DEFAULT_SURVEYS,
    normalize_survey,
)
from unittest import TestCase


class SurveysTestCase(TestCase):
    def test_normalize_is_case_insensitive(self):
        self.assertEqual(normalize_survey("nvss"), "NVSS")
        self.assertEqual(normalize_survey(" vlass "), "VLASS")

    def test_unknown_survey_raises(self):
        with self.assertRaises(ValueError):
            normalize_survey("BOGUS")

    def test_defaults_are_available(self):
        for survey in DEFAULT_SURVEYS:
            self.assertIn(survey, AVAILABLE_SURVEYS)
