""" Generates the geonames database.

Geographical data © GeoNames,
licensed under CC BY 4.0 — www.geonames.org
"""

import io
import math
import os
import sqlite3
import zipfile
from contextlib import contextmanager

import requests

from ofrom_outils.common import DATA
from ofrom_outils.common_types import Path, Iterator, Callable, Any
from ofrom_outils.db.db import read_sql
from ofrom_outils.meta.meta import Meta

GEONAME: str = "https://download.geonames.org/export/dump/"
LOCAL_DB: Path = os.path.join(DATA, "geonames.db")
DB = read_sql(os.path.join(os.path.dirname(str(__file__)), "geonames.sql"))
LTABLE = "local_geonames"
GTABLE = "remote_geonames"

ALLCOUNTRIES_COLS: dict[str, int] = {
    "geonameid": 0,
    "name": 1,
    "asciiname": 2,
    "alternatenames": 3,
    "latitude": 4,
    "longitude": 5,
    "feature_class": 6,
    "feature_code": 7,
    "country_code": 8,
    "cc2": 9,
    "admin1_code": 10,
    "admin2_code": 11,
    "admin3_code": 12,
    "admin4_code": 13,
    "population": 14,
    "elevation": 15,
    "dem": 16,
    "timezone": 17,
    "modification_date": 18,
}
ALTNAMES_COLS: dict[str, int] = {
    "alternateNameId": 0,
    "geonameid": 1,
    "isolanguage": 2,
    "alternate_name": 3,
    "isPreferredName": 4,
    "isShortName": 5,
    "isColloquial": 6,
    "isHistoric": 7,
    "from": 8,
    "to": 9,
}
ADMIN_COLS: dict[str, int] = {
    "code": 0,
    "name": 1,
    "asciiname": 2,
    "geonameid": 3
}


@contextmanager
def _open_zip_txt(zip_path: Path, filename: str) -> Iterator[io.TextIOWrapper]:
    """Pour lire un fichier 'txt' dans un zip."""
    with zipfile.ZipFile(zip_path) as zf:
        with zf.open(filename, "r") as raw:
            with io.TextIOWrapper(raw, encoding="utf-8") as rf:
                yield rf


def _iter_geo(zip_path: Path, filename: str) -> Iterator[dict[str, str]]:
    """
    Pour itérer sur un fichier 'zip' (contenant un 'txt') ligne par ligne.
    Transforme chaque ligne en dictionnaire.
    """
    select_cols = {
        'allCountries.txt': ALLCOUNTRIES_COLS,
        'alternateNamesV2.txt': ALTNAMES_COLS,
    }
    cols: dict[str, int] = select_cols[filename]

    with _open_zip_txt(zip_path, filename) as rf:
        for line in rf:
            split_line = line.rstrip("\n").split("\t")
            yield {name: split_line[i] for name, i in cols.items()}


@contextmanager
def _open_connection(
        conn: sqlite3.Connection | None = None
) -> Iterator[tuple[sqlite3.Connection, sqlite3.Cursor]]:
    if conn is not None:
        yield conn, conn.cursor()
        return

    local_conn = sqlite3.connect(LOCAL_DB)
    try:
        yield local_conn, local_conn.cursor()
    finally:
        local_conn.close()


def _check_admin(fr: str) -> str:
    """Retirer les 'républiques' et 'cantons'."""
    if not fr.lower().startswith(
            ("république", "canton", "région", "département", "district")
    ):
        return fr
    fr = fr.rsplit(" ", 1)[1]
    return fr.split("d'", 1)[1] if fr.startswith("d'") else fr


def _get_french_names(alternate_file: Path) -> dict[str, str]:
    """Récupère les noms français d'à peu près tout, par geonameid."""
    if not os.path.isfile(alternate_file):
        return {}
    french_geonames = {}
    with _open_zip_txt(alternate_file, "alternateNamesV2.txt") as rf:
        for line in rf:
            row = line.rstrip("\n").split("\t")
            if (row[ALTNAMES_COLS["isolanguage"]] != 'fr' or
                row[ALTNAMES_COLS["isPreferredName"]]) != '1':
                continue
            fr = row[ALTNAMES_COLS["alternate_name"]]
            french_geonames[row[ALTNAMES_COLS["geonameid"]]] = \
                _check_admin(fr)
    return french_geonames


def _download_file(
        geo_path: Path,
        local_path: Path,
        replace: bool = False
) -> None:
    """Fonction tierce pour 'download_geonames'."""
    if (not replace) and os.path.isfile(local_path):
        return
    with requests.get(geo_path, stream=True) as response:
        response.raise_for_status()

        with open(local_path, mode="wb") as wbf:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    wbf.write(chunk)


def download_geonames(
        list_files: list[str] | None = None,
        replace: bool = False
) -> list[Path]:
    """
    Télécharge les fichiers de GeoNames.
    Retourne la liste des chemins
    """
    if not os.path.isdir(DATA):
        os.mkdir(DATA)
    if list_files is None:  # default values
        list_files = [
            "allCountries.zip",
            "alternateNamesV2.zip",
            "admin1CodesASCII.txt",
            "admin2Codes.txt",
            "countryInfo.txt"
        ]
    list_paths: list[Path] = []
    for i, file in enumerate(list_files):
        geo_path = os.path.join(GEONAME, file)
        local_path = os.path.join(DATA, file)
        _download_file(geo_path, local_path, replace)
        list_paths.append(local_path)
    return list_paths


def _get_admin_geoids(admin_file: Path) -> dict[str, str]:
    """Fonction tierce pour 'get_location_dict'."""
    if not os.path.isfile(admin_file):
        return {}
    admin_geoids = {}
    with (open(admin_file, "r", encoding="utf-8") as rf):
        for line in rf:
            row = line.rstrip("\n").split("\t")
            admin_geoids[row[ADMIN_COLS["code"]]] = \
                row[ADMIN_COLS["geonameid"]]
    return admin_geoids


def _get_country_geoids(country_file: Path) -> dict[str, str]:
    """Fonction tierce pour 'get_location_dict'."""
    if not os.path.isfile(country_file):
        return {}
    country_geoids = {}
    with (open(country_file, "r", encoding="utf-8") as rf):
        header = rf.readline().strip("\n")
        while not header.startswith("#ISO"):
            header = rf.readline().strip("\n")
            if not header:
                raise ValueError(
                    (f"Invalid country info file: "
                     "'#ISO' header not found in {country_file}")
                )
        header = {k: i for i, k in enumerate(header.split("\t"))}
        for line in rf:
            row = line.rstrip("\n").split("\t")
            country_geoids[row[header["#ISO"]]] = row[header["geonameid"]]
    return country_geoids


LOCATION_FUNC: dict[str, tuple[str, Callable]] = {
    "pays": ("countryInfo.txt", _get_country_geoids),
    "region": ("admin1CodesASCII.txt", _get_admin_geoids),
    "departement": ("admin2Codes.txt", _get_admin_geoids),
}


def get_location_dict(
        loc: str = "pays",
        french_geonames: dict[str, str] | None = None
) -> dict[str, str]:
    """
    Renvoie un dict' de lieux par code, traduits.
    type: 'country', 'region', 'departement'
    """
    file, f = LOCATION_FUNC.get(loc, ("", None))
    if not f:
        raise ValueError(
            f"Unsupported location file: {loc}. "
            f"Expected one of: {', '.join(LOCATION_FUNC)}"
        )
    if french_geonames is None:
        french_geonames = _get_french_names(
            os.path.join(DATA, "alternateNamesV2.zip")
        )
    geoids_dict = f(os.path.join(DATA, file))
    location_dict = {}
    for code, geoid in geoids_dict.items():
        location_dict[code] = french_geonames.get(geoid, "")
    return location_dict


def create_database(
        conn: sqlite3.Connection | None = None,
        table: str = "remote_geonames"
) -> None:
    """Crée la base de données"""
    with _open_connection(conn) as (local_conn, cursor):
        cursor.execute(DB['create'].format(table=table))
        local_conn.commit()


def _score_geonames(row) -> int:
    feature_class = row['feature_class']
    feature_code = row['feature_code']
    pop = int(row['population'])
    if feature_class != 'P' or pop <= 0:
        return -10
    feature_score = {
        "PPLC": 100,  # capital
        "PPLA": 90,  # first-order admin seat
        "PPLA2": 80,
        "PPLA3": 70,
        "PPLA4": 60,
        "PPL": 50,  # populated place
    }
    return round((feature_score.get(feature_code, 40)
                  + math.log10(pop + 1)) * 10)


def _vacuum_database(
        conn: sqlite3.Connection | None = None,
        table: str = "remote_geonames"
) -> None:
    """
    Nettoie la base de données.
    Retire les doublons régionaux, puis 'vacuum' l'ensemble.
    """
    with _open_connection(conn) as (local_conn, cursor):
        cursor.execute(DB['vacuum'].format(table=table))
        local_conn.commit()
        cursor.execute("VACUUM")
        local_conn.commit()


def fill_local(
        conn: sqlite3.Connection | None = None,
        table: str = "local_geonames"
) -> None:
    """
    Remplit la base de données depuis le metadata.
    Pour chaque transcription, ajoute le lieu si données complètes.
    """
    meta = Meta()
    meta.load()
    locs = {}
    for tr, spk, mspk in meta.iter_spk():
        nom = mspk['domicile_jeunesse']
        dept = mspk['departement']
        region = mspk['region']
        pays = mspk['pays']
        lon = mspk['longitude']
        lat = mspk['latitude']
        if lon and lon != "NR":
            locs[nom] = (nom, dept, region, pays, lon, lat, 1000)
    locs = list(locs.values())
    with _open_connection(conn) as (local_conn, cursor):
        cursor.executemany(DB['insert'].format(table=table), locs)
        local_conn.commit()
    _vacuum_database(conn, table)


def fill_remote(
        conn: sqlite3.Connection | None = None,
        table: str = "remote_geonames"
) -> None:
    """
    Remplit la base de données depuis GeoNames.
    1. Récupère les dictionnaires (pays, région, département)
    2. Pour chaque ligne de 'allCountries', l'ajoute à la db.
    """
    french_geonames = _get_french_names(
        os.path.join(DATA, "alternateNamesV2.zip")
    )
    country_dict = get_location_dict("pays", french_geonames)
    region_dict = get_location_dict("region", french_geonames)
    dept_dict = get_location_dict("departement", french_geonames)
    with _open_connection(conn) as (local_conn, cursor):
        cursor.execute(DB['exists'].format(table=table))
        if cursor.fetchone() is None:
            create_database(local_conn, table)

        locs = []
        local_conn.execute("PRAGMA journal_mode = MEMORY")
        for row in _iter_geo(os.path.join(DATA, "allCountries.zip"),
                             "allCountries.txt"):
            score = _score_geonames(row)
            if score < 0:
                continue
            code_d = row["admin2_code"]
            code_r = row["admin1_code"]
            code_c = row["country_code"]
            code_r = ".".join([code_c, code_r]) if code_r else ""
            code_d = ".".join([code_r, code_d]) if code_r and code_c else ""
            locs.append((
                french_geonames.get(row["geonameid"], row["name"]),
                dept_dict.get(code_d, ""),
                region_dict.get(code_r, ""),
                country_dict.get(code_c, ""),
                row["latitude"],
                row["longitude"],
                score
            ))
            if len(locs) >= 10000:
                cursor.executemany(DB['insert'].format(table=table), locs)
                local_conn.commit()
                locs.clear()
        if len(locs) > 0:  # last loop
            cursor.executemany(DB['insert'].format(table=table), locs)
            local_conn.commit()

    _vacuum_database(conn, table)


def create_index(
        conn: sqlite3.Connection | None = None,
        table: str = "remote_geonames"
) -> None:
    """Fonction à part pour créer l'index de la base de données."""
    with _open_connection(conn) as (local_conn, cursor):
        cursor.execute(DB['index'].format(table=table))
        local_conn.commit()


def rebuild_database(clear: bool = False) -> None:
    if os.path.isfile(LOCAL_DB):
        os.remove(LOCAL_DB)
    with _open_connection() as (local_conn, cursor):
        create_database(local_conn, GTABLE)
        fill_remote(local_conn, GTABLE)
        create_index(local_conn, GTABLE)
        create_database(local_conn, LTABLE)
        fill_local(local_conn, LTABLE)
        create_index(local_conn, LTABLE)
    if clear:
        for file in os.listdir(DATA):
            path = os.path.join(DATA, file)
            if os.path.isdir(path) or os.path.samefile(path, LOCAL_DB):
                continue
            os.remove(path)


def _build_select(
        name: str,
        department: str,
        region: str,
        country: str,
        table: str = "remote_geonames"
) -> tuple[str, list[str]]:
    """Retourne la requête SQL ('select') et ses paramètres."""
    select = DB['select'].format(table=table)
    params = [name]
    for pname, pval in [
        ("departement", department),
        ("region", region),
        ("pays", country)
    ]:
        if pval:
            select = select + "\n" + DB['select_a'].format(col=pname)
            params += [pval]
    return select, params

def get_raw_geoname(
        name: str,
        department: str = "",
        region: str = "",
        country: str = "",
        conn: sqlite3.Connection | None = None,
        table: str = "remote_geonames"
) -> list[tuple[str, str, str, str, float, float]] | None:
    """Récupère un lieu dans une table de la db."""
    sql, params = _build_select(name, department, region, country, table)
    with _open_connection(conn) as (local_conn, cursor):
        db_data = cursor.execute(sql, params).fetchall()
        return db_data


def get_geoname(
        name: str,
        department: str = "",
        region: str = "",
        country: str = "",
        conn: sqlite3.Connection | None = None
) -> dict[str, Any]:
    """Récupère un lieu dans la db, retourne son dictionnaire."""
    keys = ("nom", "departement", "region", "pays", "lon", "lat")
    sql, params = _build_select(name, department, region, country, LTABLE)
    with _open_connection(conn) as (local_conn, cursor):
        db_data = cursor.execute(sql, params).fetchall()
        if not db_data:
            sql, params = _build_select(
                name, department, region, country, GTABLE
            )
            db_data = cursor.execute(sql, params).fetchall()
    result = max(db_data, key=lambda x: x[-1], default=None)
    return dict(zip(keys, result[1:-1])) if result else {}

if "__main__" == __name__:
    # rebuild_database()
    print(get_geoname("Yverdon"))
