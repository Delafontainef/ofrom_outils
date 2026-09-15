import os
import re
import tkinter as tk
from abc import abstractmethod, ABC
from dataclasses import asdict, is_dataclass
from tkinter import filedialog
from tkinter import ttk
from typing import Generic, TypeVar

from ofrom_outils.common_types import Any, Path, Callable

T = TypeVar("T", bound=tk.Widget)


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
        self.label.grid(row=0, column=0, sticky="w")
        self.entry.grid(row=0, column=1, sticky="ew")
        self.button.grid(row=0, column=2, sticky="e")
        self.columnconfigure(1, weight=1)

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


class TreePath(tk.Frame):
    def __init__(
            self,
            parent: tk.Misc,
            l_ext: list[str] | None = None
    ):
        super().__init__(parent)
        self.l_ext = l_ext if l_ext is not None else []
        self.tip = None
        header = tk.Frame(self)
        self.addbutton = tk.Button(
            header,
            text="Ajout...",
            command=self.add,
        )
        self.sel = tk.IntVar(value=0)
        self.selectall = tk.Checkbutton(
            header,
            text="tout",
            variable=self.sel,
            offvalue=0,
            tristatevalue=1,
            onvalue=2,
            command=self.select_all,
        )
        self.remove = tk.Button(
            header,
            text="X",
            fg="red",
            command=self.remove_selected
        )
        self.tree = ttk.Treeview(
            self,
            show="tree headings",
            selectmode="extended"
        )
        self.tree.heading("#0", text="Fichiers")

        header.grid(row=0, column=0, sticky="new")
        self.addbutton.grid(row=0, column=0, sticky="w")
        self.selectall.grid(row=0, column=1, sticky="w")
        self.remove.grid(row=0, column=3, sticky="e")
        self.tree.grid(row=1, column=0, sticky="nsew")
        header.columnconfigure(2, weight=1)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self.tree.bind("<Insert>", lambda _: self.add())
        self.tree.bind("<Delete>", lambda _: self.remove_selected())
        self.tree.bind("<<TreeviewSelect>>", self._selection)
        self.tree.bind("<Motion>", self._motion)

    def _selection(self, _=None) -> None:
        """Met à jour la valeur du bouton 'tout sélectionner'."""
        total = len(self.tree.get_children())
        selected = len(self.tree.selection())
        self.sel.set(
            0 if selected == 0
            else 2 if selected == total
            else 1
        )

    def _show_tooltip(self, x: int, y: int, text: str) -> None:
        self._hide_tooltip()

        self.tip = tk.Toplevel(self.tree)
        self.tip.wm_overrideredirect(True)
        self.tip.wm_geometry(f"+{x}+{y}")

        label = tk.Label(
            self.tip,
            text=text,
            relief="solid",
            borderwidth=1,
            padx=4,
            pady=2,
        )
        label.grid(row=0, column=0, sticky="nsew")
        self.tip.columnconfigure(0, weight=1)
        self.tip.rowconfigure(0, weight=1)

    def _hide_tooltip(self, _=None):
        if self.tip:
            self.tip.destroy()
            self.tip = None

    def _motion(self, e: tk.Event):
        iid = self.tree.identify_row(e.y)
        if not iid:
            self._hide_tooltip()
            return
        path = self.tree.item(iid, "values")[0]
        self._show_tooltip(e.x_root + 10, e.y_root + 10, path)

    def add(self) -> None:
        """
        Ajoute des fichiers à la liste.
        Utilise 'l_ext' pour trier le résultat par extension de fichier.
        """
        ask = tk.filedialog.askopenfilenames()
        for ask_file in ask:
            f = os.path.basename(ask_file)
            fi, ext = os.path.splitext(f)
            if self.l_ext and ext.lower() not in self.l_ext:
                continue
            self.tree.insert("", "end", text=f, values=(ask_file,))

    def select_all(self) -> None:
        """(Dé)sélectionne tous les fichiers."""
        if self.sel.get() == 2:
            self.tree.selection_set(self.tree.get_children())
        else:
            self.tree.selection_remove(self.tree.selection())
            self.sel.set(0)

    def remove_selected(self) -> None:
        """Retire les fichiers sélectionnés."""
        self.tree.delete(*self.tree.selection())

    def get(self) -> list[str]:
        """Renvoie la liste des fichiers."""
        return [
            self.tree.item(iid, "values")[0]
            for iid in self.tree.get_children()
        ]

    def get_selected(self) -> list[str]:
        """Renvoie la liste des fichiers sélectionnés."""
        return [
            self.tree.item(iid, "values")[0]
            for iid in self.tree.selection()
        ]

    def set(self, paths: list[str]) -> None:
        """Remplace la liste de fichiers."""
        self.tree.delete(*self.tree.get_children())

        for path in paths:
            f = os.path.basename(path)
            fi, ext = os.path.splitext(f)
            if (
                    (not os.path.isfile(path)) or
                    (self.l_ext and ext.lower() not in self.l_ext)
            ):
                continue
            self.tree.insert(
                "",
                "end",
                text=os.path.basename(path),
                values=(path,),
            )

        self.tree.selection_remove(self.tree.selection())
        self._selection()

    def set_selected(self, paths: list[str]) -> None:
        selected = set(paths)
        self.tree.selection_remove(self.tree.selection())

        for iid in self.tree.get_children():
            path = self.tree.item(iid, "values")[0]
            if path in selected:
                self.tree.selection_add(iid)

        self._selection()


class Options(tk.Frame):
    def __init__(self, parent, title="Options"):
        super().__init__(parent)
        self.expanded = False

        header = tk.Frame(self)
        label = tk.Label(header, text=title)
        self.button = tk.Button(
            header,
            text=" - ",
            command=self.toggle,
        )
        self.content = tk.Frame(
            self,
            borderwidth=1,
            relief=tk.GROOVE,
        )

        self.columnconfigure(0, weight=1)
        header.grid(row=0, column=0, sticky="ew")
        label.grid(row=0, column=0)
        self.button.grid(row=0, column=1)
        self.content.grid(row=1, column=0, sticky="nsew")

    def toggle(self):
        if self.expanded:
            self.content.grid_remove()
            self.button.config(text=" + ")
        else:
            self.content.grid()
            self.button.config(text=" - ")

        self.expanded = not self.expanded
        self.update_idletasks()

    def add(self, widget: type[T], *args, **kwargs) -> T:
        return widget(self.content, *args, **kwargs)


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
            b.grid(row=r, column=c, sticky="ew")
            self.columnconfigure(c, weight=1)
            self.rowconfigure(r, weight=1)

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
            b.grid(row=r, column=c, sticky="ew")
            self.columnconfigure(c, weight=1)
            self.rowconfigure(r, weight=1)


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

        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

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
