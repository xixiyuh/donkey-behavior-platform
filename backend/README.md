# MySQL数据库使用指南

## 1. 环境要求

- MySQL 5.7 或更高版本
- Python 3.7 或更高版本
- pymysql 库

## 2. 数据库初始化

### 2.1 方法一：使用SQL脚本初始化

1. 确保MySQL服务已经启动
2. 打开命令行工具，执行以下命令：

```bash
# 登录MySQL（输入密码后按回车）
mysql -u root -p

# 执行初始化脚本
SOURCE E:\donkey\萤石云\realtime-detector\backend\init.sql;

# 退出MySQL
EXIT;
```

### 2.2 方法二：使用Python脚本初始化

1. 安装依赖：

```bash
pip install pymysql
```

2. 运行数据库测试脚本：

```bash
python test_db_connection.py
```

## 3. 数据库结构

### 表结构

- **barns**：养殖舍表
  - id：主键
  - name：养殖舍名称
  - total_pens：总栏数
  - created_at：创建时间

- **pens**：栏表
  - id：主键
  - pen_number：栏号
  - barn_id：养殖舍ID（外键）
  - created_at：创建时间

- **cameras**：摄像头表
  - id：主键
  - camera_id：摄像头ID
  - pen_id：栏ID（外键）
  - barn_id：养殖舍ID（外键）
  - flv_url：视频流地址
  - created_at：创建时间

- **camera_configs**：摄像头配置表
  - id：主键
  - camera_id：摄像头ID
  - flv_url：视频流地址
  - barn_id：养殖舍ID（外键）
  - pen_id：栏ID（外键）
  - status：状态（1=启用，0=禁用）
  - start_time：开始检测时间
  - end_time：结束检测时间
  - created_at：创建时间

- **mating_events**：交配事件表
  - id：主键
  - camera_id：摄像头ID
  - pen_id：栏ID（外键）
  - barn_id：养殖舍ID（外键）
  - start_time：开始时间
  - end_time：结束时间
  - duration：持续时间（秒）
  - avg_confidence：平均置信度
  - max_confidence：最高置信度
  - movement：移动距离
  - screenshot：截图路径
  - created_at：创建时间

## 4. 数据导入

### 4.1 从SQLite迁移数据

如果您之前使用的是SQLite数据库，可以使用以下步骤迁移数据：

1. 确保SQLite数据库文件存在于 `backend/data/farm.db`
2. 运行数据迁移脚本：

```bash
python data_migration.py
```

### 4.2 手动导入数据

您可以通过以下方式手动导入数据：

1. 使用MySQL Workbench或其他MySQL客户端工具
2. 执行SQL INSERT语句
3. 使用CSV文件导入

## 5. 配置修改

### 5.1 数据库连接配置

如果需要修改数据库连接配置，请编辑 `database.py` 文件：

```python
# MySQL连接配置
DB_CONFIG = {
    'host': 'localhost',      # 数据库主机
    'user': 'root',           # 数据库用户名
    'password': '123456',      # 数据库密码
    'database': 'farm',        # 数据库名称
    'cursorclass': pymysql.cursors.DictCursor
}
```

### 5.2 静态文件配置

确保静态文件目录存在：

```bash
# 创建静态文件目录
mkdir -p static/mating_screenshots
mkdir -p static/mating_screenshots_trash
```

## 6. 常见问题

### 6.1 外键约束错误

如果遇到外键约束错误（如 `Cannot add or update a child row: a foreign key constraint fails`），请确保：

1. 先插入父表数据（如barns、pens），再插入子表数据
2. 外键引用的ID在父表中存在
3. 对于本地视频测试，可以修改 `mating_detector.py` 中的代码，使用有效的pen_id和barn_id

### 6.2 数据库连接失败

如果遇到数据库连接失败，请检查：

1. MySQL服务是否启动
2. 数据库用户名和密码是否正确
3. 数据库名称是否存在
4. 网络连接是否正常

## 7. 测试

### 7.1 测试数据库连接

运行以下命令测试数据库连接：

```bash
python test_db_connection.py
```

### 7.2 测试数据插入

运行以下命令测试数据插入：

```bash
# 启动后端服务
uvicorn modules.main:app --host 127.0.0.1 --port 8080

# 在浏览器中访问
http://localhost:8080/health
```

## 8. 注意事项

1. 确保MySQL服务始终运行
2. 定期备份数据库
3. 避免直接修改数据库结构，如需修改请更新 `init.sql` 文件
4. 对于生产环境，建议使用更安全的数据库用户和密码
