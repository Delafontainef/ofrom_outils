import io
import os
import sqlite3
import tempfile
import unittest
import zipfile
from unittest.mock import MagicMock, patch

from ofrom_outils.meta.meta_geonames import (
    _open_zip_txt, _open_connection, _download_file, download_geonames,
    _get_admin_geoids, _get_country_geoids, _get_french_names,
    get_location_dict, create_database, fill_database, create_index,
    rebuild_database
)

MOCK_GEONAME: str = "https://example.com/"


class OpenZipTxt(unittest.TestCase):

    def test_open_zip_txt(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            zip_path = os.path.join(temp_dir, "test.zip")

            with zipfile.ZipFile(zip_path, "w") as zf:
                zf.writestr(
                    "test.txt",
                    "first line\nsecond line\n"
                )

            with _open_zip_txt(zip_path, "test.txt") as rf:
                self.assertEqual(
                    rf.readlines(),
                    ["first line\n", "second line\n"]
                )


class DownloadFiles(unittest.TestCase):
    @patch("ofrom_outils.meta.meta_geonames.requests.get")
    def test_download_single_file(self, mock_get):
        response = MagicMock()
        response.iter_content.return_value = [b"abc", b"def"]
        mock_get.return_value.__enter__.return_value = response

        with tempfile.TemporaryDirectory() as temp_dir:
            local_path = os.path.join(temp_dir, "test.zip")

            _download_file(
                os.path.join(MOCK_GEONAME, 'test.zip'),
                local_path
            )
            with open(local_path, "rb") as rf:
                self.assertEqual(rf.read(), b"abcdef")

        response.raise_for_status.assert_called_once()
        response.iter_content.assert_called_once_with(
            chunk_size=1024 * 1024
        )

    @patch("ofrom_outils.meta.meta_geonames.requests.get")
    def test_download_single_file_exists(self, mock_get):
        response = MagicMock()
        response.iter_content.return_value = [b"abc", b"def"]
        mock_get.return_value.__enter__.return_value = response

        with tempfile.TemporaryDirectory() as temp_dir:
            local_path = os.path.join(temp_dir, "test.zip")
            with open(local_path, "wb") as wf:
                wf.write(b"original")

            _download_file(
                os.path.join(MOCK_GEONAME, 'test.zip'),
                local_path,
                replace=False
            )
            with open(local_path, "rb") as rf:
                self.assertEqual(rf.read(), b"original")
            mock_get.assert_not_called()

            _download_file(
                os.path.join(MOCK_GEONAME, 'test.zip'),
                local_path,
                replace=True
            )
            with open(local_path, "rb") as rf:
                self.assertEqual(rf.read(), b"abcdef")

    @patch("ofrom_outils.meta.meta_geonames.GEONAME", MOCK_GEONAME)
    @patch("ofrom_outils.meta.meta_geonames._download_file")
    def test_download_from_geonames(self, mock_download):
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch(
                    "ofrom_outils.meta.meta_geonames.LOCAL_GEO_DIR", temp_dir):
                result = download_geonames([
                    'allCountries.zip',
                    'alternateNamesV2.zip'
                ])

                self.assertEqual(result, [
                    os.path.join(temp_dir, "allCountries.zip"),
                    os.path.join(temp_dir, "alternateNamesV2.zip"),
                ])

                self.assertTrue(os.path.isdir(temp_dir))

                self.assertEqual(mock_download.call_count, 2)

                mock_download.assert_any_call(
                    os.path.join(MOCK_GEONAME, "allCountries.zip"),
                    os.path.join(temp_dir, "allCountries.zip"),
                    False,
                )

                mock_download.assert_any_call(
                    os.path.join(MOCK_GEONAME, "alternateNamesV2.zip"),
                    os.path.join(temp_dir, "alternateNamesV2.zip"),
                    False,
                )


@patch("ofrom_outils.meta.meta_geonames.ALTNAMES_COLS", {
    "geonameid": 0,
    "isolanguage": 1,
    "alternate_name": 2,
})
class GetCountryDict(unittest.TestCase):

    def test_get_admin_geoids(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            admin_file = os.path.join(temp_dir, "admin2Codes.txt")

            with open(admin_file, "w", encoding="utf-8") as wf:
                wf.write((
                    "FR.11\tthis-place\tthis-place\t1000001\n"
                    "FR.18\tthat-place\tthat-place\t1000002\n"
                ))

            result = _get_admin_geoids(admin_file)

            self.assertEqual(result, {
                "FR.11": "1000001",
                "FR.18": "1000002",
            })

    def test_get_country_geoids(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            country_file = os.path.join(temp_dir, "countryInfo.txt")

            with open(country_file, "w", encoding="utf-8") as wf:
                wf.write((
                    "# comment\n"
                    "# another comment\n"
                    "#ISO\tCountry\tgeonameid\n"
                    "FR\tFrance\t3017382\n"
                    "DE\tGermany\t2921044\n"
                ))

            result = _get_country_geoids(country_file)

            self.assertEqual(result, {
                "FR": "3017382",
                "DE": "2921044",
            })

    def test_get_country_geoids_missing_file(self):
        result = _get_country_geoids("does_not_exist.txt")
        self.assertEqual(result, {})

    def test_get_country_geoids_wrong_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            country_file = os.path.join(temp_dir, "countryInfo.txt")

            with open(country_file, "w", encoding="utf-8") as wf:
                wf.write((
                    "# comment\n"
                    "FR\tFrance\t3017382\n"
                    "DE\tGermany\t2921044\n"
                ))

            with self.assertRaises(ValueError):
                _get_country_geoids(country_file)

    @patch("ofrom_outils.meta.meta_geonames.os.path.isfile")
    @patch("ofrom_outils.meta.meta_geonames._open_zip_txt")
    def test_get_french_names(self, mock_open_zip, mock_isfile):
        mock_isfile.return_value = True
        content = (
            "3017382\tfr\tFrance\n"
            "2921044\tde\tDeutschland\n"
            "2921044\tfr\tAllemagne\n"
        )

        mock_open_zip.return_value.__enter__.return_value = io.StringIO(content)

        result = _get_french_names("alternateNamesV2.zip")

        self.assertEqual(result, {
            "3017382": "France",
            "2921044": "Allemagne",
        })

        mock_open_zip.assert_called_once_with(
            "alternateNamesV2.zip",
            "alternateNamesV2.txt"
        )

    @patch("ofrom_outils.meta.meta_geonames.os.path.isfile")
    def test_get_french_names_missing(self, mock_isfile):
        mock_isfile.return_value = False
        self.assertEqual(
            _get_french_names("missing.zip"),
            {}
        )

    @patch("ofrom_outils.meta.meta_geonames._get_french_names")
    @patch("ofrom_outils.meta.meta_geonames._get_country_geoids")
    def test_get_location_dict(self, mock_loc, mock_names):
        mock_loc.return_value = {
            "FR": "3017382",
            "DE": "2921044",
            "CH": "2658434",
        }

        mock_names.return_value = {
            "3017382": "France",
            "2921044": "Allemagne",
            "1000001": "this-place",
            "1000002": "that-place",
        }

        with patch.dict(
                "ofrom_outils.meta.meta_geonames.LOCATION_FUNC",
                {"pays": ("countryInfo.txt", mock_loc)}
        ):
            result = get_location_dict()

        self.assertEqual(result, {
            "FR": "France",
            "DE": "Allemagne",
            "CH": "",
        })

        mock_loc.return_value = {
            "FR.11": "1000001",
            "FR.18": "1000002",
            "FR.42": "1000003",
        }

        with patch.dict(
                "ofrom_outils.meta.meta_geonames.LOCATION_FUNC",
                {"region": ("admin1CodesASCII.txt", mock_loc)}
        ):
            result = get_location_dict('region')

        self.assertEqual(result, {
            "FR.11": "this-place",
            "FR.18": "that-place",
            "FR.42": "",
        })


class TestOpenConnection(unittest.TestCase):

    def test_uses_provided_connection(self):
        conn = sqlite3.connect(":memory:")

        with _open_connection(conn) as (local_conn, cursor):
            self.assertIs(local_conn, conn)
            self.assertIsInstance(cursor, sqlite3.Cursor)

        conn.execute("SELECT 1")
        conn.close()

    @patch("ofrom_outils.meta.meta_geonames.sqlite3.connect")
    def test_creates_and_closes_connection(self, mock_connect):
        mock_conn = MagicMock(spec=sqlite3.Connection)
        mock_cursor = MagicMock(spec=sqlite3.Cursor)

        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        with _open_connection() as (local_conn, cursor):
            self.assertIs(local_conn, mock_conn)
            self.assertIs(cursor, mock_cursor)

        mock_connect.assert_called_once()
        mock_conn.close.assert_called_once_with()


@patch.dict("ofrom_outils.meta.meta_geonames.ALLCOUNTRIES_COLS", {
    "geonameid": 0,
    "name": 1,
    "admin1_code": 2,
    "admin2_code": 3,
    "country_code": 4,
    "latitude": 5,
    "longitude": 6,
}, clear=True)
class TestDatabase(unittest.TestCase):

    def setUp(self):
        self.conn = sqlite3.connect(":memory:")

    def tearDown(self):
        self.conn.close()

    def test_create_database_tables_exists(self):
        create_database(self.conn)
        cursor = self.conn.cursor()
        cursor.execute("""
                       SELECT name
                       FROM sqlite_master
                       WHERE type = 'table'
                         AND name IN (
                                      'locations',
                                      'pays',
                                      'regions',
                                      'departements'
                           )
                       """)
        tables = {row[0] for row in cursor.fetchall()}
        self.assertEqual(
            tables,
            {"locations", "pays", "regions", "departements"},
        )

    def test_create_database_columns(self):
        create_database(self.conn)
        cursor = self.conn.cursor()
        cursor.execute("PRAGMA table_info(locations)")

        columns = [row[1] for row in cursor.fetchall()]

        self.assertEqual(
            columns,
            [
                "geonameid",
                "nom",
                "code_dept",
                "code_region",
                "code_pays",
                "latitude",
                "longitude",
            ],
        )

    def test_create_index(self):
        create_database(self.conn)
        create_index(self.conn)
        cursor = self.conn.cursor()
        cursor.execute("""
                       SELECT name
                       FROM sqlite_master
                       WHERE type = 'index'
                         AND name = 'idx_locations_nom'
                       """)

        self.assertIsNotNone(cursor.fetchone())

    @patch("ofrom_outils.meta.meta_geonames.create_database",
           wraps=create_database)
    @patch("ofrom_outils.meta.meta_geonames.get_location_dict")
    @patch("ofrom_outils.meta.meta_geonames._open_zip_txt")
    def test_fill_database(self, mock_zip, mock_dict, mock_create):
        mock_dict.side_effect = [
            {"FR": "France"},
            {"FR.11": "Île-de-France"},
            {"FR.11.75": "Paris"},
        ]

        mock_zip.return_value.__enter__.return_value = [
            "10000024\tParis\t11\t75\tFR\t48.8566\t2.3522\n"
        ]

        fill_database(self.conn)

        row = self.conn.execute(
            "SELECT nom, code_pays, latitude, longitude "
            "FROM locations"
        ).fetchone()
        country = self.conn.execute(
            "SELECT nom "
            "FROM pays"
        ).fetchone()
        region = self.conn.execute(
            "SELECT nom "
            "FROM regions"
        ).fetchone()
        dept = self.conn.execute(
            "SELECT nom "
            "FROM departements"
        ).fetchone()
        print(region)
        print(dept)

        self.assertEqual(
            row,
            ("Paris", "FR", 48.8566, 2.3522),
        )
        self.assertEqual(
            country,
            ('France',)
        )
        self.assertEqual(
            region,
            ("Île-de-France",)
        )
        self.assertEqual(
            dept,
            ("Paris",)
        )
        mock_create.assert_called_once_with(self.conn)

    @patch("ofrom_outils.meta.meta_geonames.create_database",
           wraps=create_database)
    @patch("ofrom_outils.meta.meta_geonames.get_location_dict")
    @patch("ofrom_outils.meta.meta_geonames._open_zip_txt")
    def test_fill_database_no_creation(self, mock_zip, mock_dict, mock_create):
        mock_dict.side_effect = [
            {"FR": "France"},
            {"FR.11": "Île-de-France"},
            {"FR.11.75": "Paris"},
        ]

        mock_zip.return_value.__enter__.return_value = [
            "10000024\tParis\t11\t75\tFR\t48.8566\t2.3522\n"
        ]
        create_database(self.conn)
        mock_create.reset_mock()
        fill_database(self.conn)

        row = self.conn.execute(
            "SELECT nom, code_dept, latitude, longitude "
            "FROM locations"
        ).fetchone()

        self.assertEqual(
            row,
            ("Paris", "75", 48.8566, 2.3522),
        )
        mock_create.assert_not_called()

    @patch("ofrom_outils.meta.meta_geonames.LOCAL_DB")
    @patch("ofrom_outils.meta.meta_geonames.sqlite3.connect")
    @patch("ofrom_outils.meta.meta_geonames.create_database")
    @patch("ofrom_outils.meta.meta_geonames.fill_database")
    @patch("ofrom_outils.meta.meta_geonames.create_index")
    def test_rebuild_database(
            self,
            mock_index,
            mock_fill,
            mock_create,
            mock_connect,
            mock_local_db
    ):
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        rebuild_database()

        mock_connect.assert_called_once_with(mock_local_db)
        mock_create.assert_called_once_with(mock_conn)
        mock_fill.assert_called_once_with(mock_conn)
        mock_index.assert_called_once_with(mock_conn)
        mock_conn.close.assert_called_once()

    ## LACKS 'get_geoname' test

if __name__ == '__main__':
    unittest.main()
