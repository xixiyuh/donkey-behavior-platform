# backend/database.py
import pymysql
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]

# MySQL连接配置
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '123456',
    'database': 'farm',
    'cursorclass': pymysql.cursors.DictCursor
}

def get_db_connection():
    conn = pymysql.connect(**DB_CONFIG)
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 创建养殖舍表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS barns (
        id INT PRIMARY KEY AUTO_INCREMENT,
        name VARCHAR(255) NOT NULL UNIQUE,
        total_pens INT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    ''')
    
    # 创建栏表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS pens (
        id INT PRIMARY KEY AUTO_INCREMENT,
        pen_number INT NOT NULL,
        barn_id INT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (barn_id) REFERENCES barns (id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    ''')
    
    # 创建摄像头表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS cameras (
        id INT PRIMARY KEY AUTO_INCREMENT,
        camera_id VARCHAR(255) NOT NULL UNIQUE,
        pen_id INT NOT NULL,
        barn_id INT NOT NULL,
        flv_url TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (pen_id) REFERENCES pens (id) ON DELETE CASCADE,
        FOREIGN KEY (barn_id) REFERENCES barns (id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    ''')
    
    # 创建mating事件表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS mating_events (
        id INT PRIMARY KEY AUTO_INCREMENT,
        camera_id VARCHAR(255) NOT NULL,
        pen_id INT NOT NULL,
        barn_id INT NOT NULL,
        start_time TIMESTAMP NOT NULL,
        end_time TIMESTAMP NOT NULL,
        duration INT NOT NULL,
        avg_confidence FLOAT NOT NULL,
        max_confidence FLOAT NOT NULL,
        movement FLOAT NOT NULL,
        screenshot VARCHAR(255),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (pen_id) REFERENCES pens (id) ON DELETE CASCADE,
        FOREIGN KEY (barn_id) REFERENCES barns (id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    ''')
    
    # 创建摄像头配置表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS camera_configs (
        id INT PRIMARY KEY AUTO_INCREMENT,
        camera_id VARCHAR(255) NOT NULL,
        flv_url TEXT NOT NULL,
        barn_id INT NOT NULL,
        pen_id INT NOT NULL,
        status INT DEFAULT 1,
        start_time VARCHAR(5) DEFAULT '09:00',
        end_time VARCHAR(5) DEFAULT '19:00',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (barn_id) REFERENCES barns (id) ON DELETE CASCADE,
        FOREIGN KEY (pen_id) REFERENCES pens (id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    ''')

    # 兼容旧版本数据库：如果表中仍然使用 enable 字段，则迁移到 status 字段
    cursor.execute('SHOW COLUMNS FROM camera_configs LIKE "status"')
    if not cursor.fetchone():
        cursor.execute('ALTER TABLE camera_configs ADD COLUMN status INT DEFAULT 1')
        cursor.execute('SHOW COLUMNS FROM camera_configs LIKE "enable"')
        if cursor.fetchone():
            cursor.execute('UPDATE camera_configs SET status = enable WHERE enable IN (0, 1)')
    
    conn.commit()
    conn.close()

# 初始化数据库 - 移到应用启动时调用，避免导入时数据库不可用导致服务启动失败
# init_db()