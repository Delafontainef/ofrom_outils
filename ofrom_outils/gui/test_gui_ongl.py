import tkinter as tk
import unittest
from dataclasses import dataclass
from typing import Any
from unittest.mock import patch, Mock

from ofrom_outils.gui.gui_ongl import (
    AbsPath, FilePath, DirPath, CheckOptions, RadioOptions,
    CorOngl
)


@dataclass
class MockData:
    name: str
    value: int


class TestPath(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()

    def tearDown(self):
        self.root.destroy()

    @patch("ofrom_outils.gui.gui_ongl.os.path.exists")
    def test_format_path(self, mock_exists):
        widget = AbsPath(self.root)

        mock_exists.return_value = True
        for p1, p2 in [
            ("/tmp/file.txt", "/tmp/file.txt"),
            ("/tmp/file.csv", "/tmp/file.csv")
        ]:
            self.assertEqual(widget.format_path(p1), p2)
        widget = AbsPath(self.root, regex=r"\.txt$")
        for p1, p2 in [
            ("/tmp/file.txt", "/tmp/file.txt"),
            ("/tmp/file.csv", "")
        ]:
            self.assertEqual(widget.format_path(p1), p2)
        mock_exists.return_value = False
        self.assertEqual(widget.format_path("/tmp/file.txt"), "")

    def test_set_path(self):
        pf = AbsPath(self.root, "Test")
        with patch.object(
                AbsPath,
                "format_path",
                return_value="foo"
        ):
            pf.set("bar")
        self.assertEqual(pf.value.get(), "foo")

    def test_set_path_as(self):
        mock_setopen = Mock(return_value="/tmp/file.csv")
        pf = AbsPath(self.root, "", setopen=mock_setopen)
        with patch.object(pf, "set") as mock_set:
            pf.set_path_as()
            mock_set.assert_called_once_with("/tmp/file.csv")
            mock_set.reset_mock()
            mock_setopen.return_value = ""
            pf.set_path_as()
            mock_set.assert_not_called()

    def test_get_path(self):
        pf = AbsPath(self.root, "")
        pf.value.set("hello/world/")
        value = pf.get()
        self.assertEqual(value, "")
        with patch.object(pf, "format_path", return_value="foo"):
            value = pf.get()
            self.assertEqual(value, "foo")

    def test_file(self):
        widget = FilePath(self.root)
        self.assertIs(widget.setopen, tk.filedialog.askopenfilename)

    def test_dirs(self):
        widget = DirPath(self.root)
        self.assertIs(widget.setopen, tk.filedialog.askdirectory)


def _buttons(widget):
    return [
        w for w in widget.winfo_children()
        if isinstance(w, tk.Radiobutton)
    ]


def _test_grid(self, widget):
    buttons = _buttons(widget)

    self.assertEqual(buttons[0].grid_info()["row"], 0)
    self.assertEqual(buttons[0].grid_info()["column"], 0)
    self.assertEqual(buttons[1].grid_info()["row"], 0)
    self.assertEqual(buttons[1].grid_info()["column"], 1)
    self.assertEqual(buttons[2].grid_info()["row"], 1)
    self.assertEqual(buttons[2].grid_info()["column"], 0)


class TestCheckOptions(unittest.TestCase):

    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()

        self.ops = {
            "copy": ["Copier", True],
            "move": ["Déplacer", False],
            "delete": ["Supprimer", True],
        }

    def tearDown(self):
        self.root.destroy()

    def test_init(self):
        widget = CheckOptions(self.root, self.ops)

        self.assertEqual(len(_buttons(widget)), 3)
        self.assertEqual(len(widget.vals), 3)
        self.assertIn("copy", widget.vals)
        self.assertIn("move", widget.vals)
        self.assertIn("delete", widget.vals)
        self.assertTrue(widget.vals["copy"].get())
        self.assertFalse(widget.vals["move"].get())
        self.assertTrue(widget.vals["delete"].get())

    def test_get(self):
        widget = CheckOptions(self.root, self.ops)

        self.assertEqual(
            widget.get(),
            {
                "copy": True,
                "move": False,
                "delete": True,
            }
        )

    def test_checkboxes(self):
        widget = CheckOptions(self.root, self.ops)

        buttons = _buttons(widget)
        self.assertEqual(len(buttons), 3)
        self.assertFalse(widget.get()["move"])

        buttons[1].invoke()
        self.assertTrue(widget.get()["move"])

    def test_grid(self):
        widget = CheckOptions(self.root, self.ops, nb_cols=2)
        _test_grid(self, widget)

    def test_trace(self):
        widget = CheckOptions(self.root, self.ops)
        values = []

        def callback(*_):
            values.append(widget.get())

        widget.trace_add("write", callback)
        widget.vals["move"].set(True)
        self.assertEqual(values[-1]["move"], True)


class TestRadioOptions(unittest.TestCase):

    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()

        self.ops = {
            "copy": ["Copier", True],
            "move": ["Déplacer", False],
            "delete": ["Supprimer", True],
        }

    def tearDown(self):
        self.root.destroy()

    def test_init(self):
        widget = RadioOptions(self.root, self.ops)

        self.assertEqual(len(_buttons(widget)), 3)
        self.assertEqual(widget.get(), "delete")

    def test_radiobuttons(self):
        ops = {
            "copy": ["Copier", False],
            "move": ["Déplacer", False],
            "delete": ["Supprimer", False],
        }
        widget = RadioOptions(self.root, ops)
        buttons = _buttons(widget)

        self.assertEqual(widget.get(), "")
        buttons[2].invoke()
        self.assertEqual(widget.get(), "delete")
        buttons[0].invoke()
        self.assertEqual(widget.get(), "copy")

    def test_grid(self):
        widget = RadioOptions(self.root, self.ops, nb_cols=2)
        _test_grid(self, widget)


class MockOngl(CorOngl[MockData]):
    def fill_data(self, data: dict[str, Any]) -> MockData:
        return MockData(**data)


class TestCorOngl(unittest.TestCase):

    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.ongl = MockOngl(
            self.root,
            {"name": "abc", "value": 10},
            lambda a, b: None
        )

    def tearDown(self):
        self.root.destroy()

    def test_init_fill_data(self):
        self.assertEqual(
            self.ongl.data,
            MockData(name="abc", value=10)
        )

    def test_get_data(self):
        result = self.ongl.get_data()

        self.assertEqual(
            result,
            {"name": "abc", "value": 10}
        )
        result["name"] = "changed"

        self.assertEqual(self.ongl.data.name, "abc")

    def test_set_data(self):
        self.ongl.set_data({"name": "changed"})

        self.assertEqual(self.ongl.data.name, "changed")
        self.assertEqual(self.ongl.data.value, 10)

        self.ongl.set_data({"unknown": 123})

        self.assertFalse(hasattr(self.ongl.data, "unknown"))
