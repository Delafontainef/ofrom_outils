import tkinter as tk

from ofrom_outils.common_types import Any, Callable
from ofrom_outils.gui.gui import CorOngl
from ofrom_outils.gui.gui_models import CorAudioData

class CorAudio(CorOngl[CorAudioData]):

    def __init__(
            self,
            parent: tk.Misc,
            data: dict[str, Any],
            pyw: Callable[[str, str], None]
    ):
        super().__init__(parent, data, pyw)

    def fill_data(self, data: dict[str, Any]) -> CorAudioData:
        return CorAudioData()

