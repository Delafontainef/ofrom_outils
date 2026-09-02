import re
import tkinter as tk
from dataclasses import asdict

from ofrom_outils.common_types import Any, Callable, Path
from ofrom_outils.gui.gui_ongl import (
    update_dc, DirPath, RadioOptions, CorOngl
)
from ofrom_outils.gui.gui_models import CorAudioData
from ofrom_outils.audio.audio import all_audio_convert, all_audio_mean


def validate_mean(val: str) -> bool:
    return bool(re.fullmatch(r"-?\d*\.?\d*", val))


def run_convert(
        path: Path,
        npath: Path,
        typ: str
) -> None:
    rem = True if path == npath else False
    all_audio_convert(path, npath, typ, rem, False, False)


def run_mean(
        path: Path,
        npath: Path,
        mean: int | float | None
) -> None:
    rem = True if path == npath else False
    all_audio_mean(path, npath, None, mean, rem, False)


class CorAudio(CorOngl[CorAudioData]):

    def __init__(
            self,
            parent: tk.Misc,
            data: dict[str, Any],
            pyw: Callable[[str, str], None]
    ):
        super().__init__(parent, data, pyw)
        convert = tk.Frame(self)
        conv_paths = tk.Frame(convert)
        self.conv_in = DirPath(
            conv_paths,
            "Dossier d'entrée : ",
            self.data.c.indir
        )
        self.conv_out = DirPath(
            conv_paths,
            "Dossier de sortie : ",
            self.data.c.outdir
        )
        self.conv_opts = RadioOptions(convert, self.data.c.opts)
        self.conv_button = tk.Button(
            convert,
            text="Convertir",
            command=self.convert
        )
        mean = tk.Frame(self)
        mean_paths = tk.Frame(mean)
        self.mean_in = DirPath(
            mean_paths,
            "Dossier d'entrée : ",
            self.data.m.indir
        )
        self.mean_out = DirPath(
            mean_paths,
            "Dossier de sortie : ",
            self.data.m.outdir
        )
        mean_opts = tk.Frame(mean)
        vcmd = (self.register(validate_mean), "%P")
        mean_label = tk.Label(mean_opts, text="Moyenne : ", anchor="w")
        self.mean_value = tk.StringVar(
            mean_opts,
            self.data.m.mean if self.data.m.mean is not None else ""
        )
        mean_entry = tk.Entry(
            mean_opts,
            textvariable=self.mean_value,
            validate="key",
            validatecommand=vcmd
        )
        self.mean_button = tk.Button(
            mean,
            text="Ajuster le volume",
            command=self.mean
        )

        convert.grid(row=0, column=0)
        conv_paths.grid(row=0, column=0)
        self.conv_in.grid(row=0, column=0)
        self.conv_out.grid(row=0, column=1)
        self.conv_opts.grid(row=0, column=1)
        self.conv_button.grid(row=0, column=2)
        mean.grid(row=0, column=1)
        mean_paths.grid(row=0, column=0)
        self.mean_in.grid(row=0, column=0)
        self.mean_out.grid(row=0, column=1)
        mean_opts.grid(row=0, column=1)
        mean_label.grid(row=0, column=0)
        mean_entry.grid(row=0, column=1)
        mean_label.grid(row=0, column=0)

        self.mean_button.grid(row=0, column=2)
        self.columnconfigure(0, weight=1)

    def fill_data(self, data: dict[str, Any]) -> CorAudioData:
        dat = CorAudioData()
        update_dc(dat, data)
        return dat

    def get_data(self):
        """Récupère et renvoie les données pour cet onglet."""
        self.data.c.indir = self.conv_in.get()
        self.data.c.outdir = self.conv_out.get()
        opt = self.conv_opts.get()
        for k in self.data.c.opts.keys():
            self.data.c.opts[k][1] = True if k == opt else False
        self.data.m.indir = self.mean_in.get()
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
        self.conv_in.set(self.data.c.indir)
        self.conv_out.set(self.data.c.outdir)
        self.conv_opts.reset(self.data.c.opts)
        self.mean_in.set(self.data.m.indir)
        self.mean_out.set(self.data.m.outdir)
        self.mean_value.set(
            self.data.m.mean if self.data.m.mean is not None else ""
        )

    def convert(self):
        self.get_data()
        typ = next((k for k, (_, v) in self.data.c.opts.items() if v), "")
        run_convert(self.data.c.indir, self.data.c.outdir, typ)

    def mean(self):
        self.get_data()
        run_mean(self.data.m.indir, self.data.m.outdir, self.data.m.mean)
