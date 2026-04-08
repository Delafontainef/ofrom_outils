import unittest
from unittest.mock import patch, MagicMock

from ofrom_outils.stats.stats import (
    open_excel, write_table, Stats, get_corpus_stats
)
from ofrom_outils.stats.stats_models import StFile, StList


def set_tmp(suffix=".xlsx"):
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp_name = tmp.name
    return tmp_name


@patch("ofrom_outils.stats.stats.xl")
@patch("ofrom_outils.stats.stats.os.path.isfile")
class TestOpenExcel(unittest.TestCase):

    def test_empty(self, mock_isfile, mock_xl):
        mock_isfile.return_value = False
        mock_xl.Workbook.return_value = MagicMock()
        wb, sh = open_excel("nope.xlsx", "mine")
        self.assertEqual(wb.active, sh)
        self.assertEqual(sh.title, "mine")

    def test_exists(self, mock_isfile, mock_xl):
        mock_isfile.return_value = True
        mock_xl.load_workbook.return_value = MagicMock()
        mock_wb = mock_xl.load_workbook.return_value
        mock_wb.sheetnames = ["Sheet1", "mine", "yours"]
        mock_wb.__getitem__.side_effect = lambda key: {
            "mine": MagicMock(return_value="Yup")
        }.get(key)
        wb, sh = open_excel("yup.xlsx", "mine")
        mock_xl.load_workbook.assert_called_with("yup.xlsx")
        self.assertEqual(sh.return_value, "Yup")


class TestWriteTable(unittest.TestCase):

    def test_empty(self):
        mock_sh = MagicMock()
        d_st = {
            "typ1": StList(100, 25., {}, {'bobby': [100, 25.]}),
            "typ2": StList(80, 15., {}, {'fred': [40, 15.], 'jane': [60, 15.]})
        }
        gloc, genr, gwd, gdur = write_table(mock_sh, d_st, [])
        self.assertEqual(gloc, 3)
        self.assertEqual(genr, 0)
        self.assertEqual(gwd, 180)
        self.assertEqual(gdur, 40.)


class TestStats(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.patch_md = patch("ofrom_outils.stats.stats.Stats._set_md")
        cls.md = cls.patch_md.start()

    @classmethod
    def tearDownClass(cls):
        cls.patch_md.stop()

    def setUp(self):
        self.st = Stats()
        self.st.f = "meta.xlsx"
        self.st.l_ext = ['.textgrid']
        self.st.md = MagicMock()
        self.md.reset_mock()

    def test_set_meta_stats(self):
        st = StList(30, 30., {
            'fi1': StFile(10, 10., {'bobby': (10, 10.)}),
            'fi2': StFile(10, 10., {'fred': (10, 10.)}),
            'fi3': StFile(10, 10., {'jane': (10, 10.)}),
        })
        self.st.md.get.side_effect = lambda _tr, _spk, key: {
            "date_enregistrement": "1999-01-01",
            "date_naissance": "2010"
        }.get(key)
        self.st.set_meta_stats(st, save=False)
        assert self.st.md.get.call_count == 6
        assert self.st.md.ch_set.call_count == 9
        self.st.md.save.assert_called_once()

    def test_ch_typ(self):
        self.st.md.ch_key.return_value = True
        self.assertEqual(self.st.ch_typ("tr_typ"), self.st.sort_tr)
        self.st.md.ch_key.assert_called_once_with("tr_typ")
        self.st.md.reset_mock()
        self.st.md.ch_key.return_value = False
        self.assertEqual(self.st.ch_typ("spk_typ"), self.st.sort_spk)
        self.st.md.ch_key.assert_called_once_with("spk_typ")

    @patch("ofrom_outils.stats.stats.fill_stlist")
    def test_sort_tr(self, _mock_fillstlist):
        st = StList(0, 0., {
            'fi1': StFile(10, 10., {'bobby': (10, 10.)}),
            'fi2': StFile(10, 10., {'fred': (10, 10.)}),
            'fi3': StFile(10, 10., {'jane': (10, 10.)}),
        })
        self.st.md.get.return_value = "k"
        res = self.st.sort_tr(st, "typ_k")
        self.assertEqual(res['k'], st)
        assert self.st.md.get.call_count == 3

    def test_sort_spk(self):
        st = StList(0, 0.,
                    {
                        'fi1': StFile(10, 10., {'bobby': (10, 10.)}),
                        'fi2': StFile(10, 10., {'fred': (10, 10.)}),
                        'fi3': StFile(10, 10., {'jane': (10, 10.)}),
                    },
                    {
                        'bobby': [10, 10.],
                        'fred': [10, 10.],
                        'jane': [10, 10.],
                    })
        self.st.md.get.return_value = "k"
        res = self.st.sort_spk(st, "typ_k")
        self.assertEqual(res['k'].wd, 30)
        assert self.st.md.get.call_count == 3

    @patch("ofrom_outils.stats.stats.all_file_stats")
    def test_load_dir(self, mock_stats):
        mock_stats.return_value = StList(10, 40., {}, {})
        st = self.st.load_dir("a_path")
        mock_stats.assert_called_once_with("a_path", self.st.mode,
                                           self.st.l_ext)
        self.assertEqual(st.dur, 40.)

    @patch("ofrom_outils.stats.stats.corp_stats")
    def test_load_corp(self, mock_stats):
        mock_stats.return_value = StList(10, 40., {}, {})
        st = self.st.load_corp()
        mock_stats.assert_called_once_with(None, self.st.mode,
                                           self.st.l_ext)
        self.assertEqual(st.dur, 40.)

    def test_load_meta(self):
        self.st.load_meta("new_meta_path.xlsx")
        self.md.assert_called_once_with("new_meta_path.xlsx")

    @patch("ofrom_outils.stats.stats.Stats.sort_tr")
    @patch("ofrom_outils.stats.stats.Stats.ch_typ")
    def test_sort(self, mock_typ, mock_tr):
        mock_typ.return_value = mock_tr
        mock_tr.return_value = {"tr_typ": StList(4, 40.)}
        res = self.st.sort(StList(), "tr_typ")
        self.assertEqual(res["tr_typ"], StList(4, 40.))
        mock_typ.assert_called_once_with("tr_typ")
        mock_tr.assert_called_once_with(StList(), "tr_typ")

    @patch("ofrom_outils.stats.stats.write_table")
    @patch("ofrom_outils.stats.stats.open_excel")
    def test_to_excel(self, mock_open, mock_write):
        mock_open.return_value = MagicMock(), MagicMock()
        mock_wb, _ = mock_open.return_value
        self.st.to_excel("a_path.xlsx", {})
        mock_open.assert_called_once_with("a_path.xlsx", "general")
        mock_write.assert_called_once()
        mock_wb.save.assert_called_once_with("a_path.xlsx")

    @patch("ofrom_outils.stats.stats.Stats.ch_typ")
    @patch("ofrom_outils.stats.stats.Stats.sort")
    @patch("ofrom_outils.stats.stats.write_table")
    @patch("ofrom_outils.stats.stats.open_excel")
    def test_to_excel_typ(self, mock_open, mock_write, mock_sort, mock_ch):
        mock_open.return_value = MagicMock(), MagicMock()
        mock_wb, _ = mock_open.return_value
        mock_sort.return_value = {'k1': StList(), 'k2': StList()}
        self.st.to_excel_typ("a_path.xlsx", StList(), "typ")
        mock_open.assert_called_once_with("a_path.xlsx", "typ")
        assert mock_write.call_count == 3
        assert mock_sort.call_count == 4
        assert mock_ch.call_count == 1
        mock_wb.save.assert_called_once_with("a_path.xlsx")

@patch("ofrom_outils.stats.stats.Stats")
class TestGetCorpusStats(unittest.TestCase):

    def test_get_corpus_stats(self, mstats):
        mock = mstats.return_value
        mock.sort.return_value = {}
        get_corpus_stats(l_typs=["typ1", "typ2"])
        mock.load_corp.assert_called_once()
        mock.sort.assert_called_once()
        mock.to_excel.assert_called_once()
        assert mock.to_excel_typ.call_count == 2

if __name__ == "__main__":
    unittest.main()