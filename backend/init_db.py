#!/usr/bin/env python3
"""
初始化数据库脚本
"""
import pymysql
from pathlib import Path

# MySQL连接配置
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '123456',
    'cursorclass': pymysql.cursors.DictCursor
}

def init_database():
    """初始化数据库"""
    print("[INFO] 初始化数据库...")
    
    # 读取SQL脚本
    sql_file = Path(__file__).parent / "init.sql"
    if not sql_file.exists():
        print(f"[ERROR] SQL文件不存在: {sql_file}")
        return False
    
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_commands = f.read()
    
    # 分割SQL命令
    commands = sql_commands.split(';')
    
    try:
        # 连接到MySQL服务器
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 执行SQL命令
        for command in commands:
            command = command.strip()
            if command:
                try:
                    cursor.execute(command)
                    conn.commit()
                except pymysql.MySQLError as e:
                    print(f"[WARNING] 执行SQL命令失败: {e}")
                    print(f"[WARNING] 命令: {command}")
                    conn.rollback()
        
        # 关闭连接
        cursor.close()
        conn.close()
        
        print("[OK] 数据库初始化成功！")
        return True
        
    except pymysql.MySQLError as e:
        print(f"[ERROR] 数据库连接失败: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] 初始化过程中出现错误: {e}")
        return False

def test_db_connection():
    """测试数据库连接"""
    print("[INFO] 测试数据库连接...")
    
    try:
        # 连接到数据库
        conn = pymysql.connect(**DB_CONFIG, database='farm')
        cursor = conn.cursor()
        
        # 测试查询
        cursor.execute('SELECT VERSION()')
        version = cursor.fetchone()
        print(f"[OK] 数据库连接成功！MySQL版本: {version['VERSION()']}")
        
        # 测试表结构
        cursor.execute('SHOW TABLES')
        tables = cursor.fetchall()
        print(f"[INFO] 数据库中的表:")
        for table in tables:
            print(f"  - {list(table.values())[0]}")
        
        # 测试默认数据
        cursor.execute('SELECT COUNT(*) as count FROM barns')
        barn_count = cursor.fetchone()['count']
        print(f"[INFO] 养殖舍数量: {barn_count}")
        
        cursor.execute('SELECT COUNT(*) as count FROM pens')
        pen_count = cursor.fetchone()['count']
        print(f"[INFO] 栏数量: {pen_count}")
        
        cursor.execute('SELECT COUNT(*) as count FROM cameras')
        camera_count = cursor.fetchone()['count']
        print(f"[INFO] 摄像头数量: {camera_count}")
        
        # 关闭连接
        cursor.close()
        conn.close()
        
        print("[OK] 数据库测试完成，一切正常！")
        return True
        
    except pymysql.MySQLError as e:
        print(f"[ERROR] 数据库连接失败: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] 测试过程中出现错误: {e}")
        return False

def main():
    """主函数"""
    print("======================================")
    print("数据库初始化")
    print("======================================")
    
    # 初始化数据库
    success = init_database()
    
    if success:
        # 测试数据库连接
        test_db_connection()
    
    print("======================================")
    print("数据库初始化完成！")
    print("======================================")

if __name__ == "__main__":
    main()
