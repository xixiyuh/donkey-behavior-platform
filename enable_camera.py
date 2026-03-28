#!/usr/bin/env python3
"""
启用摄像头配置
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
    
    # 启用摄像头配置
    print("Enabling camera config...")
    cursor.execute("UPDATE camera_configs SET enable = 1 WHERE id = 1")
    conn.commit()
    
    # 查看更新后的配置
    print("\nUpdated camera configs:")
    cursor.execute("SELECT id, camera_id, enable FROM camera_configs")
    configs = cursor.fetchall()
    for config in configs:
        print(f"  ID: {config[0]}, Camera: {config[1]}, Enable: {config[2]}")
    
    # 关闭连接
    conn.close()
    
    print("\nCamera enabled successfully!")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
