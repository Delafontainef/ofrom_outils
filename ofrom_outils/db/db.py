import os
from ofrom_outils.common_types import Path


NAME = "-- name: "
CH = "*/"


def _check_line(
        line: str,
        key: str,
        value: str,
        data: dict[str, str]
) -> tuple[str, str, dict[str, str]]:
    """Fonction de soutien pour 'read_db'."""
    l = line.strip()
    if not l: # nothing
        return key, value, data
    if l.startswith(NAME): # nouvelle fonction
        if key and value:
            data[key] = value.rstrip()
        key = l.split(NAME, 1)[1]
        value = ""
    elif l.endswith(CH): # commentaire multiligne
        value = ""
    else: # code SQL
        value += line
    return key, value, data

def read_sql(f: Path) -> dict[str, str]:
    """Lit des commandes SQL et les retourne sous forme de dictionnaire."""
    if not os.path.isfile(f):
        return {}
    key, value, data = "", "", {}
    with open(f, mode="r", encoding="utf-8") as rf:
        for line in rf:
            key, value, data = _check_line(line, key, value, data)
    if key and value:
        data[key] = value.rstrip()
    return data

