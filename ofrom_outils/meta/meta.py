"""17.02.2026

Gère les métadonnées du corpus.
- Récupère les métadonnées avec 'Meta.load()'
- Édite les métadonnées avec 'Meta.edit()'
- Génère les métadonnées publiques avec 'Meta.set_pub()'
L'ancienne fonction 'load_meta()' est toujours présente.

"""

from ofrom_outils.common import META, DFLT, setParent
from ofrom_outils.common_types import Self, Iterator, Path, Transcription
from ofrom_outils.meta.meta_models import AbsMeta, MetaDict
from ofrom_outils.meta.meta_functions import (
    set_pub_meta, save_as_csv,
    iter_shn, load_meta, get_meta, set_meta
)
import openpyxl as xl
import os

from openpyxl.workbook.workbook import Workbook # typing

class Meta(AbsMeta):
    """Classe gérant les métadonnées du corpus OFROM+."""
    
    def __init__(self, f: Path = ""):
        self.f: Path = ""
        self.wb: Workbook = None
        self.d: MetaDict = MetaDict()
        self.set_path(f) # initialise f/d
    
    def set_path(self, f: Path) -> None:
        """Sélectionne 'f' ou un chemin par défaut pour les métadonnées."""
        f = META if not f else f # chemin par défaut
        _, ext = os.path.splitext(f)
        of = self.f
        self.f = f if (os.path.isfile(f) and
                       ext == ".xlsx") else self.f
        if of != self.f: # réinitialise wb/d
            self.wb, self.d = None, MetaDict()
    def open(self, f: Path = "") -> Workbook:
        """Ouvre le WorkBook."""
        self.set_path(f)
        self.wb = xl.load_workbook(self.f)
        return self.wb
    def close(self) -> None:
        """Ferme (et oublie) le WorkBook."""
        try:
            self.wb.close()
        except AttributeError:  # we want to erase anyway
            pass
        self.wb = None
    def clear(self) -> None:
        """Ferme le WorkBook et vide le dictionnaire."""
        self.close(); self.d = MetaDict()
    def save(self, f: Path = "", close: bool = False) -> None:
        """Sauvegarde le WorkBook."""
        f = self.f if not f else f
        self.wb.save(f)
        if close:
            self.close()
    
    def load(self, f: Path = "", keep_open: bool = False) -> Self:
        """
        Charge les métadonnées dans l'instance.
        Note: valeurs validées (voir 'meta_validation.py')
        """
        self.open(f)
        self.d = load_meta(self.wb)
        if not keep_open:
            self.close()
        return self
    def ch_key(self, k: str = "") -> str:
        """
        Vérifie si 'k' est une métadonnée de transcription / locuteur.
        Renvoie : 
        - "" :      locuteur
        - "trans":  transcription
        """
        for trcode, tr in self.d.tr.items():            # single loop
            if k in tr.d:                               # transcription
                return "trans"
            spkcode = tr.spk[0]
            if k in self.d.spk[(trcode, spkcode)].d:    # speaker
                return ""
            raise KeyError(f"{k} not in MetaDict.")     # not found
    def get(
            self, trcode: str, spkcode: str = 'trans', k: str = ""
        ) -> str | list[str] | dict[str, str]:
        """
        Récupère une métadonnée.
        trcode          le nom de la transcription
        spkcode         le code locuteur
        k               le nom de la métadonnée
        Note: valeur validée (voir 'meta_validation.py')
        """
        spkcode = self.ch_key(k) if (k and not spkcode) else spkcode
        return get_meta(self.d, trcode, spkcode, k)
    def set(
            self, trcode: str, spkcode: str, k: str, v: any,
            save: bool = False, close: bool = False, f: Path = ""
        ) -> None:
        """
        Modifie le WorkBook à l'aide de 'self.d'.
        trcode          le nom de la transcription
        spkcode         le code locuteur
        k/v             le nom de la métadonnée / le nouveau contenu
        Note: valeur validée (voir 'meta_validation.py')
        """
        if not self.wb:
            self.open(f)
        spkcode = self.ch_key(k) if (k and not spkcode) else spkcode
        self.d = set_meta(self.wb, self.d, trcode, spkcode, k, v)
        if save:
            self.save(f)
        if close: 
            self.close()
    def ch_set(
            self, trcode: str, spkcode: str, k: str, v: any, 
            save: bool = False, close: bool = False, f: Path = "", 
            dflt: str = ""
        ) -> bool:
        """
        Modifie le WorkBook à l'aide de 'self.d'.
        Ne modifie rien si une valeur est déjà en place.
        trcode          le nom de la transcription
        spkcode         le code locuteur
        k/v             le nom de la métadonnée / le nouveau contenu
        Note: valeur validée (voir 'meta_validation.py')
        """
        dflt = DFLT if not dflt else dflt
        if not self.wb:
            self.open(f)
        val = self.get(trcode, spkcode, k)  # should be 'str'
        ch = False
        if (not val) or (val != dflt):
            self.d = set_meta(self.wb, self.d, trcode, spkcode, k, v)
            if save:
                self.save(f)
            ch = True
        if close:
            self.close()
        return ch
    
    def tr_cols() -> list[str]:
        """Renvoie les noms de métadonnées des transcriptions."""
        return self.d.tr_cols.copy()
    def spk_cols() -> list[str]:
        """Renvoie les noms de métadonnées des locuteurs."""
        return self.d.spk_cols.copy()
    def iter_tr() -> Iterator[tuple[str, dict]]:
        """Itère sur les transcriptions."""
        for trcode, mtr in self.d.tr.items():
            yield trocde, mtr.copy()
    def iter_spk(trcode: str|list[str]: "") -> Iterator[tuple[str, str, dict]]:
        """Itère sur les locuteurs."""
        if not trcode:
            for tpl, mspk in self.d.spk.items():
                yield tpl[0], tpl[1], mspk.copy()
            return
        trcode = [trcode] if isinstance(trcode, str) else trcode
        for trc in trcode:
            if trc not in self.d.tr:
                continue
            for spk in self.d.tr[trc].spk:
                yield trc, spk, self.d.spk[(trc, spk)].d.copy()
    
    def add_to_trans(tr: Transcription) -> Transcription:
        """
        Ajoute les métadonnées à la Transcription.
        On est forcés de créer les locuteurs ici donc parentage également.
        """
        stf = self.d.tr.get(tr.name, None)
        if not stf:                             # rien à ajouter
            return tr
        for k, v in stf.d.items():              # métadonnées de transcription
            tr.setMeta(k, v, 'omni')
        setParent(tr)                           # parentage
        for ptier in tr.getTop():
            ptier.setMeta("speaker", ptier.name)
            for ctier in ptier.children():
                ctier.setMeta("speaker", ptier.name)
            d = self.d.spk.get((tr.name, tier.name), {})
            tr.addSpk(tier.name, {k: v for k, v in d.items()}) # meta locuteurs
        return tr
    
    def set_pub(self, corp: str, core: str = "",
                save: bool = False, close: bool = False
        ) -> Workbook:
        """
        Génère et sauvegarde directement un metadata public
        pour un corpus donné.
        corp :      le nom du sous-corpus
        core :      l'emplacement du corpus
        """
        if not self.wb:
            self.open()
        mwb, c_path = set_pub_meta(self.wb, corp, core)
        if save:
            mwb.save(os.path.join(c_path+".xlsx"))
            save_as_csv(mwb.active, os.path.join(c_path+".csv"))
        if close:
            self.close()
        return mwb



