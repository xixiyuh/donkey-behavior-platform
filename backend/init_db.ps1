# 初始化数据库脚本

Write-Host "======================================"
Write-Host "初始化MySQL数据库"
Write-Host "======================================"

# 执行SQL脚本
Write-Host "[INFO] 执行init.sql脚本..."
try {
    # 先创建数据库
    mysql -u root -p123456 -e "CREATE DATABASE IF NOT EXISTS farm CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;"
    
    # 执行init.sql脚本
    mysql -u root -p123456 -D farm -e "SOURCE E:\donkey\萤石云\realtime-detector\backend\init.sql;"
    
    Write-Host "[OK] 数据库初始化成功！"
} catch {
    Write-Host "[ERROR] 数据库初始化失败: $($_.Exception.Message)"
    exit 1
}

# 测试数据库连接
Write-Host "[INFO] 测试数据库连接..."
try {
    $result = mysql -u root -p123456 -D farm -e "SELECT VERSION();"
    Write-Host "[OK] 数据库连接成功！MySQL版本: $($result[1])"
    
    # 测试表结构
    $tables = mysql -u root -p123456 -D farm -e "SHOW TABLES;"
    Write-Host "[INFO] 数据库中的表:"
    for ($i = 1; $i -lt $tables.Length; $i++) {
        Write-Host "  - $($tables[$i])"
    }
    
    # 测试默认数据
    $barn_count = mysql -u root -p123456 -D farm -e "SELECT COUNT(*) FROM barns;"
    Write-Host "[INFO] 养殖舍数量: $($barn_count[1])"
    
    $pen_count = mysql -u root -p123456 -D farm -e "SELECT COUNT(*) FROM pens;"
    Write-Host "[INFO] 栏数量: $($pen_count[1])"
    
    $camera_count = mysql -u root -p123456 -D farm -e "SELECT COUNT(*) FROM cameras;"
    Write-Host "[INFO] 摄像头数量: $($camera_count[1])"
    
} catch {
    Write-Host "[ERROR] 测试数据库连接失败: $($_.Exception.Message)"
    exit 1
}

Write-Host "======================================"
Write-Host "数据库初始化完成！"
Write-Host "======================================"
