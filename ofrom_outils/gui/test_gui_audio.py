import unittest
from unittest.mock import patch
import tkinter as tk

from ofrom_outils.gui.gui_audio import (
    validate_mean, run_convert, run_mean, CorAudio
)


class TestAudioStaticFunctions(unittest.TestCase):
    def test_validate_mean(self):
        self.assertEqual(validate_mean(''), True)
        self.assertEqual(validate_mean('-.'), True)
        self.assertEqual(validate_mean('-12.136'), True)
        self.assertEqual(validate_mean('a'), False)

    @patch("ofrom_outils.gui.gui_audio.all_audio_convert")
    def test_run_convert(self, mock_conv):
        run_convert("test", "test2", "typ")
        mock_conv.assert_called_once_with(
            "test",
            "test2",
            "typ",
            False,
            False,
            False
        )
        mock_conv.reset_mock()
        run_convert("test", "test", "typ")
        mock_conv.assert_called_once_with(
            "test",
            "test",
            "typ",
            True,
            False,
            False
        )

    @patch("ofrom_outils.gui.gui_audio.all_audio_mean")
    def test_run_mean(self, mock_mean):
        run_mean("test", "test2", -1.3)
        mock_mean.assert_called_once_with(
            "test",
            "test2",
            None,
            -1.3,
            False,
            False
        )
        mock_mean.reset_mock()
        run_mean("test", "test", None)
        mock_mean.assert_called_once_with(
            "test",
            "test",
            None,
            None,
            True,
            False
        )


class TestCorAudio(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.data = {
            "c": {
                "indir": "testc",
                "outdir": "testc2",
                "opts": {
                    "copy": ["Copier", True],
                    "move": ["Déplacer", False],
                    "delete": ["Supprimer", True],
                }
            },
            "m": {
                "indir": "testm",
                "outdir": "testm2",
                "mean": 5.31
            }
        }

    def tearDown(self):
        self.root.destroy()

    def pyw(self, text: str = "", mode: str = "w") -> None:
        return

    def test_init(self):
        aud = CorAudio(self.root, self.data, self.pyw)
        self.assertEqual(aud.data.m.indir, "testm")
        self.assertEqual(aud.data.c.opts['copy'], ['Copier', True])

