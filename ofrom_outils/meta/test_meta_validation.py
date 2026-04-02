import datetime
import re
import unittest
from unittest.mock import patch, Mock

from openpyxl.cell.cell import Cell

from ofrom_outils.meta.meta_validation import (
    val_to_str, str_to_regex, regex_to_list, regex_to_date,
    str_val, list_val, date_val, VVal, VCell
)

CELL = Mock(spec=Cell)


class TestValToStr(unittest.TestCase):

    def test_str(self):
        self.assertEqual(val_to_str("lo"), "lo")

    def test_int(self):
        self.assertEqual(val_to_str(-42), "-42")

    def test_float(self):
        self.assertEqual(val_to_str(12.483), "12.483")

    def test_date(self):
        """Not this function's job to format dates."""
        self.assertEqual(val_to_str(datetime.datetime(2000, 1, 1)),
                         "2000-01-01 00:00:00")

    def test_none(self):
        self.assertEqual(val_to_str(None), "None")


class TestStrToRegex(unittest.TestCase):

    def setUp(self):
        self.r = re.compile(r"[01]+")

    def test_not_string(self):
        self.assertRaises(TypeError, str_to_regex, 10, self.r)

    def test_not_re(self):
        self.assertRaises(AttributeError, str_to_regex, "10", "[01]+")

    def test_string(self):
        self.assertEqual(str_to_regex("1098-404-180", self.r), "10010")


class TestRegexToList(unittest.TestCase):

    def setUp(self):
        self.lst = ['true', 'false']

    def test_valid(self):
        self.assertEqual(regex_to_list("true", self.lst), "true")

    def test_invalid(self):
        self.assertEqual(regex_to_list("none", self.lst), "")


class TestRegexToDate(unittest.TestCase):

    def test_valid(self):
        self.assertEqual(regex_to_date("10-12-2011"), "2011-12-10")

    def test_invalid(self):
        self.assertEqual(regex_to_date("10-2011-12"), "")

    def test_standard(self):
        self.assertEqual(regex_to_date("2000-01-01 00:00:00"),
                         "2000-01-01")


@patch("ofrom_outils.meta.meta_validation.str_to_regex")
@patch("ofrom_outils.meta.meta_validation.val_to_str")
class TestStrVal(unittest.TestCase):

    def test_get(self, mock_str, mock_re):
        mock_str.return_value = "legit"
        mock_re.return_value = "legit"
        self.assertEqual(str_val(None), "legit")

    def test_get_empty(self, mock_str, mock_re):
        mock_str.return_value = ""
        mock_re.return_value = ""
        self.assertEqual(str_val(128, dflt="None"), "None")


@patch("ofrom_outils.meta.meta_validation.regex_to_list")
@patch("ofrom_outils.meta.meta_validation.str_to_regex")
@patch("ofrom_outils.meta.meta_validation.val_to_str")
class TestListVal(unittest.TestCase):

    def setUp(self):
        self.l = ['true']

    def test_get(self, mock_str, mock_re, mock_list):
        mock_str.return_value = "true"
        mock_re.return_value = "true"
        mock_list.return_value = "true"
        self.assertEqual(list_val(CELL, self.l), 'true')

    def test_get_empty(self, mock_str, mock_re, mock_list):
        mock_str.return_value = "None"
        mock_re.return_value = "None"
        mock_list.return_value = "None"
        CELL.value = "false"
        self.assertEqual(list_val(CELL, self.l, "None"), 'None')


@patch("ofrom_outils.meta.meta_validation.regex_to_date")
@patch("ofrom_outils.meta.meta_validation.str_to_regex")
@patch("ofrom_outils.meta.meta_validation.val_to_str")
class TestDateVal(unittest.TestCase):

    def setUp(self):
        self.strf = "%Y"

    def test_get(self, _mock_str, mock_re, mock_date):
        _mock_str.return_value = "10-10-2011"
        mock_re.return_value = "10-10-2011"
        mock_date.return_value = "2011-10-10"
        self.assertEqual(date_val(CELL, strf="YYYY-MM-DD"), '2011-10-10')

    def test_get_empty(self, _mock_str, mock_re, mock_date):
        _mock_str.return_value = "None"
        mock_re.return_value = "None"
        mock_date.return_value = ""
        CELL.value = 1888
        self.assertEqual(date_val(CELL, strf="YYYY-MM-DD", dflt="NA"), 'NA')


@patch("ofrom_outils.meta.meta_validation.str_val")
class TestVVal(unittest.TestCase):

    def setUp(self):
        CELL.value = "42"

    def test_create(self, _mock_str):
        self.assertIsInstance(VVal(CELL, 'str'), VVal)

    def test_create_spec(self, _mock_str):
        vc = VVal(CELL, 'sexe')
        self.assertEqual(vc.vfun, list_val)

    def test_create_fails(self, _mock_str):
        self.assertRaises(TypeError, VVal)

    def test_get(self, mock_str):
        mock_str.return_value = "legit"
        vc = VVal(CELL, 'str')
        vc.vfun = mock_str
        _ = vc.value
        mock_str.assert_called_once()
        args = mock_str.call_args.args
        self.assertIn(CELL, args)
        self.assertEqual(vc.value, "legit")

    def test_set(self, mock_str):
        mock_str.return_value = "true"
        vc = VVal(CELL, 'str')
        vc.vfun = mock_str
        vc.value = "true"
        mock_str.assert_called_once()
        args = mock_str.call_args.args
        self.assertIn('true', args)


@patch("ofrom_outils.meta.meta_validation.str_val")
class TestVCell(unittest.TestCase):

    def setUp(self):
        CELL.value = "42"

    def test_create(self, _mock_str):
        self.assertIsInstance(VCell(CELL, 'str'), VCell)

    def test_create_spec(self, _mock_str):
        vc = VCell(CELL, 'sexe')
        self.assertEqual(vc.vfun, list_val)

    def test_create_fails(self, _mock_str):
        self.assertRaises(TypeError, VCell)

    def test_create_fails_args(self, _mock_str):
        self.assertRaises(TypeError, VCell, "cell!", 'str')

    def test_get(self, mock_str):
        mock_str = mock_str.return_value
        mock_str.get.return_value = "legit"
        vc = VCell(CELL, 'str')
        vc.vfun = mock_str
        _ = vc.value
        mock_str.get.assert_called_once_with(CELL)
        self.assertEqual(vc.value, "legit")

    def test_set(self, mock_str):
        mock_str = mock_str.return_value
        vc = VCell(CELL, 'str')
        vc.vfun = mock_str
        vc.value = "true"
        mock_str.set.assert_called_once_with('true')


if __name__ == "__main__":
    unittest.main()
