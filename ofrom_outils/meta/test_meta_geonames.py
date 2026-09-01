import io
import math
import os
import sqlite3
import tempfile
import unittest
import zipfile
from unittest.mock import MagicMock, patch, call

from ofrom_outils.meta.meta_geonames import (
    DB, _open_zip_txt, _iter_geo, _open_connection, _download_file,
    download_geonames,
    _get_admin_geoids, _get_country_geoids, _check_admin,
    _get_french_names, _score_geonames, _vacuum_database,
    get_location_dict, create_database, fill_local, fill_remote, create_index,
    rebuild_database, _build_select, get_raw_geoname, get_geoname
)

MOCK_GEONAME: str = "https://example.com/"


class TestOpenZipTxt(unittest.TestCase):

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


class TestIterGeo(unittest.TestCase):
    @patch("ofrom_outils.meta.meta_geonames.ALLCOUNTRIES_COLS", {
        "geonameid": 0, "name": 1
    })
    @patch("ofrom_outils.meta.meta_geonames._open_zip_txt")
    def test_iter_geo(self, mock_open_zip_txt):
        mock_open_zip_txt.return_value.__enter__.return_value = io.StringIO(
            "123\tParis\tParis\t48.8534\t2.3488\n"
            "888\tVevey\tSoleure\t6.777\t-48.3\n"
        )

        result = list(_iter_geo("dummy.zip", "allCountries.txt"))

        self.assertEqual(
            result,
            [
                {"geonameid": "123", "name": "Paris"},
                {"geonameid": "888", "name": "Vevey"},
            ],
        )


class TestDownloadFiles(unittest.TestCase):
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
                    "ofrom_outils.meta.meta_geonames.DATA", temp_dir):
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
    "isPreferredName": 3
})
class TestGetCountryDict(unittest.TestCase):

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


    def test_check_admin(self):
        for k, v in [
            ("Canton de Genève", "Genève"),
            ("République du Congo", "Congo"),
            ("Canton d'Argovie", "Argovie"),
            ("Paris", "Paris")
        ]:

            self.assertEqual(
                _check_admin(k),
                v
            )

    @patch("ofrom_outils.meta.meta_geonames.os.path.isfile")
    @patch("ofrom_outils.meta.meta_geonames._open_zip_txt")
    def test_get_french_names(self, mock_open_zip, mock_isfile):
        mock_isfile.return_value = True
        content = (
            "3017382\tfr\tFrance\t1\n"
            "2921044\tde\tDeutschland\t1\n"
            "2921044\tfr\tAllemagne\t1\n"
            "3017382\tfr\tItalie\t0\n"
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


class TestScoreGeonames(unittest.TestCase):
    def test_non_populated_place(self):
        row = {
            "feature_class": "A",
            "feature_code": "PPLC",
            "population": "1_000_000",
        }
        self.assertEqual(_score_geonames(row), -10)

    def test_known_feature_code(self):
        row = {
            "feature_class": "P",
            "feature_code": "PPLA2",
            "population": "999",
        }
        self.assertEqual(
            _score_geonames(row),
            (80 + math.log10(1000)) * 10,
        )

    def test_unknown_feature_code(self):
        row = {
            "feature_class": "P",
            "feature_code": "PPLX",
            "population": "1",
        }
        self.assertEqual(_score_geonames(row), 403)


class TestVacuumDatabase(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.table = "test"
        self.conn.execute("""
                          CREATE TABLE test
                          (
                              geonameid   INTEGER PRIMARY KEY,
                              nom         TEXT,
                              departement TEXT,
                              region      TEXT,
                              pays        TEXT,
                              score       INTEGER
                          )
                          """)

    def tearDown(self):
        self.conn.close()

    def test_vacuum_database_keeps_highest_score(self):
        self.conn.executemany(
            """
            INSERT INTO test
                (geonameid, nom, departement, region, pays, score)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (1, "Paris", "Paris", "Île-de-France", "France", 50),
                (2, "Paris", "Paris", "Île-de-France", "France", 100),
                (3, "Paris", "Paris", "Île-de-France", "France", 70),
                (4, "Paris", "", "Texas", "USA", 60),
            ],
        )
        self.conn.commit()

        _vacuum_database(self.conn, self.table)

        rows = self.conn.execute(
            "SELECT geonameid FROM test ORDER BY geonameid"
        ).fetchall()

        self.assertEqual(rows, [(2,), (4,)])


@patch.dict("ofrom_outils.meta.meta_geonames.ALLCOUNTRIES_COLS", {
    "geonameid": 0,
    "name": 1,
    "admin1_code": 2,
    "admin2_code": 3,
    "country_code": 4,
    "latitude": 5,
    "longitude": 6,
    "feature_class": 7,
    "feature_code": 8,
    "population": 9,
}, clear=True)
class TestDatabase(unittest.TestCase):

    def setUp(self):
        self.conn = sqlite3.connect(":memory:")

    def tearDown(self):
        self.conn.close()

    def test_create_database_table_exists(self):
        create_database(self.conn, "test")
        cursor = self.conn.cursor()
        cursor.execute("""
                       SELECT name
                       FROM sqlite_master
                       WHERE type = 'table'
                       """)
        tables = {row[0] for row in cursor.fetchall()}
        self.assertEqual(
            tables,
            {"test"},
        )

    def test_create_database_columns(self):
        create_database(self.conn, "test")
        cursor = self.conn.cursor()
        cursor.execute("PRAGMA table_info(test)")

        columns = [row[1] for row in cursor.fetchall()]

        self.assertEqual(
            columns,
            [
                "geonameid",
                "nom",
                "departement",
                "region",
                "pays",
                "latitude",
                "longitude",
                "score"
            ],
        )

    def test_create_index(self):
        create_database(self.conn, "test")
        create_index(self.conn, "test")
        cursor = self.conn.cursor()
        cursor.execute("""
                       SELECT name
                       FROM sqlite_master
                       WHERE type = 'index'
                         AND name = 'idx_test_nom'
                       """)

        self.assertIsNotNone(cursor.fetchone())

    @patch("ofrom_outils.meta.meta_geonames._vacuum_database")
    @patch("ofrom_outils.meta.meta_geonames._open_connection")
    @patch("ofrom_outils.meta.meta_geonames.Meta")
    def test_fill_local(
            self,
            mock_meta,
            mock_open_connection,
            mock_vacuum,
    ):
        meta = mock_meta.return_value
        meta.iter_spk.return_value = [
            (
                "tr1",
                "spk1",
                {
                    "domicile_jeunesse": "Genève",
                    "departement": "Genève",
                    "region": "GE",
                    "pays": "CH",
                    "longitude": "6.14",
                    "latitude": "46.20",
                },
            ),
            (
                "tr2",
                "spk2",
                {
                    "domicile_jeunesse": "Inconnu",
                    "departement": "",
                    "region": "",
                    "pays": "",
                    "longitude": "NR",
                    "latitude": "",
                },
            ),
        ]

        conn = MagicMock()
        cursor = MagicMock()

        context = mock_open_connection.return_value
        context.__enter__.return_value = (conn, cursor)

        fill_local(conn, table="test_table")

        meta.load.assert_called_once()

        cursor.executemany.assert_called_once_with(
            unittest.mock.ANY,
            [("Genève", "Genève", "GE", "CH", "6.14", "46.20", 1000)]
        )

        conn.commit.assert_called_once()
        mock_vacuum.assert_called_once_with(conn, "test_table")

    @patch("ofrom_outils.meta.meta_geonames._score_geonames")
    @patch("ofrom_outils.meta.meta_geonames.create_database",
           wraps=create_database)
    @patch("ofrom_outils.meta.meta_geonames.get_location_dict")
    @patch("ofrom_outils.meta.meta_geonames._open_zip_txt")
    def test_fill_remote(self, mock_zip, mock_dict, mock_create, mock_score):
        mock_dict.side_effect = [
            {"FR": "France"},
            {"FR.11": "Île-de-France"},
            {"FR.11.75": "Paris"},
        ]
        mock_score.return_value = 0

        mock_zip.return_value.__enter__.return_value = [
            "10000024\tParis\t11\t75\tFR\t48.8566\t2.3522\t\t\t\n"
        ]

        fill_remote(self.conn, "test")

        row = self.conn.execute(
            "SELECT nom, departement, region, pays, latitude, longitude "
            "FROM test"
        ).fetchone()

        self.assertEqual(
            row,
            ("Paris", "Paris", "Île-de-France", "France", 48.8566, 2.3522),
        )
        mock_create.assert_called_once_with(self.conn, "test")

    @patch("ofrom_outils.meta.meta_geonames._score_geonames")
    @patch("ofrom_outils.meta.meta_geonames.create_database",
           wraps=create_database)
    @patch("ofrom_outils.meta.meta_geonames.get_location_dict")
    @patch("ofrom_outils.meta.meta_geonames._open_zip_txt")
    def test_fill_remote_no_creation(
            self, mock_zip, mock_dict, mock_create, mock_score
    ):
        mock_dict.side_effect = [
            {"FR": "France"},
            {"FR.11": "Île-de-France"},
            {"FR.11.75": "Paris"},
        ]
        mock_score.return_value = 0

        mock_zip.return_value.__enter__.return_value = [
            "10000024\tParis\t11\t75\tFR\t48.8566\t2.3522\t\t\t\n"
        ]
        create_database(self.conn, "test")
        mock_create.reset_mock()
        fill_remote(self.conn, "test")

        row = self.conn.execute(
            "SELECT nom, departement, region, pays, latitude, longitude "
            "FROM test"
        ).fetchone()

        self.assertEqual(
            row,
            ("Paris", "Paris", "Île-de-France", "France", 48.8566, 2.3522),
        )
        mock_create.assert_not_called()

    @patch("ofrom_outils.meta.meta_geonames.get_location_dict")
    @patch("ofrom_outils.meta.meta_geonames._open_zip_txt")
    def test_fill_remote_scores(self, mock_zip, mock_dict):
        mock_dict.side_effect = [
            {"FR": "France"},
            {"FR.11": "Île-de-France"},
            {"FR.11.75": "Paris"},
        ]

        mock_zip.return_value.__enter__.return_value = [
            "1\tParis\t11\t75\tFR\t1.0\t2.0\tP\tPPL\t1000\n",
            "2\tParis\t11\t75\tFR\t48.8566\t2.3522\tP\tPPLC\t2000000\n",
            "3\tParis\t11\t75\tFR\t9.0\t9.0\tP\tPPL\t10\n",
        ]

        fill_remote(self.conn, "test")

        rows = self.conn.execute(
            """
            SELECT nom, latitude, longitude, score
            FROM test
            """
        ).fetchall()

        self.assertEqual(
            rows,
            [("Paris", 48.8566, 2.3522, 1063)],
        )

    @patch("ofrom_outils.meta.meta_geonames.LOCAL_DB")
    @patch("ofrom_outils.meta.meta_geonames.sqlite3.connect")
    @patch("ofrom_outils.meta.meta_geonames.create_database")
    @patch("ofrom_outils.meta.meta_geonames.fill_remote")
    @patch("ofrom_outils.meta.meta_geonames.fill_local")
    @patch("ofrom_outils.meta.meta_geonames.create_index")
    def test_rebuild_database(
            self,
            mock_index,
            mock_local,
            mock_remote,
            mock_create,
            mock_connect,
            mock_local_db
    ):
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        rebuild_database()

        mock_create.assert_has_calls([
            call(mock_conn, "local_geonames"),
            call(mock_conn, "remote_geonames"),
        ], any_order=True)
        mock_local.assert_called_once_with(mock_conn, "local_geonames")
        mock_remote.assert_called_once_with(mock_conn, "remote_geonames")
        mock_index.assert_has_calls([
            call(mock_conn, "local_geonames"),
            call(mock_conn, "remote_geonames"),
        ], any_order=True)
        mock_conn.close.assert_called_once()


class TestGetGeoname(unittest.TestCase):
    def test_build_select(self):
        sql, params = _build_select(
            "Genève", "", "", "", table="test"
        )
        self.assertEqual(
            sql,
            DB["select"].format(table="test")
        )
        self.assertEqual(params, ["Genève"])

        sql, params = _build_select(
            "Genève", "Genève", "GE", "CH", table="test"
        )
        expected = DB["select"].format(table="test")
        expected += "\n" + DB["select_a"].format(col="departement")
        expected += "\n" + DB["select_a"].format(col="region")
        expected += "\n" + DB["select_a"].format(col="pays")
        self.assertEqual(sql, expected)
        self.assertEqual(
            params,
            ["Genève", "Genève", "GE", "CH"]
        )

    @patch("ofrom_outils.meta.meta_geonames._open_connection")
    @patch("ofrom_outils.meta.meta_geonames._build_select")
    def test_get_raw_name(self, mock_build, mock_conn):
        mock_build.return_value = ("SQL", ("params",))

        cursor = MagicMock()
        cursor.execute.return_value.fetchall.return_value = [("result",)]
        mock_conn.return_value.__enter__.return_value = (MagicMock(),
                                                                    cursor)

        result = get_raw_geoname("Paris")

        cursor.execute.assert_called_once_with(
            "SQL", ("params",),
        )
        self.assertEqual(result, [("result",)])

    @patch("ofrom_outils.meta.meta_geonames._open_connection")
    @patch("ofrom_outils.meta.meta_geonames._build_select")
    def test_get_raw_filters(self, mock_build, mock_conn):
        mock_build.return_value = ("SQL", ("params",))

        cursor = MagicMock()
        cursor.execute.return_value.fetchall.return_value = [("result",)]
        mock_conn.return_value.__enter__.return_value = (MagicMock(), cursor)

        result = get_raw_geoname(
            "Paris",
            department="75",
            region="Île-de-France",
            country="France",
        )

        cursor.execute.assert_called_once_with(
            "SQL", ('params',),
        )
        self.assertEqual(result, [("result",)])

    @patch("ofrom_outils.meta.meta_geonames._open_connection")
    @patch("ofrom_outils.meta.meta_geonames._build_select")
    def test_get_local(self, mock_build, mock_open):
        mock_build.return_value = ("SQL", ("params",))

        cursor = MagicMock()
        cursor.execute.return_value.fetchall.return_value = [
            (1, "Genève", "Genève", "GE", "CH", 6.14, 46.20, 10),
            (2, "Genève", "Genève", "GE", "CH", 6.15, 46.21, 20),
        ]

        mock_open.return_value.__enter__.return_value = (
            MagicMock(), cursor
        )

        result = get_geoname("Genève")

        self.assertEqual(
            result,
            {
                "nom": "Genève",
                "departement": "Genève",
                "region": "GE",
                "pays": "CH",
                "lon": 6.15,
                "lat": 46.21,
            },
        )

    @patch("ofrom_outils.meta.meta_geonames._open_connection")
    @patch("ofrom_outils.meta.meta_geonames._build_select")
    def test_fallback_to_global(self, mock_build, mock_open):
        mock_build.side_effect = [
            ("LOCAL SQL", ()),
            ("GLOBAL SQL", ()),
        ]

        cursor = MagicMock()
        cursor.execute.return_value.fetchall.side_effect = [
            [],
            [(1, "Paris", "75", "IDF", "FR", 2.35, 48.85, 100)],
        ]

        mock_open.return_value.__enter__.return_value = (
            MagicMock(), cursor
        )

        result = get_geoname("Paris")

        self.assertEqual(result["nom"], "Paris")
        self.assertEqual(cursor.execute.call_count, 2)

    @patch("ofrom_outils.meta.meta_geonames._open_connection")
    @patch("ofrom_outils.meta.meta_geonames._build_select")
    def test_no_result(self, mock_build, mock_open):
        mock_build.side_effect = [
            ("LOCAL SQL", ()),
            ("GLOBAL SQL", ()),
        ]

        cursor = MagicMock()
        cursor.execute.return_value.fetchall.return_value = []

        mock_open.return_value.__enter__.return_value = (
            MagicMock(), cursor
        )

        self.assertEqual(get_geoname("Unknown"), {})


if __name__ == '__main__':
    unittest.main()
