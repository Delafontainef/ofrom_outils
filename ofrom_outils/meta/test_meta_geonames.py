import io
import os
import tempfile
import unittest
import zipfile
from unittest.mock import MagicMock, patch

from ofrom_outils.meta.meta_geonames import (
    _open_zip_txt, _download_file, download_geonames,
    _get_admin_geoids,
    _get_country_geoids, _get_french_names, get_location_dict
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

    @patch("ofrom_outils.meta.meta_geonames.os.path.isfile",
           return_value=False)
    def test_get_french_names_missing(self, mock_isfile):
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
                {"country": ("countryInfo.txt", mock_loc)}
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


if __name__ == '__main__':
    unittest.main()
