#!/usr/bin/env python3
"""
检查MySQL数据库中mating_events表的screenshot字段内容
"""
import pymysql

# MySQL连接配置
MYSQL_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '123456',
    'database': 'farm',
    'cursorclass': pymysql.cursors.DictCursor
}

def get_mysql_connection():
    """获取MySQL数据库连接"""
    conn = pymysql.connect(**MYSQL_CONFIG)
    return conn

def check_screenshot_fields():
    """检查screenshot字段"""
    print("[INFO] 检查MySQL数据库中的mating_events表...")
    
    conn = get_mysql_connection()
    cursor = conn.cursor()
    
    try:
        # 获取表结构
        cursor.execute('DESCRIBE mating_events')
        columns = cursor.fetchall()
        print("[INFO] 表结构:")
        for col in columns:
            print(f"  {col['Field']}: {col['Type']}")
        
        # 查看数据
        cursor.execute('SELECT id, screenshot, start_time FROM mating_events LIMIT 10')
        events = cursor.fetchall()
        print("\n[INFO] 前10条记录:")
        for event in events:
            print(f"  ID: {event['id']}")
            print(f"  Screenshot: {event['screenshot']}")
            print(f"  Start Time: {event['start_time']}")
            print(f"  Screenshot类型: {type(event['screenshot'])}")
            if event['screenshot']:
                print(f"  Screenshot长度: {len(str(event['screenshot']))}")
            print()
        
        # 统计screenshot字段的不同类型
        cursor.execute('SELECT DISTINCT screenshot FROM mating_events LIMIT 20')
        distinct_screenshots = cursor.fetchall()
        print("\n[INFO] 不同的screenshot值:")
        for item in distinct_screenshots:
            print(f"  {item['screenshot']}")
        
    except Exception as e:
        print(f"[ERROR] 检查失败: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    check_screenshot_fields()
