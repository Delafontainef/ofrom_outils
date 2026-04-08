import os
import unittest
from unittest.mock import patch

from ofrom_outils.audio.audio import (
    clean_ext, check, probe, setup_conv
)


@patch("ofrom_outils.audio.audio.os.replace")
class TestCleanExt(unittest.TestCase):

    def test_clean_ext(self, mock_replace):
        path = os.path.join("path", ".file.ext")
        self.assertEqual(clean_ext(path), path)
        path = os.path.join("path", "file.ext")
        self.assertEqual(clean_ext(path), path)
        path2 = os.path.join("path", "file.ext3.ext2.ext")
        self.assertEqual(clean_ext(path2), path)
        mock_replace.assert_called_once_with(path2, path)


@patch("ofrom_outils.audio.audio.clean_ext")
@patch("ofrom_outils.audio.audio.os.path.isfile")
class TestCheck(unittest.TestCase):

    def test_check(self, mock_isfile, mock_clean):
        mock_isfile.return_value = True
        mock_clean.side_effect = lambda path: path
        tpl = check("file", ".ext", "file.ext",
                    os.path.join("path", "file.ext"))
        self.assertEqual(tpl[0], False)
        tpl = check("file", ".wav", "file.ext3.wav",
                    os.path.join("path", "file.ext3.wav"))
        self.assertEqual(tpl[0], True)
        self.assertEqual(tpl[3], "file.ext3.wav")


@patch("ofrom_outils.audio.audio.subprocess")
class TestProbe(unittest.TestCase):

    def test_probe_md(self, mock_sproc):
        mock = mock_sproc.run.return_value
        mock.stdout.decode.return_value = "duration=40.\nchannels=2\n"
        d_res = probe("a_path")
        self.assertEqual(d_res,
                         {"duration": 40, "channel": 2, 'sample_rate': -1})

    def test_probe_all(self, mock_sproc):
        mock = mock_sproc.Popen.return_value
        _mock2 = mock.stdout.read.return_value = (
            b"Duration: 00:04:31.281, 44100 Hz, 2 channels Stream mapping")
        d_res = probe("a_path", True)
        self.assertEqual(d_res, {'duration': 273.81, 'channel': 2,
                                 'sample_rate': 44100})


@patch("ofrom_outils.audio.audio.probe")
class TestSetupConv(unittest.TestCase):

    def test_setup_conv(self, mock_probe):
        mock_probe.return_value = {'duration': 0., 'channel': 2,
                                   'sample_rate': 96000}
        npath, ac, ar, _ = setup_conv("file.ext", "", ".wav")
        self.assertEqual(npath, "file.wav")
        self.assertEqual(ac, "1")
        self.assertEqual(ar, "44100")
        mock_probe.return_value = {'duration': 0., 'channel': 2,
                                   'sample_rate': 8000}
        _npath, _ac, ar, d_md = setup_conv("file.ext", "", ".wav")
        self.assertEqual(ar, "8000")
        self.assertEqual(d_md,
                         {'duration': 0., 'channel': 1, 'sample_rate': 8000})
        print(d_md)

