from ofrom_outils.meta.meta import (
    Meta
)
from ofrom_outils.meta.meta_models import (
    MetaDict, Tr, Spk
)
import unittest
from unittest.mock import patch, Mock
import openpyxl as xl
from openpyxl.workbook import Workbook
import os, tempfile

def set_tmp(suffix=".xlsx"):
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp_name = tmp.name
    return tmp_name

    # test classes #
    #--------------#
class TestMeta(unittest.TestCase):
    """'Meta', manipulation de fichiers."""
    #### TODO: refaire tous les tests de méthodes
    
    def setUp(self):
        self.meta = Meta()
        self.wb = xl.Workbook()
        sh = self.wb.active; sh.title = "sup"
        sh.append(['nom_dossier', 'code_locuteur'])
        sh.append(['t26a01', 't26_001'])

    def test_invalid_path(self):
        of = self.meta.f
        self.meta.set_path("hello world")
        self.assertEqual(self.meta.f, of)
    def test_valid_path(self):
        tmp_name = set_tmp()
        try:
            self.meta.set_path(tmp_name)
            self.assertEqual(self.meta.f, tmp_name)
        finally:
            os.remove(tmp_name)
    def test_open(self):
        tmp_name = set_tmp()
        try:
            self.wb.save(tmp_name)
            self.meta.open(tmp_name)
            self.assertEqual(self.wb.sheetnames, self.meta.wb.sheetnames)
        finally:
            os.remove(tmp_name)
    def test_close(self):
        self.meta.close()
        self.assertTrue(self.meta.wb == None)
    def test_clear(self):
        self.meta.wb = "invalid structure"
        self.meta.d = {"filler2": {}}
        self.meta.clear()
        self.assertEqual((self.meta.wb, self.meta.d), (None, MetaDict()))
    def test_save(self):
        self.meta.wb = self.wb
        tmp_name = set_tmp()
        try:
            self.meta.save(tmp_name)
            wb = xl.load_workbook(tmp_name)
            self.assertTrue(self.meta.wb.sheetnames, self.wb.sheetnames)
        finally:
            os.remove(tmp_name)
    
@patch.object(Meta, 'open')
@patch.object(Meta, 'close')
@patch.object(Meta, 'clear')
@patch.object(Meta, 'save')
class TestMetaContinued(unittest.TestCase):
    """'Meta', manipulation de données.."""
    
    def setUp(self):
        self.meta = Meta()
        self.md = MetaDict()
        self.md.tr['t26a01'] = Tr()
        self.md.tr['t26a01'].spk.append("t26_001")
        kspk = ('t26a01', 't26_001')
        self.md.spk[kspk] = Spk()
        self.md.spk[kspk].sh = ('sup', 2)

    @patch("ofrom_outils.meta.meta.load_meta")
    def test_load(self, mload, msave, mclear, mclose, mopen):
        mload.return_value = self.md
        self.meta.load("some/path")
        mload.assert_called_once()
        self.assertEqual(self.meta.d, self.md)
    @patch("ofrom_outils.meta.meta.get_meta")
    def test_get(self, mget, msave, mclear, mclose, mopen):
        mget.return_value = ["t26_001"]
        res = self.meta.get("t26a01")
        mget.assert_called_once()
        self.assertEqual(res, ["t26_001"])
    @patch("ofrom_outils.meta.meta.set_meta")
    def test_set(self, mset, msave, mclear, mclose, mopen):
        mset.return_value = self.md
        self.meta.set("t26a01", "t26_001", "nom", "Petzi")
        mset.assert_called_once()
        self.assertEqual(self.meta.d, self.md)
    # manque ch_set 
    # manque tr_cols
    # manque spk_cols
    # manque iter_tr
    # manque iter_spk
    # manque add_to_trans
    @patch("ofrom_outils.meta.meta.set_pub_meta")
    @patch("ofrom_outils.meta.meta.save_as_csv")
    def test_set_pub(self, mcsv, mpub, msave, mclear, mclose, mopen):
        wb = xl.Workbook()
        wb.active.append(["a1", "b1"])
        wb.active.append(["1", "2"])
        tmp = set_tmp(suffix="")
        try:
            mpub.return_value = (wb, tmp)
            md = self.meta.set_pub("OFROM-test", "", save=True)
            xl.load_workbook(tmp+".xlsx")
            self.assertTrue(isinstance(md, Workbook))
        finally:
            os.remove(tmp)
if __name__ == "__main__":
    unittest.main()