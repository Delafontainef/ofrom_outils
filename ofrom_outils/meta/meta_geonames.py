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

from ofrom_outils.common_types import Path, Iterator, Callable

GEONAME: str = "https://download.geonames.org/export/dump/"
META_HOME: Path = os.path.abspath(os.path.dirname(__file__))
LOCAL_GEO_DIR: Path = os.path.join(META_HOME, "geonames")
LOCAL_DB: Path = os.path.join(LOCAL_GEO_DIR, "geonames.db")

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
            french_geonames[row[ALTNAMES_COLS["geonameid"]]] = \
                row[ALTNAMES_COLS["alternate_name"]]
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
        list_files: list[str] = None,
        replace: bool = False
) -> list[Path]:
    """
    Télécharge les fichiers de GeoNames.
    Retourne la liste des chemins
    """
    if not os.path.isdir(LOCAL_GEO_DIR):
        os.mkdir(LOCAL_GEO_DIR)
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
        local_path = os.path.join(LOCAL_GEO_DIR, file)
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
        french_geonames: dict[str, str] = None
) -> dict[str, str]:
    """
    Renvoie un dict' de lieux par code, traduits.
    type: 'country', 'region', 'departement'
    """
    file, f = LOCATION_FUNC.get(loc, None)
    if not f:
        raise ValueError(
            f"Unsupported location file: {loc}. "
            f"Expected one of: {', '.join(LOCATION_FUNC)}"
        )
    if french_geonames is None:
        french_geonames = _get_french_names(
            os.path.join(LOCAL_GEO_DIR,
                         "alternateNamesV2.zip")
        )
    geoids_dict = f(os.path.join(LOCAL_GEO_DIR, file))
    location_dict = {}
    for code, geoid in geoids_dict.items():
        location_dict[code] = french_geonames.get(geoid, "")
    return location_dict


def create_database(conn: sqlite3.Connection = None) -> None:
    """Crée la base de données"""
    with _open_connection(conn) as (local_conn, cursor):
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS locations
            (
                geonameid   INTEGER PRIMARY KEY,
                nom         VARCHAR(200),
                departement VARCHAR(20),
                region      VARCHAR(20),
                pays        VARCHAR(20),
                latitude    FLOAT,
                longitude   FLOAT,
                score       INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        local_conn.commit()


def _score_geonames(row) -> float:
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


def _vacuum_database(conn: sqlite3.Connection = None) -> None:
    """
    Nettoie la base de données.
    Retire les doublons régionaux, puis 'vacuum' l'ensemble.
    """
    with _open_connection(conn) as (local_conn, cursor):
        cursor.execute(
            """
            DELETE FROM locations
            WHERE geonameid IN (
                SELECT geonameid
                FROM (
                         SELECT geonameid,
                                ROW_NUMBER() OVER (
                            PARTITION BY nom, departement, region, pays
                            ORDER BY score DESC
                        ) AS rn
                         FROM locations
                     )
                WHERE rn > 1
            )
            """
        )
        local_conn.commit()
        cursor.execute("VACUUM")
        local_conn.commit()


def fill_database(conn: sqlite3.Connection = None) -> None:
    """
    Remplit la base de données.
    1. Récupère les dictionnaires (pays, région, département)
    2. Pour chaque ligne de 'allCountries', l'ajoute à la db.
    """
    sql = """
          INSERT INTO locations
              (nom, departement, region, pays, latitude, longitude, score)
          VALUES (?, ?, ?, ?, ?, ?, ?)
          """
    french_geonames = _get_french_names(
        os.path.join(LOCAL_GEO_DIR, "alternateNamesV2.zip")
    )
    country_dict = get_location_dict("pays", french_geonames)
    region_dict = get_location_dict("region", french_geonames)
    dept_dict = get_location_dict("departement", french_geonames)
    with _open_connection(conn) as (local_conn, cursor):
        cursor.execute("""
                       SELECT name
                       FROM sqlite_master
                       WHERE type = 'table'
                         AND name = 'locations'
                       """)
        if cursor.fetchone() is None:
            create_database(local_conn)

        locs = []
        local_conn.execute("PRAGMA journal_mode = MEMORY")
        for row in _iter_geo(os.path.join(LOCAL_GEO_DIR, "allCountries.zip"),
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
                cursor.executemany(sql, locs, )
                local_conn.commit()
                locs.clear()
        if len(locs) > 0:  # last loop
            cursor.executemany(sql, locs, )
            local_conn.commit()

    _vacuum_database(conn)


def create_index(conn: sqlite3.Connection = None) -> None:
    """Fonction à part pour créer l'index de la base de données."""
    ch_conn = conn is not None
    local_conn = sqlite3.connect(LOCAL_DB) if conn is None else conn
    cursor = local_conn.cursor()

    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_locations_nom ON locations(nom)"
    )

    local_conn.commit()
    if not ch_conn:
        local_conn.close()


def rebuild_database(clear: bool = False) -> None:
    gconn = sqlite3.connect(LOCAL_DB)
    create_database(gconn)
    fill_database(gconn)
    create_index(gconn)
    gconn.close()
    if clear:
        for file in os.listdir(LOCAL_GEO_DIR):
            path = os.path.join(LOCAL_GEO_DIR, file)
            if os.path.isdir(path) or os.path.samefile(path, LOCAL_DB):
                continue
            os.remove(path)


def get_raw_geoname(
        name: str,
        department: str = None,
        region: str = None,
        country: str = None,
        conn: sqlite3.Connection = None
) -> list[tuple[str, str, str, str, float, float]] | None:
    """Récupère les informations d'un lieu dans la db."""
    select = [
        "SELECT *",
        "FROM locations",
        "WHERE nom = ?"
    ]
    params = [name]
    for pname, pval in [
        ("departement", department),
        ("region", region),
        ("pays", country)
    ]:
        if pval is not None:
            select += [f"AND {pname} = ?"]
            params += [pval]

    with _open_connection(conn) as (local_conn, cursor):
        db_data = cursor.execute("\n".join(select), params).fetchall()
        return db_data

