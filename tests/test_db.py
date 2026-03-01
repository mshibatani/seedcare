"""db モジュールのテスト。"""

from datetime import datetime, timedelta
from pathlib import Path

import pytest

from seedcare import db


@pytest.fixture
def tmp_db(tmp_path):
    db_path = tmp_path / "test.db"
    db.setup(db_path)
    return db_path


def _make_record(dt_str="2025-03-01 12:00:00"):
    return {
        "DateTime": dt_str,
        "Temperature": {0: 25.5, 1: 24.0},
        "Moisture": {0: 60, 1: 55},
        "Relay": {0: "OFF", 1: "OFF"},
    }


def test_setup_creates_table(tmp_db):
    assert tmp_db.exists()
    assert db.count_records(tmp_db) == 0


def test_append_and_count(tmp_db):
    db.append(tmp_db, _make_record())
    assert db.count_records(tmp_db) == 1


def test_fetch_latest(tmp_db):
    db.append(tmp_db, _make_record("2025-03-01 12:00:00"))
    db.append(tmp_db, _make_record("2025-03-01 13:00:00"))
    row = db.fetch_latest(tmp_db)
    assert row is not None
    assert "13:00:00" in str(row[0])


def test_fetch_range(tmp_db):
    db.append(tmp_db, _make_record("2025-03-01 12:00:00"))
    db.append(tmp_db, _make_record("2025-03-02 12:00:00"))
    db.append(tmp_db, _make_record("2025-03-03 12:00:00"))
    since = datetime(2025, 3, 2, 0, 0, 0)
    rows = db.fetch_range(tmp_db, since)
    assert len(rows) == 2


def test_purge_old(tmp_db):
    db.append(tmp_db, _make_record("2025-01-01 00:00:00"))
    db.append(tmp_db, _make_record("2025-03-01 12:00:00"))
    before = datetime(2025, 2, 1, 0, 0, 0)
    deleted = db.purge_old(tmp_db, before)
    assert deleted == 1
    assert db.count_records(tmp_db) == 1


def test_fetch_latest_empty(tmp_db):
    assert db.fetch_latest(tmp_db) is None
