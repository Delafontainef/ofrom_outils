"""Copied from corflow.toTEI.
   '_writeBody()' edited to add semantic information for OFROM+.
   annotation tags, symbols, etc. are hard-coded."""

import html
import os

from corflow.Transcription import Corpus, Transcription


# Technical functions
def _ch_encoding(trans, encoding):
    """Seeks encoding (default "utf_8")."""

    # No user-defined encoding
    if not encoding:
        # Check metadata for one
        return trans.meta('encoding', 'tech', empty="utf_8")
    else:
        return encoding

    # Writing functions


def _meta_note(elem, tab: str = "\t" * 6):
    """Iterator for metadata."""
    for k, l_v in elem.iterMeta(div="omni", ch_list=True):  # omni
        for v in l_v:
            yield (tab + "<note type=\"" + html.escape(k) + "\">" +
                   html.escape(v) + "</note>\n")


def _write_fil_desc(ntrans, tab="\t\t"):
    """Writes the file description part of the header."""
    ttab = tab + tab + tab
    # Transcription name
    txt = (tab + "<fileDesc>\n" + tab + "\t<titleStmt>\n" + tab + tab +
           "<title>\n" + tab + tab + "\t<desc>" + html.escape(ntrans.name) +
           "</desc>\n" + tab + tab + "</title>\n" + tab + "\t</titleStmt>\n" +
           tab + "\t<publicationStmt>\n" + tab + tab + "<distributor>corflow"
                                                       "</distributor>\n" + tab + "\t</publicationStmt>\n" + tab +
           "\t<notesStmt>\n" + tab + tab + "<note type=\"COMMENTS_DESC\">\n" +
           tab + tab + "\t<note type=\"lastUsedAnnotationId\">0</note>\n" +
           tab + tab + "</note>\n")
    # Transcription metadata
    mtxt = ""
    for note in _meta_note(ntrans, tab + tab + "\t"):
        mtxt = mtxt + note
    if mtxt:
        txt = txt + (tab + tab + "<note type=\"METADATA\">\n" + mtxt +
                     tab + tab + "</note>\n")
    txt = txt + (tab + "\t</notesStmt>\n")
    # Sound metadata
    if ntrans.meta("audio"):
        txt = txt + (tab + "\t<sourceDesc>\n" + tab + tab + "<recordingStmt>\n" +
                     tab + tab + "\t<recording>\n")
        l_audio = ntrans.meta("audio", ch_list=True)
        for audio in l_audio:
            txt = txt + (ttab + "<media mimeType=\"audio/x-wav\" url=\"" +
                         html.escape(audio) + "\"/>\n")
        txt = txt + (tab + tab + "\t</recording>\n" + tab + tab + "</recordingStmt>\n" +
                     tab + "\t</sourceDesc>\n")
    else:
        txt = txt + (tab + "\t<sourceDesc></sourceDesc>\n")
    return txt + (tab + "</fileDesc>\n")


def _write_pro_desc(ntrans, tab="\t\t"):
    """Writes the profile description (speakers) of the header."""
    d_spk = ntrans.getSpk()
    i = 1
    l_attr = ['age', 'gender']
    # Setting
    txt = (tab + "<profileDesc>\n" + tab + "\t<settingDesc>\n" + tab + tab +
           "<setting xml:id=\"d0\">\n" + tab + tab + "\t<activity/>\n" +
           tab + tab + "</setting>\n" + tab + "\t</settingDesc>\n")
    if not d_spk:
        return txt + (tab + "\t<particDesc/>\n" + tab + "</profileDesc>\n")
    else:
        txt = txt + (tab + "\t<particDesc>\n" + tab + tab + "<listPerson>\n")
        # For each speaker...
    ttab = tab + tab + tab
    for spk, d_vals in d_spk.items():
        l_tiers = d_vals.get('tiers')
        ida = "SPK" + str(i)
        i += 1
        txt = txt + (tab + tab + "\t<person xml:id=\"" + ida + "\"")  # attributes
        for k in l_attr:
            v = d_vals.get(k)
            if v:
                txt = txt + (" " + html.escape(k) + "=\"" + html.escape(v) + "\"")
        txt = txt + ">\n"
        if l_tiers:  # tiers
            d_vals.pop('tiers')
            txt = txt + (ttab + "<altGrp mode=\"incl\">\n")
            for tier in l_tiers:
                if "[" in tier.name:
                    continue
                txt = txt + (ttab + "\t<alt type=\"" +
                             html.escape(tier.name) + "\"/>\n")
                tier.setMeta('spk_id', id, 'tech')
            txt = txt + (ttab + "</altGrp>\n")
        if 'name' in d_vals:  # name
            txt = txt + (ttab + "<persName>" + html.escape(d_vals['name']) +
                         "</persName>\n")
            d_vals.pop('name')
        if d_vals:  # omni
            txt = txt + (ttab + "<noteGrp>\n")
            for k, v in d_vals.items():
                k, v = html.escape(k), html.escape(v)
                txt = txt + (ttab + "\t<note type=\"" + k + "\">" + v + "</note>\n")
            txt = txt + (ttab + "</noteGrp>\n")
        txt = txt + (tab + tab + "\t</person>\n")
    return txt + (tab + tab + "</listPerson>\n" + tab + "\t</particDesc>\n" + tab +
                  "</profileDesc>\n")


def _write_enc_desc(tab="\t\t"):
    """Writes the encoding description (application) of the header."""
    return (tab + "<encodingDesc style=\"0.9.1\">\n" + tab +
            "\t<appInfo>\n" + tab + tab + "<application ident=\"toTXM\" "
                                          "version=\"3.4\">\n" + tab + tab +
            "\t<desc>OFROM variation of Python's library 'corflow.toTEI'." +
            "</desc>\n" + tab + tab + "</application>\n" + tab + "\t</appInfo>\n" + tab +
            "</encodingDesc>\n")


def _write_header(f, ntrans, encoding):
    """Writes the file header."""

    txt = ("<?xml version=\"1.0\" encoding=\"{}\"?>\n"  # static
           "<TEI xmlns=\"https://www.tei-c.org/ns/1.0\">\n"
           "\t<teiHeader>\n"
           .format(encoding.replace("_", "-")))
    tab = "\t\t"
    txt = txt + _write_fil_desc(ntrans, tab)  # fileDesc (name,tiers,audio)
    txt = txt + _write_pro_desc(ntrans, tab)  # profileDesc (speakers)
    txt = txt + _write_enc_desc(tab)  # encodingDesc (static)
    # Note: no <revisionDesc>
    f.write(txt + "\t</teiHeader>\n")


def _write_time_table(f, ntrans):
    """Writes the text timeline."""

    def quick_conv(ta):
        it = int(ta)
        mn, s = (it // 60), (it % 60)
        h, m = (mn // 60), (mn % 60)
        return "{:02d}:{:02d}:{:02d}".format(h, m, s)

    ttable = ntrans.timetable()
    tab = "\t\t"
    txt = ("\t<text>\n" + tab + "<timeline unit=\"ms\"")
    if not ttable:
        f.write(txt + "/>\n")
        return None
    mina = ttable[0]
    ida, i = "T0", 1
    d_timetable = {mina: ida}
    tmin = quick_conv(mina)
    txt = txt + (">\n" + tab + "\t<when absolute=\"" + tmin + "\" xml:id=\"T0\"/>\n")
    for a in range(1, len(ttable)):
        ts = ttable[a]
        ida = "T" + str(i)
        i += 1
        t = ("{:.3f}".format(ts - mina)).replace('.', '')
        txt = txt + (tab + "\t<when interval=\"" + t + "\" since=\"T0\" xml:id=\"" +
                     ida + "\"/>\n")
        d_timetable[ts] = ida
    f.write(txt + (tab + "</timeline>\n"))
    return d_timetable, ida


def _write_u(ttab, a, n, seg, s, e):
    """Starts an utterance."""
    if a > 0:
        n = n + f"{ttab}</u>\n"
    n = n + (f"{ttab}<u xml:id=\"u{a}\" " +
             f"start=\"{s}\" end=\"{e}\" " +
             f"who=\"{html.escape(seg.struct.name)}\" ")
    if seg.struct.meta('spk_id', 'tech'):
        n = n + f"ana=\"#{seg.struct.meta('spk_id', 'tech')}\" "
    n = n + f">\n{ttab}\t<speaker>{seg.struct.name.upper()}</speaker>\n"
    return a + 1, n


def _write_w(ttab, i, n, typ, s, _e, w, p, lem):
    """Writes a word."""
    n = n + f"{ttab}\t<{typ} xml:id=\"i{i}\" synch=\"{s}\" "
    if typ == "w":
        n = n + f"pos=\"{p}\" lemma=\"{lem}\" "
    n = n + f">{w}</{typ}>\n"
    return i + 1, n


def _write_body(f, ntrans, d_timetable, ida):
    """Writes the body."""

    # write body start
    tab, ttab, i = "\t\t", "\t\t\t\t", 0
    txt = (tab + "<body>\n" + tab + "\t<div subtype=\"d0\" type=\"Situation\">\n" +
           tab + tab + "<head>\n" + tab + tab + "\t<note type=\"start\">#T0</note>\n" +
           tab + tab + "\t<note type=\"end\">#" + ida + "</note>\n" + tab + tab +
           "</head>\n")
    # set structure
    l_par = []
    for tier in ntrans:
        if "[" not in tier.name:  # top (transcription) OFROM tier
            l_par.append(tier)
            continue
        n, typ = tier.name.split("[", 1)
        ptier = ntrans.getName(n)
        tier.timeParent(ptier, 0.5)
        # build dict
    d_par = {par: {} for par in l_par}
    for par in d_par:
        d_par[par] = {
            "w": ntrans.getName(par.name + "[tok_mwu]"),
            "p": ntrans.getName(par.name + "[pos_mwu]"),
            "l": ntrans.getName(par.name + "[lemma]")
        }  # hard-coded OFROM tags
        # start writing
    iw, iu = 0, 0
    l_syms = ["#", "%", "@"]
    for seg in ntrans.iterTime(l_par):
        tier = seg.struct
        s, e = d_timetable[seg.start], d_timetable[seg.end]
        iu, txt = _write_u(ttab, iu, txt, seg, s, e)  # utterance
        d_cti = d_par[tier]
        d_csegs = seg._childDict(seg.allChildren())
        try:
            l_ws = d_csegs[d_cti['w']]  # tokens
            l_ps = d_csegs[d_cti['p']]  # pos
            l_ls = d_csegs[d_cti['l']]  # lemma
        except KeyError:  # assume "%"+NOM:pro case
            continue
        for i in range(len(l_ws)):  # words (mwu)
            w, p, lem = l_ws[i], l_ps[i], l_ls[i]
            s, e = d_timetable[w.start], d_timetable[w.end]
            w, p, lem = w.content, p.content, lem.content
            typ = "w" if w not in l_syms else "pc"
            iw, txt = _write_w(ttab, iw, txt, typ, s, e, w, p, lem)
        f.write(txt)
        txt = ""
    if iu > 0:
        txt = txt + "{ttab}</u>\n"
    f.write(txt + tab + "\t</div>\n" + tab + "</body>\n\t</text>\n</TEI>")


def save_txm(path, trans, encoding, ext):
    """Exports a single Transcription into a TEI file.
    ARGUMENTS:
    - path          : (str) Full path to a directory or file.
    - trans         : (pntr) A Transcription instance.
    - encoding      : (str) The TEI file encoding.
    - ext           : (str) The TEI file extension.
    RETURNS:
    - Creates a TEI file at 'path' from 'trans'.
    Note: 'path' is tested here, everything else should be known.
    """

    # Path
    if os.path.isdir(path):  # If it's a directory
        path = os.path.join(path, trans.name + ext)  # Use 'trans.name'
    encoding = _ch_encoding(trans, encoding)  # Encoding
    ntrans = trans.copy()  # We use a copy from there

    f = open(path, 'w', encoding=encoding)  # Open file
    _write_header(f, ntrans, encoding)  # Write header
    d_timetable, ida = _write_time_table(f, ntrans)  # Write timetable
    _write_body(f, ntrans, d_timetable, ida)  # Write tiers
    f.close()  # Close file


def _save_list(path, trans, encoding, ext):
    """Exports a list of / a Corpus' transcriptions into TEI files."""
    for tr in trans:
        save_txm(path, tr, encoding, ext)

    # Main function


def to_txm(path, trans, **args):
    """Exports one or more TEIs.
    ARGUMENTS:
    - path          : (str) A full path to either a directory or a file.
    - trans         : (overloaded) A Transcription, Corpus or list of
                                   Transcriptions.
    - encoding      : (str) The file encoding.
    - ext           : (str) The file extension (default '.xml').
    RETURNS:
    - Creates the TEI(s) at 'path' from 'trans'.
    Note: Creates a copy for each Transcription while exporting."""

    # Args
    encoding = args.get('encoding')  # file encoding (for all files)
    ext = args.get('ext', '.xml')
    # Overload
    f = d_load.get(type(trans))
    if f:
        f(path, trans, encoding, ext)
    else:
        raise KeyError("First argument must be of type 'Transcription/" +
                       "/Corpus/list'.")


d_load = {Transcription: save_txm, Corpus: _save_list,
          list: _save_list}
