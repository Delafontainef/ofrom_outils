""" 18.09.2025
Une série de fonctions génériques pour les scripts d'OFROM+.
"""

# from ofrom_outils.logs.log import log
from ofrom_outils.common_types import (
    Callable, Iterator, Path, IterPath, IterCorp, MPList,
    Transcription, Tier, Segment
)
from ofrom_outils.pr.private_paths import (
    ROOT, CORE, CORP, META, sub_corpus
)
import os, re, time, subprocess
import multiprocessing as mp
import threading as thr

# Données communes #
# -----------------#
"""Constantes globales
clé         type        description
-------------------------------------------------
ROOT        Path        racine du package.
PRAAT       Path        dossier contenant Praat et ses scripts.
FFMPEG      Path        dossier contenant ffmpeg.
LOGS        Path        dossier où déposer les journaux.
CORE        Path        dossier des sous-corpus d'OFROM+.
CORP        list<str>   noms de dossier des sous-corpus.
META        Path        chemin du fichier de métadonnées.
PAUSE       str         symbole de pause d'OFROM+.
TRUNC       str         symbole de troncation d'OFROM+.
SYMS        str         symboles réservés d'OFROM+ (sauf troncation).
DFLT        str         valeur par défaut (métadonnées).
TAGS        dict        suffixes des tires d'annotation.
"""
COMMON_HOME: Path = os.path.abspath(os.path.dirname(__file__))
# ROOT                  # déjà importé de 'private_paths'
PRAAT: Path = os.path.join(ROOT, "programmes", "praat")
FFMPEG: Path = os.path.join(ROOT, "programmes", "ffmpeg", "bin")
LOGS: Path = os.path.join(ROOT, "ofrom_outils", "logs")
CORE = CORE
CORP = CORP
META = META
PAUSE: str = "_"
TRUNC: str = "-"
SYMS: str = r"[_#%@]"
DFLT: str = "NR"
TAGS: dict[str, str] = {
    'phn': "[phon]",
    'wrd': "[word]",
    'tok': "[tok_min]",
    'pos': "[pos_min]",
    'tkw': "[tok_mwu]",
    'psw': "[pos_mwu]",
    'lem': "[lemma]"
}


# sys.argv #
# ----------#
def kwarg(argv: list[str]) -> tuple[list[str], dict[str, str]]:
    """Transforme 'sys.argv' en args et kwargs."""
    args, kwargs = [], {}
    for i in range(1, len(argv)):
        k, arg = None, argv[i]
        if "=" in arg:
            k, arg = arg.split("=", 1)
        arg = arg.replace("\"", "").replace("'", "").strip()
        arg = float(arg) if re.match(r"(|-)\d+(.(|\d+)|e(|-)\d+)", arg) \
            else int(arg) if re.match(r"(|-)\d+", arg) \
            else bool(arg) if arg in ["True", "False"] \
            else None if arg == "None" else arg
        if k:
            kwargs[k] = arg
            continue
        args.append(arg)
    return args, kwargs

    # Fichiers #
    # ----------#


def fix_lext(l_ext: str | list[str] | None) -> list[str]:
    """S'assure que 'l_ext' est une liste."""

    def fix(ext: str) -> str:
        ext = "." + ext if not ext.startswith(".") else ext
        return ext.lower()

    l_ext = [".textgrid"] if l_ext is None else l_ext
    if isinstance(l_ext, list):
        return [fix(ext) for ext in l_ext]
    return [fix(l_ext)]


def iter_file(
        d: Path,
        l_ext: str | list[str] = None
) -> Iterator[IterPath]:
    """Itère de façon non-récursive sur un dossier.
       [!] Si 'l_ext' a des extensions, ne retourne que les fichiers
           avec ces extensions.
    """
    l_ext = fix_lext(l_ext)
    for file in os.listdir(d):
        fi, ext = os.path.splitext(file)
        if l_ext and ext.lower() not in l_ext:
            continue
        path = os.path.join(d, file)
        yield fi, ext, file, path


def iter_all(
        d: Path,
        l_ext: str | list[str] = None
) -> Iterator[IterPath]:
    """Itère récursivement sur un dossier.
       [!] Si 'l_ext' a des extensions, ne retourne que les fichiers
           avec ces extensions.
    """
    l_ext = fix_lext(l_ext)
    for root, dirs, files in os.walk(d):
        for file in files:
            fi, ext = os.path.splitext(file)
            if l_ext and ext.lower() not in l_ext:
                continue
            path = os.path.join(root, file)
            yield fi, ext, file, path


def iter_core(
        corp: list[str] = None,
        sub: str = "",
        l_ext: str | list[str] = None
) -> Iterator[IterCorp]:
    """Itère non-récursivement sur l'ensemble du corpus.
       - core:      (str) le dossier du corpus.
       - corp:      (list<str>) les sous-corpus à lire.
       - sub:       (str) le type de données à retourner.
       - l_ext:     (list<str>) ne retourne que les fichiers avec 
                                ces extensions.
    """
    corp = CORP if corp is None else corp
    l_ext = fix_lext(l_ext)
    for c in corp:
        sd = sub_corpus(c, sub)
        if not os.path.isdir(sd):  # ignore non-existing corpora
            continue
        for fi, ext, file, path in iter_file(sd, l_ext):
            yield c, fi, ext, file, path


def get_core(
        corp: list[str] = None,
        sub: str = "",
        l_ext: list[str] = None,
        verbose: bool = False
) -> list[Path] | list[IterCorp]:
    """Renvoie la liste de toutes les transcriptions du corpus.
       (Voir 'iter_core' pour les arguments, plus : 
        - verbose:  (bool) contient des IterCorp si vrai, sinon des Path)
    """
    corp = [] if corp is None else corp
    l_core, l_tmp, o_corp = [], [], ""
    for scorp, fi, ext, file, path in iter_core(corp, sub, l_ext):
        if scorp != o_corp:
            l_tmp.sort()
            l_core.extend(l_tmp)
            o_corp = scorp
            l_tmp = []
        if verbose:
            l_tmp.append((scorp, fi, ext, file, path))
        else:
            l_tmp.append(path)
    l_tmp.sort()
    l_core.extend(l_tmp)
    return l_core


def load_files(
        d: Path,
        l_ext: list[str] = None
) -> list[Path]:
    """Renvoie une liste de chemins."""
    l_files = [path for fi, ext, file, path in iter_file(d, l_ext=l_ext)]
    l_files.sort()
    return l_files


def ensure_outdir(d: Path) -> None:
    """S'assure que le dossier de sortie 'd' existe
       en créant chaque sous-dossier manquant dans le chemin."""
    fi, ext = os.path.splitext(os.path.basename(d))
    l_d = os.path.normpath(d).lstrip(os.path.sep).split(os.path.sep)
    l_d = l_d[:-1] if ext else l_d
    path = ""
    for sd in l_d:
        path = os.path.join(path, sd)
        if not os.path.isdir(path):
            os.mkdir(path)

    # corflow #
    # ---------#


def iter_top_tiers(tr: Transcription, spk: list | str = None) -> Iterator[Tier]:
    """
    Itère sur les tires d'une transcription.
    Ignore les tires d'annotation et si 'spk', ne lit que ce.s locuteur.s.
    """
    spk = [spk] if isinstance(spk, str) else [] if spk is None else spk
    for tier in tr:
        if ("[" in tier.name) or (spk and tier.name not in spk):
            continue
        yield tier


def iter_segs(
        tr: Transcription,
        tag: str | list[str] = TAGS['tok'],
        spk: list | str = ""
) -> Iterator[Segment]:
    """
    Itère sur les segments d'une transcription.
    Seulement les 'tag' et si 'spk', ne lit que ce locuteur.
    """
    if isinstance(spk, str):
        spk = [spk] if spk else []
    for tier in tr:
        n, t = tier.name.split("[", 1) if ("[" in tier.name) \
            else (tier.name, "")
        t = f"[{t}" if t else t
        if (tag and t not in tag) or (not tag and t):  # first check type
            continue
        if spk and n not in spk:  # then speaker
            continue
        for seg in tier:
            yield seg


def get_top_tiers(tr: Transcription, spk: list | str = None) -> list[Tier]:
    """La liste des tires de transcription."""
    return [ti for ti in iter_top_tiers(tr, spk)]


def get_spk(tr: Transcription) -> list[str]:
    """Récupère la liste des locuteurs."""
    return [ti.name for ti in iter_top_tiers(tr)]


def set_parent(tr: Transcription) -> Transcription:
    """Parente les tires selon OFROM+."""
    for ti in tr:
        pname, tag = ti.name.split("[", 1) if "[" in ti.name \
            else ti.name, ""
        if tag:
            ti.timeParent(tr.getName(pname))
    return tr

    # scripts Praat #
    # ---------------#


def call_praat(script: str, args: list[str]) -> None:
    """Appelle un script Praat depuis Python.
       - script     (str) peut être nom (sans extension) ou Path
       - args       (list<str>) liste d'arguments pour le script
    """
    praat = os.path.join(PRAAT, "Praat.exe")
    if not os.path.isfile(script):
        script = os.path.join(PRAAT, script + ".praat")
    subprocess.run([praat, '--run', script] + args)


def anon_ofrom_plus(paths: list[Path]) -> None:
    """Anonymise le fichier son.
       - paths      (list<str>) les chemins du TextGrid/WAV et 
                     le chemin du dossier où générer la sortie."""
    tgd_path, aud_path, anon_path = paths
    call_praat("anon_ofrom_plus", [aud_path, tgd_path, anon_path, "WAV",
                                   "#", "yes", "0.01", "60", "700", "0.9"])


def ph_ofrom(
        paths: list[Path],
        sym_t: str = r"[\[/]", sym_i: str = "", words: str = "0"
) -> None:
    """Annotation phonémique."""
    tgd_path, aud_path, ph_path = paths
    sym_i = SYMS if not sym_i else sym_i
    call_praat("ph_ofrom", [aud_path, tgd_path, ph_path, sym_t, sym_i, words])

    # multiprocessing #
    # -----------------#


def mp_wait(
        l_out: list[None], t: float = 0.5, timeout: float = -1.
) -> Iterator[tuple[int, int]]:
    """Vérifie toutes les 't' seconde où en est le remplissage de 'l_out'.
       Interrompt si 'timeout' est atteint (< 1. pour ignorer).
       Renvoie le nombre d'entrées non-remplies et le total."""
    ch_mp, lo, ti = 0, len(l_out), time.time()
    while True:
        ch_mp = 0
        for out in l_out:
            if out is not None:
                ch_mp += 1
        yield ch_mp, lo
        if ch_mp >= lo or (1. <= timeout <= time.time() - ti):
            break
        time.sleep(t)


def _mp_size(f: Path) -> int:
    """Renvoie la taille d'un fichier (en octets). Tient compte des tuples."""
    nf = f
    while not isinstance(nf, str):
        nf = nf[0]
    return os.stat(nf).st_size if os.path.isfile(nf) else len(nf)


def _mp_proc(
        l_proc: list[mp.Process], func: Callable,
        l_fi: list[Path], args: list
) -> list[mp.Process]:
    """Génère un sous-processus et l'ajoute à 'l_proc'.
       - l_proc     (list) la liste des sous-processus.
       - func       (function) la function à lancer.
       - l_fi       (list<str>) les chemins de fichiers pour la fonction.
       - args       (list) les autres arguments de la fonction.
       Note : 'func' devrait donc toujours avoir 'l_fi' comme premier 
              argument.
    """
    l_proc.append(mp.Process(target=func, args=[l_fi] + args))
    l_proc[-1].start()
    return l_proc


def _mp_thr(
        l_thr: list[thr.Thread], func: Callable,
        l_fi: list[Path], args: list
) -> list[thr.Thread]:
    """Voir '_mp_proc' mais pour les threads."""
    l_thr.append(thr.Thread(target=func, args=[l_fi] + args))
    l_thr[-1].start()
    return l_thr


def multiprocess(
        func: Callable,
        l_files: list[Path],
        args: list = None,
        n: int = -1, wait: bool = True
) -> None | tuple[list[mp.Process], MPList]:
    """Génère des sous-processus pour une fonction 'func' 
       avec une liste de fichiers comme premier argument.
       - func       (function) la fonction
       - l_files    (list<str>) la liste des fichiers
       - args       (list) les autres arguments de 'func'
       - n          (int) le nombre de threads/processus
       - wait       (bool) si on attend leur complétion
       Note : on divise 'l_files' en paquets pour chaque sous-processus.
       Note : si 'wait' alors on ne retourne rien.
              Sinon on renvoie la liste des processus
              et celle de sortie.
    """
    args = [] if args is None else args
    n = os.cpu_count() if n < 1 else n  # number of cores
    l_proc, max_size = [], 0  # batch size by file size
    mp_man = mp.Manager()
    l_out = mp_man.list()
    for fi in l_files:
        max_size += _mp_size(fi)
        l_out.append(None)
    l_tmp, batch_size, max_size, oi = [], 0, int(max_size / n), 0
    for i, fi in enumerate(l_files):  # process by batches
        batch_size += _mp_size(fi)
        l_tmp.append(fi)
        if batch_size >= max_size:
            l_proc = _mp_proc(l_proc, func, l_tmp, [l_out, oi] + args)
            l_tmp, batch_size, oi = [], 0, i + 1
    if l_tmp:  # last loop
        l_proc = _mp_proc(l_proc, func, l_tmp, [l_out, oi] + args)
    if wait:
        for proc in l_proc:  # wait it out
            proc.join()
        del l_proc
        return None
    else:
        return l_proc, l_out


def multithread(
        func: Callable,
        l_files: list[Path],
        args: list = None,
        n: int = -1,
        wait: bool = True
) -> None | tuple[list[thr.Thread], list]:
    """Voir 'multiprocess' mais avec des threads."""
    args = [] if args is None else args
    n = os.cpu_count() if n < 1 else n  # number of cores
    l_thr, l_out, max_size = [], [None for _ in l_files], 0
    for fi in l_files:  # get max_size (of l_files)
        max_size += _mp_size(fi)
    l_tmp, batch_size, max_size, oi = [], 0, int(max_size / n), 0
    for i, fi in enumerate(l_files):  # threads in batches
        batch_size += _mp_size(fi)
        l_tmp.append(fi)
        if batch_size >= max_size:  # full batch
            l_thr = _mp_thr(l_thr, func, l_tmp, [l_out, oi] + args)
            l_tmp, batch_size, oi = [], 0, i + 1
    if l_tmp:  # last loop
        l_thr = _mp_thr(l_thr, func, l_tmp, [l_out, oi] + args)
    if wait:
        for th in l_thr:
            th.join()
        del l_thr
        return None
    else:
        return l_thr, l_out
