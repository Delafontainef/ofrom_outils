import sys
import unittest
import tempfile
from unittest.mock import patch, MagicMock

from ofrom_outils.logs.log import log, Log

def set_tmp(suffix=".xlsx"):
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp_name = tmp.name
    return tmp_name

@patch("ofrom_outils.logs.log.print")
class TestLog(unittest.TestCase):

    def test_print(self, mock_print):
        log("hello")
        mock_print.assert_called_once()
        mock_print.reset_mock()
        log("hello", verbose=False)
        assert mock_print.call_count == 0
        log("hello", end=" world")
        mock_print.assert_called_once()
        args, kwargs = mock_print.call_args
        self.assertEqual(args, ('hello',))
        self.assertEqual(kwargs, {"end": " world"})


@patch("ofrom_outils.logs.log._w")
class TestLogClass(unittest.TestCase):

    def setUp(self):
        self.tlog = Log()

    def test_write_terminal(self, _mock_w):
        ...

    @unittest.skipUnless(sys.platform.startswith("win"),
                         "Windows only")
    @patch("msvcrt.getwch")
    def test_update_for_windows(self, mock_getwch, _mock_w):
        mock_getwch.side_effect = list("\x1b[12;40R")
        tlog = Log() # internal import
        pos = tlog.update()
        self.assertEqual(pos, [12, 39])

    @unittest.skipUnless(not sys.platform.startswith("win"),
                         "Unix only")
    @patch("ofrom_outils.logs.log.sys.stdin.read")
    @patch("termios.tcgetattr")
    @patch("termios.tcsetattr")
    @patch("tty.setcbreak")
    def test_update_for_linux(
            self, _mock_tcbreak, _mock_tcsetattr, mock_tcgetattr,
            mock_read, _mock_w
    ):
        mock_tcgetattr.return_value = "state"
        mock_read.side_effect = list("\x1b[12;40R")
        tlog = Log() # internal imports
        pos = tlog.update()
        self.assertEqual(pos, [12, 39])

    def test_move(self, mock_w):
        self.tlog.move(12, 39)
        mock_w.assert_called_once_with("\x1b[12;40H")

    def test_clear(self, mock_w):
        self.tlog.clear()
        mock_w.assert_called_once_with("\x1b[J")

    @patch("ofrom_outils.logs.log.os.system")
    def test_prt_clear(self, mock_os, mock_w):
        self.tlog.prt("", "clear")
        mock_os.assert_called_once()
        assert mock_w.call_count == 0
        self.assertEqual(self.tlog.cursor, [1, 0])

    @patch("ofrom_outils.logs.log.Log.clear")
    @patch("ofrom_outils.logs.log.Log.move")
    def test_prt_w(self, mock_move, mock_clear, mock_w):
        self.tlog.prt("hallo", "w")
        mock_move.assert_called_once()
        mock_clear.assert_called_once()
        mock_w.assert_called_once_with("hallo")

    @patch("ofrom_outils.logs.log.Log.update")
    def test_prt_a(self, mock_update, mock_w):
        self.tlog.prt("nope")
        mock_w.assert_called_once_with("nope")
        mock_update.assert_called_once()

    def test_write(self, _mock_w):
        self.tlog.file_path = set_tmp()
        self.tlog.write("I don't ")
        self.tlog.write("know what ")
        with open(self.tlog.file_path, 'r', encoding="utf-8") as rf:
            txt = rf.read()
        self.assertEqual(txt, "I don't know what ")
        self.tlog.write("went wrong", "w")
        with open(self.tlog.file_path, 'r', encoding="utf-8") as rf:
            txt = rf.read()
        self.assertEqual(txt, "went wrong")
        self.tlog.file_path = ""

    @patch("ofrom_outils.logs.log.Log.write")
    @patch("ofrom_outils.logs.log.Log.prt")
    def test_log_terminal(self, mock_prt, mock_write, _mock_w):
        self.tlog.log("terminal")
        mock_prt.assert_called_once_with("terminal", mode="a")
        assert mock_write.call_count == 0

    @patch("ofrom_outils.logs.log.Log.write")
    @patch("ofrom_outils.logs.log.Log.prt")
    def test_log_file(self, mock_prt, mock_write, _mock_w):
        self.tlog.log("file", "file.npo")
        assert mock_prt.call_count == 0
        mock_write.assert_called_once_with("file", mode="a")
        mock_write.reset_mock()
        self.assertEqual(self.tlog.file_path, "file.npo")
        self.tlog.log("file", "")
        assert mock_prt.call_count == 0
        mock_write.assert_called_once_with("file", mode="a")
        self.assertEqual(self.tlog.file_path, "file.npo")

    @patch("ofrom_outils.logs.log.Log.write")
    @patch("ofrom_outils.logs.log.Log.prt")
    def test_log_io(self, mock_prt, mock_write, _mock_w):
        mock_io = MagicMock()
        self.tlog.log("custom-io", mock_io)
        assert mock_prt.call_count == 0
        assert mock_write.call_count == 0
        mock_io.assert_called_once_with("custom-io", mode="a")