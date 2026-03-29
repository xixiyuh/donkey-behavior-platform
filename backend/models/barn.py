from ..database import get_db_connection
import sqlite3

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
    def get_all(page=1, page_size=10):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取总记录数
        cursor.execute('SELECT COUNT(*) FROM barns')
        total = cursor.fetchone()[0]
        
        # 获取分页数据
        offset = (page - 1) * page_size
        cursor.execute('SELECT * FROM barns ORDER BY id LIMIT ? OFFSET ?', (page_size, offset))
        barns = cursor.fetchall()
        conn.close()
        
        return {
            'items': barns,
            'total': total,
            'page': page,
            'page_size': page_size
        }
    
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
