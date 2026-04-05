-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS farm CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;

-- 使用farm数据库
USE farm;

-- 创建养殖舍表
CREATE TABLE IF NOT EXISTS barns (
    id INT NOT NULL AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    total_pens INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 创建栏表
CREATE TABLE IF NOT EXISTS pens (
    id INT NOT NULL AUTO_INCREMENT,
    pen_number INT NOT NULL,
    barn_id INT NOT NULL,
    created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY barn_id (barn_id),
    CONSTRAINT pens_ibfk_1 FOREIGN KEY (barn_id) REFERENCES barns (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 创建摄像头表
CREATE TABLE IF NOT EXISTS cameras (
    id INT NOT NULL AUTO_INCREMENT,
    camera_id VARCHAR(255) NOT NULL,
    pen_id INT NOT NULL,
    barn_id INT NOT NULL,
    flv_url VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY pen_id (pen_id),
    KEY barn_id (barn_id),
    CONSTRAINT cameras_ibfk_1 FOREIGN KEY (pen_id) REFERENCES pens (id) ON DELETE CASCADE,
    CONSTRAINT cameras_ibfk_2 FOREIGN KEY (barn_id) REFERENCES barns (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 创建摄像头配置表
CREATE TABLE IF NOT EXISTS camera_configs (
    id INT NOT NULL AUTO_INCREMENT,
    camera_id VARCHAR(255) NOT NULL,
    flv_url VARCHAR(255) NOT NULL,
    barn_id INT NOT NULL,
    pen_id INT NOT NULL,
    status INT NOT NULL DEFAULT 1,
    start_time VARCHAR(5) NOT NULL DEFAULT '09:00',
    end_time VARCHAR(5) NOT NULL DEFAULT '19:00',
    created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY barn_id (barn_id),
    KEY pen_id (pen_id),
    CONSTRAINT camera_configs_ibfk_1 FOREIGN KEY (barn_id) REFERENCES barns (id) ON DELETE CASCADE,
    CONSTRAINT camera_configs_ibfk_2 FOREIGN KEY (pen_id) REFERENCES pens (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 创建交配事件表
CREATE TABLE IF NOT EXISTS mating_events (
    id INT NOT NULL AUTO_INCREMENT,
    camera_id VARCHAR(255) NOT NULL,
    pen_id INT NOT NULL,
    barn_id INT NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    duration INT NOT NULL,
    avg_confidence FLOAT NOT NULL,
    max_confidence FLOAT NOT NULL,
    movement FLOAT NOT NULL,
    screenshot VARCHAR(255) DEFAULT NULL,
    created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY pen_id (pen_id),
    KEY barn_id (barn_id),
    CONSTRAINT mating_events_ibfk_1 FOREIGN KEY (pen_id) REFERENCES pens (id) ON DELETE CASCADE,
    CONSTRAINT mating_events_ibfk_2 FOREIGN KEY (barn_id) REFERENCES barns (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 插入默认数据
-- 插入默认养殖舍
INSERT IGNORE INTO barns (id, name, total_pens) VALUES
(1, '养殖舍1', 5),
(2, '养殖舍2', 5);

-- 插入默认栏
INSERT IGNORE INTO pens (id, pen_number, barn_id) VALUES
(1, 1, 1),
(2, 2, 1),
(3, 3, 1),
(4, 4, 1),
(5, 5, 1),
(6, 1, 2),
(7, 2, 2),
(8, 3, 2),
(9, 4, 2),
(10, 5, 2);

-- 插入默认摄像头
INSERT IGNORE INTO cameras (id, camera_id, pen_id, barn_id, flv_url) VALUES
(1, 'camera1', 1, 1, 'rtsp://example.com/camera1'),
(2, 'camera2', 2, 1, 'rtsp://example.com/camera2'),
(3, 'camera3', 6, 2, 'rtsp://example.com/camera3'),
(4, 'camera4', 7, 2, 'rtsp://example.com/camera4');

-- 插入默认摄像头配置
INSERT IGNORE INTO camera_configs (id, camera_id, flv_url, barn_id, pen_id, status, start_time, end_time) VALUES
(1, 'camera1', 'rtsp://example.com/camera1', 1, 1, 1, '09:00', '19:00'),
(2, 'camera2', 'rtsp://example.com/camera2', 1, 2, 1, '09:00', '19:00'),
(3, 'camera3', 'rtsp://example.com/camera3', 2, 6, 1, '09:00', '19:00'),
(4, 'camera4', 'rtsp://example.com/camera4', 2, 7, 1, '09:00', '19:00');
