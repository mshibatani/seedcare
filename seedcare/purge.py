"""データ保持期限管理。"""

import logging
from datetime import datetime, timedelta
from pathlib import Path

from seedcare import db

logger = logging.getLogger(__name__)


def purge(db_path: Path, retention_days: int = 120) -> int:
    """retention_days より古いレコードを削除し、削除件数を返す。"""
    before = datetime.now() - timedelta(days=retention_days)
    deleted = db.purge_old(db_path, before)
    if deleted > 0:
        logger.info("%d 件の古いレコードを削除しました（%d日以前）", deleted, retention_days)
    return deleted
