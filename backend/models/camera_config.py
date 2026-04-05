from ..database import get_db_connection
from datetime import datetime

class CameraConfig:
    @staticmethod
    def create(camera_id, flv_url, barn_id, pen_id, start_time='09:00', end_time='19:00', status=1):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO camera_configs (camera_id, flv_url, barn_id, pen_id, start_time, end_time, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', (camera_id, flv_url, barn_id, pen_id, start_time, end_time, status))
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
        total = cursor.fetchone()['COUNT(*)']
        
        # 获取分页数据
        offset = (page - 1) * page_size
        cursor.execute('SELECT * FROM camera_configs LIMIT %s OFFSET %s', (page_size, offset))
        configs = cursor.fetchall()
        conn.close()
        
        return {
            'items': configs,
            'total': total,
            'page': page,
            'page_size': page_size
        }
    
    @staticmethod
    def get_active():
        """
        获取当前应该激活的摄像头配置
        - status=1: 启用状态，直接返回
        - status=2: 自动状态，根据时间判断
        - status=0: 禁用状态，不返回
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM camera_configs')
        all_configs = cursor.fetchall()
        conn.close()
        
        active_configs = []
        current_time = datetime.now().time()
        
        for config in all_configs:
            status = config['status']
            
            # 启用状态，直接加入
            if status == 1:
                active_configs.append(config)
            # 自动状态，根据时间判断
            elif status == 2:
                start_time = datetime.strptime(config['start_time'], '%H:%M').time()
                end_time = datetime.strptime(config['end_time'], '%H:%M').time()
                if start_time <= current_time <= end_time:
                    active_configs.append(config)
            # 禁用状态，跳过
            else:
                continue
        
        return active_configs
    
    @staticmethod
    def set_status(id, status):
        """
        设置摄像头配置的状态
        status: 0=禁用, 1=启用, 2=自动
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE camera_configs SET status = %s WHERE id = %s', (status, id))
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_by_id(id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM camera_configs WHERE id = %s', (id,))
        config = cursor.fetchone()
        conn.close()
        return config
    
    @staticmethod
    def delete(id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM camera_configs WHERE id = %s', (id,))
        conn.commit()
        conn.close()
