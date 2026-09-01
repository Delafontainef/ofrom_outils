import os
import re
import tkinter as tk
from abc import abstractmethod, ABC
from dataclasses import asdict
from tkinter import filedialog
from typing import Generic, TypeVar

from ofrom_outils.common import update_dc
from ofrom_outils.common_types import Any, Path, Callable


class AbsPath(tk.Frame):
    def __init__(
            self,
            parent: tk.Misc,
            label: str = "",
            path: Path = "",
            regex: str = r"",
            setopen: Callable | None = None
    ):
        super().__init__(parent)
        self.regex = regex
        self.setopen = setopen
        self.label = tk.Label(self, text=label, anchor="w")
        self.value = tk.StringVar(self, self.format_path(path))
        self.entry = tk.Entry(
            self,
            textvariable=self.value,
            state="readonly"
        )
        self.button = tk.Button(
            self,
            text="...",
            command=self.set_path_as
        )

    def format_path(self, npath: Path) -> Path:
        """Formatte le chemin pour l'affichage."""
        return "" if (
                not os.path.exists(npath)
                or (self.regex and not re.search(self.regex, str(npath)))
        ) else npath

    def set(self, npath: Path) -> None:
        """Change le chemin."""
        self.value.set(self.format_path(npath))
        self.entry.icursor(tk.END)
        self.entry.xview_moveto(1.0)

    def set_path_as(self) -> None:
        label = self.label.cget("text")
        npath = self.setopen(title=label)
        if not npath:
            return
        self.set(npath)

    def get(self):
        return self.format_path(self.value.get())


class FilePath(AbsPath):
    def __init__(
            self,
            parent: tk.Misc,
            label: str = "",
            path: Path = "",
            regex: str = r""
    ):
        super().__init__(
            parent,
            label,
            path,
            regex,
            tk.filedialog.askopenfilename
        )


class FilesPath(AbsPath):
    def __init__(
            self,
            parent: tk.Misc,
            label: str = "",
            path: Path = "",
            regex: str = r""
    ):
        super().__init__(
            parent,
            label,
            path,
            regex,
            tk.filedialog.askopenfilenames
        )


class DirPath(AbsPath):
    def __init__(
            self,
            parent: tk.Misc,
            label: str = "",
            path: Path = "",
            regex: str = r""
    ):
        super().__init__(
            parent,
            label,
            path,
            regex,
            tk.filedialog.askdirectory
        )


CorOnglData = TypeVar("CorOnglData")


class CorOngl(tk.Frame, Generic[CorOnglData], ABC):
    """Composant de base pour les onglets."""

    def __init__(
            self,
            parent: tk.Misc,
            data: dict[str, Any],
            pyw: Callable[[str, str], None]
    ):
        super().__init__(parent)
        self.parent = parent
        self.data = self.fill_data(data)
        self.pyw = pyw

    @abstractmethod
    def fill_data(self, data: dict[str, Any]) -> CorOnglData:
        """Transforme le dict' en dataclass."""
        ...

    def get_data(self):
        """Récupère et renvoie les données pour cet onglet."""
        return asdict(self.data)

    def set_data(self, dat: dict[str, Any]):
        """Permet de modifier les données pour cet onglet."""
        update_dc(self.data, dat)
