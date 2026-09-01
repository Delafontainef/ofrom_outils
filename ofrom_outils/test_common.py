import os
import time
import unittest
from unittest.mock import patch, Mock, MagicMock
from dataclasses import dataclass

from ofrom_outils.common import (
    kwarg, fix_lext, update_dc,
    iter_file, iter_all, get_files, iter_core, get_core,
    ensure_outdir, iter_top_tiers, iter_segs, get_top_tiers, get_spk,
    set_parent, call_praat, anon_ofrom_plus, ph_ofrom,
    mp_wait, multiprocess, multithread
)


def fake_mp_proc(l_proc, _func, _l_files, _args):
    proc = Mock()
    proc.join = Mock()
    l_proc.append(proc)
    return l_proc


class TestKwarg(unittest.TestCase):

    def test_args(self):
        args, _ = kwarg(["True", "one", "'two and a half'"])
        self.assertEqual(args, ["one", "two and a half"])

    def test_kwargs(self):
        _, kwargs = kwarg([
            "True", "one", "two=2", "three=3.14", "four=False"
        ])
        self.assertEqual(kwargs, {"two": 2, "three": 3.14, "four": False})


class TestFixLext(unittest.TestCase):

    def test_string(self):
        l_ext = fix_lext(".xml")
        self.assertEqual(l_ext, [".xml"])

    def test_fix(self):
        l_ext = fix_lext(["xml", ".TEI"])
        self.assertEqual(l_ext, [".xml", ".tei"])

    def test_default(self):
        l_ext = fix_lext()
        self.assertEqual(l_ext, [".textgrid"])


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


@patch("ofrom_outils.common.fix_lext")
@patch("ofrom_outils.common.os.listdir")
class TestIterFile(unittest.TestCase):

    def test_files(self, mock_os, mock_lext):
        mock_os.return_value = [
            "file1.TextGrid",
            "file2.TextGrid",
            "file3.xml"
        ]
        mock_lext.return_value = [".textgrid"]
        l_res = [tpl for tpl in iter_file("dir")]
        self.assertEqual(l_res, [
            ("file1", ".TextGrid", "file1.TextGrid",
             os.path.join("dir", "file1.TextGrid")),
            ("file2", ".TextGrid", "file2.TextGrid",
             os.path.join("dir", "file2.TextGrid"))
        ])
        assert mock_os.call_count == 1


@patch("ofrom_outils.common.fix_lext")
@patch("ofrom_outils.common.os.walk")
class TestIterAll(unittest.TestCase):

    def test_all(self, mock_os, mock_lext):
        mock_os.return_value = [
            (
                "dir", ["subdir1, subdir2"],
                ["file1.TextGrid", "file2.TextGrid", "file5.xml"]
            ),
            (
                os.path.join("dir", "subdir1"), [],
                ["file3.TextGrid"]
            ),
            (
                os.path.join("dir", "subdir2"), [],
                ["file4.TextGrid"]
            )
        ]
        mock_lext.return_value = [".textgrid"]
        l_res = [tpl for tpl in iter_all("dir")]
        self.assertEqual(l_res, [
            ("file1", ".TextGrid", "file1.TextGrid",
             os.path.join("dir", "file1.TextGrid")),
            ("file2", ".TextGrid", "file2.TextGrid",
             os.path.join("dir", "file2.TextGrid")),
            ("file3", ".TextGrid", "file3.TextGrid",
             os.path.join("dir", "subdir1", "file3.TextGrid")),
            ("file4", ".TextGrid", "file4.TextGrid",
             os.path.join("dir", "subdir2", "file4.TextGrid"))
        ])
        assert mock_os.call_count == 1


class TestGetFiles(unittest.TestCase):

    @patch("ofrom_outils.common.iter_file")
    def test_file(self, mock_iter):
        mock_iter.return_value = [
            ("file2", ".TextGrid", "file2.TextGrid",
             "dir\\file2.TextGrid"),
            ("file1", ".TextGrid", "file1.TextGrid",
             "dir\\file1.TextGrid")
        ]
        l_res = get_files("")
        self.assertEqual(l_res, [
            "dir\\file1.TextGrid", "dir\\file2.TextGrid"
        ])

    @patch("ofrom_outils.common.iter_all")
    def test_all(self, mock_iter):
        mock_iter.return_value = [
            ("file2", ".TextGrid", "file2.TextGrid",
             "dir\\file2.TextGrid"),
            ("file1", ".TextGrid", "file1.TextGrid",
             "dir\\file1.TextGrid")
        ]
        l_res = get_files("", ch_all=True)
        self.assertEqual(l_res, [
            "dir\\file1.TextGrid", "dir\\file2.TextGrid"
        ])

    @patch("ofrom_outils.common.iter_file")
    def test_verbose(self, mock_iter):
        mock_iter.return_value = [
            ("file1", ".TextGrid", "file1.TextGrid",
             "dir\\file1.TextGrid"),
            ("file2", ".TextGrid", "file2.TextGrid",
             "dir\\file2.TextGrid")
        ]
        l_res = get_files("", verbose=True)
        self.assertEqual(l_res, mock_iter.return_value)


@patch("ofrom_outils.common.iter_file")
@patch("ofrom_outils.common.sub_corpus")
@patch("ofrom_outils.common.fix_lext")
@patch("ofrom_outils.common.os.path.isdir")
@patch("ofrom_outils.common.CORP", ["corp1", "corp2"])
class TestIterCore(unittest.TestCase):

    def test_core(self, mock_isdir, mock_lext, mock_sub, mock_iter):
        mock_isdir.return_value = True
        mock_lext.return_value = []
        mock_sub.return_value = ["subcorp"]
        mock_iter.return_value = [
            ("file", ".xml", "file.xml", "subcorp\\file.xml")
        ]
        l_res = [tpl for tpl in iter_core()]
        self.assertEqual(l_res, [
            ("corp1", "file", ".xml", "file.xml", "subcorp\\file.xml"),
            ("corp2", "file", ".xml", "file.xml", "subcorp\\file.xml")
        ])
        assert mock_sub.call_count == 2
        assert mock_iter.call_count == 2


@patch("ofrom_outils.common.iter_core")
class TestGetCore(unittest.TestCase):

    def test_core(self, mock_core):
        mock_core.return_value = [
            ("corp2", "file3", ".xml", "file3.xml", "corp2\\file3.xml"),
            ("corp2", "file2", ".xml", "file2.xml", "corp2\\file2.xml"),
            ("corp1", "file1", ".xml", "file1.xml", "corp1\\file1.xml")
        ]
        l_res = get_core()
        self.assertEqual(l_res, [
            "corp2\\file2.xml", "corp2\\file3.xml", "corp1\\file1.xml"
        ])

    def test_verbose(self, mock_core):
        mock_core.return_value = [
            ("corp1", "file", ".xml", "file.xml", "subcorp\\file.xml"),
            ("corp2", "file", ".xml", "file.xml", "subcorp\\file.xml")
        ]
        l_res = get_core(verbose=True)
        self.assertEqual(l_res, mock_core.return_value)


@patch("ofrom_outils.common.os.mkdir")
@patch("ofrom_outils.common.os.path.isdir")
class TestEnsureOutdir(unittest.TestCase):

    def test_file_path(self, mock_isdir, mock_mkdir):
        mock_isdir.return_value = False
        ensure_outdir(os.path.join("dir", "subdir", "ssubdir", "file.xml"))
        assert mock_mkdir.call_count == 3

    def test_dir_path(self, mock_isdir, mock_mkdir):
        mock_isdir.return_value = False
        ensure_outdir(os.path.join("dir", "subdir", "ssubdir", "onemore"))
        assert mock_mkdir.call_count == 4


class TestIterTopTiers(unittest.TestCase):

    def setUp(self):
        patcher = patch("ofrom_outils.common.Transcription")
        self.addCleanup(patcher.stop)
        self.mock_trans = patcher.start()
        self.trans = self.mock_trans.return_value
        self.trans.elem = []
        for tname in ["tier1", "tier1[anno]", "tier2", "tier2[anno]", "tier3"]:
            tier = MagicMock()
            tier.name = tname
            self.trans.elem.append(tier)
        self.trans.__iter__.return_value = iter(self.trans.elem)

    def test_tiers(self):
        l_tiers = [tier.name for tier in iter_top_tiers(self.trans)]
        self.assertEqual(l_tiers, ["tier1", "tier2", "tier3"])

    def test_spk(self):
        l_tiers = [tier.name for tier in iter_top_tiers(self.trans,
                                                        ["tier1", "tier3"])]
        self.assertEqual(l_tiers, ["tier1", "tier3"])


class TestIterSegs(unittest.TestCase):

    def setUp(self):
        patch_trans = patch("ofrom_outils.common.Transcription")
        self.addCleanup(patch_trans.stop)
        self.mock_trans = patch_trans.start()
        patch_tier = patch("ofrom_outils.common.Tier")
        self.addCleanup(patch_tier.stop)
        self.mock_tier = patch_tier.start()
        self.trans = self.mock_trans.return_value
        self.trans.elem = []
        for tname, l_segs in [
            ["tier1", ["a1", "a2"]],
            ["tier1[anno]", ["a3"]],
            ["tier2", ["a4", "a5"]],
            ["tier2[anno]", ["a6"]],
            ["tier3", ["a7", "a8"]]
        ]:
            tier = MagicMock()
            tier.name = tname
            tier.elem = []
            for sname in l_segs:
                seg = MagicMock()
                seg.name = sname
                tier.elem.append(seg)
            tier.__iter__.return_value = iter(tier.elem)
            self.trans.elem.append(tier)
        self.trans.__iter__.return_value = iter(self.trans.elem)

    def test_iter(self):
        l_res = [seg.name for seg in iter_segs(self.trans, "")]
        self.assertEqual(l_res,
                         ["a1", "a2", "a4", "a5", "a7", "a8"])

    def test_iter_spk(self):
        l_res = [seg.name for seg in iter_segs(self.trans, "", "tier2")]
        self.assertEqual(l_res, ["a4", "a5"])

    def test_iter_tag(self):
        l_res = [seg.name for seg in iter_segs(self.trans, "[anno]")]
        self.assertEqual(l_res, ["a3", "a6"])


@patch("ofrom_outils.common.iter_top_tiers")
@patch("ofrom_outils.common.Transcription")
class TestGetTopTiers(unittest.TestCase):

    def test_list(self, mock_trans, mock_iter):
        trans = mock_trans.return_value
        mock_iter.return_value = ["just", "a", "wrapper", "around",
                                  "this", "function"]
        self.assertEqual(get_top_tiers(trans), mock_iter.return_value)
        assert mock_iter.call_count == 1


@patch("ofrom_outils.common.iter_top_tiers")
@patch("ofrom_outils.common.Transcription")
class TestGetSpk(unittest.TestCase):

    def test_spk(self, mock_trans, mock_iter):
        trans = mock_trans.return_value
        l_tiers = []
        for tname in ["tier1", "tier2", "tier3"]:
            tier = MagicMock()
            tier.name = tname
            l_tiers.append(tier)
        mock_iter.return_value = l_tiers
        self.assertEqual(get_spk(trans), ["tier1", "tier2", "tier3"])
        assert mock_iter.call_count == 1


class TestSetParent(unittest.TestCase):

    def setUp(self):
        patcher = patch("ofrom_outils.common.Transcription")
        self.addCleanup(patcher.stop)
        self.mock_trans = patcher.start()
        self.trans = self.mock_trans.return_value
        self.trans.elem = []
        self.trans.getName.return_value = "parenting"
        for tname in ["tier1", "tier1[anno]", "tier2", "tier2[anno]", "tier3"]:
            tier = MagicMock()
            tier.name = tname
            tier.timeParent.return_value = None
            self.trans.elem.append(tier)
        self.trans.__iter__.return_value = iter(self.trans.elem)

    def test_parenting(self):
        set_parent(self.trans)
        for tier in self.trans:
            if "[" not in tier.name:
                assert tier.timeParent.call_count == 0
            else:
                assert tier.timeParent.call_count == 1


@patch("ofrom_outils.common.subprocess")
@patch("ofrom_outils.common.os.path.isfile")
@patch("ofrom_outils.common.PRAAT", "praatpath")
class TestCallPraat(unittest.TestCase):

    def test_call(self, mock_isfile, mock_sproc):
        mock_isfile.return_value = True
        mock_sproc.run.return_value = None
        call_praat("script", [])
        mock_sproc.run.assert_called_with([
            os.path.join("praatpath", "Praat.exe"),
            '--run', "script.praat"
        ])


@patch("ofrom_outils.common.call_praat")
class TestAnonOfromPlus(unittest.TestCase):

    def test_anon(self, mock_call):
        anon_ofrom_plus(["tgd", "audio", "anon"])
        mock_call.assert_called_with('anon_ofrom_plus', [
            "audio", "tgd", "anon", "WAV",
            "#", "yes", "0.01", "60", "700", "0.9"
        ])


@patch("ofrom_outils.common.call_praat")
class TestPhOfrom(unittest.TestCase):

    def test_phonemic(self, mock_call):
        ph_ofrom(["tgd", "audio", "ph"], "sym_t", "sym_i")
        mock_call.assert_called_with('ph_ofrom', [
            "audio", "tgd", "ph", "sym_t", "sym_i", "0"
        ])


class TestMpWait(unittest.TestCase):

    def test_mp_wait(self):
        l_res = [tpl for tpl in mp_wait([None, None], 0.1, 0.3)]
        self.assertEqual(l_res, [(0, 2), (0, 2), (0, 2), (0, 2)])

    @patch("ofrom_outils.common.time", spec=time)
    def test_mp_wait_mutate(self, mock_time):
        l_res: list = [None, None]
        mock_time.time.return_value = 0.
        mock_time.sleep.return_value = None
        for a, tpl in enumerate(mp_wait(l_res, 0.1, -1.)):
            if a < len(l_res):  # imite le retour de fonctions asynchrones
                l_res[a] = "hello"
        self.assertEqual(l_res, ["hello", "hello"])
        assert mock_time.sleep.call_count == 2


@patch("ofrom_outils.common.os.cpu_count")
@patch("ofrom_outils.common.mp.Manager")
@patch("ofrom_outils.common._mp_proc")
@patch("ofrom_outils.common._mp_size")
class TestMultiprocess(unittest.TestCase):

    def test_mp(self, mock_mpsize, mock_proc, mock_manager, mock_cpu):
        mock_mpsize.return_value = 100
        mock_cpu.return_value = 1
        dummy_list = []
        mock_manager.return_value.list.return_value = dummy_list
        mock_proc.side_effect = fake_mp_proc
        files = [f"file{i}.txt" for i in range(5)]
        mock_func = Mock()

        result = multiprocess(mock_func, files, n=2, wait=True)
        self.assertIsNone(result)
        assert mock_proc.call_count >= 1
        self.assertEqual(len(dummy_list), len(files))
        self.assertTrue(all(x is None for x in dummy_list))


@patch("ofrom_outils.common.os.cpu_count")
@patch("ofrom_outils.common._mp_thr")
@patch("ofrom_outils.common._mp_size")
class TestMultithread(unittest.TestCase):

    def test_thread(self, mock_mpsize, mock_thr, mock_cpu):
        mock_mpsize.return_value = 100
        mock_cpu.return_value = 1
        mock_thr.side_effect = fake_mp_proc
        files = [f"file{i}.txt" for i in range(5)]
        mock_func = Mock()
        result = multithread(mock_func, files, n=2, wait=True)
        self.assertIsNone(result)
        assert mock_thr.call_count >= 1


if __name__ == "__main__":
    unittest.main()
