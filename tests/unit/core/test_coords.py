from senpy.core.coords import _blank, parse_position, source_label
from unittest import TestCase, mock

from astropy.coordinates import SkyCoord


class CoordsTestCase(TestCase):
    def test_blank(self):
        for value in (None, "", "  ", "nan", float("nan")):
            self.assertTrue(_blank(value))
        for value in ("M87", "187.7", 0.0):
            self.assertFalse(_blank(value))

    def test_decimal_degrees(self):
        pos = parse_position(187.7059, 12.3911, None)
        self.assertAlmostEqual(pos.ra.deg, 187.7059, places=4)
        self.assertAlmostEqual(pos.dec.deg, 12.3911, places=4)

    def test_sexagesimal(self):
        pos = parse_position("05h 35m 18s", "-05d 23m 0s", None)
        self.assertAlmostEqual(pos.ra.deg, 83.825, places=2)
        self.assertAlmostEqual(pos.dec.deg, -5.3833, places=2)

    def test_strips_stray_quotes(self):
        pos = parse_position("'00 42 30", " +41 12 00'", None)
        self.assertAlmostEqual(pos.ra.deg, 10.625, places=2)

    def test_prefers_coords_over_name(self):
        # ra/dec present -> name is never resolved (no network).
        pos = parse_position(10.0, 20.0, "SomeName")
        self.assertAlmostEqual(pos.ra.deg, 10.0)

    @mock.patch("senpy.core.coords.SkyCoord.from_name")
    def test_name_resolution(self, mock_from_name):
        mock_from_name.return_value = SkyCoord(187.7, 12.4, unit="deg")
        parse_position(None, None, "M87")
        mock_from_name.assert_called_once_with("M87")

    def test_no_target_raises(self):
        with self.assertRaises(ValueError):
            parse_position(None, None, None)

    def test_label_from_name(self):
        pos = SkyCoord(10, 20, unit="deg")
        self.assertEqual(source_label(None, None, "M 87", pos), "M_87")

    def test_label_from_coords(self):
        pos = SkyCoord(187.7059, 12.3911, unit="deg")
        self.assertEqual(source_label(187.7059, 12.3911, None, pos), "187.7059+12.3911")
