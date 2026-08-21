import tkinter as tk
from contextlib import contextmanager
from tkinter import ttk

import os
import json
from ofrom_outils.common import DATA


class CorMenu(tk.Menu):
    """Composant menu de l'interface."""

    def __init__(self, parent: tk.Misc = None):
        super().__init__(parent, tearoff=0)
        self.parent = parent
        menu1 = tk.Menu(self, tearoff=0)
        menu1.add_command(label="Nouvel onglet",
                          command=lambda: print("Not implemented"))
        menu1.add_command(label="Fermer l'onglet",
                          command=lambda: print("Not implemented"))
        menu1.add_separator()
        menu1.add_command(label="Charger...",
                          command=lambda: print("Not implemented"))
        menu1.add_command(label="Sauvegarder...",
                          command=lambda: print("Not implemented"))
        menu1.add_command(label="Sauvegarder sous...",
                          command=lambda: print("Not implemented"))
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

    def __init__(self, parent: tk.Misc = None):
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
                l, c = map(int, self.text.index("w").split('.'))
                self.text.delete("w", "end")
                if c == 0 and l != 1:  # retours à la ligne
                    self.text.insert("w", "\n")
                    self.mark()
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
        self.menu = CorMenu(self)  # Menu
        self.champ = ttk.Notebook(self)  # Champ d'onglets
        self.console = CorConsole(self)  # Messages à l'utilisateur
        self.data = {}  # Données générales
        self.ongl = []  # Liste d'onglets

        self.config(menu=self.menu)
        self.champ.grid(row=0, sticky='nwse')
        self.console.grid(row=1, sticky='nwse', padx=2, pady=2)
        self.columnconfigure(0, weight=1)

        self.setup()
        self.bind("<Destroy>", self._save_config)

    def _load_config(self):
        """Chargement du fichier de configuration."""
        config_file = os.path.join(DATA, "ofrom_gui_config.json")
        if not os.path.isfile(config_file):
            self.data = {
                "taille": [720, 480],
                "save_file": "",
                "actif": -1
            }
            return
        with open(config_file, "r", encoding="utf-8") as rf:
            self.data = json.load(rf)

    def _save_config(self, event: tk.Event = None) -> None:
        """Sauvegarde du fichier de configuration."""
        if event and event.widget is not self:
            return
        config_file = os.path.join(DATA, "ofrom_gui_config.json")
        with open(config_file, "w", encoding="utf-8") as wf:
            json.dump(self.data, wf, indent=4)

    def setup(self):
        """Mise en place des données / onglets."""
        self._load_config()


if __name__ == "__main__":
    """Génère l'interface quand on double-clique."""
    import sys

    window = CorMain()
    window.mainloop()
    sys.stdout.close()
    sys.exit()
