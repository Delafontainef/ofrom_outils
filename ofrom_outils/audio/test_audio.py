import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from ofrom_outils.audio.audio import (
    clean_ext, check, probe, setup_conv, subp, audio_level, all_audio_level,
    audio_mean, all_audio_mean, audio_cut, to_mp3, to_wav, to_m4a,
    all_audio_convert, args
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


@patch("ofrom_outils.audio.audio.tempfile")
@patch("ofrom_outils.audio.audio.subprocess")
@patch("ofrom_outils.audio.audio.os")
class TestSubp(unittest.TestCase):

    def test_subp(self, mock_os, mock_sproc, mock_tempfile):
        p1 = os.path.join("path", "file.wav")
        p2 = os.path.join("path", "file2.wav")
        mock_os.path.exists.return_value = True
        mock_os.path.isfile.return_value = False
        mock_file = MagicMock()
        mock_file.__enter__.return_value = mock_file  # for 'with' statement
        mock_file.name = p1
        mock_tempfile.NamedTemporaryFile.return_value = mock_file
        p3 = subp(p1, p2, ".wav", [], False)
        self.assertEqual(p3, p2)
        mock_os.remove.assert_called_once_with(p1)
        mock_sproc.run.assert_called_once_with(
            [p1], shell=False, stdout=None, stderr=None)
        mock_os.replace.assert_called_once_with(p1, p2)
        mock_tempfile.NamedTemporaryFile.assert_called_once_with(delete=False,
                                                                 suffix=".wav")

    def test_subp_rem(self, mock_os, mock_sproc, mock_tempfile):
        p1 = os.path.join("path", "file.mp3")
        p2 = os.path.join("path", "file2.wav")
        mock_os.path.exists.return_value = True
        mock_os.path.isfile.return_value = True
        mock_file = MagicMock()
        mock_file.__enter__.return_value = mock_file  # for 'with' statement
        mock_file.name = p1
        mock_tempfile.NamedTemporaryFile.return_value = mock_file
        p3 = subp(p1, p2, ".wav", [])
        self.assertEqual(p3, p2)
        assert mock_os.remove.call_count == 2
        mock_sproc.run.assert_called_once_with(
            [p1], shell=False, stdout=None, stderr=None)
        mock_os.replace.assert_called_once_with(p1, p2)
        mock_tempfile.NamedTemporaryFile.assert_called_once_with(delete=False,
                                                                 suffix=".wav")


@patch("ofrom_outils.audio.audio.subprocess")
class TestAudioLevel(unittest.TestCase):

    def test_audio_level(self, mock_sproc):
        mock_res = mock_sproc.run.return_value
        mock_res.stdout.decode.return_value = (
            "mean_volume:4.8 dB max_volume:9 dB")
        m_vol, max_vol = audio_level("file.ext")
        self.assertEqual(m_vol, 4.8)
        self.assertEqual(max_vol, 9)

    def test_audio_level_fail(self, mock_sproc):
        mock_res = mock_sproc.run.return_value
        mock_res.stdout.decode.return_value = (
            "mean_volume:4.8 dB")
        m_vol, max_vol = audio_level("file.ext")
        self.assertEqual(m_vol, 4.8)
        self.assertEqual(max_vol, None)


@patch("ofrom_outils.audio.audio.check")
@patch("ofrom_outils.audio.audio.iter_all")
@patch("ofrom_outils.audio.audio.audio_level")
class TestAllAudioLevel(unittest.TestCase):

    def test_all_audio_level(self, mock_audio, mock_iter, mock_check):
        mock_iter.return_value = iter([
            ("fi1", ".wav", "fi1.wav", "path_fi1.wav"),
            ("fi2", ".wav", "fi2.wav", "path_fi2.wav"),
            ("fi3", ".wav", "fi3.wav", "path_fi3.wav")
        ])
        mock_check.side_effect = lambda fi, ext, file, path: (True, fi, ext,
                                                              file, path)
        mock_audio.side_effect = lambda path: {
            'path_fi1.wav': (4., 12.),
            'path_fi2.wav': (6., 9.),
            'path_fi3.wav': (5., 8.)
        }.get(path)
        l_out, g_mean, sd = all_audio_level("a_dir", verbose=False)
        self.assertIn('fi1', l_out[0])
        self.assertIn('fi2', l_out[1])
        self.assertEqual(g_mean, 5.)
        self.assertAlmostEqual(sd, 0.816, 3)


@patch("ofrom_outils.audio.audio.subp")
@patch("ofrom_outils.audio.audio.setup_conv")
class TestAudioMean(unittest.TestCase):

    def test_audio_mean(self, mock_setup, mock_subp):
        mock_setup.return_value = ("npath", 1, 44100, {})
        audio_mean("a_path", "another_path", 4., 5., ".wav")
        mock_subp.assert_called_once()
        args, _ = mock_subp.call_args
        self.assertEqual(args[0], "a_path")
        self.assertEqual(args[1], "npath")
        args = args[3]
        self.assertEqual(args[-1], 'volume=1.0dB')


@patch("ofrom_outils.audio.audio.check")
@patch("ofrom_outils.audio.audio.iter_all")
@patch("ofrom_outils.audio.audio.audio_mean")
class TestAllAudioMean(unittest.TestCase):

    def test_all_audio_mean(self, mock_audio, mock_iter, mock_check):
        l_out = [
            ("fi1", "LOW", 4., 5., 0.8),
            ("fi2", "HIGH", 6., 5., 0.8)
        ]
        mock_iter.return_value = iter([
            ("fi1", ".wav", "fi1.wav", "path_fi1.wav"),
            ("fi2", ".wav", "fi2.wav", "path_fi2.wav"),
            ("fi3", ".wav", "fi3.wav", "path_fi3.wav")
        ])
        mock_check.side_effect = lambda fi, ext, file, path: (True, fi, ext,
                                                              file, path)
        all_audio_mean("a_dir", "a_dir", l_out, verbose=False)
        assert mock_audio.call_count == 2
        args, _ = mock_audio.call_args
        self.assertEqual(
            args, (
                'path_fi2.wav', os.path.join('a_dir', 'fi2.wav'),
                6.0,
                5.0, '.wav',
                True)
        )

    @patch("ofrom_outils.audio.audio.all_audio_level")
    def test_with_all_audio_level(self, mock_all, mock_audio, mock_iter,
                                  mock_check):
        mock_all.return_value = (
            [
                ("fi1", "LOW", 4., 5., 0.8),
                ("fi2", "HIGH", 6., 5., 0.8)
            ], 5., 0.8
        )
        mock_iter.return_value = iter([
            ("fi1", ".wav", "fi1.wav", "path_fi1.wav"),
            ("fi2", ".wav", "fi2.wav", "path_fi2.wav"),
            ("fi3", ".wav", "fi3.wav", "path_fi3.wav")
        ])
        mock_check.side_effect = lambda fi, ext, file, path: (True, fi, ext,
                                                              file, path)
        all_audio_mean("a_dir", "a_dir", verbose=False)
        assert mock_audio.call_count == 2
        args, _ = mock_audio.call_args
        self.assertEqual(
            args, (
                'path_fi2.wav', os.path.join('a_dir', 'fi2.wav'),
                6.0,
                5.0, '.wav',
                True)
        )

    def test_with_to_list(self, mock_audio, mock_iter, mock_check):
        mock_iter.return_value = iter([
            ("fi1", ".wav", "fi1.wav", "path_fi1.wav"),
            ("fi2", ".wav", "fi2.wav", "path_fi2.wav"),
            ("fi3", ".wav", "fi3.wav", "path_fi3.wav")
        ])
        mock_check.side_effect = lambda fi, ext, file, path: (True, fi, ext,
                                                              file, path)
        l_out = ("nb;file;type;file_mean;global_mean;deviation\n" +
                 f"0;Global;None;5,0;5,0;0,8\n" +
                 f"1;fi1;LOW;4,0;5,0;0,8\n" +
                 f"1;fi2;HIGH;6,0;5,0;0,8\n").encode("utf-8")
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
            tmp.write(l_out)
            l_out = tmp.name
        try:
            all_audio_mean("a_dir", "a_dir", l_out, verbose=False)
        finally:
            os.remove(l_out)
        assert mock_audio.call_count == 2
        args, _ = mock_audio.call_args
        self.assertEqual(
            args, (
                'path_fi2.wav', os.path.join('a_dir', 'fi2.wav'),
                6.0,
                5.0, '.wav',
                True)
        )


@patch("ofrom_outils.audio.audio.subp")
class TestAudioCut(unittest.TestCase):

    def test_audio_cut(self, mock_subp):
        audio_cut("a_path", "another_path", 40., 65.)
        mock_subp.assert_called_once()
        args, _ = mock_subp.call_args
        self.assertEqual(args[0], "a_path")
        self.assertEqual(args[1], "another_path")
        args = args[3]
        self.assertEqual(args[-3], '00:00:40.000')
        self.assertEqual(args[-1], '00:01:05.000')


@patch("ofrom_outils.audio.audio.subp")
@patch("ofrom_outils.audio.audio.setup_conv")
class TestToMp3(unittest.TestCase):

    def test_to_mp3(self, mock_setup, mock_subp):
        mock_setup.return_value = ("npath", 1, 44100, {})
        to_mp3("my_file.ogg")
        mock_subp.assert_called_once()
        args, _ = mock_subp.call_args
        self.assertEqual(args[:3], ('my_file.ogg', 'npath', '.mp3'))
        args = args[3]
        self.assertEqual(args[-4], 'my_file.ogg')


@patch("ofrom_outils.audio.audio.subp")
@patch("ofrom_outils.audio.audio.setup_conv")
class TestToWav(unittest.TestCase):

    def test_to_wav(self, mock_setup, mock_subp):
        mock_setup.return_value = ("npath", 1, 44100, {})
        to_wav("my_file.ogg")
        mock_subp.assert_called_once()
        args, _ = mock_subp.call_args
        self.assertEqual(args[:3], ('my_file.ogg', 'npath', '.wav'))
        args = args[3][-8:-2]
        self.assertEqual(args, ['my_file.ogg',
                                "-vn", "-ac", 1,
                                "-ar", 44100])


@patch("ofrom_outils.audio.audio.subp")
@patch("ofrom_outils.audio.audio.setup_conv")
class TestToM4a(unittest.TestCase):

    def test_to_m4a(self, mock_setup, mock_subp):
        mock_setup.return_value = ("npath", 1, 44100, {})
        to_m4a("my_file.ogg")
        mock_subp.assert_called_once()
        args, _ = mock_subp.call_args
        self.assertEqual(args[:3], ('my_file.ogg', 'npath', '.m4a'))
        args = args[3][-6:]
        self.assertEqual(args, ['my_file.ogg', '-vn', '-ac', 1, '-ar', 44100])

@patch("ofrom_outils.audio.audio.D_F")
@patch("ofrom_outils.audio.audio.check")
@patch("ofrom_outils.audio.audio.iter_all")
class TestAllAudioConvert(unittest.TestCase):

    def test_all_audio_convert(self, mock_iter, mock_check, mdf):
        mock_iter.return_value = iter([
            ("fi1", ".wav", "fi1.wav", "path_fi1.wav"),
            ("fi2", ".wav", "fi2.wav", "path_fi2.wav"),
            ("fi3", ".wav", "fi3.wav", "path_fi3.wav")
        ])
        mock_check.side_effect = lambda fi, ext, file, path: (True, fi, ext,
                                                              file, path)
        mock_wav = MagicMock()
        mdf.get.side_effect = lambda key: {
            "wav": (mock_wav, ".wav"),
            "mp3": (MagicMock(), ".mp3"),
            "m4a": (MagicMock(), ".m4a")
        }.get(key)
        all_audio_convert("a_path", "", verbose=False)
        assert mock_wav.call_count == 3
        args, _ = mock_wav.call_args
        self.assertEqual(args, ('path_fi3.wav', 'fi3.wav', False, False))

class TestArgs(unittest.TestCase):

    def test_args(self):
        func, d_args = args(["buff", "convert", "a_path", "another_path", "m4a"])
        self.assertEqual(func, all_audio_convert)
        self.assertEqual(d_args, {
            'path': "a_path", 'npath': "another_path",
            'typ': 'm4a',
            'rem': False, 'ch_all': False
        })

if __name__ == "__main__":
    unittest.main()
