import sqlite3
from pathlib import Path

PROJECT_ROOT = Path("/var/www/realtime-detector")
DB_PATH = PROJECT_ROOT / "data" / "farm.db"

def delete_events_on_20260330():
    """删除 start_time 在 2026-03-30 的所有事件记录"""
    try:
        print(f"数据库路径: {DB_PATH}")
        print(f"数据库是否存在: {DB_PATH.exists()}")

        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()

        delete_sql = """
        DELETE FROM mating_events
        WHERE start_time >= '2026-03-30 00:00:00'
          AND start_time <  '2026-03-31 00:00:00'
        """
        cursor.execute(delete_sql)

        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()

        print(f"成功删除 {deleted_count} 条 2026-03-30 的事件记录")
        return deleted_count

    except Exception as e:
        print(f"删除操作失败: {e}")
        return 0

if __name__ == "__main__":
    delete_events_on_20260330()
