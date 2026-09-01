import tkinter as tk

from ofrom_outils.common import update_dc
from ofrom_outils.common_types import Any, Callable
from ofrom_outils.gui.gui_ongl import DirPath, CorOngl
from ofrom_outils.gui.gui_models import CorAudioData
from ofrom_outils.audio.audio import all_audio_convert, all_audio_mean

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
        self.cin = DirPath(conv_paths, "Dossier d'entrée : ")
        self.cout = DirPath(conv_paths, "Dossier de sortie : ")
        conv_opts = tk.Frame(convert)
        self.convert = tk.Button(convert, text="Convertir")
        mean = tk.Frame(self)
        mean_paths = tk.Frame(mean)
        self.cin = DirPath(mean_paths, "Dossier d'entrée : ")
        self.cout = DirPath(mean_paths, "Dossier de sortie : ")
        mean_opts = tk.Frame(mean)
        self.mean = tk.Button(mean, text="Ajuster le volume")

        convert.grid(row=0, column=0)
        conv_paths.grid(row=0, column=0)
        conv_opts.grid(row=0, column=1)
        self.convert.grid(row=0, column=2)
        mean.grid(row=0, column=1)
        mean_paths.grid(row=0, column=0)
        mean_opts.grid(row=0, column=1)
        self.mean.grid(row=0, column=2)
        self.columnconfigure(0, weight=1)

    def fill_data(self, data: dict[str, Any]) -> CorAudioData:
        dat = CorAudioData()
        update_dc(dat, data)
        return dat

