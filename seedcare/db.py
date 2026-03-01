"""SQLite アクセス層（WAL モード対応）。"""

import sqlite3
from datetime import datetime
from pathlib import Path

CREATE_TABLE = """\
CREATE TABLE IF NOT EXISTS plantGrowerDB(
    dateTime    TIMESTAMP,
    temperature0 FLOAT,
    temperature1 FLOAT,
    moisture0    FLOAT,
    moisture1    FLOAT,
    relay0       VARCHAR(8),
    relay1       VARCHAR(8)
)"""

CREATE_INDEX = """\
CREATE INDEX IF NOT EXISTS idx_datetime ON plantGrowerDB(dateTime)"""


def _connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(
        str(db_path),
        detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
    )
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA busy_timeout=5000")
    sqlite3.dbapi2.converters["DATETIME"] = sqlite3.dbapi2.converters["TIMESTAMP"]
    return con


def setup(db_path: Path) -> None:
    con = _connect(db_path)
    con.execute(CREATE_TABLE)
    con.execute(CREATE_INDEX)
    con.commit()
    con.close()


def append(db_path: Path, record: dict) -> None:
    con = _connect(db_path)
    con.execute(
        "INSERT INTO plantGrowerDB VALUES(?,?,?,?,?,?,?)",
        [
            record["DateTime"],
            record["Temperature"][0],
            record["Temperature"][1],
            record["Moisture"][0],
            record["Moisture"][1],
            record["Relay"][0],
            record["Relay"][1],
        ],
    )
    con.commit()
    con.close()


def fetch_range(db_path: Path, since: datetime) -> list[tuple]:
    con = _connect(db_path)
    rows = con.execute(
        "SELECT * FROM plantGrowerDB WHERE dateTime >= ? ORDER BY dateTime",
        [since],
    ).fetchall()
    con.close()
    return rows


def fetch_latest(db_path: Path) -> tuple | None:
    con = _connect(db_path)
    row = con.execute(
        "SELECT * FROM plantGrowerDB ORDER BY dateTime DESC LIMIT 1"
    ).fetchone()
    con.close()
    return row


def purge_old(db_path: Path, before: datetime) -> int:
    con = _connect(db_path)
    cur = con.execute("DELETE FROM plantGrowerDB WHERE dateTime < ?", [before])
    deleted = cur.rowcount
    con.commit()
    con.close()
    return deleted


def count_records(db_path: Path) -> int:
    con = _connect(db_path)
    count = con.execute("SELECT COUNT(*) FROM plantGrowerDB").fetchone()[0]
    con.close()
    return count
