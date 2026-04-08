""" 15.06.2025

Permet de convertir les fichiers sonores.
Permet aussi de modifier le volume sonore.
Permet également de tronquer les fichiers sonores (legacy).

Conversion
    - fonction 'all_audio_convert()'
    - paramètres : 
    | - indir:  (str) dossier d'entrée, contenant audios à convertir
    | - outdir: (str) dossier de sortie, par défaut le même qu'à l'entrée
    | - typ:    (str) le format vers lequel convertir (voir D_F)
    |                 ("wav", "mp3", "m4a")
    | - rem:    (bool) s'il faut supprimer les fichiers d'origine
    | - ch_all: (bool) si on convertit même les fichiers déjà au format
    - par terminal : 
      'python audio.py convert "path/to/audio" typ=wav'
      Supporte args et kwargs (voir 'args()').
Volume:
    - fonction 'all_audio_mean()'
    - paramètres : 
    | - indir:  (str) dossier d'entrée, contenant audios à balancer
    | - outdir: (str) dossier de sortie, par défaut le même qu'à l'entrée
    | - rem:    (bool) s'il faut supprimer les fichiers d'origine
    - par terminal :
      'python audio.py mean r"path\to\audio" rem=True'

Note: ffmpeg est un exécutable local, à mettre à jour, seulement pour Windows.
Note: Normalement sécurisé mais préférer convertir vers un dossier à part,
      avec rem=False
"""

import os
import re
import subprocess
import sys
import tempfile

from ofrom_outils.common import CORE, FFMPEG, kwarg, iter_all
from ofrom_outils.common_types import (Callable, Path)
from ofrom_outils.logs.log import log

"""Constantes globales
clé         type        description
-------------------------------------------------
L_EXT       list<str>   formats gérés (extensions de fichier).
FFP         Path        chemin de ffprobe.
FFM         Path        chemin de ffmpeg.
"""
L_EXT = ['.wma', '.mp3', '.wav', '.m4a', '.opus', '.ogg']
FFP = os.path.join(FFMPEG, 'ffprobe.exe')
FFM = os.path.join(FFMPEG, 'ffmpeg.exe')

type ProbeResult = dict[str, int | float]
type AudioLevel = tuple[list[str | float], float, float]


# General functions #
# ----------------- #

def clean_ext(path: Path) -> Path:
    """Ne conserve que la dernière extension."""
    d, file = os.path.split(path)
    fi, o_ext = os.path.splitext(file)
    ch = True if fi.startswith(".") else False
    fi = fi[1:] if ch else fi
    while "." in fi:
        fi, ext = os.path.splitext(fi)
        if "." not in fi:
            break
    fi = "." + fi if ch else fi
    npath = os.path.join(d, fi + o_ext)
    if path == npath:
        return npath
    os.replace(path, npath)
    return npath


def check(
        fi: str, _ext: str, file: str, path: Path
) -> tuple[bool, str, str, str, Path]:
    """Vérifie si la conversion est possible."""
    # static check
    path = clean_ext(path)  # new path
    _, ext = os.path.splitext(path)  # new extension
    if (not os.path.isfile(path)) or (ext.lower() not in L_EXT):
        return False, fi, ext, file, path
    return True, fi, ext, file, path  # all good


def probe(path: Path, ch_all: bool = False) -> ProbeResult:
    """Vérifie le contenu d'un fichier."""

    def get_arg(txt: str, arg: str) -> str:
        if arg not in txt:
            return "-1"
        t_arg = txt.split(arg, 1)[1]
        return t_arg.split("\n", 1)[0]

    def read_md(d_ares: ProbeResult) -> ProbeResult:
        res = subprocess.run([FFP, "-hide_banner", "-loglevel",
                              "error", "-show_streams", "-i", path],
                             capture_output=True)
        res = res.stdout.decode("utf-8")
        d_ares['duration'] = float(get_arg(res, "duration="))
        d_ares['channel'] = int(get_arg(res, "channels="))
        d_ares['sample_rate'] = int(get_arg(res, "sample_rate="))
        return d_ares

    def read_all(d_ares: ProbeResult) -> ProbeResult:
        res = subprocess.Popen([FFM, "-i", path, "-f", "null", "-"],
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        txt = res.stdout.read().decode("utf-8")
        txt = txt.split("Duration: ", 1)[1].split("Stream mapping", 1)[0]
        dur = txt.split(",", 1)[0]
        l_dur = dur.split(":")
        l_dur.append("")
        l_dur[2], l_dur[3] = l_dur[2].split(".")
        l_dur.reverse()
        for a, d in enumerate(l_dur):
            mult = 60 ** (a - 1) if a >= 1 else 0.01
            d_ares['duration'] += float(d) * mult
        rate = txt.split(" Hz", 1)[0]
        rate = rate.rsplit(", ", 1)[1]
        d_ares['sample_rate'] = int(rate)
        if "channels" in txt:
            chan = txt.split(" channels", 1)[0]
            d_ares['channel'] = int(chan.rsplit(" ", 1)[1])
        else:
            d_ares['channel'] = 1 if " mono" in txt else 2
        return d_ares

    d_res = {'channel': 0, 'sample_rate': 0, 'duration': 0.}
    if ch_all:
        return read_all(d_res)
    else:
        return read_md(d_res)

    # Conversion utility functions #
    # ------------------------------#


def _new_ext(path: Path, new_ext: str = ".wav") -> Path:
    """Attribue la nouvelle extension."""
    p, ext = os.path.splitext(path)
    return p + new_ext


def _to_time(s: float) -> str:
    """Un datetime.strftime du pauvre."""
    h = s // 3600
    s = s % 3600
    m = s // 60
    s = s % 60
    return f"{h:02n}:{m:02n}:{s:06.3f}"


def setup_conv(
        path: Path, npath: Path, ext: str, ch_ar: int = 44100
) -> tuple[Path, str, str, dict[str, int | float]]:
    """Prépare les valeurs pour la conversion."""
    npath = _new_ext(path, ext) if not npath else npath
    ac, ar = "1", "44100"  # nb_channels, sample_rate
    d_md = probe(path)  # check audio metadata
    d_md['channel'] = 1
    if 0 < ch_ar < d_md['sample_rate']:  # keep Hz under threshold
        d_md['sample_rate'] = ch_ar
    ar = str(d_md['sample_rate'])
    return npath, ac, ar, d_md


def _subp(
        path: Path,
        npath: Path,
        ext: str,
        argsa: list,
        rem: bool = True
) -> Path:
    """Force la conversion. Supprime l'ancien fichier si 'rem==True'."""
    if not npath:
        npath = _new_ext(path, ext)
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp_file:
        tmp = tmp_file.name
    try:
        argsa.append(tmp)
        subprocess.run(
            argsa,
            shell=False, stdout=None, stderr=None
        )
        os.replace(tmp, npath)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)
    if os.path.isfile(npath) and rem and os.path.isfile(path):
        os.remove(path)
    return npath

    # Audio volume #
    # --------------#


def audio_level(path: Path) -> tuple[float, float]:
    """Renvoie le volume moyen/maximum d'un fichier en dB."""
    res = subprocess.run(f"{FFM} -i \"{path}\" " +
                         "-af volumedetect -f null /dev/null",
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    res = res.stdout.decode("utf-8")
    m_vol = re.search(r"mean_volume:\s*(-?\d+\.?\d*) dB", res)
    max_vol = re.search(r"max_volume:\s*(-?\d+\.?\d*) dB", res)
    m_vol = float(m_vol.group(1)) if m_vol else None
    max_vol = float(max_vol.group(1)) if max_vol else None
    return m_vol, max_vol


def all_audio_level(
        path: Path,
        ch_file: str = "", ch_all: bool = False,
        verbose: bool = True
) -> AudioLevel:
    """Vérifie le volume audio d'une série de fichiers."""
    l_ch, g_mean = [], 0.
    for fi, ext, file, path in iter_all(path, l_ext=L_EXT):  # check all files
        ch, fi, ext, file, path = check(fi, ext, file, path)  # conditions
        if not ch:
            continue
        log(fi, verbose=verbose)
        mean_vol, max_vol = audio_level(path)
        g_mean += mean_vol
        l_ch.append((fi, path, mean_vol, max_vol))
    lc, l_out = len(l_ch), []
    if lc == 0:  # nothing to process
        return l_out, 0., 0.
    g_mean, sd = g_mean / lc, 0.
    for fi, path, mean_vol, max_vol in l_ch:  # deviation
        sd = sd + ((mean_vol - g_mean) ** 2)
    sd = (sd / lc) ** (1 / 2)
    for fi, path, mean_vol, max_vol in l_ch:  # outliers
        if mean_vol < (g_mean - sd):
            l_out.append((fi, "LOW", mean_vol, g_mean, sd))
        elif mean_vol > (g_mean + sd):
            l_out.append((fi, "HIGH", mean_vol, g_mean, sd))
        elif ch_all:
            l_out.append((fi, "-", mean_vol, g_mean, sd))
    if ch_file:
        with open(ch_file, "w", encoding="utf-8") as f:
            f.write("nb;file;type;file_mean;global_mean;deviation\n")
            f.write(f"0;Global;None;{g_mean};{g_mean};{sd}\n")
            for a, tup in enumerate(l_out):
                f.write(f"{a + 1};{tup[0]};{tup[1]};{tup[2]};{tup[3]};"
                        f"{tup[4]}\n")
    return l_out, g_mean, sd


def audio_mean(
        path: Path, npath: Path,
        mean: float, g_mean: float, ext: str, rem: bool = True
) -> None:
    """Change le volume d'un fichier audio à 'mean'."""
    n_path, ac, ar, d_md = setup_conv(path, npath, ext, 44100)
    dif = (mean - g_mean) * -1
    _subp(path, n_path, os.path.splitext(path)[1],
          [FFM, "-hide_banner", "-stats", "-loglevel", "error", "-y",
           "-i", path, "-filter:a", f"volume={dif}dB"], rem)


def all_audio_mean(
        path: Path, npath: Path,
        l_out: None | str | list = None,
        mean: None | float = None,
        rem: bool = True, verbose: bool = True, **_kwargs
) -> None:
    """Lance 'audio_mean' sur les fichiers de 'path' correspondant à 'l_out'."""

    def to_list(of: Path) -> list[tuple[str, str, float, float, float]]:
        l_res = []
        wf, che = open(of, "r", encoding="utf-8"), False
        for line in wf:
            if (not che) and line.startswith("1"):
                che = True
            elif not che:
                continue
            tup = line.strip("\n").replace(",", ".").split(";")
            l_res.append((tup[1], tup[2], float(tup[3]), float(tup[4]),
                          float(tup[5])))
        wf.close()
        return l_res

    d_out = {}
    if isinstance(l_out, str):  # file to list
        l_out = to_list(l_out)
    elif l_out is None:
        l_out = all_audio_level(path)[0]
    for fi, mes, mean_vol, g_mean, sd in l_out:  # fit l_out in d_out
        d_out[fi] = (mean_vol, g_mean)
    for fi, ext, file, path in iter_all(path):  # process
        ch, fi, ext, file, path = check(fi, ext, file, path)
        if (not ch) or (fi not in d_out):
            continue
        log(fi, verbose=verbose)
        mean_vol, g_mean = d_out[fi]
        if mean:
            g_mean = mean
        audio_mean(path, os.path.join(npath, file), mean_vol, g_mean, ext, rem)

    # Audio cut #
    # -----------#


def audio_cut(path: Path, npath: Path, s: float, e: float) -> None:
    """(Legacy) Découpe le son avec ffmpeg."""
    ns, ne = _to_time(s), _to_time(e)
    log(f"{s}, {e}, {ns}, {ne}")
    _subp(path, npath, os.path.splitext(path)[1],
          [FFM, "-hide_banner", "-stats", "-loglevel", "error", "-y",
           "-i", path, "-ss", f"{ns}", "-to", f"{ne}"], False)

    # Format conversion #
    # -------------------#


def to_mp3(
        path: Path, npath: Path = "", rem: bool = True, _ch_all: bool = True
) -> Path:
    """Convertit en MP3."""
    npath, ac, ar, d_md = setup_conv(path, npath, ".mp3", 44100)
    return _subp(path, npath, ".mp3", [FFM, "-hide_banner", "-stats",
                                       "-loglevel", "error", "-y", "-i", path,
                                       "-vn", "-qscale:a",
                                       "2"], rem)


def to_wav(
        path: Path, npath: Path = "", rem: bool = True, ch_all: bool = True
) -> Path | None:
    """
    Convertit en WAV.
    - 'path':   (str) le fichier d'entrée.
    - 'npath':  (str) le fichier de sortie.
    - 'rem':    (bool) conserver ou non le fichier d'entrée.
    - 'ch_all': (bool) convertir tous les fichiers.
    """
    npath, ac, ar, d_md = setup_conv(path, npath, ".wav", 44100)
    if not ch_all and os.path.isfile(npath):  # already there
        d_md = probe(npath)
        if d_md['channel'] == 1 and d_md['sample_rate'] <= 44100:
            return None
    return _subp(path, npath, ".wav", [FFM, "-hide_banner", "-stats",
                                       "-loglevel", "error", "-y", "-i", path,
                                       "-vn", "-ac", ac,
                                       "-ar", ar, "-sample_fmt", "s16"], rem)


def to_m4a(
        path: Path, npath: Path = "", rem: bool = True, _ch_all: bool = True
) -> Path:
    """Convertit en M4A."""
    npath, ac, ar, d_md = setup_conv(path, npath, ".wav", 44100)
    return _subp(path, npath, ".m4a", [FFM, "-hide_banner", "-stats",
                                       "-loglevel", "error", "-y", "-i", path,
                                       "-vn", "-ac", ac,
                                       "-ar", ar], rem)


D_F = {"wav": (to_wav, ".wav"),
       "mp3": (to_mp3, ".mp3"),
       "m4a": (to_m4a, ".m4a")}


def all_audio_convert(
        path: Path = "", npath: Path = "",
        typ: str = "wav", rem: bool = False, ch_all: bool = False,
        verbose: bool = True
) -> None:
    """
    Convertit dans le format 'typ'.
    - 'path':   (str) le dossier d'entrée.
    - 'npath':  (str) le dossier de sortie.
    - 'typ':    (str) le format de sortie.
    - 'rem':    (bool) conserver ou non le fichier d'entrée.
    - 'ch_all': (bool) convertir tous les fichiers.
    """
    path = CORE if not path else path
    npath = path if not npath else npath
    for fi, ext, file, path in iter_all(path, l_ext=[]):
        ch, fi, ext, file, path = check(fi, ext, file, path)  # conditions
        if not ch:
            continue
            # main task
        out_tmp: str = os.path.dirname(npath)
        f, n_ext = D_F.get(typ)
        log(path, "\n", verbose)
        f(path, os.path.join(out_tmp, fi + n_ext), rem, ch_all)


def args(argv: list[str]) -> tuple[Callable, dict[str, str]]:
    """Gère sys.argv."""
    d_func = {
        "mean": all_audio_mean,
        "convert": all_audio_convert
    }  # function keys
    d_args = {
        'function': "convert",
        'indir': "", 'outdir': "",
        'typ': "wav", 'rem': False, 'ch_all': False
    }  # default parameters
    argsa, kwargsa = kwarg(argv)
    la = len(argsa)
    for i, k in enumerate(d_args):  # user-defined parameters
        if k in kwargsa:
            d_args[k] = kwargsa[k]
        elif i < la:
            d_args[k] = argsa[i]
    funca = d_args.pop('function')
    funca = d_func[funca] if funca in d_func else None
    d_args['path'] = d_args.pop('indir')  # key renaming
    d_args['npath'] = d_args.pop('outdir')
    return funca, d_args


if __name__ == "__main__":
    func, kwargs = args(sys.argv)
    if func is None:  # manual code here...
        sys.exit()
    elif not os.path.isdir(kwargs['path']):  # invalid path
        log(f"Missing arguments.\nindir='{kwargs['path']}'\n" +
            f"outdir='{kwargs['npath']}'", end="\n")
        sys.exit()
    elif not os.path.isdir(kwargs['npath']):  # same folder
        kwargs['npath'] = kwargs['path']
    func(**kwargs)  # function call
