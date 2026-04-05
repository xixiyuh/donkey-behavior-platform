#!/usr/bin/env python3
"""
数据迁移脚本：将SQLite数据库中的数据迁移到MySQL
"""
import sqlite3
import pymysql
import os
from pathlib import Path

# SQLite数据库路径
SQLITE_DB = str(Path(__file__).parent / "data" / "farm.db")

# MySQL连接配置
MYSQL_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '123456',
    'database': 'farm',
    'cursorclass': pymysql.cursors.DictCursor
}

def get_sqlite_connection():
    """获取SQLite数据库连接"""
    conn = sqlite3.connect(SQLITE_DB)
    conn.row_factory = sqlite3.Row
    return conn

def get_mysql_connection():
    """获取MySQL数据库连接"""
    conn = pymysql.connect(**MYSQL_CONFIG)
    return conn

def truncate_tables():
    """清空MySQL中的表数据"""
    print("[INFO] 清空MySQL表数据...")
    
    conn = get_mysql_connection()
    cursor = conn.cursor()
    
    try:
        # 禁用外键检查
        cursor.execute('SET FOREIGN_KEY_CHECKS = 0')
        
        # 按照依赖关系的反序清空表
        tables = ['mating_events', 'cameras', 'camera_configs', 'pens', 'barns']
        for table in tables:
            cursor.execute(f'DELETE FROM {table}')
        
        # 重置自增ID
        for table in tables:
            cursor.execute(f'ALTER TABLE {table} AUTO_INCREMENT = 1')
        
        # 启用外键检查
        cursor.execute('SET FOREIGN_KEY_CHECKS = 1')
        
        conn.commit()
        print("[OK] 成功清空表数据")
    except Exception as e:
        print(f"[ERROR] 清空表数据失败: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def get_column_names(cursor, table):
    """获取表的列名"""
    cursor.execute(f'PRAGMA table_info({table})')
    columns = [row[1] for row in cursor.fetchall()]
    return columns

def migrate_barns():
    """迁移养殖舍数据"""
    print("[INFO] 开始迁移养殖舍数据...")
    
    sqlite_conn = get_sqlite_connection()
    sqlite_cursor = sqlite_conn.cursor()
    
    mysql_conn = get_mysql_connection()
    mysql_cursor = mysql_conn.cursor()
    
    try:
        # 获取SQLite表的列名
        columns = get_column_names(sqlite_cursor, 'barns')
        
        # 从SQLite读取数据
        sqlite_cursor.execute('SELECT * FROM barns')
        barns = sqlite_cursor.fetchall()
        
        # 插入到MySQL
        for barn in barns:
            # 使用索引访问，避免get方法
            id = barn[0] if 'id' in columns else None
            name = barn[1] if 'name' in columns else ''
            total_pens = barn[2] if 'total_pens' in columns else 0
            created_at = barn[3] if 'created_at' in columns else None
            
            mysql_cursor.execute(
                'INSERT INTO barns (id, name, total_pens, created_at) VALUES (%s, %s, %s, %s)',
                (id, name, total_pens, created_at)
            )
        
        mysql_conn.commit()
        print(f"[OK] 成功迁移 {len(barns)} 个养殖舍")
        
    except Exception as e:
        print(f"[ERROR] 迁移养殖舍数据失败: {e}")
        mysql_conn.rollback()
    finally:
        sqlite_cursor.close()
        sqlite_conn.close()
        mysql_cursor.close()
        mysql_conn.close()

def migrate_pens():
    """迁移栏数据"""
    print("[INFO] 开始迁移栏数据...")
    
    sqlite_conn = get_sqlite_connection()
    sqlite_cursor = sqlite_conn.cursor()
    
    mysql_conn = get_mysql_connection()
    mysql_cursor = mysql_conn.cursor()
    
    try:
        # 获取SQLite表的列名
        columns = get_column_names(sqlite_cursor, 'pens')
        
        # 从SQLite读取数据
        sqlite_cursor.execute('SELECT * FROM pens')
        pens = sqlite_cursor.fetchall()
        
        # 插入到MySQL
        for pen in pens:
            # 使用索引访问，避免get方法
            id = pen[0] if 'id' in columns else None
            pen_number = pen[1] if 'pen_number' in columns else 0
            barn_id = pen[2] if 'barn_id' in columns else 0
            created_at = pen[3] if 'created_at' in columns else None
            
            mysql_cursor.execute(
                'INSERT INTO pens (id, pen_number, barn_id, created_at) VALUES (%s, %s, %s, %s)',
                (id, pen_number, barn_id, created_at)
            )
        
        mysql_conn.commit()
        print(f"[OK] 成功迁移 {len(pens)} 个栏")
        
    except Exception as e:
        print(f"[ERROR] 迁移栏数据失败: {e}")
        mysql_conn.rollback()
    finally:
        sqlite_cursor.close()
        sqlite_conn.close()
        mysql_cursor.close()
        mysql_conn.close()

def migrate_cameras():
    """迁移摄像头数据"""
    print("[INFO] 开始迁移摄像头数据...")
    
    sqlite_conn = get_sqlite_connection()
    sqlite_cursor = sqlite_conn.cursor()
    
    mysql_conn = get_mysql_connection()
    mysql_cursor = mysql_conn.cursor()
    
    try:
        # 获取SQLite表的列名
        columns = get_column_names(sqlite_cursor, 'cameras')
        
        # 从SQLite读取数据
        sqlite_cursor.execute('SELECT * FROM cameras')
        cameras = sqlite_cursor.fetchall()
        
        # 插入到MySQL
        for camera in cameras:
            # 使用索引访问，避免get方法
            id = camera[0] if 'id' in columns else None
            camera_id = camera[1] if 'camera_id' in columns else ''
            pen_id = camera[2] if 'pen_id' in columns else 0
            barn_id = camera[3] if 'barn_id' in columns else 0
            flv_url = camera[4] if 'flv_url' in columns else ''
            created_at = camera[5] if 'created_at' in columns else None
            
            mysql_cursor.execute(
                'INSERT INTO cameras (id, camera_id, pen_id, barn_id, flv_url, created_at) VALUES (%s, %s, %s, %s, %s, %s)',
                (id, camera_id, pen_id, barn_id, flv_url, created_at)
            )
        
        mysql_conn.commit()
        print(f"[OK] 成功迁移 {len(cameras)} 个摄像头")
        
    except Exception as e:
        print(f"[ERROR] 迁移摄像头数据失败: {e}")
        mysql_conn.rollback()
    finally:
        sqlite_cursor.close()
        sqlite_conn.close()
        mysql_cursor.close()
        mysql_conn.close()

def migrate_mating_events():
    """迁移交配事件数据"""
    print("[INFO] 开始迁移交配事件数据...")
    
    # 获取static/mating目录下的图片列表
    static_mating_dir = Path(__file__).parent.parent / "static" / "mating"
    mating_images = []
    if static_mating_dir.exists():
        for file in static_mating_dir.iterdir():
            if file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif']:
                mating_images.append(f"/static/mating/{file.name}")
    
    if mating_images:
        print(f"[INFO] 找到 {len(mating_images)} 张图片用于替换screenshot字段")
    else:
        print("[WARNING] 未找到图片，screenshot字段将保持原值")
    
    sqlite_conn = get_sqlite_connection()
    sqlite_cursor = sqlite_conn.cursor()
    
    mysql_conn = get_mysql_connection()
    mysql_cursor = mysql_conn.cursor()
    
    try:
        # 禁用外键检查
        mysql_cursor.execute('SET FOREIGN_KEY_CHECKS = 0')
        
        # 获取SQLite表的列名
        columns = get_column_names(sqlite_cursor, 'mating_events')
        
        # 从SQLite读取数据
        sqlite_cursor.execute('SELECT * FROM mating_events')
        events = sqlite_cursor.fetchall()
        
        # 插入到MySQL
        for i, event in enumerate(events):
            # 使用索引访问，避免get方法
            id = event[0] if 'id' in columns else None
            camera_id = event[1] if 'camera_id' in columns else ''
            pen_id = event[2] if 'pen_id' in columns else 0
            barn_id = event[3] if 'barn_id' in columns else 0
            start_time = event[4] if 'start_time' in columns else None
            end_time = event[5] if 'end_time' in columns else None
            duration = event[6] if 'duration' in columns else 0
            avg_confidence = event[7] if 'avg_confidence' in columns else 0.0
            max_confidence = event[8] if 'max_confidence' in columns else 0.0
            # 检查是否有movement字段，并处理数据类型
            movement = 0.0
            if 'movement' in columns and len(event) > 9:
                try:
                    movement = float(event[9])
                except (ValueError, TypeError):
                    movement = 0.0
            # 检查是否有screenshot字段
            screenshot = None
            if 'screenshot' in columns and len(event) > 10:
                screenshot = event[10]
                # 如果screenshot是时间格式，替换为图片路径
                if screenshot and isinstance(screenshot, str) and ' ' in screenshot and ':' in screenshot:
                    if mating_images:
                        # 循环使用图片
                        image_index = i % len(mating_images)
                        screenshot = mating_images[image_index]
            # 检查是否有created_at字段，并处理无效值
            created_at = None
            if 'created_at' in columns and len(event) > 11:
                created_at_val = event[11]
                if created_at_val:
                    created_at_str = str(created_at_val)
                    # 过滤掉非datetime格式的值
                    if created_at_str != '0' and '.' not in created_at_str:
                        created_at = created_at_val
            
            mysql_cursor.execute(
                'INSERT INTO mating_events (id, camera_id, pen_id, barn_id, start_time, end_time, duration, avg_confidence, max_confidence, movement, screenshot, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
                (id, camera_id, pen_id, barn_id, start_time, end_time, duration, avg_confidence, max_confidence, movement, screenshot, created_at)
            )
        
        # 启用外键检查
        mysql_cursor.execute('SET FOREIGN_KEY_CHECKS = 1')
        
        mysql_conn.commit()
        print(f"[OK] 成功迁移 {len(events)} 个交配事件")
        
    except Exception as e:
        print(f"[ERROR] 迁移交配事件数据失败: {e}")
        mysql_conn.rollback()
    finally:
        # 确保启用外键检查
        try:
            mysql_cursor.execute('SET FOREIGN_KEY_CHECKS = 1')
        except:
            pass
        sqlite_cursor.close()
        sqlite_conn.close()
        mysql_cursor.close()
        mysql_conn.close()

def migrate_camera_configs():
    """迁移摄像头配置数据"""
    print("[INFO] 开始迁移摄像头配置数据...")
    
    sqlite_conn = get_sqlite_connection()
    sqlite_cursor = sqlite_conn.cursor()
    
    mysql_conn = get_mysql_connection()
    mysql_cursor = mysql_conn.cursor()
    
    try:
        # 获取SQLite表的列名
        columns = get_column_names(sqlite_cursor, 'camera_configs')
        
        # 从SQLite读取数据
        sqlite_cursor.execute('SELECT * FROM camera_configs')
        configs = sqlite_cursor.fetchall()
        
        # 插入到MySQL
        for config in configs:
            # 使用索引访问，避免get方法
            id = config[0] if 'id' in columns else None
            camera_id = config[1] if 'camera_id' in columns else ''
            flv_url = config[2] if 'flv_url' in columns else ''
            barn_id = config[3] if 'barn_id' in columns else 0
            pen_id = config[4] if 'pen_id' in columns else 0
            # 检查是否有status字段，并处理数据类型
            status = 1
            if 'status' in columns and len(config) > 5:
                try:
                    status = int(config[5])
                except (ValueError, TypeError):
                    status = 1
            # 检查是否有start_time字段
            start_time = '09:00'
            if 'start_time' in columns and len(config) > 6:
                start_time = config[6]
            # 检查是否有end_time字段，并限制长度
            end_time = '19:00'
            if 'end_time' in columns and len(config) > 7:
                end_time_val = str(config[7])
                # 限制长度为5（HH:MM格式）
                if len(end_time_val) > 5:
                    end_time = end_time_val[:5]
                else:
                    end_time = end_time_val
            # 检查是否有created_at字段，并处理无效值
            created_at = None
            if 'created_at' in columns and len(config) > 8:
                created_at_val = config[8]
                if created_at_val:
                    created_at_str = str(created_at_val)
                    # 过滤掉非datetime格式的值
                    if created_at_str != '0' and '.' not in created_at_str:
                        created_at = created_at_val
            
            mysql_cursor.execute(
                'INSERT INTO camera_configs (id, camera_id, flv_url, barn_id, pen_id, status, start_time, end_time, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)',
                (id, camera_id, flv_url, barn_id, pen_id, status, start_time, end_time, created_at)
            )
        
        mysql_conn.commit()
        print(f"[OK] 成功迁移 {len(configs)} 个摄像头配置")
        
    except Exception as e:
        print(f"[ERROR] 迁移摄像头配置数据失败: {e}")
        mysql_conn.rollback()
    finally:
        sqlite_cursor.close()
        sqlite_conn.close()
        mysql_cursor.close()
        mysql_conn.close()

def main():
    """主函数"""
    print("======================================")
    print("数据迁移：SQLite -> MySQL")
    print("======================================")
    
    # 先清空MySQL表数据
    truncate_tables()
    
    # 迁移数据
    migrate_barns()
    migrate_pens()
    migrate_cameras()
    migrate_mating_events()
    migrate_camera_configs()
    
    print("======================================")
    print("数据迁移完成！")
    print("======================================")

if __name__ == "__main__":
    main()
