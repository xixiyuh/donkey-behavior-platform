from ..database import get_db_connection

class Barn:
    @staticmethod
    def create(name, total_pens):
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute('INSERT INTO barns (name, total_pens) VALUES (%s, %s)', (name, total_pens))
                conn.commit()
                return cursor.lastrowid

    @staticmethod
    def get_all(page=1, page_size=10):
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute('SELECT COUNT(*) FROM barns')
                total = cursor.fetchone()['COUNT(*)']

                offset = (page - 1) * page_size
                cursor.execute('SELECT * FROM barns ORDER BY id LIMIT %s OFFSET %s', (page_size, offset))
                barns = cursor.fetchall()

                return {
                    'items': barns,
                    'total': total,
                    'page': page,
                    'page_size': page_size
                }

    @staticmethod
    def get_by_id(barn_id):
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute('SELECT * FROM barns WHERE id = %s', (barn_id,))
                return cursor.fetchone()

    @staticmethod
    def update(barn_id, name, total_pens):
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute('UPDATE barns SET name = %s, total_pens = %s WHERE id = %s', (name, total_pens, barn_id))
                conn.commit()

    @staticmethod
    def delete(barn_id):
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute('SELECT id FROM pens WHERE barn_id = %s', (barn_id,))
                pen_ids = [pen['id'] for pen in cursor.fetchall()]

                if pen_ids:
                    for pen_id in pen_ids:
                        cursor.execute('DELETE FROM cameras WHERE pen_id = %s', (pen_id,))

                cursor.execute('DELETE FROM pens WHERE barn_id = %s', (barn_id,))
                cursor.execute('DELETE FROM barns WHERE id = %s', (barn_id,))

                conn.commit()
