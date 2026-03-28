#!/usr/bin/env python3
"""
检查数据库中的摄像头配置情况
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
    
    # 查看camera_configs表结构
    print("\nCamera configs table schema:")
    cursor.execute("PRAGMA table_info(camera_configs)")
    schema = cursor.fetchall()
    for column in schema:
        print(f"  {column[1]} ({column[2]})")
    
    # 查询所有摄像头配置
    print("\nAll camera configs:")
    cursor.execute("SELECT * FROM camera_configs")
    all_configs = cursor.fetchall()
    for config in all_configs:
        print(f"  ID: {config[0]}, Camera: {config[1]}, FLV: {config[2]}, Barn: {config[3]}, Pen: {config[4]}, Enabled: {config[8]}")
    
    # 查询启用的摄像头配置
    print("\nEnabled camera configs:")
    cursor.execute("SELECT * FROM camera_configs WHERE enable = 1")
    enabled_configs = cursor.fetchall()
    for config in enabled_configs:
        print(f"  ID: {config[0]}, Camera: {config[1]}, FLV: {config[2]}, Barn: {config[3]}, Pen: {config[4]}")
    
    # 关闭连接
    conn.close()
    
    print(f"\nTotal configs: {len(all_configs)}")
    print(f"Enabled configs: {len(enabled_configs)}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
