-- name: create
CREATE TABLE IF NOT EXISTS {table}
(
    geonameid   INTEGER PRIMARY KEY,
    nom         VARCHAR(200),
    departement VARCHAR(20),
    region      VARCHAR(20),
    pays        VARCHAR(20),
    latitude    FLOAT,
    longitude   FLOAT,
    score       INTEGER NOT NULL DEFAULT 0
);

-- name: exists
SELECT name
FROM sqlite_master
WHERE type = 'table'
  AND name = '{table}';

-- name: vacuum
DELETE FROM {table}
WHERE geonameid IN (
    SELECT geonameid
    FROM (
         SELECT geonameid,
                ROW_NUMBER() OVER (
                    PARTITION BY nom, departement, region, pays
                    ORDER BY score DESC
                ) AS rn
         FROM {table}
         )
    WHERE rn > 1
);

-- name: insert
INSERT INTO {table}
(nom, departement, region, pays, latitude, longitude, score)
VALUES (?, ?, ?, ?, ?, ?, ?);

-- name: insertd
INSERT INTO {table}
(nom, departement, region, pays, latitude, longitude, score)
VALUES (:nom, :departement, :region, :pays, :latitude, :longitude, :score);

-- name: index
CREATE INDEX IF NOT EXISTS idx_{table}_nom ON {table}(nom);

-- name: index_c
CREATE INDEX IF NOT EXISTS idx_{table}_nom_pays ON {table}(nom, pays);

-- name: select
SELECT * FROM {table}
WHERE nom = ?

-- name: select_a
AND {col} = ?