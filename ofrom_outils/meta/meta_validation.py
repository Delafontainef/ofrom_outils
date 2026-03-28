import datetime
import re

from openpyxl.cell.cell import Cell

from ofrom_outils.common import DFLT
from ofrom_outils.common_types import Any, Callable
from ofrom_outils.meta.meta_models import ModelVVal, ModelVCell

"""Constantes globales
clé         type        description
-------------------------------------------------
CELL_R      str         regex par défaut pour filtrer le contenu des cellules
CELL_D      str         format de date d'OFROM+
CELL_Y      str         format de date pour l'année seulement.
Note : dictionnaires (de fonctions) en fin de fichier. 
"""
CELL_R = r"[\w\-,;:/. ]+"
CELL_D = "%Y-%m-%d"
CELL_Y = "%Y"


# Fonctions de Validation #
# -------------------------#
def _cmsg(cell: Cell) -> str:
    """Affiche les informations de la cellule en texte."""
    return (f"{cell.parent.title} ({cell.column}{cell.row})"
            if cell else "- (--)")


def _vmsg(val: Any) -> str:
    """Affiche les informations de la valeur en texte."""
    return f"'{val}' ({type(val)})"


def val_to_str(val: Any = "") -> str:
    """Transforme toute valeur en 'string'."""
    return str(val) if not isinstance(val, str) else val


def str_to_regex(val: str, r: re.Pattern = None) -> str:
    """Retire tout symbole non-autorisé via une expression régulière."""
    r = re.compile(CELL_R) if not r else r
    return "".join(r.findall(val)).strip()


def regex_to_list(val: str = "", l: list[str] = None) -> str:
    """Vérifie si la valeur est dans la liste."""
    l = [] if l is None else l
    return "" if val not in l else val


def regex_to_date(val: str = "", strf: str = CELL_D) -> str:
    """
    Vérifie le format de date.
    Le contenu ayant déjà été transformé en texte (string), 
    on doit d'abord reconvertir en 'datetime'.
    """
    if " " in val:  # remove hh:mm:ss
        val = val.split(" ", 1)[0]
    val = val.replace(".", "-").replace("/", "-").strip()
    l_fmt = [
        "%d-%m-%Y", "%d-%m-%y", "%m-%d-%Y", "%m-%d-%y",
        "%Y-%m-%d", "%y-%m-%d", "%Y"
    ]  # date formats (avoids 'dateutil' library)
    for fmt in l_fmt:
        try:
            parsed = datetime.datetime.strptime(val, fmt)
            return parsed.strftime(strf)
        except ValueError:
            continue
    return ""  # invalid date, to default

    # Fonctions principales #
    # -----------------------#


def str_val(val, r: str = CELL_R, dflt: str = DFLT):
    """
    Gère les valeurs devant contenir du texte.
    Élimine les caractères ne correspondant pas à l'expression régulière.
    """
    v = str_to_regex(val_to_str(val), re.compile(r))
    return v if v else dflt


def list_val(val, l: list[str], dflt: str = DFLT):
    """
    Gère les valeurs avec un contenu contraint (liste).
    """
    v = regex_to_list(str_to_regex(val_to_str(val)), l)
    return v if v else dflt


def date_val(val, strf: str, dflt: str = DFLT):
    """
    Gère les valeurs avec une date.
    """
    v = regex_to_date(str_to_regex(val_to_str(val)), strf)
    return v if v else dflt

    # Wrappers #
    # ----------#


"""Constantes globales
D_VAL       dict        fonction par nom de métadonnée
D_CVAL      dict        (legacy) fonction par type de donnée
"""
D_VAL: dict[str, tuple[Callable, str | list[str]]] = {
    'statut': (
        list_val, ["Prêt", "EnCours", "Res1", "Res2", "Res3", "Res4"]
    ),
    'sous-corpus': (str_val, "[\\w\\-, ]+"),
    'date_enregistrement': (date_val, CELL_D),
    'reviseur_1_date': (date_val, CELL_D),
    'reviseur_2_date': (date_val, CELL_D),
    'nb_mots': (str_val, r"^[+-]?\d+$"),
    'duree': (str_val, r"^[+-]?(\d+\.\d+)$"),
    'qualite': (list_val, ["bonne", "moyenne", "mauvaise"]),
    'sexe': (list_val, ["F", "H", "A"]),
    'age': (str_val, r"^[+-]?\d+$"),
    'annee_naissance': (date_val, CELL_Y),
    'habite_depuis': (date_val, CELL_Y),
    'langage': (list_val, ["Français L1", "Français L2"]),
    'niveau_socioeducatif': (
        list_val, [
        "Scolarité obligatoire", "Maturité, apprentissage",
        "Formation supérieure"
    ]
    ),
    'role': (list_val, ["Témoin", "Enquêteur", "Enquêteur-interactant"]),
    'longitude': (str_val, r"^[+-]?(\d+\.\d+)$"),
    'latitude': (str_val, r"^[+-]?(\d+\.\d+)$"),
    'extr_deb': (str_val, r"^[+-]?(\d+\.\d+)$"),
    'extr_fin': (str_val, r"^[+-]?(\d+\.\d+)$")
}
D_CVAL: dict[str, tuple[Callable, str | list[str]]] = {
    'str': (str_val, CELL_R),
    'list': (list_val, []),
    'date': (date_val, CELL_D),
    'int': (str_val, r"^[+-]?\d+$"),
    'float': (str_val, r"^[+-]?(\d+\.\d+)$")
}


class VVal(ModelVVal):
    """Wrapper autour d'une cellule pour lui intégrer un validateur."""

    def __init__(self, val: Any, k: str = "", dflt: str = DFLT):
        self.val = val
        vfun, arg = D_VAL.get(k, D_CVAL['str'])  # default case
        self.vfun = vfun  # validation function
        self.args = [arg, dflt]  # function arguments

    @property
    def value(self):
        try:
            return self.vfun(self.val, *self.args)
        except Exception as e:
            raise Exception(f"{_vmsg(self.val)}: {e}") from e

    @value.setter
    def value(self, val):
        try:
            self.val = self.vfun(val, *self.args)
        except Exception as e:
            raise Exception(f"{_vmsg(self.val)}: {e}") from e


class VCell(ModelVCell):
    """Wrapper autour d'une cellule pour lui intégrer un validateur."""

    def __init__(self, cell: Cell, k: str = "", dflt: str = DFLT):
        if not isinstance(cell, Cell):  # runtime type check
            raise TypeError(f"{cell} is not a Cell.")
        self.cell = cell
        vfun, arg = D_VAL.get(k, D_CVAL['str'])  # default case
        self.vfun = vfun  # validation function
        self.args = [arg, dflt]  # function arguments

    @property
    def value(self):
        try:
            return self.vfun(self.cell.value, *self.args)
        except Exception as e:
            raise Exception(f"{_cmsg(self.cell)}: {e}") from e

    @value.setter
    def value(self, val):
        try:
            self.cell.value = self.vfun(val, *self.args)
        except Exception as e:
            raise Exception(f"{_vmsg(self.cell.value)}: {e}") from e
