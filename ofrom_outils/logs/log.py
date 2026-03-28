import os
import sys

from ofrom_outils.common_types import IO


def log(txt: str, end: str = " " * 40 + "\r", verbose: bool = True):
    """Quand on veut juste 'print' dans la console."""
    if verbose:
        print(txt, end=end)


def _w(txt: str, wf: IO | None = None) -> None:
    """Écrit dans un fichier/terminal."""
    wf = sys.stdout if wf is None else wf
    wf.write(txt)
    wf.flush()


class Log:
    """Pour quand les 'print' ne suffisent pas...
       Log.log() gère l'écriture en terminal, en fichier et en GUI.
       - prt()   pour les terminaux
       - write() pour les fichiers
       Les deux ont les mêmes arguments (que GUI devrait imiter) :
       - txt     (str) le texte à écrire/afficher
       - mode    (str) 'a' pour ajouter, 'w' pour réécrire, 'clear' pour vider.
       Note : 'print(..., end=' '*40+'\r')' suffit généralement,
              'Log' est surtout là pour le GUI.
       Note : requiert de lire le buffer IO, donc peut causer des erreurs.
    """

    def __init__(self):
        self.cursor = [1, 0]  # cursor start at line-1, column-0
        self.file_path = ""  # path to a log file
        self.pyw = None  # object to write to
        self._setwu()  # cross-platform library setup

        # Support #
        # ---------#

    def _setwu(self) -> None:
        """Sélectionne la librairie pour le terminal."""
        if os.name == "nt":
            import msvcrt
            self.msvcrt = msvcrt
        else:
            import tty, termios
            self.tty, self.termios = tty, termios

    def _readw(self) -> str:
        """Lit le buffer (Windows)."""
        buf = ''
        while True:
            ch = self.msvcrt.getwch()
            buf += ch
            if ch == 'R':
                break
        return buf

    def _readu(self) -> str:
        """Lit le buffer (Linux, etc.)."""
        fd = sys.stdin.fileno()
        old_s = self.termios.tcgetattr(fd)
        try:
            self.tty.setcbreak(fd)
            buf = ''
            while True:
                ch = sys.stdin.read(1)
                buf += ch
                if ch == 'R':
                    break
        finally:
            self.termios.tcsetattr(fd, self.termios.TCSADRAIN, old_s)
        return buf

    def update(self) -> list[int]:
        """Retourne la position du curseur sur le terminal."""
        _w("\x1b[6n")
        try:
            f = self._readw if os.name == "nt" else self._readu
            _, pos = f().split("[")
            row, col = map(int, pos[:-1].split(";"))
            self.cursor = [row, max(0, col - 1)]
        except (ImportError, ValueError, OSError):
            pass
        return self.cursor

    @staticmethod
    def move(line: int, col: int) -> None:
        """Déplace le curseur à la position (1-based)."""
        _w(f"\x1b[{line};{col + 1}H")

    @staticmethod
    def clear() -> None:
        """Retire le texte après le curseur."""
        _w("\x1b[J")

        # Main #
        # ------#

    def prt(self, txt: str, mode: str = "a") -> None:
        """
        Écrit selon le mode:
        - 'a' pour ajouter
        - 'w' pour réécrire
        - 'clear' pour vider
        """
        if mode == "clear":  # clear the terminal
            os.system("cls" if os.name == "nt" else "clear")
            self.cursor = [1, 0]
            return
        if mode == "w":  # overwrite
            self.move(*self.cursor)
            self.clear()
        _w(txt)
        if mode == "a":  # append
            self.update()

    def write(self, txt: str, mode: str = "a") -> None:
        """Écrit dans  'file_path' with a mode:
           - 'a' to append
           - 'w' to overwrite"""
        with open(self.file_path, mode=mode, encoding="utf-8") as wf:
            wf.write(txt)

    def log(self,
            txt: str, pyw: object | str | None = None, mode: str = "a"
            ) -> None:
        """Écrit dans 'pyw'.
           - txt        (str) le texte à écrire/afficher.
           - pyw        (None)   le terminal
                        (str)    un fichier
                        (object) une instance, p.ex. GUI...
           - mode       (str) le mode d'écriture, qui dépend de 'pyw'.
        """
        pyw = self.pyw if (pyw is None) else pyw  # try instance object
        pyw = self.prt if (pyw is None) else pyw  # default to terminal
        if isinstance(pyw, str):  # file log case
            self.file_path = pyw if pyw else self.file_path
            pyw = self.write
        try:
            pyw(txt, mode=mode)
        except Exception as e:
            _w(f"Failed to log {txt}: {e}\n", wf=sys.stderr)
