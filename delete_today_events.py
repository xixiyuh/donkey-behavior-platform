import sqlite3
import datetime

# 连接到SQLite数据库
conn = sqlite3.connect('data/farm.db')
cursor = conn.cursor()

# 获取今天的日期（格式：YYYY-MM-DD）
today = datetime.date.today().strftime('%Y-%m-%d')
print(f"删除日期为 {today} 的所有事件")

# 1. 查看数据库中的表结构
print("\n数据库表结构：")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
for table in tables:
    print(f"表名: {table[0]}")
    # 查看表的列结构
    cursor.execute(f"PRAGMA table_info({table[0]});")
    columns = cursor.fetchall()
    for column in columns:
        print(f"  - {column[1]} ({column[2]})")

# 2. 查找事件相关的表
# 通常事件表可能命名为 events, mating_events 等
# 假设表名为 mating_events
print("\n查看 mating_events 表中的今天事件：")
try:
    cursor.execute(f"SELECT COUNT(*) FROM mating_events WHERE DATE(created_at) = '{today}';")
    count = cursor.fetchone()[0]
    print(f"今天的事件数量: {count}")
    
    # 如果有今天的事件，删除它们
    if count > 0:
        cursor.execute(f"DELETE FROM mating_events WHERE DATE(created_at) = '{today}';")
        conn.commit()
        print(f"成功删除 {count} 条今天的事件")
    else:
        print("今天没有事件需要删除")
except sqlite3.Error as e:
    print(f"错误: {e}")

# 关闭数据库连接
conn.close()
print("\n操作完成")
