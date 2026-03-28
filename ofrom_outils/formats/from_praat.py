import os

from corflow import fromPraat as fromOrigPraat

from ofrom_outils.common import set_parent
from ofrom_outils.common_types import Path, Transcription
from ofrom_outils.meta.meta import Meta


def from_praat(
        path: Path,
        meta: Meta = None
) -> Transcription | list[Transcription]:
    """Wrapper pour récupérer les TextGrids d'OFROM+."""
    d, file = os.path.split(path)
    fi, ext = os.path.splitext(file)
    tr = fromOrigPraat.fromPraat(path)
    func = meta.add_to_trans if meta else set_parent
    tr.setMeta("audio_path", os.path.join(d, fi + ".wav"))
    return [func(tri) for tri in tr] if isinstance(tr, list) else func(tr)
