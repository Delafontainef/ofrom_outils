import os
import tempfile
import unittest

from ofrom_outils.db.db import (
    _check_line, read_sql
)


class TestCheckLine(unittest.TestCase):

    def test_append_line(self):
        key, value, data = _check_line(
            "SELECT * FROM table\n", "query", "", {},
        )

        self.assertEqual(key, "query")
        self.assertEqual(value, "SELECT * FROM table\n")

        key, value, data = _check_line(
            "WHERE animal = 'Wapiti';\n", key, value, data
        )

        self.assertEqual(
            value,
            "SELECT * FROM table\nWHERE animal = 'Wapiti';\n",
        )
        self.assertEqual(data, {})

    def test_new_key(self):
        key, value, data = _check_line(
            "-- name: new_query\n", "query", "SELECT 1;", {}
        )

        self.assertEqual(key, "new_query")
        self.assertEqual(value, "")
        self.assertEqual(
            data,
            {"query": "SELECT 1;"},
        )

    def test_multiline(self):
        key, value, data = _check_line(
            "end of comment */\n",
            "query",
            "something",
            {},
        )

        self.assertEqual(key, "query")
        self.assertEqual(value, "")
        self.assertEqual(data, {})

    def test_empty_line(self):
        key, value, data = _check_line(
            "\n",
            "query",
            "SELECT 1;",
            {},
        )

        self.assertEqual(key, "query")
        self.assertEqual(value, "SELECT 1;")
        self.assertEqual(data, {})


class TestReadDb(unittest.TestCase):

    def test_file_does_not_exist(self):
        self.assertEqual(
            read_sql("this_file_does_not_exist.sql"),
            {},
        )

    def test_read_sql_file(self):
        sql = """
-- name: mock_un
/* It's for kicks and giggles */
SELECT * FROM stuff
  WHERE x = 'Wapiti';
-- name: mock_deux
SELECT * FROM moar;
"""

        with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                delete=False,
        ) as f:
            f.write(sql)
            path = f.name

        try:
            data = read_sql(path)

            self.assertEqual(
                data,
                {
                    "mock_un":
                        ("SELECT * FROM stuff\n"
                         "  WHERE x = 'Wapiti';"),
                    "mock_deux":
                        "SELECT * FROM moar;"
                },
            )
        finally:
            os.remove(path)


if __name__ == "__main__":
    unittest.main()
