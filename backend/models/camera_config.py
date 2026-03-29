from ..database import get_db_connection
import sqlite3

class CameraConfig:
    @staticmethod
    def create(camera_id, flv_url, barn_id, pen_id, start_time='09:00', end_time='19:00'):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO camera_configs (camera_id, flv_url, barn_id, pen_id, start_time, end_time)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (camera_id, flv_url, barn_id, pen_id, start_time, end_time))
        conn.commit()
        config_id = cursor.lastrowid
        conn.close()
        return config_id
    
    @staticmethod
    def get_all(page=1, page_size=10):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取总记录数
        cursor.execute('SELECT COUNT(*) FROM camera_configs')
        total = cursor.fetchone()[0]
        
        # 获取分页数据
        offset = (page - 1) * page_size
        cursor.execute('SELECT * FROM camera_configs LIMIT ? OFFSET ?', (page_size, offset))
        configs = cursor.fetchall()
        conn.close()
        
        return {
            'items': configs,
            'total': total,
            'page': page,
            'page_size': page_size
        }
    
    @staticmethod
    def get_enabled():
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM camera_configs WHERE enable = 1')
        configs = cursor.fetchall()
        conn.close()
        return configs
    
    @staticmethod
    def toggle(id):
        conn = get_db_connection()
        cursor = conn.cursor()
        # 获取当前状态
        cursor.execute('SELECT enable FROM camera_configs WHERE id = ?', (id,))
        result = cursor.fetchone()
        if result:
            new_state = 0 if result[0] == 1 else 1
            cursor.execute('UPDATE camera_configs SET enable = ? WHERE id = ?', (new_state, id))
            conn.commit()
        conn.close()
    
    @staticmethod
    def get_by_id(id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM camera_configs WHERE id = ?', (id,))
        config = cursor.fetchone()
        conn.close()
        return config
    
    @staticmethod
    def delete(id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM camera_configs WHERE id = ?', (id,))
        conn.commit()
        conn.close()
