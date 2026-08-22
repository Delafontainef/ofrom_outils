import tkinter as tk
from contextlib import AbstractContextManager
from dataclasses import dataclass
from tkinter import ttk
from typing import Any, Protocol, runtime_checkable


@dataclass
class CorMainData:
    pos: list[int]
    size: list[int]
    save_file: str
    active: int


@runtime_checkable
class CorMenu(Protocol):
    """Composant menu de l'interface."""

    parent: tk.Misc


@runtime_checkable
class CorConsole(Protocol):
    parent: tk.Misc

    def activate(self) -> AbstractContextManager[None]:
        ...

    def mark(self, mark_name: str, mark: str) -> None:
        ...

    def clear(self, line: int, col: int) -> None:
        ...

    def write(self, txt: str, mode: str) -> None:
        ...

    def pyw(self, txt: str, mode: str) -> None:
        ...


@runtime_checkable
class CorMain(Protocol):
    menu: CorMenu
    champ: ttk.Notebook
    console: CorConsole
    data: dict[str, Any]
    ongl: list
    actif: int

    def _load_config(self) -> None:
        ...

    def _save_config(self, event: tk.Event) -> None:
        ...
