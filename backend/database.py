# backend/database.py
import pymysql
from datetime import datetime

from .config import settings

MYSQL_CONFIG = {
    'host': settings.db_host,
    'port': settings.db_port,
    'user': settings.db_user,
    'password': settings.db_password,
    'database': settings.db_name,
    'charset': settings.db_charset,
    'cursorclass': pymysql.cursors.DictCursor
}

def get_db_connection():
    conn = pymysql.connect(**MYSQL_CONFIG)
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS barns (
        id INTEGER PRIMARY KEY AUTO_INCREMENT,
        name VARCHAR(100) NOT NULL UNIQUE,
        total_pens INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS pens (
        id INTEGER PRIMARY KEY AUTO_INCREMENT,
        pen_number INTEGER NOT NULL,
        barn_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (barn_id) REFERENCES barns (id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS cameras (
        id INTEGER PRIMARY KEY AUTO_INCREMENT,
        camera_id VARCHAR(50) NOT NULL UNIQUE,
        pen_id INTEGER NOT NULL,
        barn_id INTEGER NOT NULL,
        flv_url TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (pen_id) REFERENCES pens (id),
        FOREIGN KEY (barn_id) REFERENCES barns (id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS mating_events (
        id INTEGER PRIMARY KEY AUTO_INCREMENT,
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

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS camera_configs (
        id INTEGER PRIMARY KEY AUTO_INCREMENT,
        camera_id TEXT NOT NULL,
        flv_url TEXT NOT NULL,
        barn_id INTEGER NOT NULL,
        pen_id INTEGER NOT NULL,
        status INTEGER DEFAULT 1,
        enable INTEGER DEFAULT 1,
        start_time VARCHAR(10) DEFAULT '09:00',
        end_time VARCHAR(10) DEFAULT '19:00',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (barn_id) REFERENCES barns (id),
        FOREIGN KEY (pen_id) REFERENCES pens (id)
    )
    ''')

    cursor.execute('SHOW COLUMNS FROM camera_configs')
    columns = [row['Field'] for row in cursor.fetchall()]
    if 'status' not in columns:
        cursor.execute('ALTER TABLE camera_configs ADD COLUMN status INTEGER DEFAULT 1')
    if 'enable' not in columns:
        cursor.execute('ALTER TABLE camera_configs ADD COLUMN enable INTEGER DEFAULT 1')

    conn.commit()
    conn.close()
