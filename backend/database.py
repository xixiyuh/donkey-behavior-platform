# backend/database.py
import sqlite3
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = str(BASE_DIR / "data" / "farm.db")

# 确保data目录存在
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 创建养殖舍表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS barns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        total_pens INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # 创建栏表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS pens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pen_number INTEGER NOT NULL,
        barn_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (barn_id) REFERENCES barns (id)
    )
    ''')
    
    # 创建摄像头表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS cameras (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        camera_id TEXT NOT NULL UNIQUE,
        pen_id INTEGER NOT NULL,
        barn_id INTEGER NOT NULL,
        flv_url TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (pen_id) REFERENCES pens (id),
        FOREIGN KEY (barn_id) REFERENCES barns (id)
    )
    ''')
    
    # 创建mating事件表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS mating_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        camera_id TEXT NOT NULL,
        pen_id INTEGER NOT NULL,
        barn_id INTEGER NOT NULL,
        start_time TIMESTAMP NOT NULL,
        end_time TIMESTAMP NOT NULL,
        duration INTEGER NOT NULL,
        avg_confidence REAL NOT NULL,
        max_confidence REAL NOT NULL,
        movement REAL NOT NULL,
        screenshot TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (pen_id) REFERENCES pens (id),
        FOREIGN KEY (barn_id) REFERENCES barns (id)
    )
    ''')
    
    # 创建摄像头配置表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS camera_configs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        camera_id TEXT NOT NULL,
        flv_url TEXT NOT NULL,
        barn_id INTEGER NOT NULL,
        pen_id INTEGER NOT NULL,
        enable INTEGER DEFAULT 1,
        start_time TEXT DEFAULT '09:00',
        end_time TEXT DEFAULT '19:00',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (barn_id) REFERENCES barns (id),
        FOREIGN KEY (pen_id) REFERENCES pens (id)
    )
    ''')
    
    conn.commit()
    conn.close()

# 初始化数据库
init_db()