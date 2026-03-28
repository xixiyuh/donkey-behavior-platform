# backend/models.py
from .database import get_db_connection
import sqlite3
from datetime import datetime

class Barn:
    @staticmethod
    def create(name, total_pens):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO barns (name, total_pens) VALUES (?, ?)', (name, total_pens))
        conn.commit()
        barn_id = cursor.lastrowid
        conn.close()
        return barn_id
    
    @staticmethod
    def get_all():
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM barns ORDER BY id')
        barns = cursor.fetchall()
        conn.close()
        return barns
    
    @staticmethod
    def get_by_id(barn_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM barns WHERE id = ?', (barn_id,))
        barn = cursor.fetchone()
        conn.close()
        return barn
    
    @staticmethod
    def update(barn_id, name, total_pens):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE barns SET name = ?, total_pens = ? WHERE id = ?', (name, total_pens, barn_id))
        conn.commit()
        conn.close()
    
    @staticmethod
    def delete(barn_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 先获取该养殖舍下的所有栏
        cursor.execute('SELECT id FROM pens WHERE barn_id = ?', (barn_id,))
        pen_ids = [pen[0] for pen in cursor.fetchall()]
        
        # 删除这些栏下的所有摄像头
        if pen_ids:
            placeholders = ','.join(['?'] * len(pen_ids))
            cursor.execute(f'DELETE FROM cameras WHERE pen_id IN ({placeholders})', pen_ids)
        
        # 删除该养殖舍下的所有栏
        cursor.execute('DELETE FROM pens WHERE barn_id = ?', (barn_id,))
        
        # 最后删除养殖舍本身
        cursor.execute('DELETE FROM barns WHERE id = ?', (barn_id,))
        
        conn.commit()
        conn.close()

class Pen:
    @staticmethod
    def create(pen_number, barn_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO pens (pen_number, barn_id) VALUES (?, ?)', (pen_number, barn_id))
        conn.commit()
        pen_id = cursor.lastrowid
        conn.close()
        return pen_id
    
    @staticmethod
    def get_all():
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM pens ORDER BY barn_id, pen_number')
        pens = cursor.fetchall()
        conn.close()
        return pens
    
    @staticmethod
    def get_by_id(pen_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM pens WHERE id = ?', (pen_id,))
        pen = cursor.fetchone()
        conn.close()
        return pen
    
    @staticmethod
    def get_by_barn(barn_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM pens WHERE barn_id = ? ORDER BY pen_number', (barn_id,))
        pens = cursor.fetchall()
        conn.close()
        return pens
    
    @staticmethod
    def update(pen_id, pen_number, barn_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE pens SET pen_number = ?, barn_id = ? WHERE id = ?', (pen_number, barn_id, pen_id))
        conn.commit()
        conn.close()
    
    @staticmethod
    def delete(pen_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 先删除该栏下的所有摄像头
        cursor.execute('DELETE FROM cameras WHERE pen_id = ?', (pen_id,))
        
        # 然后删除栏本身
        cursor.execute('DELETE FROM pens WHERE id = ?', (pen_id,))
        
        conn.commit()
        conn.close()

class Camera:
    @staticmethod
    def create(camera_id, pen_id, barn_id, flv_url):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO cameras (camera_id, pen_id, barn_id, flv_url) VALUES (?, ?, ?, ?)', 
                      (camera_id, pen_id, barn_id, flv_url))
        conn.commit()
        camera_id = cursor.lastrowid
        conn.close()
        return camera_id
    
    @staticmethod
    def get_all():
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM cameras ORDER BY barn_id, pen_id')
        cameras = cursor.fetchall()
        conn.close()
        return cameras
    
    @staticmethod
    def get_by_id(camera_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM cameras WHERE id = ?', (camera_id,))
        camera = cursor.fetchone()
        conn.close()
        return camera
    
    @staticmethod
    def get_by_pen(pen_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM cameras WHERE pen_id = ?', (pen_id,))
        cameras = cursor.fetchall()
        conn.close()
        return cameras
    
    @staticmethod
    def get_by_barn(barn_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM cameras WHERE barn_id = ? ORDER BY pen_id', (barn_id,))
        cameras = cursor.fetchall()
        conn.close()
        return cameras
    
    @staticmethod
    def update(camera_id, camera_id_str, pen_id, barn_id, flv_url):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE cameras SET camera_id = ?, pen_id = ?, barn_id = ?, flv_url = ? WHERE id = ?', 
                      (camera_id_str, pen_id, barn_id, flv_url, camera_id))
        conn.commit()
        conn.close()
    
    @staticmethod
    def delete(camera_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM cameras WHERE id = ?', (camera_id,))
        conn.commit()
        conn.close()

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
    def get_all():
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM mating_events ORDER BY start_time DESC')
        events = cursor.fetchall()
        conn.close()
        return events
    
    @staticmethod
    def get_by_id(event_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM mating_events WHERE id = ?', (event_id,))
        event = cursor.fetchone()
        conn.close()
        return event
    
    @staticmethod
    def get_by_pen(pen_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM mating_events WHERE pen_id = ? ORDER BY start_time DESC', (pen_id,))
        events = cursor.fetchall()
        conn.close()
        return events
    
    @staticmethod
    def get_by_barn(barn_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM mating_events WHERE barn_id = ? ORDER BY start_time DESC', (barn_id,))
        events = cursor.fetchall()
        conn.close()
        return events

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
    def get_all():
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM camera_configs')
        configs = cursor.fetchall()
        conn.close()
        return configs
    
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