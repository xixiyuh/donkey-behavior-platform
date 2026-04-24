from ..database import get_db_connection

class MatingEvent:
    @staticmethod
    def create(camera_id, pen_id, barn_id, start_time, end_time, duration, avg_confidence, max_confidence, movement, 
               screenshot=None):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO mating_events (camera_id, pen_id, barn_id, start_time, end_time, duration, 
                                 avg_confidence, max_confidence, movement, screenshot)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (camera_id, pen_id, barn_id, start_time, end_time, duration, avg_confidence, max_confidence, movement,
              screenshot))
        conn.commit()
        event_id = cursor.lastrowid
        conn.close()
        return event_id

    @staticmethod
    def get_all(page=1, page_size=10):
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM mating_events')
        total = cursor.fetchone()['COUNT(*)']

        offset = (page - 1) * page_size
        cursor.execute('SELECT * FROM mating_events ORDER BY start_time DESC LIMIT %s OFFSET %s', (page_size, offset))
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
        cursor.execute('SELECT * FROM mating_events WHERE id = %s', (event_id,))
        event = cursor.fetchone()
        conn.close()
        return event

    @staticmethod
    def get_by_pen(pen_id, page=1, page_size=10):
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM mating_events WHERE pen_id = %s', (pen_id,))
        total = cursor.fetchone()['COUNT(*)']

        offset = (page - 1) * page_size
        cursor.execute('SELECT * FROM mating_events WHERE pen_id = %s ORDER BY start_time DESC LIMIT %s OFFSET %s', (pen_id, page_size, offset))
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

        cursor.execute('SELECT COUNT(*) FROM mating_events WHERE barn_id = %s', (barn_id,))
        total = cursor.fetchone()['COUNT(*)']

        offset = (page - 1) * page_size
        cursor.execute('SELECT * FROM mating_events WHERE barn_id = %s ORDER BY start_time DESC LIMIT %s OFFSET %s', (barn_id, page_size, offset))
        events = cursor.fetchall()
        conn.close()

        return {
            'items': events,
            'total': total,
            'page': page,
            'page_size': page_size
        }

    @staticmethod
    def get_by_camera(camera_id, page=1, page_size=10):
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM mating_events WHERE camera_id = %s', (camera_id,))
        total = cursor.fetchone()['COUNT(*)']

        offset = (page - 1) * page_size
        cursor.execute(
            'SELECT * FROM mating_events WHERE camera_id = %s ORDER BY start_time DESC LIMIT %s OFFSET %s',
            (camera_id, page_size, offset)
        )
        events = cursor.fetchall()
        conn.close()

        return {
            'items': events,
            'total': total,
            'page': page,
            'page_size': page_size
        }