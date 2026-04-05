#!/usr/bin/env python3
"""
修复MySQL数据库中mating_events表的screenshot字段，将时间字符串替换为实际的图片路径
"""
import pymysql
import os
from pathlib import Path

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

def fix_screenshot_paths():
    """修复screenshot字段"""
    print("[INFO] 开始修复screenshot字段...")
    
    # 获取static/mating目录下的图片列表
    static_mating_dir = Path(__file__).parent / "static" / "mating"
    if not static_mating_dir.exists():
        print("[ERROR] static/mating目录不存在")
        return
    
    mating_images = []
    for file in static_mating_dir.iterdir():
        if file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif']:
            mating_images.append(f"/static/mating/{file.name}")
    
    if not mating_images:
        print("[ERROR] static/mating目录下没有图片文件")
        return
    
    print(f"[INFO] 找到 {len(mating_images)} 张图片")
    
    conn = get_mysql_connection()
    cursor = conn.cursor()
    
    try:
        # 获取所有screenshot字段为时间格式的记录
        cursor.execute('SELECT id, screenshot FROM mating_events WHERE screenshot LIKE "%-% %:%:%"')
        events = cursor.fetchall()
        
        print(f"[INFO] 找到 {len(events)} 条记录需要修复")
        
        # 更新记录
        for i, event in enumerate(events):
            # 循环使用图片
            image_index = i % len(mating_images)
            screenshot_path = mating_images[image_index]
            
            cursor.execute(
                'UPDATE mating_events SET screenshot = %s WHERE id = %s',
                (screenshot_path, event['id'])
            )
            
            if (i + 1) % 10 == 0:
                print(f"[INFO] 已修复 {i + 1} 条记录")
        
        conn.commit()
        print(f"[OK] 成功修复 {len(events)} 条记录")
        
    except Exception as e:
        print(f"[ERROR] 修复失败: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    fix_screenshot_paths()
