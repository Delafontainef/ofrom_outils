import os
import re
import tkinter as tk
from abc import abstractmethod, ABC
from dataclasses import asdict, is_dataclass
from tkinter import filedialog
from typing import Generic, TypeVar

from ofrom_outils.common_types import Any, Path, Callable


T = TypeVar("T")


def update_dc(
        obj: object,
        data: dict[str, Any]
) -> None:
    for key, value in data.items():
        if not hasattr(obj, key):
            continue
        current = getattr(obj, key)
        if is_dataclass(current) and isinstance(value, dict):
            update_dc(current, value)
        else:
            setattr(obj, key, value)


class AbsPath(tk.Frame):
    """Composant pour la sélection de documents."""

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
    """Sélection de fichier."""

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


class DirPath(AbsPath):
    """Sélection de dossier."""

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


class CheckOptions(tk.Frame):
    """Composant de CheckButtons pour les options."""

    def __init__(
            self,
            parent: tk.Misc,
            opts: dict[str, list[str | bool]],
            nb_cols: int = 4
    ):
        super().__init__(parent)
        self.vals = {}
        self.reset(opts, nb_cols)

    def get(self):
        return {k: v.get() for k, v in self.vals.items()}

    def set(self, key: str):
        if key not in self.vals:
            return
        self.vals[key] = True if self.vals[key] == False else False

    def reset(self, opts: dict[str, list[str | bool]], nb_cols: int = 4):
        self.vals = {}
        for child in self.winfo_children():
            child.destroy()
        for i, (key, (name, value)) in enumerate(opts.items()):
            r, c = divmod(i, nb_cols)
            val = tk.BooleanVar(self, value=value)
            self.vals[key] = val

            b = tk.Checkbutton(
                self,
                text=name,
                variable=val
            )
            b.grid(row=r, column=c, sticky=tk.W)

    def trace_add(self, mode, callback):
        return [
            var.trace_add(mode, callback)
            for var in self.vals.values()
        ]


class RadioOptions(tk.Frame):
    """Composant de RadioButtons pour les options."""

    def __init__(
            self,
            parent: tk.Misc,
            opts: dict[str, list[str | bool]],
            nb_cols: int = 4
    ):
        super().__init__(parent)
        self.val = tk.StringVar(self)
        self.reset(opts, nb_cols)

    def get(self):
        return self.val.get()

    def set(self, key: str):
        self.val.set(key)

    def reset(self, opts: dict[str, list[str | bool]], nb_cols: int = 4):
        self.val = tk.StringVar(self)
        for child in self.winfo_children():
            child.destroy()
        for i, (key, (name, value)) in enumerate(opts.items()):
            r, c = divmod(i, nb_cols)
            if value:
                self.val.set(key)
            b = tk.Radiobutton(
                self,
                text=name,
                variable=self.val,
                value=key
            )
            b.grid(row=r, column=c, sticky=tk.W)


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
