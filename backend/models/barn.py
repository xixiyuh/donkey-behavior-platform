from ..database import get_db_connection

class Barn:
    @staticmethod
    def create(name, total_pens):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO barns (name, total_pens) VALUES (%s, %s)', (name, total_pens))
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
        total = cursor.fetchone()['COUNT(*)']
        
        # 获取分页数据
        offset = (page - 1) * page_size
        cursor.execute('SELECT * FROM barns ORDER BY id LIMIT %s OFFSET %s', (page_size, offset))
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
        cursor.execute('SELECT * FROM barns WHERE id = %s', (barn_id,))
        barn = cursor.fetchone()
        conn.close()
        return barn
    
    @staticmethod
    def update(barn_id, name, total_pens):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE barns SET name = %s, total_pens = %s WHERE id = %s', (name, total_pens, barn_id))
        conn.commit()
        conn.close()
    
    @staticmethod
    def delete(barn_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 由于设置了外键级联删除，不需要手动删除关联数据
        cursor.execute('DELETE FROM barns WHERE id = %s', (barn_id,))
        
        conn.commit()
        conn.close()
