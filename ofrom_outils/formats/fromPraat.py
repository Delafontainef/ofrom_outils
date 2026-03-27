from corflow import fromPraat as fromOrigPraat
from ofrom_outils.common import setParent
from ofrom_outils.meta.meta import Meta
from ofrom_outils.common_types import Path, Transcription

def fromPraat(
        path: Path, 
        meta: Meta = None
    ) -> Transcription|list[Transcription]:
    """Wrapper pour récupérer les TextGrids d'OFROM+."""
    tr = fromOrigPraat.fromPraat(path)
    func = meta.add_to_trans if meta else setParent
    tr.setMeta("audio_path", os.path.join(d, fi+".wav"))
    return [func(tri) for tri in tr] if isinstance(tr, list) else func(tr)



