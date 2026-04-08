"""28.02.2026
Modèles pour les statistiques d'OFROM+.
"""

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from ofrom_outils.common_types import Path, Callable
from ofrom_outils.meta.meta import Meta

type OFRDict = dict[str, dict[str, dict[str, str | list[str] | int]]]


@dataclass
class StFile:
    """
    Statistiques pour un fichier.
    - wd    (int)   nombre de mots du fichier
    - dur   (float) durée du fichier
    - spk   (dict)  dictionnaire de locuteurs (avec mots/durée)
    """
    wd: int = 0
    dur: float = 0.0
    spk: dict[str, tuple[int, float]] = field(default_factory=dict)


@dataclass
class StList:
    """
    Statistiques pour une liste de fichiers.
    - wd    (int)   nombre global de mots
    - dur   (float) durée globale
    - fi    (dict)  dictionnaire de fichiers (avec mots/durée)
    - spk   (dict)  dictionnaire de locuteurs (avec mots/durée)
    """
    wd: int = 0
    dur: float = 0.0
    fi: dict[str, StFile] = field(default_factory=dict)
    spk: dict[str, list[int | float]] = field(default_factory=dict)


@runtime_checkable
class AbsStats(Protocol):
    """Gère les opérations de statistiques."""

    f: Path
    md: Meta | None
    st: StList | None
    mode: str
    l_ext: list[str]

    def set_meta_stats(
            self, st: StList, path: Path, safe: bool, save: bool = True
    ) -> None:
        ...

    def sort_tr(
            self, st: StList, typ: str, path: Path
    ) -> dict[str, StList]:
        ...

    def sort_spk(
            self, st: StList, typ: str, path: Path
    ) -> dict[str, StList]:
        ...

    def ch_typ(self, typ: str) -> Callable | None:
        ...

    def load_dir(self,
                 path: Path,
                 mode: str = "",
                 l_ext: str | list[str] = None
                 ) -> StList:
        ...

    def load_corp(self,
                  corp: list[str] = None,
                  mode: str = "",
                  l_ext: str | list[str] = None
                  ) -> StList:
        ...

    def load_meta(self, path: Path) -> None:
        ...

    def sort(
            self, st: StList, typ: str, func: Callable = None
    ) -> dict[str, StList]:
        ...

    def to_excel(self,
                 path: Path, d_st: dict[str, StList], shn: str = "general"
                 ) -> None:
        ...

    def to_excel_typ(self,
                     path: Path, st: StList, typ: str
                     ) -> None:
        ...


@runtime_checkable
class AbsTokenDict(Protocol):
    """Gère le dictionnaire de tokens."""

    f: str
    d: OFRDict

    def generate(self) -> OFRDict:
        ...

    def load(self, path: Path = "") -> OFRDict:
        ...

    def save(self, path: Path = "") -> None:
        ...

    def get(self, word: str) -> None | dict[str, str]:
        ...
