#!/usr/bin/env python3
"""
检查数据库中的事件记录
"""
import sqlite3
import os
from pathlib import Path

# 获取数据库路径
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = str(BASE_DIR / "data" / "farm.db")

print(f"Database path: {DB_PATH}")
print(f"Database exists: {os.path.exists(DB_PATH)}")

if not os.path.exists(DB_PATH):
    print("Error: Database file not found!")
    exit(1)

# 连接数据库
try:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 查看mating_events表结构
    print("\nMating events table schema:")
    cursor.execute("PRAGMA table_info(mating_events)")
    schema = cursor.fetchall()
    for column in schema:
        print(f"  {column[1]} ({column[2]})")
    
    # 查询所有事件
    print("\nAll events:")
    cursor.execute("SELECT * FROM mating_events ORDER BY created_at DESC")
    all_events = cursor.fetchall()
    for event in all_events:
        print(f"  ID: {event[0]}, Camera: {event[1]}, Pen: {event[2]}, Barn: {event[3]}, Start: {event[4]}, End: {event[5]}, Duration: {event[6]}s, Avg Conf: {event[7]:.2f}")
    
    # 关闭连接
    conn.close()
    
    print(f"\nTotal events: {len(all_events)}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
