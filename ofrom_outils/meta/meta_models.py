"""18.02.2026
Modèles pour les métadonnées d'OFROM+.
"""

from ofrom_outils.common_types import (Path, Callable)
from typing import Protocol, runtime_checkable
from types import MappingProxyType
from dataclasses import dataclass, field
from openpyxl.cell.cell import Cell
from openpyxl.workbook.workbook import Workbook

type spk_key = Tuple[str, str]

@dataclass
class Spk:
    """
    Métadonnées d'un locuteur.
    - d     (dict) les champs de métadonnées
    - sh    (list) l'emplacement dans le fichier
    """
    d: dict[str, str] = field(default_factory=dict)
    sh: tuple[str|int] = field(default_factory=lambda: ("", 0))
    
    def copy(self) -> "Spk":
        return Spk(
            d: self.d.copy()
            sh: self.sh.copy()
        )
    
@dataclass
class Tr:
    """
    Métadonnées d'une transcription.
    - d     (dict) les champs de métadonnées
    - spk   (dict) les ids des locuteurs
    """
    d: dict[str, str] = field(default_factory=dict)
    spk: list[str] = field(default_factory=list)
    
    def copy(self) -> "Tr":
        return Tr(
            d: self.d.copy()
            spk: self.spk.copy()
        )
    
@dataclass
class MetaDict:
    """
    L'ensemble des métadonnées.
    - tr    (dict) pour les transcriptions
    - spk   (dict) pour les locuteurs
    Note : les locuteurs ont des "ids" (incréments). Le même locuteur
           peut avoir des différences entre deux transcriptions
           (notamment relations entre locuteurs).
           Les 'Trans' ont la relation 'code_locuteur' > 'int'.
    """
    tr_cols: list[str] = field(default_factory=list)
    spk_cols: list[str] = field(default_factory=list)
    tr: dict[str, Tr] = field(default_factory=dict)
    spk: dict[spk_key, Spk] = field(default_factory=dict)

@runtime_checkable   
class ModelVVal(Protocol):
    """Wrapper autour d'une valeur pour lui intégrer un validateur."""
    
    val: Any
    vfun: Callable
    args: list

    @property
    def value(self) -> str:
        ...

    @value.setter
    def value(self, val: Any) -> None:
        ...
    
@runtime_checkable
class ModelVCell(Protocol):
    """Wrapper autour d'une cellule pour lui intégrer un validateur."""
    
    cell: Cell
    vfun: Callable
    args: list

    @property
    def value(self) -> str:
        ...

    @value.setter
    def value(self, val: Any) -> None:
        ...

@runtime_checkable
class AbsMeta(Protocol):
    """
    Gère le fichier de métadonnées et les métadonnées en mémoire.
    Ne gère pas le dépôt / la récupération dans les transcriptions. 
    """
    
    f: Path
    wb: Workbook
    d: Metadict
    
    def open(self, f: Path) -> Workbook:
        ...
    def close(self) -> None:
        ...
    def clear(self) -> None:
        ...
    def save(self, f: Path, close: bool) -> None:
        ...
    
    def set_path(self, f: Path) -> None:
        ...
    def load(self, f: Path, keep_open: bool) -> None:
        ...
    def ch_key(self, k: str) -> str:
        ...
    def get(self, trcode: str, spkcode: str, k: str) -> str | dict[str, str]:
        ...
    def set(
            self, trcode: str, spkcode: str, k: str, v: any,
            save: bool, close: bool, f: Path
        ) -> None:
        ...
    def ch_set(
            self, trcode: str, spkcode: str, k: str, v: any, 
            save: bool, close: bool, f: Path, dflt: str
        ) -> None:
        ...
    def set_pub(corp: str, core: str, save: bool, close: bool) -> Workbook:
        ...