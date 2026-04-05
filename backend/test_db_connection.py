#!/usr/bin/env python3
"""
测试数据库连接
"""
import pymysql
from pathlib import Path

# MySQL连接配置
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '123456',
    'database': 'farm',
    'cursorclass': pymysql.cursors.DictCursor
}

def test_db_connection():
    """测试数据库连接"""
    print("[INFO] 测试数据库连接...")
    
    try:
        # 尝试连接数据库
        conn = pymysql.connect(**DB_CONFIG)
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
        print("[INFO] 请确保MySQL服务已启动，并且init.sql脚本已执行")
        return False
    except Exception as e:
        print(f"[ERROR] 测试过程中出现错误: {e}")
        return False

def main():
    """主函数"""
    print("======================================")
    print("数据库连接测试")
    print("======================================")
    
    success = test_db_connection()
    
    if not success:
        print("\n[INFO] 请按照以下步骤操作:")
        print("1. 启动MySQL服务")
        print("2. 执行init.sql脚本初始化数据库")
        print("   mysql -u root -p < init.sql")
        print("3. 再次运行此测试脚本")
    
    print("======================================")

if __name__ == "__main__":
    main()
