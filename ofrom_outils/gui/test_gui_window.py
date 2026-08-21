import tkinter as tk
import unittest
from ofrom_outils.gui.gui_window import (
    CorMenu, CorConsole
)

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


if __name__ == "__main__":
    unittest.main()