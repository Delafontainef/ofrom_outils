"""26.02.2026
Fonctions de 'lecture' pour récupérer les statistiques depuis les fichiers.
"""

import os
import re

from corflow import fromPraat

from ofrom_outils.common import (
    CORP, SYMS, iter_segs, get_top_tiers,
    iter_file, get_spk, fix_lext
)
from ofrom_outils.common_types import Path, Transcription
from ofrom_outils.formats.from_ofrom import from_ofrom
from ofrom_outils.logs.log import log

try:
    from ofrom_outils.pr.private_paths import sub_corpus
except ImportError:
    sub_corpus = None
from ofrom_outils.stats.stats_models import StFile, StList


# Modes #
# ------#
def wd_simple(tr: Transcription, spk: str = "") -> int:
    """Compte tous les tokens sans exception."""
    wd = 0
    for _seg in iter_segs(tr, spk=spk):
        wd += 1
    return wd


def wd_xml(tr: Transcription, _spk: str = "") -> int:
    """Récupère le nombre de mots calculé par le XML."""
    return int(tr.meta("word_count", "stats"))


def wd_full(tr: Transcription, spk: str = "") -> int:
    """Compte les tokens qui ne sont pas des pauses ou réservés."""
    wd = 0
    for seg in iter_segs(tr, spk=spk):
        if re.search(SYMS, seg.content):
            continue
        wd += 1
    return wd


def dur_simple(tr: Transcription, _spk: str = "") -> float:
    """Récupère la durée totale du fichier."""
    return tr.end


def dur_xml(tr: Transcription, spk: str = "") -> float:
    """Retourne la durée calculée par le XML."""
    if not spk:
        dur1 = float(tr.meta("TimeSingleSpeaker", "stats"))
        dur2 = float(tr.meta("TimeOverlap", "stats"))
        return dur1 + dur2
    return float(tr.meta("TimeArticulation", f"stats_{spk}"))


def dur_full(tr: Transcription, spk: str = "") -> float:
    """Récupère la durée sans les silences."""
    dur, f = 0.0, 0.0
    l_tiers = get_top_tiers(tr, spk)
    for seg in tr.iterTime(l_tiers):
        if seg.end <= f:
            continue
        if not re.search(SYMS, seg.content):
            s = seg.start if seg.start >= f else f
            dur += seg.end - s
            f = seg.end
    return dur


"""Constantes globales
D_FROM      dict        sélection de l'import par l'extension de fichier.
D_FUN       dict        sélection des stats' par le mode.
"""
D_FROM = {
    '.textgrid': fromPraat.fromPraat,
    '.xml': from_ofrom
}
D_FUN = {
    's': [wd_simple, dur_simple],
    'x': [wd_xml, dur_xml],
    'f': [wd_full, dur_full]
}


# Lecture #
# --------#
def fill_stlist(st: StList, fia: str):
    st.wd += st.fi[fia].wd
    st.dur += st.fi[fia].dur
    for spk, tpl in st.fi[fia].spk.items():
        if spk not in st.spk:
            st.spk[spk] = [el for el in tpl]
            continue
        st.spk[spk][0] = st.spk[spk][0] + tpl[0]
        st.spk[spk][1] = st.spk[spk][1] + tpl[1]


def file_stats(path: Path, mode: str = "s") -> StFile:
    """
    Récupère les statistiques pour un fichier (TextGrid).
    - path      (str)   le chemin du fichier.
    - mode      (str)   comment récupérer les statistiques.
    """
    # mise en place
    fi, ext = os.path.splitext(path)
    tr, st = D_FROM[ext.lower()](path), StFile()
    mode = "f" if (ext.lower() != ".xml" and mode == "x") else mode
    wdf, durf = D_FUN.get(mode, [wd_full, dur_full])
    # récupération des statistiques
    st.wd, st.dur = wdf(tr), durf(tr)
    st.spk = {spk: (wdf(tr, spk), durf(tr, spk)) for spk in get_spk(tr)}
    return st


def all_file_stats(
        path: Path,
        mode: str = "s",
        l_ext: str | list[str] = None,
        st: StList = None,
        verbose: bool = False
) -> StList:
    """
    Récupère les statistiques pour un dossier de TextGrids.
    - path      (str)   le chemin du dossier.
    - mode      (str)   comment récupérer les statistiques.
    - l_ext     (list)  les extensions à lire.
    - st        (pntr)  un StFile pré-existant.
    - verbose   (bool)  si on affiche la progression.
    """
    l_ext = fix_lext(l_ext)
    st = StList() if not st else st
    if os.path.isfile(path):
        _, file = os.path.split(path)
        fi, _ = os.path.splitext(file)
        st.fi[fi] = file_stats(path, mode)
        fill_stlist(st, fi)
        return st
    for fi, ext, file, spath in iter_file(path, l_ext=l_ext):
        log(f"fill_stats: {fi}", verbose=verbose)
        st.fi[fi] = file_stats(spath, mode)
        fill_stlist(st, fi)
    return st


def corp_stats(
        corp: list[str] = None,
        mode: str = "s",
        l_ext: str | list[str] = None
) -> StList:
    """Récupère les fichiers d'OFROM+."""
    l_ext = fix_lext(l_ext)
    corp = CORP if corp is None else corp
    st = StList()
    for c in corp:
        scorp = sub_corpus(c)
        st = all_file_stats(scorp, mode, l_ext, st)
    return st
