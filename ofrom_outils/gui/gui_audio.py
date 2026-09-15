import re
import threading
import tkinter as tk
from tkinter import ttk
from dataclasses import asdict

from ofrom_outils.common_types import Any, Callable, Path
from ofrom_outils.gui.gui_ongl import (
    update_dc, DirPath, RadioOptions, CorOngl, TreePath, Options
)
from ofrom_outils.gui.gui_models import CorAudioData
from ofrom_outils.audio.audio import L_EXT, all_audio_convert, all_audio_mean
from ofrom_outils.logs.log import Log

LOG = Log()


def validate_mean(val: str) -> bool:
    return bool(re.fullmatch(r"-?\d*\.?\d*", val))


def run_convert(
        l_paths: list[Path],
        npath: Path,
        typ: str
) -> None:
    LOG.clear()
    threading.Thread(
        target=all_audio_convert,
        args=(l_paths, npath, typ, False, False, True, LOG)
    ).start()


def run_mean(
        l_paths: list[Path],
        npath: Path,
        mean: int | float | None
) -> None:
    LOG.clear()
    all_audio_mean(
        l_paths, npath, None, mean, False, True, LOG
    )


class CorAudio(CorOngl[CorAudioData]):

    def __init__(
            self,
            parent: tk.Misc,
            data: dict[str, Any],
            pyw: Callable[[str, str], None]
    ):
        super().__init__(parent, data, pyw)
        global LOG
        LOG.pyw = pyw
        top = ttk.PanedWindow(self, orient="horizontal")
        self.files = TreePath(top, l_ext=L_EXT)
        right_pane = tk.Frame(top)
        convert = tk.Frame(right_pane, bd=1, relief="groove", padx=8, pady=8)
        self.conv_button = tk.Button(
            convert,
            text="Convertir",
            command=self.convert
        )
        conv_opts = Options(convert, "Options de conversion")
        self.conv_out = conv_opts.add(
            DirPath,
            "Dossier de sortie : ",
            self.data.c.outdir
        )
        self.conv_ext = conv_opts.add(
            RadioOptions,
            self.data.c.ext
        )
        mean = tk.Frame(right_pane, bd=1, relief="groove", padx=8, pady=8)
        self.mean_button = tk.Button(
            mean,
            text="Ajuster le volume",
            command=self.mean
        )
        mean_opts = Options(mean, "Options de volume")
        self.mean_out = mean_opts.add(
            DirPath,
            "Dossier de sortie : ",
            self.data.m.outdir
        )
        mean_target = mean_opts.add(tk.Frame)

        vcmd = (self.register(validate_mean), "%P")
        mean_label = tk.Label(mean_target, text="Volume moyen : ", anchor="w")
        self.mean_value = tk.StringVar(
            mean_target,
            self.data.m.mean if self.data.m.mean is not None else ""
        )
        mean_entry = tk.Entry(
            mean_target,
            textvariable=self.mean_value,
            validate="key",
            validatecommand=vcmd
        )

        top.add(self.files, weight=1)
        top.add(right_pane, weight=1)
        top.grid(row=0, column=0, sticky="nsew")
        convert.grid(row=0, column=0, sticky="nsew")
        mean.grid(row=1, column=0, sticky="nsew")
        self.conv_button.grid(row=0, column=0, sticky="new")
        conv_opts.grid(row=1, column=0, sticky="nsew")
        self.mean_button.grid(row=0, column=0, sticky="new")
        mean_opts.grid(row=1, column=0, sticky="nsew")
        self.conv_out.grid(row=0, column=0, sticky="new")
        self.conv_ext.grid(row=1, column=0, sticky="new")
        self.mean_out.grid(row=0, column=0, sticky="new")
        mean_target.grid(row=1, column=0, sticky="new")
        mean_label.grid(row=0, column=0, sticky="e")
        mean_entry.grid(row=0, column=1, sticky="w")

        self.columnconfigure(0, weight=1)
        right_pane.columnconfigure(0, weight=1)
        convert.columnconfigure(0, weight=1)
        mean.columnconfigure(0, weight=1)

    def fill_data(self, data: dict[str, Any]) -> CorAudioData:
        dat = CorAudioData()
        update_dc(dat, data)
        return dat

    def get_data(self):
        """Récupère et renvoie les données pour cet onglet."""
        self.data.files = self.files.get()
        self.data.c.outdir = self.conv_out.get()
        ext = self.conv_ext.get()
        for k in self.data.c.ext.keys():
            self.data.c.ext[k][1] = True if k == ext else False
        self.data.m.outdir = self.mean_out.get()
        m = self.mean_value.get()
        try:
            self.data.m.mean = float(m)
        except ValueError:
            self.data.m.mean = None
        return asdict(self.data)

    def set_data(self, dat: dict[str, Any]):
        """Permet de modifier les données pour cet onglet."""
        update_dc(self.data, dat)
        self.files.set(self.data.files)
        self.conv_out.set(self.data.c.outdir)
        self.conv_ext.reset(self.data.c.ext)
        self.mean_out.set(self.data.m.outdir)
        self.mean_value.set(
            self.data.m.mean if self.data.m.mean is not None else ""
        )

    def convert(self):
        self.get_data()
        typ = next((k for k, (_, v) in self.data.c.ext.items() if v), "")
        run_convert(self.data.files, self.data.c.outdir, typ)

    def mean(self):
        self.get_data()
        run_mean(self.data.files, self.data.m.outdir, self.data.m.mean)
