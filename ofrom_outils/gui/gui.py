""" 22.08.2026
Contient les composants principaux pour l'interface.
Cela inclut la fenêtre principale, la console et le menu,
le modèle d'onglet et les composants génériques.

Cela exclut un onglet spécifique qui doit être ajouté dans ONGL.
"""

import json
import os
import tkinter as tk
from abc import abstractmethod, ABC
from contextlib import contextmanager
from dataclasses import asdict
from tkinter import filedialog
from tkinter import ttk
from typing import Generic, TypeVar

from ofrom_outils.common import DATA
from ofrom_outils.common_types import Any, Path, Callable
from ofrom_outils.gui.gui_models import CorMainData


def update_dc(obj: object, data: dict[str, Any]):
    """Updates a dataclass (CorOnglData, CorMainData, ...)."""
    for key, value in data.items():
        if hasattr(obj, key):
            setattr(obj, key, value)


class Pathfinder(tk.Frame):

    def __init__(
            self,
            parent: tk.Misc,
            label: str = "",
            path: Path = "",
    ):
        super().__init__(parent)
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

    @staticmethod
    def format_path(npath: Path, endswith: str = "metadata.xlsx") -> Path:
        """Formatte le chemin pour l'affichage."""
        if (not os.path.isdir(npath)) and (not os.path.isfile(npath) or
                                           (endswith and not npath.endswith(
                                               endswith))):
            return ""
        return npath

    def set(self, npath: Path) -> None:
        """Change le chemin."""
        self.value.set(self.format_path(npath))
        self.entry.icursor(tk.END)
        self.entry.xview_moveto(1.0)

    def set_path_as(self) -> None:
        """Change le chemin en demandant à l'utilisateur."""
        label = self.label.cget("text")
        if "métadonnées" in label.lower():  # recherche un fichier
            npath = tk.filedialog.askopenfilename(title=label)
        else:  # recherche un dossier
            npath = tk.filedialog.askdirectory(title=label)
        if not npath:
            return
        self.set(npath)

    def get(self):
        return self.format_path(self.value.get())


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


ONGL: dict[str, type[CorOngl]] = {

}  # composants accessibles par 'CorMain'


class CorMenu(tk.Menu):
    """Composant menu de l'interface."""

    def __init__(
            self,
            parent: tk.Misc,
            commands: dict[str, Callable]
    ):
        super().__init__(parent, tearoff=0)
        self.parent = parent
        menu1 = tk.Menu(self, tearoff=0)
        menu1.add_command(label="Nouvel onglet",
                          command=lambda: print("Not implemented"))
        menu1.add_command(label="Fermer l'onglet",
                          command=lambda: print("Not implemented"))
        menu1.add_separator()
        menu1.add_command(
            label="Charger...",
            command=commands['load'],
            accelerator="Ctrl+O"
        )
        menu1.add_command(label="Sauvegarder...", command=commands['save'])
        menu1.add_command(
            label="Sauvegarder sous...",
            command=commands['save_as'],
            accelerator="Ctrl+S"
        )
        menu1.add_separator()
        menu1.add_command(label="Options",
                          command=lambda: print("Not implemented"))
        menu1.add_separator()
        menu1.add_command(label="Quitter",
                          command=lambda: print("Not implemented"))
        menu2 = tk.Menu(self, tearoff=0)
        self.add_cascade(label="Fichiers", menu=menu1)
        self.add_cascade(label="Aide", menu=menu2)


class CorConsole(tk.Frame):
    """Composant console de l'interface."""

    def __init__(self, parent: tk.Misc | None = None):
        super().__init__(parent)
        self.parent = parent

        self.text = tk.Text(self, state="disabled")
        self.scroll = ttk.Scrollbar(
            self,
            orient="vertical",
            command=self.text.yview
        )
        self.text.configure(yscrollcommand=self.scroll.set)
        self.text.grid(row=0, column=0, sticky="nsew")
        self.scroll.grid(row=0, column=1, sticky="ns")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

    @contextmanager
    def activate(self):
        """Active la console le temps d'opérer sur le texte."""
        state = self.text.cget("state")
        self.text.config(state='normal')
        try:
            yield
        finally:
            self.text.config(state=state)

    def mark(
            self,
            mark_name: str = "w",
            mark: str = "end-1c"
    ):
        """Ajoute/déplace un marqueur dans la 'console'."""
        self.text.mark_set(mark_name, mark)
        self.text.mark_gravity(mark_name, "left")

    def clear(self, line: int = 1, col: int = 0):
        """Vide la 'console'."""
        pos = f"{line}.{col}"
        with self.activate():
            self.text.delete(pos, "end")

    def write(self, txt: str, mode: str = "a"):
        """Écrit dans la console."""
        with self.activate():
            if mode == "a":  # écrire à la fin
                self.text.insert("end", txt)
            elif mode == "w":  # écrire au marqueur
                self.text.delete("w", "end")
                self.text.insert("w", txt)
            self.text.see("end")  # voir la fin du texte

    def pyw(self, txt: str, mode: str = "a"):
        """
        Opérations sur le texte.
        txt:    le texte à ajouter.
        mode:   'a' ajouter,
                'w' pour réécrire depuis le marqueur,
                'mark' pour créer un marqueur,
                'clear' pour vider la 'console'.
        """
        if mode in ["a", "w"]:  # écrit
            self.write(txt, mode)
        elif mode == "mark":  # crée/déplace le marqueur
            self.mark()
        elif mode == "clear":  # vide la 'console'
            self.clear()


class CorMain(tk.Tk):
    """Fenêtre principale du programme."""

    def __init__(self):
        super().__init__()
        self.menu = CorMenu(self,
                            commands={
                                'load': self.load_as,
                                'save': self.save,
                                'save_as': self.save_as
                            })
        self.panes = ttk.PanedWindow(self, orient="vertical")
        self.champ = ttk.Notebook(self.panes)
        self.console = CorConsole(self.panes)
        self.data = CorMainData([0, 0], [720, 480], 50, "", -1)
        self.ongl: list[CorOngl] = []
        self.plus_tab = ttk.Frame(self.champ, height=100)

        self.config(menu=self.menu)
        self.champ.add(self.plus_tab, text="+")
        self.panes.grid(row=0, column=0, sticky="nwse")
        self.panes.add(self.champ, weight=1)
        self.panes.add(self.console, weight=1)
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        self._geometry_job = None
        self.setup()
        self.bind("<Configure>", self._on_configure)
        self.bind("<Destroy>", self._save_config)
        self.bind(
            "<Control-r>",
            lambda event: self.set_geometry([0, 0], [720, 480])
        )
        self.bind("<Control-o>", lambda event: self.load_as())
        self.bind("<Control-s>", lambda event: self.save())
        self.champ.bind("<<NotebookTabChanged>>",
                        lambda event: None)
        self.panes.bind(
            "<ButtonRelease-1>",
            lambda event: self._save_sash()
        )

    def _save_geometry(self, event: tk.Event) -> None:
        """Sauvegarde la géométrie dans la configuration."""
        self._geometry_job = None
        self.data.pos = [event.x, event.y]
        self.data.size = [event.width, event.height]

    def _on_configure(self, event: tk.Event) -> None:
        """S'assure de n'appeler '_save_geometry' qu'une fois."""
        if event.widget is not self:
            return

        if self._geometry_job is not None:
            self.after_cancel(self._geometry_job)

        self._geometry_job = self.after(300, self._save_geometry, event)

    def set_geometry(
            self,
            pos: list[int] | None = None,
            size: list[int] | None = None
    ):
        assert self.data.pos is not None  # shut up IDEA
        assert self.data.size is not None

        pos = self.data.pos if pos is None else pos
        size = self.data.size if size is None else size
        self.geometry(f"{size[0]}x{size[1]}+{pos[0]}+{pos[1]}")
        self.data.pos = pos
        self.data.size = size
        self.after(
            100,
            self.panes.sashpos,
            0,
            self.data.sash_pos
        )

    def _save_sash(self):
        """Sauvegarde la position du séparateur onglets / console."""
        self.data.sash_pos = self.panes.sashpos(0)

    def _load_config(self):
        """Chargement du fichier de configuration."""
        config_file = os.path.join(DATA, "ofrom_gui_config.json")
        if not os.path.isfile(config_file):
            return
        with open(config_file, "r", encoding="utf-8") as rf:
            json_data = json.load(rf)
            update_dc(self.data, json_data)
        self.set_geometry()

    def _save_config(self, event: tk.Event | None = None) -> None:
        """Sauvegarde du fichier de configuration."""
        if event and event.widget is not self:
            return
        config_file = os.path.join(DATA, "ofrom_gui_config.json")
        with open(config_file, "w", encoding="utf-8") as wf:
            json.dump(asdict(self.data), wf, indent=4)

    def _empty_ongl(self) -> None:
        """Vide la liste d'onglets."""
        for widget in self.ongl:
            self.champ.forget(widget)
            widget.destroy()
        self.ongl.clear()

    def _add_ongl(self, i: int, name: str, data: dict[str, Any]) -> None:
        """Ajoute un onglet."""
        if name not in ONGL:
            return
        i = max(0, min(i, len(self.ongl)))
        self.ongl.insert(i, ONGL[name](self.champ, data, self.console.pyw))
        self.champ.insert(i, self.ongl[i], text=name)
        self.champ.select(self.ongl[i])
        self.active = i

    def load(self, file_path: Path | None = None) -> None:
        """Charge les onglets (depuis un fichier JSON)."""
        load_file = file_path if file_path is not None \
            else self.data.save_file
        if not os.path.isfile(load_file):  # leave empty
            return
        with open(load_file, "r", encoding="utf-8") as rf:
            json_data = json.load(rf)
        self._empty_ongl()
        for idx, dict_data in json_data.items():
            i = int(idx)
            if i == 0:  # load_config
                update_dc(self.data, dict_data)
                self.set_geometry()
                continue
            self._add_ongl(i, dict_data.get("name"), dict_data)

    def load_as(self) -> None:
        """Charge les données en demandant le chemin du fichier JSON."""
        f = filedialog.askopenfilename(
            title="Charger une sauvegarde",
            initialdir=self.data.save_file,
            filetypes=[("Json", ".json")]
        )
        if f:
            self.load(f)
            self.data.save_file = f

    def save(self, file_path: Path | None = None) -> None:
        """Sauvegarde les onglets (dans un fichier JSON)."""
        save_file = file_path if file_path is not None \
            else self.data.save_file
        if not os.path.isfile(save_file):  # ask user for save location
            self.save_as()
            return
        json_data: dict[str, dict[str, Any]] = {
            "0": asdict(self.data)
        }
        for i, ongl in enumerate(self.ongl):
            json_data[str(i + 1)] = ongl.get_data()
        with open(save_file, "w", encoding="utf-8") as wf:
            json.dump(json_data, wf, indent=4)

    def save_as(self):
        """Sauvegarde en demandant le chemin du fichier JSON."""
        f = tk.filedialog.asksaveasfilename(
            title="Sauvegarder sous...",
            initialdir=self.data.save_file,
            filetypes=[("JSON", "*.json")],
            defaultextension=".json"
        )
        if f:
            self.save(f)
            self.data.save_file = f

    def setup(self):
        """Mise en place des données / onglets."""
        self._load_config()
        if os.path.isfile(self.data.save_file):
            self.load(self.data.save_file)
        else:
            self.data.save_file = ""


if __name__ == "__main__":
    """Génère l'interface quand on double-clique."""
    import sys

    window = CorMain()
    window.mainloop()
    sys.stdout.close()
    sys.exit()
