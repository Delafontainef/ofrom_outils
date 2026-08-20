""" Generates the geonames database.

Geographical data © GeoNames,
licensed under CC BY 4.0 — www.geonames.org
"""

import io
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
            if row[ALTNAMES_COLS["isolanguage"]] != 'fr':
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
            CREATE TABLE pays
            (
                code VARCHAR(20) PRIMARY KEY,
                nom  VARCHAR(80)
            )
            """)

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS regions
            (
                code_pays VARCHAR(20),
                code      VARCHAR(20),
                nom       VARCHAR(80),
                PRIMARY KEY (code_pays, code)
            )
            """)

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS departements
            (
                code_pays    VARCHAR(20),
                code_region  VARCHAR(20),
                code         VARCHAR(20),
                nom          VARCHAR(80),
                PRIMARY KEY (code_pays, code_region, code)
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS locations
            (
                geonameid   INTEGER PRIMARY KEY,
                nom         VARCHAR (200),
                code_dept   VARCHAR(20),
                code_region VARCHAR(20),
                code_pays   VARCHAR(20),
                latitude    FLOAT,
                longitude   FLOAT,
                FOREIGN KEY (code_pays)
                    REFERENCES pays(code),

                FOREIGN KEY (code_pays, code_region)
                    REFERENCES regions(code_pays, code),

                FOREIGN KEY (code_pays, code_region, code_dept)
                    REFERENCES departements(code_pays, code_region, code)
            )
            """
        )
        local_conn.commit()


def fill_database(conn: sqlite3.Connection = None) -> None:
    """
    Remplit la base de données.
    1. Récupère les dictionnaires (pays, région, département)
    2. Pour chaque ligne de 'allCountries', l'ajoute à la db.
    """
    with _open_connection(conn) as (local_conn, cursor):
        cursor.execute("""
                       SELECT name
                       FROM sqlite_master
                       WHERE type = 'table'
                         AND name = 'locations'
                       """)
        if cursor.fetchone() is None:
            create_database(local_conn)

        french_geonames = _get_french_names(
            os.path.join(LOCAL_GEO_DIR, "alternateNamesV2.zip")
        )
        country_dict = get_location_dict("pays", french_geonames)
        region_dict = get_location_dict("region", french_geonames)
        dept_dict = get_location_dict("departement", french_geonames)
        country_tuples = []
        for country_code, country_name in country_dict.items():
            country_tuples.append((country_code, country_name))
        cursor.executemany(
            """
            INSERT INTO pays
                (code, nom)
            VALUES (?, ?)
            """,
            country_tuples,
        )
        local_conn.commit()
        region_tuples = []
        for region_code, region_name in region_dict.items():
            country_code, region_code = region_code.split(".")
            region_tuples.append((country_code, region_code, region_name))
        cursor.executemany(
            """
            INSERT INTO regions
                (code_pays, code, nom)
            VALUES (?, ?, ?)
            """,
            region_tuples,
        )
        local_conn.commit()
        dept_tuples = []
        for dept_code, dept_name in dept_dict.items():
            country_code, region_code, dept_code = dept_code.split(".")
            dept_tuples.append(
                (country_code, region_code, dept_code, dept_name)
            )
        cursor.executemany(
            """
            INSERT INTO departements
                (code_pays, code_region, code, nom)
            VALUES (?, ?, ?, ?)
            """,
            dept_tuples,
        )
        local_conn.commit()
        del country_dict
        del region_dict
        del dept_dict
        del country_tuples
        del region_tuples
        del dept_tuples

        locs = []
        with _open_zip_txt(os.path.join(LOCAL_GEO_DIR, "allCountries.zip"),
                           "allCountries.txt") as rf:
            for line in rf:
                row = line.rstrip("\n").split("\t")
                locs.append((
                    french_geonames.get(row[ALLCOUNTRIES_COLS["geonameid"]],
                                        row[ALLCOUNTRIES_COLS["name"]]),
                    row[ALLCOUNTRIES_COLS["admin2_code"]],
                    row[ALLCOUNTRIES_COLS["admin1_code"]],
                    row[ALLCOUNTRIES_COLS["country_code"]],
                    row[ALLCOUNTRIES_COLS["latitude"]],
                    row[ALLCOUNTRIES_COLS["longitude"]]
                ))
                if len(locs) >= 10000:
                    cursor.executemany(
                        """
                        INSERT INTO locations
                        (nom,
                         code_dept,
                         code_region,
                         code_pays,
                         latitude,
                         longitude)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        locs,
                    )
                    local_conn.commit()
                    locs.clear()
        if len(locs) > 0:  # last loop
            cursor.executemany(
                """
                INSERT INTO locations
                (nom,
                 code_dept,
                 code_region,
                 code_pays,
                 latitude,
                 longitude)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                locs,
            )
            local_conn.commit()


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


def rebuild_database() -> None:
    gconn = sqlite3.connect(LOCAL_DB)
    create_database(gconn)
    fill_database(gconn)
    create_index(gconn)
    gconn.close()


def get_geoname(
        name: str,
        region: str = None,
        department: str = None,
        country: str = None,
        conn: sqlite3.Connection = None
) -> list[tuple[str, str, str, str, float, float]] | None:
    """Récupère les informations d'un lieu dans la db."""
    select = [
        "SELECT l.*",
        "FROM locations AS l",
    ]
    where = ["l.nom = ?"]
    params = [name]

    if country is not None:
        select += [
            "JOIN pays AS p",
            "  ON p.code = l.code_pays",
        ]
        where.append("p.nom LIKE ?")
        params.append(f"%{country}%")

    if region is not None:
        select += [
            "JOIN regions AS r",
            "  ON r.code_pays = l.code_pays",
            " AND r.code = l.code_region",
        ]
        where.append("r.nom LIKE ?")
        params.append(f"%{region}%")

    if department is not None:
        select += [
            "JOIN departements AS d",
            "  ON d.code_pays = l.code_pays",
            " AND d.code_region = l.code_region",
            " AND d.code = l.code_dept",
        ]
        where.append("d.nom LIKE ?")
        params.append(f"%{department}%")

    select.append("WHERE " + " AND ".join(where))

    with _open_connection(conn) as (local_conn, cursor):
        sql_data = cursor.execute("\n".join(select), params).fetchall()
        return_data = []
        for dat in sql_data:
            code_dept = dat[2]
            code_region = dat[3]
            code_pays = dat[4]
            pays = cursor.execute(
                "SELECT nom FROM pays WHERE code = ?",
                (code_pays,),
            ).fetchone()
            pays = pays[0] if pays else ""
            region = cursor.execute(
                """
                SELECT nom
                FROM regions
                WHERE code_pays = ?
                  AND code = ?
                """,
                (code_pays, code_region),
            ).fetchone()
            region = region[0] if region else ""
            dept = cursor.execute(
                """
                SELECT nom
                FROM departements
                WHERE code_pays = ?
                  AND code_region = ?
                  AND code = ?
                """,
                (code_pays, code_region, code_dept),
            ).fetchone()
            dept = dept[0] if dept else ""

            return_data.append({
                'geonameid': dat[0],
                'nom': dat[1],
                'dept': dept,
                'region': region,
                'pays': pays,
                'latitude': dat[5],
                'longitude': dat[6],
            })

        return return_data


