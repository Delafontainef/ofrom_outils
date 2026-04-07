import unittest
from unittest.mock import patch, Mock, MagicMock

from ofrom_outils.stats.stats_models import StFile, StList
from ofrom_outils.stats.stats_reading import (
    wd_simple, wd_xml, wd_full, dur_simple, dur_xml, dur_full,
    fill_stlist, file_stats, all_file_stats, corp_stats
)


@patch("ofrom_outils.stats.stats_reading.iter_segs")
class TestWdSimple(unittest.TestCase):

    def test_wd_simple(self, mock_iter):
        trans = Mock()
        mock_iter.return_value = ["t1", "t2", "t3", "t4"]
        self.assertEqual(wd_simple(trans), 4)


class TestWdXml(unittest.TestCase):

    def test_wd_xml(self):
        trans = MagicMock()
        trans.meta.return_value = 4
        self.assertEqual(wd_xml(trans), 4)


@patch("ofrom_outils.stats.stats_reading.iter_segs")
class TestWdFull(unittest.TestCase):

    def test_wd_full(self, mock_iter):
        trans = Mock()
        l_segs = []
        for cont in ["t1", "#", "t3", "t4"]:
            mseg = MagicMock()
            mseg.content = cont
            l_segs.append(mseg)
        mock_iter.return_value = l_segs
        self.assertEqual(wd_full(trans), 3)


class TestDurSimple(unittest.TestCase):

    def test_dur_simple(self):
        trans = MagicMock()
        trans.end = 10.
        self.assertEqual(dur_simple(trans), 10.)


class TestDurXml(unittest.TestCase):

    def test_dur_xml(self):
        trans = MagicMock()
        trans.meta.side_effect = lambda key, _: {
            "TimeSingleSpeaker": "5.",
            "TimeOverlap": "5.",
            "TimeArticulation": "15."
        }.get(key)
        self.assertEqual(dur_xml(trans), 10.)
        self.assertEqual(dur_xml(trans, "bobby"), 15.)


@patch("ofrom_outils.stats.stats_reading.get_top_tiers")
class TestDurFull(unittest.TestCase):

    def test_dur_full(self, mock_top):
        mock_top.return_value = []
        trans = MagicMock()
        l_segs = []
        for i, cont in enumerate(["t1", "#", "t3", "t4"]):
            mseg = MagicMock()
            mseg.start = float(i)
            mseg.end = float(i + 1)
            mseg.content = cont
            l_segs.append(mseg)
        trans.iterTime.return_value = l_segs
        self.assertEqual(dur_full(trans), 3.)


class TestFillStList(unittest.TestCase):

    def test_fill_stlist(self):
        stf = StFile(4, 10., {'bobby': (5, 15.)})
        stl = StList(0, 0., {"stf": stf}, {})
        fill_stlist(stl, "stf")
        self.assertEqual(stl.wd, 4)
        self.assertEqual(stl.dur, 10.)
        self.assertIn("bobby", stl.spk)
        stf = StFile(12, 4., {'bobby': (5, 5.)})
        stl.fi['stf2'] = stf
        fill_stlist(stl, "stf2")
        self.assertEqual(stl.wd, 16)
        self.assertEqual(stl.dur, 14.)
        self.assertEqual(stl.spk['bobby'], [10, 20.])


class TestFileStats(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.patch_spk = patch("ofrom_outils.stats.stats_reading.get_spk")
        cls.patch_dfrom = patch("ofrom_outils.stats.stats_reading.D_FROM")
        cls.patch_dfun = patch("ofrom_outils.stats.stats_reading.D_FUN")

        cls.spk = cls.patch_spk.start()
        cls.dfrom = cls.patch_dfrom.start()
        cls.dfun = cls.patch_dfun.start()

        cls.spk.return_value = ["bobby"]
        cls.dfrom.return_value = {
            '.textgrid': MagicMock(),
            '.xml': MagicMock()
        }
        cls.dfun.get.side_effect = lambda key, _: {
            's': [MagicMock(return_value=10), MagicMock(return_value=20.)],
            'x': [MagicMock(return_value=8), MagicMock(return_value=15.)],
            'f': [MagicMock(return_value=4), MagicMock(return_value=10.)]
        }.get(key)

    @classmethod
    def tearDownClass(cls):
        cls.patch_spk.stop()
        cls.patch_dfrom.stop()
        cls.patch_dfun.stop()

    def test_praat_full(self):
        stf = file_stats("a_path.TextGrid", "f")
        self.assertEqual(stf.wd, 4)
        self.assertEqual(stf.dur, 10.)
        self.assertEqual(stf.spk, {'bobby': (4, 10.)})

    def test_xml_xml(self):
        stf = file_stats("a_path.xml", "x")
        self.assertEqual(stf.wd, 8)
        self.assertEqual(stf.dur, 15.)
        self.assertEqual(stf.spk, {'bobby': (8, 15.)})

    def test_praat_xml(self):
        stf = file_stats("a_path.textgrid", "x")
        self.assertEqual(stf.wd, 4)
        self.assertEqual(stf.dur, 10.)
        self.assertEqual(stf.spk, {'bobby': (4, 10.)})

    def test_xml_simple(self):
        stf = file_stats("a_path.xml", "s")
        self.assertEqual(stf.wd, 10)
        self.assertEqual(stf.dur, 20.)
        self.assertEqual(stf.spk, {'bobby': (10, 20.)})


@patch("ofrom_outils.stats.stats_reading.os.path.isfile")
@patch("ofrom_outils.stats.stats_reading.file_stats")
@patch("ofrom_outils.stats.stats_reading.fix_lext")
class TestAllFileStats(unittest.TestCase):

    def test_one_file(self, mock_lext, mock_stats, mock_isfile):
        mock_lext.return_value = ""
        mock_isfile.return_value = True
        mock_stats.return_value = StFile(4, 10., {})
        stl = all_file_stats("a_file.TextGrid")
        self.assertEqual(stl.wd, 4)
        self.assertEqual(stl.dur, stl.fi['a_file'].dur)

    @patch("ofrom_outils.stats.stats_reading.iter_file")
    def test_folder(self, mock_iter, mock_lext, mock_stats, mock_isfile):
        mock_lext.return_value = ""
        mock_isfile.return_value = False
        mock_stats.return_value = StFile(4, 10., {'bobby': (2, 2.)})
        mock_iter.return_value = [
            ("fi1", ".xml", "fi1.xml", "a_path"),
            ("fi2", ".xml", "fi2.xml", "a_path")
        ]
        stl = all_file_stats("a_dir")
        self.assertEqual(stl.wd, 8)
        self.assertEqual(stl.dur, stl.fi['fi1'].dur + stl.fi['fi2'].dur)
        self.assertEqual(stl.spk['bobby'], [4, 4.])


@patch("ofrom_outils.stats.stats_reading.all_file_stats")
@patch("ofrom_outils.stats.stats_reading.sub_corpus")
@patch("ofrom_outils.stats.stats_reading.fix_lext")
class TestCorpStats(unittest.TestCase):

    def test_corp_stats(self, mock_lext, mock_sub, mock_stats):
        mock_lext.return_value = ""
        mock_sub.return_value = "subcorp"
        mock_stats.side_effect = [
            StList(0, 0., {}, {}),
            StList(4, 10., {}, {'bobby': [4, 10.]}),
            StList(8, 20., {}, {'bobby': [8, 20.]})
        ]
        stl = corp_stats(["corp1", "corp2", "corp3"])
        assert mock_sub.call_count == 3
        assert mock_stats.call_count == 3
        self.assertEqual(stl.wd, 8)
        self.assertEqual(stl.dur, 20)
        self.assertEqual(stl.spk['bobby'], [8, 20.])

if __name__ == "__main__":
    unittest.main()
