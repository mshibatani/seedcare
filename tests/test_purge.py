"""purge モジュールのテスト。"""

from datetime import datetime, timedelta

import pytest

from seedcare import db
from seedcare.purge import purge


@pytest.fixture
def tmp_db(tmp_path):
    db_path = tmp_path / "test.db"
    db.setup(db_path)
    return db_path


def _make_record(dt_str):
    return {
        "DateTime": dt_str,
        "Temperature": {0: 25.0, 1: 24.0},
        "Moisture": {0: 60, 1: 55},
        "Relay": {0: "OFF", 1: "OFF"},
    }


def test_purge_removes_old_records(tmp_db):
    old_date = (datetime.now() - timedelta(days=200)).strftime("%Y-%m-%d %H:%M:%S")
    recent_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    db.append(tmp_db, _make_record(old_date))
    db.append(tmp_db, _make_record(recent_date))

    deleted = purge(tmp_db, retention_days=120)
    assert deleted == 1
    assert db.count_records(tmp_db) == 1


def test_purge_nothing_to_delete(tmp_db):
    recent_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    db.append(tmp_db, _make_record(recent_date))

    deleted = purge(tmp_db, retention_days=120)
    assert deleted == 0
    assert db.count_records(tmp_db) == 1


def test_purge_empty_db(tmp_db):
    deleted = purge(tmp_db, retention_days=120)
    assert deleted == 0
