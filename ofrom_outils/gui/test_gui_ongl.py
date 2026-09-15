import tkinter as tk
import unittest
from dataclasses import dataclass
from tkinter import filedialog
from typing import Any
from unittest.mock import patch, Mock, call

from ofrom_outils.gui.gui_ongl import (
    update_dc,
    AbsPath, FilePath, DirPath, TreePath,
    Options, CheckOptions, RadioOptions,
    CorOngl
)

widget_type = type[tk.Widget]


@dataclass
class MockData:
    name: str
    value: int


@dataclass
class MockDepthData:
    name: str
    data: MockData


class TestUpdateDc(unittest.TestCase):
    def test_update_dc(self):
        cl = MockDepthData("marsh", MockData("t", 1))
        update_dc(cl, {
            "bunk": "n",
            "data": {
                "name": "stet"
            }
        })
        self.assertEqual(cl.data.name, "stet")
        self.assertEqual(cl.data.value, 1)


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


class TestTreePath(unittest.TestCase):

    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.widget = TreePath(self.root)

    def tearDown(self):
        self.root.destroy()

    def test_initial_state(self):
        self.assertEqual(self.widget.sel.get(), 0)
        self.assertEqual(len(self.widget.tree.get_children()), 0)

    @patch(
        "tkinter.filedialog.askopenfilenames",
        return_value=("/tmp/a.txt", "/tmp/b.txt", "/tmp/b.wav")
    )
    def test_add(self, _):
        self.widget.l_ext = [".txt"]
        self.widget.add()
        items = self.widget.tree.get_children()

        self.assertEqual(len(items), 2)
        self.assertEqual(self.widget.tree.item(items[0], "text"), "a.txt")
        self.assertEqual(
            self.widget.tree.item(items[0], "values")[0],
            "/tmp/a.txt"
        )

    def test_selection_none(self):
        self.widget.tree.insert("", "end", text="a")
        self.widget.tree.insert("", "end", text="b")

        self.widget._selection()

        self.assertEqual(self.widget.sel.get(), 0)

    def test_selection_partial(self):
        a = self.widget.tree.insert("", "end", text="a")
        self.widget.tree.insert("", "end", text="b")

        self.widget.tree.selection_set(a)
        self.widget._selection()

        self.assertEqual(self.widget.sel.get(), 1)

    def test_selection_all(self):
        a = self.widget.tree.insert("", "end", text="a")
        b = self.widget.tree.insert("", "end", text="b")

        self.widget.tree.selection_set((a, b))
        self.widget._selection()

        self.assertEqual(self.widget.sel.get(), 2)

    def test_select_all(self):
        a = self.widget.tree.insert("", "end", text="a")
        b = self.widget.tree.insert("", "end", text="b")

        self.widget.sel.set(2)
        self.widget.select_all()

        self.assertEqual(
            set(self.widget.tree.selection()),
            {a, b}
        )

    def test_unselect_all(self):
        a = self.widget.tree.insert("", "end", text="a")
        b = self.widget.tree.insert("", "end", text="b")

        self.widget.tree.selection_set((a, b))
        self.widget.sel.set(0)

        self.widget.select_all()

        self.assertEqual(self.widget.tree.selection(), ())

    def test_remove_selected(self):
        a = self.widget.tree.insert("", "end", text="a")
        b = self.widget.tree.insert("", "end", text="b")

        self.widget.tree.selection_set(a)
        self.widget.remove_selected()

        self.assertEqual(self.widget.tree.get_children(), (b,))

    def test_get(self):
        self.widget.tree.insert("", "end", text="a", values=("/tmp/a.txt",))
        self.widget.tree.insert("", "end", text="b", values=("/tmp/b.txt",))

        self.assertEqual(
            self.widget.get(),
            ["/tmp/a.txt", "/tmp/b.txt"]
        )

    def test_get_selected(self):
        a = self.widget.tree.insert("", "end", text="a", values=("/tmp/a.txt",))
        self.widget.tree.insert("", "end", text="b", values=("/tmp/b.txt",))

        self.widget.tree.selection_set(a)

        self.assertEqual(
            self.widget.get_selected(),
            ["/tmp/a.txt"]
        )

    @patch("ofrom_outils.gui.gui_ongl.os.path.isfile", return_value=True)
    def test_set(self, mock_isfile):
        self.widget.tree.insert("", "end", text="old", values=("/tmp/old.txt",))

        self.widget.set([
            "/tmp/a.txt",
            "/tmp/b.txt",
        ])

        self.assertEqual(
            self.widget.get(),
            ["/tmp/a.txt", "/tmp/b.txt"]
        )
        mock_isfile.assert_has_calls([
            call("/tmp/a.txt"),
            call("/tmp/b.txt"),
        ])
        self.assertEqual(self.widget.tree.selection(), ())
        self.assertEqual(self.widget.sel.get(), 0)

    @patch("ofrom_outils.gui.gui_ongl.os.path.isfile", return_value=True)
    def test_set_selected(self, mock_isfile):
        self.widget.set([
            "/tmp/a.txt",
            "/tmp/b.txt",
            "/tmp/c.txt",
        ])

        self.widget.set_selected([
            "/tmp/a.txt",
            "/tmp/c.txt",
        ])

        self.assertEqual(
            set(self.widget.get_selected()),
            {"/tmp/a.txt", "/tmp/c.txt"}
        )
        self.assertEqual(self.widget.sel.get(), 1)


class TestOptions(unittest.TestCase):

    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.widget = Options(self.root)
        self.widget.grid()
        self.root.update_idletasks()

    def tearDown(self):
        self.root.destroy()

    def test_initial_state(self):
        self.assertFalse(self.widget.expanded)

    def test_toggle_show(self):
        self.widget.toggle()

        self.assertTrue(self.widget.expanded)
        self.assertEqual(self.widget.button.cget("text"), " - ")

    def test_toggle_hide(self):
        self.widget.toggle()
        self.widget.toggle()

        self.assertFalse(self.widget.expanded)
        self.assertEqual(self.widget.button.cget("text"), " + ")

    def test_add(self):
        entry = self.widget.add(tk.Entry)

        self.assertIsInstance(entry, tk.Entry)
        self.assertIs(entry.master, self.widget.content)

def _buttons(widget, typ: widget_type = tk.Radiobutton):
    return [
        w for w in widget.winfo_children()
        if isinstance(w, typ)
    ]


def _test_grid(self, widget, typ):
    buttons = _buttons(widget, typ)

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

        self.assertEqual(len(_buttons(widget, tk.Checkbutton)), 3)
        self.assertEqual(len(widget.vals), 3)
        self.assertIn("copy", widget.vals)
        self.assertIn("move", widget.vals)
        self.assertIn("delete", widget.vals)
        self.assertTrue(widget.vals["copy"].get())
        self.assertFalse(widget.vals["move"].get())
        self.assertTrue(widget.vals["delete"].get())

        widget.reset({})
        self.assertEqual(len(_buttons(widget, tk.Checkbutton)), 0)
        self.assertEqual(len(widget.vals), 0)

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

    def test_set(self):
        widget = CheckOptions(self.root, self.ops)
        widget.set("delete")

        self.assertEqual(widget.vals.get("delete"), False)

    def test_checkboxes(self):
        widget = CheckOptions(self.root, self.ops)

        buttons = _buttons(widget, tk.Checkbutton)
        self.assertEqual(len(buttons), 3)
        self.assertFalse(widget.get()["move"])

        buttons[1].invoke()
        self.assertTrue(widget.get()["move"])

    def test_grid(self):
        widget = CheckOptions(self.root, self.ops, nb_cols=2)
        _test_grid(self, widget, tk.Checkbutton)

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
        self.assertEqual(widget.val.get(), "delete")

        widget.reset({})
        self.assertEqual(len(_buttons(widget)), 0)
        self.assertEqual(widget.val.get(), "")

    def test_get(self):
        widget = RadioOptions(self.root, self.ops)

        self.assertEqual(widget.get(), "delete")

    def test_set(self):
        widget = RadioOptions(self.root, self.ops)
        widget.set("copy")
        self.assertEqual(widget.get(), "copy")

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
        _test_grid(self, widget, tk.Radiobutton)


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


if __name__ == "__main__":
    unittest.main()
