import json
import os
import tempfile
import tkinter as tk
import unittest
from dataclasses import asdict, dataclass
from tkinter import ttk
from typing import Any
from unittest.mock import patch, Mock, mock_open

from ofrom_outils.gui.gui import (
    update_dc, Pathfinder, CorOngl, CorMenu, CorConsole, CorMain
)
from ofrom_outils.gui.gui_models import CorMainData


@dataclass
class MockData:
    name: str
    value: int


class TestUpdateDc(unittest.TestCase):
    def test_update_dc(self):
        @dataclass
        class Data:
            name: str = "old"
            value: int = 1

        obj = Data()

        update_dc(obj, {
            "name": "new",
            "value": 42,
            "unknown": "ignored",
        })

        self.assertEqual(obj.name, "new")
        self.assertEqual(obj.value, 42)
        self.assertFalse(hasattr(obj, "unknown"))


class TestPathfinder(unittest.TestCase):

    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()

    def tearDown(self):
        self.root.destroy()

    @patch("ofrom_outils.gui.gui.os.path.isdir")
    @patch("ofrom_outils.gui.gui.os.path.isfile")
    def test_format_path_invalid(self, mock_isfile, mock_isdir):
        mock_isdir.return_value = False
        mock_isfile.return_value = False

        self.assertEqual(Pathfinder.format_path("bad"), "")

        mock_isfile.return_value = True
        self.assertEqual(Pathfinder.format_path("file.txt"), "")
        self.assertEqual(
            Pathfinder.format_path("metadata.xlsx"),
            "metadata.xlsx"
        )

        mock_isdir.return_value = True
        self.assertEqual(Pathfinder.format_path("a/b/"), "a/b/")

    def test_set_path(self):
        pf = Pathfinder(self.root, "Test")
        with patch.object(
                Pathfinder,
                "format_path",
                return_value="foo"
        ):
            pf.set("bar")
        self.assertEqual(pf.value.get(), "foo")

    @patch("tkinter.filedialog.askdirectory")
    @patch("tkinter.filedialog.askopenfilename")
    def test_set_path_as_file(self, mock_afile, mock_adir):
        pf = Pathfinder(self.root, "Métadonnées")
        with patch.object(pf, "set") as mock_set:
            mock_afile.return_value = "metadata.xlsx"
            pf.set_path_as()
            mock_set.assert_called_once_with("metadata.xlsx")
            mock_set.reset_mock()
            mock_afile.return_value = "some/path"
            pf.set_path_as()
            mock_set.assert_called_once_with("some/path")
            mock_set.reset_mock()
            mock_afile.return_value = ""
            pf.set_path_as()
            mock_set.assert_not_called()
            pf.label.config(text="Test dirs")
            mock_set.reset_mock()
            mock_adir.return_value = "some/other"
            pf.set_path_as()
            mock_set.assert_called_once_with("some/other")

    def test_get_path(self):
        pf = Pathfinder(self.root, "")
        pf.value.set("hello/world/")
        value = pf.get()
        self.assertEqual(value, "")
        with patch.object(pf, "format_path", return_value="foo"):
            value = pf.get()
            self.assertEqual(value, "foo")


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


class TestCorMenu(unittest.TestCase):

    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.menu = CorMenu(self.root, {
            "load": lambda: None,
            "save": lambda: None,
            "save_as": lambda: None,
        })

    def tearDown(self):
        self.root.destroy()

    def test_main_entries(self):
        self.assertEqual(self.menu.entrycget(0, "label"), "Fichiers")
        self.assertEqual(self.menu.entrycget(1, "label"), "Aide")

    def test_file_menu_entries(self):
        submenu_name = self.menu.entrycget(0, "menu")
        submenu = self.menu.nametowidget(submenu_name)

        self.assertEqual(submenu.entrycget(0, "label"), "Nouvel onglet")
        self.assertEqual(submenu.entrycget(1, "label"), "Fermer l'onglet")
        self.assertEqual(submenu.entrycget(3, "label"), "Charger...")


class TestCorConsole(unittest.TestCase):

    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.console = CorConsole(self.root)

    def tearDown(self):
        self.root.destroy()

    def get_text(self):
        return self.console.text.get("1.0", "end-1c")

    def test_activate(self):
        with self.assertRaises(ValueError):
            with self.console.activate():
                self.assertEqual(
                    self.console.text.cget("state"),
                    "normal"
                )
                raise ValueError

        self.assertEqual(
            self.console.text.cget("state"),
            "disabled"
        )

    def test_write_append(self):
        self.console.write("abc")
        self.console.write("def")

        self.assertEqual(self.get_text(), "abcdef")

    def test_clear(self):
        self.console.write("abcdef")

        self.console.clear()

        self.assertEqual(self.get_text(), "")

    def test_clear_from_position(self):
        self.console.write("abcdef")

        self.console.clear(1, 3)

        self.assertEqual(self.get_text(), "abc")

    def test_mark(self):
        self.console.write("abcdef")
        self.console.mark("test", "1.3")

        self.assertEqual(
            self.console.text.index("test"),
            "1.3"
        )

    def test_write_at_mark(self):
        self.console.write("abcdef")
        self.console.mark("w", "1.3")

        self.console.write("XYZ", "w")

        self.assertEqual(self.get_text(), "abcXYZ")

    def test_pyw(self):
        with (
            patch.object(self.console, "write") as mock_write,
            patch.object(self.console, "mark") as mock_mark,
            patch.object(self.console, "clear") as mock_clear
        ):
            self.console.pyw("abc", "a")
            mock_write.assert_called_once_with("abc", "a")
            self.console.pyw("abc", "w")
            self.console.pyw("abc", "d")
            self.assertEqual(mock_write.call_count, 2)
            self.console.pyw("", "mark")
            mock_mark.assert_called_once_with()
            self.console.pyw("", "clear")
            mock_clear.assert_called_once_with()



class TestCorMain(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()

        self.data_patch = patch(
            "ofrom_outils.gui.gui.DATA",
            self.tmp.name
        )
        self.data_patch.start()
        self.gui = None

    def tearDown(self):
        if self.gui:
            self.gui.destroy()
        self.data_patch.stop()
        self.tmp.cleanup()

    @staticmethod
    def _geometry(
            x: int = 0,
            y: int = 0,
            width: int = 720,
            height: int = 480,
            widget: tk.Misc = tk.Misc()
    ) -> tk.Event:
        event = tk.Event()
        event.x = x
        event.y = y
        event.width = width
        event.height = height
        event.widget = widget
        return event

    @staticmethod
    def _fake_after(delay, callback, *args):
        delay -= 300
        callback(*args)

    def test_config_default(self):
        self.gui = CorMain()  # causes '_load_config' to be called

        self.assertEqual(
            self.gui.data,
            CorMainData([0, 0], [720, 480], 50, "", -1)
        )

        self.gui.destroy()  # causes '_save_config' to be called
        self.gui = None
        config_file = os.path.join(self.tmp.name, "ofrom_gui_config.json")
        with open(config_file, "r", encoding="utf-8") as rf:
            json_data = json.load(rf)
        self.assertEqual(
            json_data,
            {
                "pos": [0, 0],
                "size": [720, 480],
                "sash_pos": 50,
                "save_file": "",
                "active": -1
            }
        )

    def test_load_config_exists(self):
        config = {
            "pos": [10, 24],
            "size": [1000, 700],
            "save_file": "test.txt",
            "active": 2,
            "unknown": "DO_NOT_LOAD"
        }
        path = os.path.join(self.tmp.name, "ofrom_gui_config.json")
        with open(path, "w", encoding="utf-8") as wf:
            json.dump(config, wf)

        self.gui = CorMain()

        self.assertEqual(
            self.gui.data,
            CorMainData([10, 24], [1000, 700], 50, "", 2)
        )
        self.assertEqual(
            self.gui.geometry(),
            "1x1+10+24"
        )  # size due to test environment

    def test_save_config_ignores(self):
        self.gui = CorMain()
        event = tk.Event()
        event.widget = tk.Frame(self.gui)  # different widget destroyed
        self.gui._save_config(event)

        path = os.path.join(self.tmp.name, "ofrom_gui_config.json")
        self.assertFalse(os.path.exists(path))

    def test_save_geometry(self):
        self.gui = CorMain()
        event = self._geometry(100, 200, 800, 600)
        self.gui._save_geometry(event)

        self.assertEqual(self.gui.data.pos, [100, 200])
        self.assertEqual(self.gui.data.size, [800, 600])

    def test_on_configure(self):
        self.gui = CorMain()
        event1 = self._geometry(0, 0, 720, 480, tk.Frame(self.gui))
        event2 = self._geometry(10, 20, 720, 480, self.gui)
        event3 = self._geometry(10, 30, 720, 480, self.gui)
        event4 = self._geometry(20, 50, 720, 480, self.gui)

        with (
            patch.object(self.gui, "after_cancel") as mock_cancel,
            patch.object(self.gui, "after") as mock_after
        ):
            self.gui._on_configure(event1)
            self.gui._on_configure(event2)
            self.gui._on_configure(event3)
            self.gui._on_configure(event4)

            self.assertEqual(mock_after.call_count, 3)
            self.assertEqual(mock_cancel.call_count, 2)
        with patch.object(self.gui, "after", side_effect=self._fake_after):
            self.gui._on_configure(event2)
            self.gui._on_configure(event3)
            self.gui._on_configure(event4)
            self.assertEqual(self.gui.data.pos, [20, 50])
            self.assertIsNone(self.gui._geometry_job)

    def test_set_geometry(self):
        self.gui = CorMain()
        self.gui.geometry(f"1x1+10+24")
        self.gui.set_geometry()  # gui.data default geometry
        self.assertEqual(self.gui.data.pos, [0, 0])
        self.assertEqual(self.gui.data.size, [720, 480])

        self.gui.set_geometry([20, 50], [1000, 800])
        self.assertEqual(self.gui.geometry(), "1x1+20+50")
        self.assertEqual(self.gui.data.pos, [20, 50])
        self.assertEqual(self.gui.data.size, [1000, 800])

    def test_empty_ongl(self):
        self.gui = CorMain()
        tab1 = Mock()
        tab2 = Mock()
        self.gui.ongl = [tab1, tab2]

        with patch.object(self.gui.champ, "forget") as mock_forget:
            self.gui._empty_ongl()

        self.assertEqual(self.gui.ongl, [])

        self.assertEqual(mock_forget.call_count, 2)
        mock_forget.assert_any_call(tab1)
        mock_forget.assert_any_call(tab2)
        tab1.destroy.assert_called_once()
        tab2.destroy.assert_called_once()
        self.assertIn(str(self.gui.plus_tab), self.gui.champ.tabs())

    def test_add_ongl(self):
        self.gui = CorMain()
        factory = Mock(
            side_effect=lambda *args, **kwargs: ttk.Frame(self.gui.champ)
        )

        with patch.dict(
                "ofrom_outils.gui.gui.ONGL",
                {"test": factory}
        ):
            self.gui._add_ongl(0, "test", {})
            self.gui._add_ongl(1, "test", {})
            self.gui._add_ongl(2, "invalid", {})

        self.assertEqual(self.gui.active, 1)
        compare = self.gui.ongl + [self.gui.plus_tab]
        for i, tab in enumerate(self.gui.champ.tabs()):
            self.assertIs(self.gui.champ.nametowidget(tab), compare[i])
        tab = self.gui.champ.nametowidget(
            self.gui.champ.tabs()[self.gui.active]
        )
        self.assertIs(
            self.gui.ongl[self.gui.active],
            tab
        )

    def test_load(self):
        self.gui = CorMain()
        with patch.object(self.gui, "_empty_ongl") as mock_empty:
            self.gui.load("missing.json")
            mock_empty.assert_not_called()

        data = {
            "0": {
                "save_file": "foo.json",
                "active": 1,
            },
            "1": {
                "name": "test",
                "value": 10,
            },
            "2": {
                "name": "test",
                "value": 20,
            },
        }
        with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".json",
                encoding="utf-8",
                delete=False
        ) as f:
            json.dump(data, f)
            path = f.name
        try:
            with (
                patch.object(self.gui, "_empty_ongl") as mock_empty,
                patch.object(self.gui, "_add_ongl") as mock_add,
                patch(
                    "ofrom_outils.gui.gui.update_dc"
                ) as mock_update,
            ):
                self.gui.load(path)

            mock_empty.assert_called_once()
            mock_update.assert_called_once_with(
                self.gui.data,
                data["0"]
            )
            self.assertEqual(mock_add.call_count, 2)
            mock_add.assert_any_call(
                2,
                "test",
                data["2"]
            )
        finally:
            f.close()

    def test_load_as(self):
        self.gui = CorMain()
        old_file = self.gui.data.save_file = "wapiti.txt"
        with (
            patch(
                "ofrom_outils.gui.gui.filedialog.askopenfilename",
                side_effect=["", "test.json"]
            ),
            patch.object(self.gui, "load") as mock_load,
        ):
            self.gui.load_as()
            mock_load.assert_not_called()
            self.assertEqual(self.gui.data.save_file, old_file)

            self.gui.load_as()
            mock_load.assert_called_once_with("test.json")
            self.assertEqual(self.gui.data.save_file, "test.json")

    def test_save(self):
        self.gui = CorMain()
        with (patch.object(self.gui, "save_as") as mock_save_as):
            self.gui.save("missing.json")
            mock_save_as.assert_called_once()

        with (
            patch(
                "ofrom_outils.gui.gui.os.path.isfile",
                return_value=False
            ) as mock_isfile,
            patch.object(self.gui, "save_as"),
        ):
            self.gui.save("saved.json")
        mock_isfile.assert_called_once_with("saved.json")

        ongl1 = Mock()
        ongl1.get_data.return_value = {"name": "A", "value": 1}
        ongl2 = Mock()
        ongl2.get_data.return_value = {"name": "B", "value": 2}
        self.gui.ongl = [ongl1, ongl2]
        m = mock_open()
        with (
            patch(
                "ofrom_outils.gui.gui.os.path.isfile",
                return_value=True
            ),
            patch("builtins.open", m),
            patch(
                "ofrom_outils.gui.gui.json.dump"
            ) as mock_dump
        ):
            self.gui.save("test.json")

        expected = {
            "0": asdict(self.gui.data),
            "1": {"name": "A", "value": 1},
            "2": {"name": "B", "value": 2},
        }
        mock_dump.assert_called_once_with(
            expected,
            m(),
            indent=4
        )
        ongl1.get_data.assert_called_once()
        ongl2.get_data.assert_called_once()

    def test_save_as(self):
        self.gui = CorMain()
        with (
            patch(
                "ofrom_outils.gui.gui.filedialog.asksaveasfilename",
                side_effect=["", "test.json"]
            ),
            patch.object(self.gui, "save") as mock_save,
        ):
            self.gui.save_as()
            mock_save.assert_not_called()
            self.assertEqual(self.gui.data.save_file, "")

            self.gui.save_as()
            mock_save.assert_called_once_with("test.json")
            self.assertEqual(self.gui.data.save_file, "test.json")

    def test_setup(self):
        self.gui = CorMain()
        with (
            patch.object(CorMain, "_load_config"),
            patch("ofrom_outils.gui.gui.os.path.isfile") as mock_isfile,
            patch.object(CorMain, "load") as mock_load,
        ):
            self.gui.data.save_file = "save.json"
            mock_isfile.return_value = False
            self.gui.setup()
            mock_load.assert_not_called()
            self.assertEqual(self.gui.data.save_file, "")
            self.gui.data.save_file = "save.json"
            mock_isfile.return_value = True
            self.gui.setup()
            mock_load.assert_called_with("save.json")

if __name__ == "__main__":
    unittest.main()
