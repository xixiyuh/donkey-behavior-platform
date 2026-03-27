#!/usr/bin/env python3
"""
更新事件表结构，将三个截图字段改为一个screenshot字段，并更新现有记录的图片路径
"""
import sqlite3
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[0]
DB_PATH = str(BASE_DIR / "data" / "farm.db")

# 确保data目录存在
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def update_event_table():
    """更新事件表结构"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 1. 创建一个新表，包含screenshot字段
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS mating_events_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            camera_id TEXT NOT NULL,
            pen_id INTEGER NOT NULL,
            barn_id INTEGER NOT NULL,
            start_time TIMESTAMP NOT NULL,
            end_time TIMESTAMP NOT NULL,
            duration INTEGER NOT NULL,
            avg_confidence REAL NOT NULL,
            max_confidence REAL NOT NULL,
            screenshot TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 2. 获取现有的事件记录
        cursor.execute('SELECT * FROM mating_events')
        events = cursor.fetchall()
        
        # 3. 获取static/mating目录下的图片列表
        mating_images = []
        mating_dir = BASE_DIR / "static" / "mating"
        if mating_dir.exists():
            for file in mating_dir.iterdir():
                if file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif']:
                    mating_images.append(f"/static/mating/{file.name}")
        
        print(f"Found {len(mating_images)} images in static/mating directory")
        
        # 4. 插入现有记录到新表，使用mating目录下的图片
        for i, event in enumerate(events):
            # 选择对应的图片，循环使用
            image_index = i % len(mating_images)
            screenshot = mating_images[image_index] if mating_images else None
            
            cursor.execute('''
            INSERT INTO mating_events_new 
            (camera_id, pen_id, barn_id, start_time, end_time, duration, avg_confidence, max_confidence, screenshot, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                event['camera_id'],
                event['pen_id'],
                event['barn_id'],
                event['start_time'],
                event['end_time'],
                event['duration'],
                event['avg_confidence'],
                event['max_confidence'],
                screenshot,
                event['created_at']
            ))
        
        # 5. 删除旧表
        cursor.execute('DROP TABLE IF EXISTS mating_events')
        
        # 6. 重命名新表为旧表名
        cursor.execute('ALTER TABLE mating_events_new RENAME TO mating_events')
        
        conn.commit()
        print(f"Updated {len(events)} events with new screenshot paths")
        
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    update_event_table()
