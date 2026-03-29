from ..database import get_db_connection
import sqlite3

class MatingEvent:
    @staticmethod
    def create(camera_id, pen_id, barn_id, start_time, end_time, duration, avg_confidence, max_confidence, 
               screenshot=None):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO mating_events (camera_id, pen_id, barn_id, start_time, end_time, duration, 
                                 avg_confidence, max_confidence, screenshot)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (camera_id, pen_id, barn_id, start_time, end_time, duration, avg_confidence, max_confidence, 
              screenshot))
        conn.commit()
        event_id = cursor.lastrowid
        conn.close()
        return event_id
    
    @staticmethod
    def get_all(page=1, page_size=10):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取总记录数
        cursor.execute('SELECT COUNT(*) FROM mating_events')
        total = cursor.fetchone()[0]
        
        # 获取分页数据
        offset = (page - 1) * page_size
        cursor.execute('SELECT * FROM mating_events ORDER BY start_time DESC LIMIT ? OFFSET ?', (page_size, offset))
        events = cursor.fetchall()
        conn.close()
        
        return {
            'items': events,
            'total': total,
            'page': page,
            'page_size': page_size
        }
    
    @staticmethod
    def get_by_id(event_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM mating_events WHERE id = ?', (event_id,))
        event = cursor.fetchone()
        conn.close()
        return event
    
    @staticmethod
    def get_by_pen(pen_id, page=1, page_size=10):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取总记录数
        cursor.execute('SELECT COUNT(*) FROM mating_events WHERE pen_id = ?', (pen_id,))
        total = cursor.fetchone()[0]
        
        # 获取分页数据
        offset = (page - 1) * page_size
        cursor.execute('SELECT * FROM mating_events WHERE pen_id = ? ORDER BY start_time DESC LIMIT ? OFFSET ?', (pen_id, page_size, offset))
        events = cursor.fetchall()
        conn.close()
        
        return {
            'items': events,
            'total': total,
            'page': page,
            'page_size': page_size
        }
    
    @staticmethod
    def get_by_barn(barn_id, page=1, page_size=10):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取总记录数
        cursor.execute('SELECT COUNT(*) FROM mating_events WHERE barn_id = ?', (barn_id,))
        total = cursor.fetchone()[0]
        
        # 获取分页数据
        offset = (page - 1) * page_size
        cursor.execute('SELECT * FROM mating_events WHERE barn_id = ? ORDER BY start_time DESC LIMIT ? OFFSET ?', (barn_id, page_size, offset))
        events = cursor.fetchall()
        conn.close()
        
        return {
            'items': events,
            'total': total,
            'page': page,
            'page_size': page_size
        }
