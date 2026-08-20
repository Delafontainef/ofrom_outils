""" Generates the geonames database.

Geographical data © GeoNames,
licensed under CC BY 4.0 — www.geonames.org
"""

import io, os
import requests
import zipfile
from contextlib import contextmanager

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
    "country": ("countryInfo.txt", _get_country_geoids),
    "region": ("admin1CodesASCII.txt", _get_admin_geoids),
    "departement": ("admin2Codes.txt", _get_admin_geoids),
}


def get_location_dict(
        loc: str = "country",
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


if __name__ == "__main__":
    download_geonames()
    country_dict = get_location_dict('countryInfo.txt')

# def create_database() -> bool:
#     sql_connection = sqlite3.connect("geonames.db")
#     cur = sql_connection.cursor()
#
#     cur.execute("""
#                 CREATE TABLE IF NOT EXISTS locations
#                 (
#                     geonameid INTEGER PRIMARY KEY,
#                     name VARCHAR(200),
#                     latitude REAL,
#                     longitude REAL,
#                     country_code TEXT,
#                     admin1 VARCHAR(20),
#                     admin2 VARCHAR(80),
#                     admin3 VARCHAR(20),
#                     admin4 VARCHAR(20),
#                 )
#                 """)
