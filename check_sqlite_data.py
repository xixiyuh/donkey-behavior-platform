#!/usr/bin/env python3
"""
检查SQLite数据库中mating_events表的screenshot字段内容
"""
import sqlite3
from pathlib import Path

# SQLite数据库路径
SQLITE_DB = str(Path(__file__).parent / "backend" / "data" / "farm.db")

def check_mating_events():
    """检查交配事件数据"""
    print("[INFO] 检查SQLite数据库中的mating_events表...")
    
    try:
        conn = sqlite3.connect(SQLITE_DB)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 获取表结构
        cursor.execute('PRAGMA table_info(mating_events)')
        columns = cursor.fetchall()
        print("[INFO] 表结构:")
        for col in columns:
            print(f"  {col[1]}: {col[2]}")
        
        # 查看数据
        cursor.execute('SELECT id, screenshot, start_time, created_at FROM mating_events LIMIT 5')
        events = cursor.fetchall()
        print("\n[INFO] 前5条记录:")
        for event in events:
            print(f"  ID: {event['id']}")
            print(f"  Screenshot: {event['screenshot']}")
            print(f"  Start Time: {event['start_time']}")
            print(f"  Created At: {event['created_at']}")
            print(f"  Screenshot类型: {type(event['screenshot'])}")
            print()
        
    except Exception as e:
        print(f"[ERROR] 检查失败: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    check_mating_events()
