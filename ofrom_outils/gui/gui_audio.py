import tkinter as tk
from dataclasses import asdict

from ofrom_outils.common import update_dc
from ofrom_outils.common_types import Any, Callable
from ofrom_outils.gui.gui_ongl import DirPath, RadioOptions, CorOngl
from ofrom_outils.gui.gui_models import CorAudioData
from ofrom_outils.audio.audio import all_audio_convert, all_audio_mean

def validate_mean(val: str) -> bool:
    return val == "" or val.isdigit()

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
        self.conv_button = tk.Button(convert, text="Convertir")
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
        self.mean_value = tk.StringVar(mean_opts, self.data.m.mean)
        mean_entry = tk.Entry(
            mean_opts,
            textvariable=self.mean_value,
            validate="key",
            validatecommand=vcmd
        )
        self.mean_button = tk.Button(mean, text="Ajuster le volume")

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
        self.data.c.indir = self.conv_in.value.get()
        self.data.c.outdir = self.conv_out.value.get()
        opt = self.conv_opts.val.get()
        for k in self.data.c.opts.keys():
            self.data.c.opts[k][1] = True if k == opt else False
        self.data.m.indir = self.mean_in.value.get()
        self.data.m.outdir = self.mean_out.value.get()
        self.data.m.mean = self.mean_value.get()
        return asdict(self.data)

    def set_data(self, dat: dict[str, Any]):
        """Permet de modifier les données pour cet onglet."""
        update_dc(self.data, dat)
