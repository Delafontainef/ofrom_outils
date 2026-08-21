import tkinter as tk
import unittest
from unittest.mock import patch

from ofrom_outils.gui.gui_window import (
    CorMenu, CorConsole, CorMain
)

import json
import os
import tempfile

class TestCorMenu(unittest.TestCase):

    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.menu = CorMenu(self.root)

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


class TestCorMain(unittest.TestCase):

    def setUp(self):
        self.gui = CorMain()
        self.tmp = tempfile.TemporaryDirectory()

        self.data_patch = patch(
            "ofrom_outils.gui.gui_window.DATA",
            self.tmp.name
        )
        self.data_patch.start()

    def tearDown(self):
        self.data_patch.stop()
        self.tmp.cleanup()
        self.gui.destroy()

    def test_load_config_default(self):
        self.gui._load_config()

        self.assertEqual(
            self.gui.data,
            {
                "taille": [720, 480],
                "save_file": "",
                "actif": -1
            }
        )

    def test_load_config_exists(self):
        config = {
            "taille": [1000, 700],
            "save_file": "test.txt",
            "actif": 2
        }
        path = os.path.join(self.tmp.name, "ofrom_gui_config.json")

        with open(path, "w", encoding="utf-8") as wf:
            json.dump(config, wf)
        self.gui._load_config()

        self.assertEqual(self.gui.data, config)

    def test_save_config(self):
        self.gui.data = {
            "taille": [800, 600],
            "save_file": "foo.txt",
            "actif": 1
        }
        self.gui._save_config()

        path = os.path.join(self.tmp.name, "ofrom_gui_config.json")
        with open(path, "r", encoding="utf-8") as rf:
            saved = json.load(rf)

        self.assertEqual(saved, self.gui.data)

    def test_save_config_ignores(self):
        self.gui.data = {"test": 1}
        event = tk.Event()
        event.widget = tk.Frame(self.gui) # different widget destroyed
        self.gui._save_config(event)

        path = os.path.join(self.tmp.name, "ofrom_gui_config.json")
        self.assertFalse(os.path.exists(path))

if __name__ == "__main__":
    unittest.main()