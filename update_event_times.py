#!/usr/bin/env python3
"""
更新事件表中所有记录的开始时间和结束时间为2026.3.27下午1-6点
确保结束时间-开始时间与持续时间匹配
"""
import sqlite3
import random
from datetime import datetime, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[0]
DB_PATH = str(BASE_DIR / "data" / "farm.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def update_event_times():
    """更新事件表中所有记录的时间"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 获取所有事件记录
        cursor.execute('SELECT id, duration FROM mating_events')
        events = cursor.fetchall()
        
        print(f"Found {len(events)} events to update")
        
        # 2026.3.27下午1-6点的时间范围
        start_range = datetime(2026, 3, 27, 13, 0, 0)  # 13:00
        end_range = datetime(2026, 3, 27, 18, 0, 0)  # 18:00
        range_seconds = (end_range - start_range).total_seconds()
        
        for event in events:
            event_id = event['id']
            duration = event['duration']
            
            # 生成随机开始时间（确保结束时间不超过18:00）
            max_start_seconds = range_seconds - duration
            if max_start_seconds <= 0:
                # 如果持续时间太长，使用13:00作为开始时间
                start_time = start_range
            else:
                # 随机生成开始时间
                start_offset = random.randint(0, int(max_start_seconds))
                start_time = start_range + timedelta(seconds=start_offset)
            
            # 计算结束时间
            end_time = start_time + timedelta(seconds=duration)
            
            # 更新数据库
            cursor.execute('''
            UPDATE mating_events 
            SET start_time = ?, end_time = ? 
            WHERE id = ?
            ''', (start_time.strftime('%Y-%m-%d %H:%M:%S'), 
                  end_time.strftime('%Y-%m-%d %H:%M:%S'), 
                  event_id))
            
            print(f"Updated event {event_id}: start={start_time.strftime('%H:%M:%S')}, end={end_time.strftime('%H:%M:%S')}, duration={duration}s")
        
        conn.commit()
        print(f"Updated {len(events)} events successfully")
        
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    update_event_times()
