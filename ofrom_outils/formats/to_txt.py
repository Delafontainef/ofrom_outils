import os


def write_txt(tr, psym="_"):
    """Writes the transcription's content."""
    spk, txt = "", ""
    for seg in tr.iterTime():
        cont = seg.content
        if "[" in seg.struct.name:  # no annotation
            continue
        if spk != seg.struct.name:
            spk = seg.struct.name
            txt = txt + f"\n{spk}: "
        if cont == psym:
            txt = txt + f"({seg.end - seg.start:.02f}) "
        else:
            txt = txt + cont + " "
    return txt


def to_txt(path, trans, **_args):
    """Lazy Corflow export implementation for OFROM+ usage."""
    if os.path.isdir(path):  # If it's a directory
        path = os.path.join(path, trans.name + ".txt")  # Use 'trans.name'
    trans = trans.copy()  # We use a copy from there
    txt = write_txt(trans)  # content
    with open(path, "w", encoding="utf-8") as wf:
        wf.write(txt)
