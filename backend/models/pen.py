from ..database import get_db_connection

class Pen:
    @staticmethod
    def create(pen_number, barn_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO pens (pen_number, barn_id) VALUES (%s, %s)', (pen_number, barn_id))
        conn.commit()
        pen_id = cursor.lastrowid
        conn.close()
        return pen_id
    
    @staticmethod
    def get_all(page=1, page_size=10):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取总记录数
        cursor.execute('SELECT COUNT(*) FROM pens')
        total = cursor.fetchone()['COUNT(*)']
        
        # 获取分页数据
        offset = (page - 1) * page_size
        cursor.execute('SELECT * FROM pens ORDER BY barn_id, pen_number LIMIT %s OFFSET %s', (page_size, offset))
        pens = cursor.fetchall()
        conn.close()
        
        return {
            'items': pens,
            'total': total,
            'page': page,
            'page_size': page_size
        }
    
    @staticmethod
    def get_by_id(pen_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM pens WHERE id = %s', (pen_id,))
        pen = cursor.fetchone()
        conn.close()
        return pen
    
    @staticmethod
    def get_by_barn(barn_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM pens WHERE barn_id = %s ORDER BY pen_number', (barn_id,))
        pens = cursor.fetchall()
        conn.close()
        return pens
    
    @staticmethod
    def update(pen_id, pen_number, barn_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE pens SET pen_number = %s, barn_id = %s WHERE id = %s', (pen_number, barn_id, pen_id))
        conn.commit()
        conn.close()
    
    @staticmethod
    def delete(pen_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 由于设置了外键级联删除，不需要手动删除关联数据
        cursor.execute('DELETE FROM pens WHERE id = %s', (pen_id,))
        
        conn.commit()
        conn.close()
