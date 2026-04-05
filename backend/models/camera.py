from ..database import get_db_connection

class Camera:
    @staticmethod
    def create(camera_id, pen_id, barn_id, flv_url):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO cameras (camera_id, pen_id, barn_id, flv_url) VALUES (%s, %s, %s, %s)', 
                      (camera_id, pen_id, barn_id, flv_url))
        conn.commit()
        camera_id = cursor.lastrowid
        conn.close()
        return camera_id
    
    @staticmethod
    def get_all(page=1, page_size=10):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取总记录数
        cursor.execute('SELECT COUNT(*) FROM cameras')
        total = cursor.fetchone()['COUNT(*)']
        
        # 获取分页数据
        offset = (page - 1) * page_size
        cursor.execute('SELECT * FROM cameras ORDER BY barn_id, pen_id LIMIT %s OFFSET %s', (page_size, offset))
        cameras = cursor.fetchall()
        conn.close()
        
        return {
            'items': cameras,
            'total': total,
            'page': page,
            'page_size': page_size
        }
    
    @staticmethod
    def get_by_id(camera_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM cameras WHERE id = %s', (camera_id,))
        camera = cursor.fetchone()
        conn.close()
        return camera
    
    @staticmethod
    def get_by_pen(pen_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM cameras WHERE pen_id = %s', (pen_id,))
        cameras = cursor.fetchall()
        conn.close()
        return cameras
    
    @staticmethod
    def get_by_barn(barn_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM cameras WHERE barn_id = %s ORDER BY pen_id', (barn_id,))
        cameras = cursor.fetchall()
        conn.close()
        return cameras
    
    @staticmethod
    def update(camera_id, camera_id_str, pen_id, barn_id, flv_url):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE cameras SET camera_id = %s, pen_id = %s, barn_id = %s, flv_url = %s WHERE id = %s', 
                      (camera_id_str, pen_id, barn_id, flv_url, camera_id))
        conn.commit()
        conn.close()
    
    @staticmethod
    def delete(camera_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM cameras WHERE id = %s', (camera_id,))
        conn.commit()
        conn.close()
