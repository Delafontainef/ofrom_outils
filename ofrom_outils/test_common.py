import os
import unittest
from unittest.mock import patch

from ofrom_outils.common import (
    kwarg, fix_lext, iter_file, iter_all, get_files, iter_core, get_core
)


class TestKwarg(unittest.TestCase):

    def test_args(self):
        args, _ = kwarg([True, "one", "'two and a half'"])
        self.assertEqual(args, ["one", "two and a half"])

    def test_kwargs(self):
        _, kwargs = kwarg([
            True, "one", "two=2", "three=3.14", "four=False"
        ])
        self.assertEqual(kwargs, {"two": 2, "three": 3.14, "four": False})


class TestFixLext(unittest.TestCase):

    def test_string(self):
        l_ext = fix_lext(".xml")
        self.assertEqual(l_ext, [".xml"])

    def test_fix(self):
        l_ext = fix_lext(["xml", ".TEI"])
        self.assertEqual(l_ext, [".xml", ".tei"])

    def test_default(self):
        l_ext = fix_lext()
        self.assertEqual(l_ext, [".textgrid"])


@patch("ofrom_outils.common.fix_lext")
@patch("ofrom_outils.common.os.listdir")
class TestIterFile(unittest.TestCase):

    def test_files(self, mock_os, mock_lext):
        mock_os.return_value = [
            "file1.TextGrid",
            "file2.TextGrid",
            "file3.xml"
        ]
        mock_lext.return_value = [".textgrid"]
        l_res = [tpl for tpl in iter_file("dir")]
        self.assertEqual(l_res, [
            ("file1", ".TextGrid", "file1.TextGrid",
             os.path.join("dir", "file1.TextGrid")),
            ("file2", ".TextGrid", "file2.TextGrid",
             os.path.join("dir", "file2.TextGrid"))
        ])
        assert mock_os.call_count == 1


@patch("ofrom_outils.common.fix_lext")
@patch("ofrom_outils.common.os.walk")
class TestIterAll(unittest.TestCase):

    def test_all(self, mock_os, mock_lext):
        mock_os.return_value = [
            (
                "dir", ["subdir1, subdir2"],
                ["file1.TextGrid", "file2.TextGrid", "file5.xml"]
            ),
            (
                os.path.join("dir", "subdir1"), [],
                ["file3.TextGrid"]
            ),
            (
                os.path.join("dir", "subdir2"), [],
                ["file4.TextGrid"]
            )
        ]
        mock_lext.return_value = [".textgrid"]
        l_res = [tpl for tpl in iter_all("dir")]
        self.assertEqual(l_res, [
            ("file1", ".TextGrid", "file1.TextGrid",
             os.path.join("dir", "file1.TextGrid")),
            ("file2", ".TextGrid", "file2.TextGrid",
             os.path.join("dir", "file2.TextGrid")),
            ("file3", ".TextGrid", "file3.TextGrid",
             os.path.join("dir", "subdir1", "file3.TextGrid")),
            ("file4", ".TextGrid", "file4.TextGrid",
             os.path.join("dir", "subdir2", "file4.TextGrid"))
        ])
        assert mock_os.call_count == 1


class TestGetFiles(unittest.TestCase):

    @patch("ofrom_outils.common.iter_file")
    def test_file(self, mock_iter):
        mock_iter.return_value = [
            ("file2", ".TextGrid", "file2.TextGrid",
             "dir\\file2.TextGrid"),
            ("file1", ".TextGrid", "file1.TextGrid",
             "dir\\file1.TextGrid")
        ]
        l_res = get_files("")
        self.assertEqual(l_res, [
            "dir\\file1.TextGrid", "dir\\file2.TextGrid"
        ])

    @patch("ofrom_outils.common.iter_all")
    def test_all(self, mock_iter):
        mock_iter.return_value = [
            ("file2", ".TextGrid", "file2.TextGrid",
             "dir\\file2.TextGrid"),
            ("file1", ".TextGrid", "file1.TextGrid",
             "dir\\file1.TextGrid")
        ]
        l_res = get_files("", ch_all=True)
        self.assertEqual(l_res, [
            "dir\\file1.TextGrid", "dir\\file2.TextGrid"
        ])

    @patch("ofrom_outils.common.iter_file")
    def test_verbose(self, mock_iter):
        mock_iter.return_value = [
            ("file1", ".TextGrid", "file1.TextGrid",
             "dir\\file1.TextGrid"),
            ("file2", ".TextGrid", "file2.TextGrid",
             "dir\\file2.TextGrid")
        ]
        l_res = get_files("", verbose=True)
        self.assertEqual(l_res, mock_iter.return_value)


@patch("ofrom_outils.common.iter_file")
@patch("ofrom_outils.common.sub_corpus")
@patch("ofrom_outils.common.fix_lext")
@patch("ofrom_outils.common.os.path.isdir")
@patch("ofrom_outils.common.CORP", ["corp1", "corp2"])
class TestIterCore(unittest.TestCase):

    def test_core(self, mock_isdir, mock_lext, mock_sub, mock_iter):
        mock_isdir.return_value = True
        mock_lext.return_value = []
        mock_sub.return_value = ["subcorp"]
        mock_iter.return_value = [
            ("file", ".xml", "file.xml", "subcorp\\file.xml")
        ]
        l_res = [tpl for tpl in iter_core()]
        self.assertEqual(l_res, [
            ("corp1", "file", ".xml", "file.xml", "subcorp\\file.xml"),
            ("corp2", "file", ".xml", "file.xml", "subcorp\\file.xml")
        ])
        assert mock_sub.call_count == 2
        assert mock_iter.call_count == 2


@patch("ofrom_outils.common.iter_core")
class TestGetCore(unittest.TestCase):

    def test_core(self, mock_core):
        mock_core.return_value = [
            ("corp2", "file3", ".xml", "file3.xml", "corp2\\file3.xml"),
            ("corp2", "file2", ".xml", "file2.xml", "corp2\\file2.xml"),
            ("corp1", "file1", ".xml", "file1.xml", "corp1\\file1.xml")
        ]
        l_res = get_core()
        self.assertEqual(l_res, [
            "corp2\\file2.xml", "corp2\\file3.xml", "corp1\\file1.xml"
        ])

    def test_verbose(self, mock_core):
        mock_core.return_value = [
            ("corp1", "file", ".xml", "file.xml", "subcorp\\file.xml"),
            ("corp2", "file", ".xml", "file.xml", "subcorp\\file.xml")
        ]
        l_res = get_core(verbose=True)
        self.assertEqual(l_res, mock_core.return_value)


