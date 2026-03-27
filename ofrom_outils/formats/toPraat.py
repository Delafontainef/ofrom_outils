from corflow import toPraat as toOrigPraat
from ofrom_outils.common_types import Path, Transcription

def check(tr: Transcription) -> Transcription:
    """Vérifie le contenu de la transcription avant sauvegarde."""
    return tr

def toPraat(
    path: Path,
    tr: Transcription|list[Transcription]
    ) -> None:
    """Wrapper pour sauvegarder les TextGrids d'OFROM+."""
    tr = [check(tri) for tri in tr] if isinstance(tr, list) else check(tr)
    toOrigPraat.toPraat(path, tr)