#!/usr/bin/env python3
"""
测试脚本：验证MySQL数据库的增删改查功能
"""
import requests
import json
import time

BASE_URL = "http://127.0.0.1:8081/api"

# 测试养殖舍管理
def test_barns():
    print("\n=== 测试养殖舍管理 ===")
    
    # 1. 创建养殖舍
    print("1. 创建养殖舍...")
    barn_name = f"测试养殖舍_{int(time.time())}"
    barn_data = {"name": barn_name, "total_pens": 5}
    response = requests.post(f"{BASE_URL}/barns", json=barn_data)
    print(f"创建养殖舍: {response.status_code}")
    if response.status_code == 200:
        barn_id = response.json()["id"]
        print(f"创建成功，ID: {barn_id}")
    else:
        print(f"创建失败: {response.text}")
        return None
    
    # 2. 获取所有养殖舍
    print("2. 获取所有养殖舍...")
    response = requests.get(f"{BASE_URL}/barns")
    print(f"获取养殖舍: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"总数量: {data['total']}")
        print(f"第一页数量: {len(data['items'])}")
    
    # 3. 获取单个养殖舍
    print("3. 获取单个养殖舍...")
    response = requests.get(f"{BASE_URL}/barns/{barn_id}")
    print(f"获取单个养殖舍: {response.status_code}")
    if response.status_code == 200:
        print(f"养殖舍名称: {response.json()['name']}")
    
    # 4. 更新养殖舍
    print("4. 更新养殖舍...")
    update_data = {"name": "更新后的养殖舍", "total_pens": 10}
    response = requests.put(f"{BASE_URL}/barns/{barn_id}", json=update_data)
    print(f"更新养殖舍: {response.status_code}")
    if response.status_code == 200:
        print(f"更新后名称: {response.json()['name']}")
    
    # 5. 删除养殖舍
    print("5. 删除养殖舍...")
    response = requests.delete(f"{BASE_URL}/barns/{barn_id}")
    print(f"删除养殖舍: {response.status_code}")
    if response.status_code == 200:
        print("删除成功")
    
    return barn_id

# 测试栏管理
def test_pens(barn_id):
    if not barn_id:
        print("\n=== 跳过测试栏管理（需要养殖舍ID）===")
        return None
    
    print("\n=== 测试栏管理 ===")
    
    # 1. 创建栏
    print("1. 创建栏...")
    pen_data = {"pen_number": 1, "barn_id": barn_id}
    response = requests.post(f"{BASE_URL}/pens", json=pen_data)
    print(f"创建栏: {response.status_code}")
    if response.status_code == 200:
        pen_id = response.json()["id"]
        print(f"创建成功，ID: {pen_id}")
    else:
        print(f"创建失败: {response.text}")
        return None
    
    # 2. 获取所有栏
    print("2. 获取所有栏...")
    response = requests.get(f"{BASE_URL}/pens")
    print(f"获取栏: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"总数量: {data['total']}")
    
    # 3. 获取单个栏
    print("3. 获取单个栏...")
    response = requests.get(f"{BASE_URL}/pens/{pen_id}")
    print(f"获取单个栏: {response.status_code}")
    if response.status_code == 200:
        print(f"栏号: {response.json()['pen_number']}")
    
    # 4. 获取养殖舍下的所有栏
    print("4. 获取养殖舍下的所有栏...")
    response = requests.get(f"{BASE_URL}/pens/barns/{barn_id}/pens")
    print(f"获取养殖舍下的栏: {response.status_code}")
    if response.status_code == 200:
        print(f"数量: {len(response.json())}")
    
    # 5. 更新栏
    print("5. 更新栏...")
    update_data = {"pen_number": 2, "barn_id": barn_id}
    response = requests.put(f"{BASE_URL}/pens/{pen_id}", json=update_data)
    print(f"更新栏: {response.status_code}")
    if response.status_code == 200:
        print(f"更新后栏号: {response.json()['pen_number']}")
    
    # 6. 删除栏
    print("6. 删除栏...")
    response = requests.delete(f"{BASE_URL}/pens/{pen_id}")
    print(f"删除栏: {response.status_code}")
    if response.status_code == 200:
        print("删除成功")
    
    return pen_id

# 测试摄像头管理
def test_cameras(barn_id, pen_id):
    if not (barn_id and pen_id):
        print("\n=== 跳过测试摄像头管理（需要养殖舍和栏ID）===")
        return None
    
    print("\n=== 测试摄像头管理 ===")
    
    # 1. 创建摄像头
    print("1. 创建摄像头...")
    camera_data = {
        "camera_id": "test-camera-1",
        "pen_id": pen_id,
        "barn_id": barn_id,
        "flv_url": "rtsp://test-url"
    }
    response = requests.post(f"{BASE_URL}/cameras", json=camera_data)
    print(f"创建摄像头: {response.status_code}")
    if response.status_code == 200:
        camera_id = response.json()["id"]
        print(f"创建成功，ID: {camera_id}")
    else:
        print(f"创建失败: {response.text}")
        return None
    
    # 2. 获取所有摄像头
    print("2. 获取所有摄像头...")
    response = requests.get(f"{BASE_URL}/cameras")
    print(f"获取摄像头: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"总数量: {data['total']}")
    
    # 3. 获取单个摄像头
    print("3. 获取单个摄像头...")
    response = requests.get(f"{BASE_URL}/cameras/{camera_id}")
    print(f"获取单个摄像头: {response.status_code}")
    if response.status_code == 200:
        print(f"摄像头标识: {response.json()['camera_id']}")
    
    # 4. 获取栏下的摄像头
    print("4. 获取栏下的摄像头...")
    response = requests.get(f"{BASE_URL}/cameras/pens/{pen_id}/cameras")
    print(f"获取栏下的摄像头: {response.status_code}")
    if response.status_code == 200:
        print(f"数量: {len(response.json())}")
    
    # 5. 获取养殖舍下的摄像头
    print("5. 获取养殖舍下的摄像头...")
    response = requests.get(f"{BASE_URL}/cameras/barns/{barn_id}/cameras")
    print(f"获取养殖舍下的摄像头: {response.status_code}")
    if response.status_code == 200:
        print(f"数量: {len(response.json())}")
    
    # 6. 更新摄像头
    print("6. 更新摄像头...")
    update_data = {
        "camera_id": "test-camera-updated",
        "pen_id": pen_id,
        "barn_id": barn_id,
        "flv_url": "rtsp://updated-url"
    }
    response = requests.put(f"{BASE_URL}/cameras/{camera_id}", json=update_data)
    print(f"更新摄像头: {response.status_code}")
    if response.status_code == 200:
        print(f"更新后标识: {response.json()['camera_id']}")
    
    # 7. 删除摄像头
    print("7. 删除摄像头...")
    response = requests.delete(f"{BASE_URL}/cameras/{camera_id}")
    print(f"删除摄像头: {response.status_code}")
    if response.status_code == 200:
        print("删除成功")
    
    return camera_id

# 测试摄像头配置
def test_camera_configs(barn_id, pen_id, camera_id_str):
    if not (barn_id and pen_id and camera_id_str):
        print("\n=== 跳过测试摄像头配置（需要完整参数）===")
        return None
    
    print("\n=== 测试摄像头配置 ===")
    
    # 1. 创建摄像头配置
    print("1. 创建摄像头配置...")
    config_data = {
        "camera_id": camera_id_str,
        "flv_url": "rtsp://test-config-url",
        "barn_id": barn_id,
        "pen_id": pen_id,
        "start_time": "08:00",
        "end_time": "20:00",
        "status": 1,
        "enable": 1
    }
    response = requests.post(f"{BASE_URL}/camera-configs", json=config_data)
    print(f"创建摄像头配置: {response.status_code}")
    if response.status_code == 200:
        config_id = response.json()["id"]
        print(f"创建成功，ID: {config_id}")
    else:
        print(f"创建失败: {response.text}")
        return None
    
    # 2. 获取所有摄像头配置
    print("2. 获取所有摄像头配置...")
    response = requests.get(f"{BASE_URL}/camera-configs")
    print(f"获取摄像头配置: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"总数量: {data['total']}")
    
    # 3. 设置启用状态
    print("3. 设置启用状态...")
    enable_data = {"enable": 0}
    response = requests.patch(f"{BASE_URL}/camera-configs/{config_id}/enable", json=enable_data)
    print(f"设置启用状态: {response.status_code}")
    if response.status_code == 200:
        print("设置成功")
    
    # 4. 设置状态
    print("4. 设置状态...")
    status_data = {"status": 2}
    response = requests.patch(f"{BASE_URL}/camera-configs/{config_id}/status", json=status_data)
    print(f"设置状态: {response.status_code}")
    if response.status_code == 200:
        print("设置成功")
    
    # 5. 删除摄像头配置
    print("5. 删除摄像头配置...")
    response = requests.delete(f"{BASE_URL}/camera-configs/{config_id}")
    print(f"删除摄像头配置: {response.status_code}")
    if response.status_code == 200:
        print("删除成功")
    
    return config_id

# 测试事件管理
def test_events(barn_id, pen_id, camera_id_str):
    if not (barn_id and pen_id and camera_id_str):
        print("\n=== 跳过测试事件管理（需要完整参数）===")
        return None
    
    print("\n=== 测试事件管理 ===")
    
    # 1. 创建事件
    print("1. 创建事件...")
    event_data = {
        "camera_id": camera_id_str,
        "pen_id": pen_id,
        "barn_id": barn_id,
        "start_time": "2024-01-01T00:00:00",
        "end_time": "2024-01-01T00:01:00",
        "duration": 60,
        "avg_confidence": 0.85,
        "max_confidence": 0.95,
        "movement": 0.75,
        "screenshot": "test.jpg"
    }
    response = requests.post(f"{BASE_URL}/mating-events", json=event_data)
    print(f"创建事件: {response.status_code}")
    if response.status_code == 200:
        event_id = response.json()["id"]
        print(f"创建成功，ID: {event_id}")
    else:
        print(f"创建失败: {response.text}")
        return None
    
    # 2. 获取所有事件
    print("2. 获取所有事件...")
    response = requests.get(f"{BASE_URL}/mating-events")
    print(f"获取事件: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"总数量: {data['total']}")
    
    # 3. 获取单个事件
    print("3. 获取单个事件...")
    response = requests.get(f"{BASE_URL}/mating-events/{event_id}")
    print(f"获取单个事件: {response.status_code}")
    if response.status_code == 200:
        print(f"事件时长: {response.json()['duration']}秒")
    
    # 4. 获取栏下的事件
    print("4. 获取栏下的事件...")
    response = requests.get(f"{BASE_URL}/pens/{pen_id}/mating-events")
    print(f"获取栏下的事件: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"数量: {data['total']}")
    
    # 5. 获取养殖舍下的事件
    print("5. 获取养殖舍下的事件...")
    response = requests.get(f"{BASE_URL}/barns/{barn_id}/mating-events")
    print(f"获取养殖舍下的事件: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"数量: {data['total']}")
    
    return event_id

if __name__ == "__main__":
    print("开始测试增删改查功能...")
    print(f"测试环境: {BASE_URL}")
    
    # 按顺序测试
    barn_id = test_barns()
    
    # 重新创建养殖舍和栏用于后续测试
    if not barn_id:
        barn_data = {"name": "测试养殖舍", "total_pens": 5}
        response = requests.post(f"{BASE_URL}/barns", json=barn_data)
        if response.status_code == 200:
            barn_id = response.json()["id"]
            print(f"重新创建养殖舍，ID: {barn_id}")
    
    if barn_id:
        # 创建栏
        pen_data = {"pen_number": 1, "barn_id": barn_id}
        response = requests.post(f"{BASE_URL}/pens", json=pen_data)
        if response.status_code == 200:
            pen_id = response.json()["id"]
            print(f"创建测试栏，ID: {pen_id}")
            
            # 测试栏管理
            test_pens(barn_id)
            
            # 测试摄像头
            camera_data = {
                "camera_id": "test-camera-1",
                "pen_id": pen_id,
                "barn_id": barn_id,
                "flv_url": "rtsp://test-url"
            }
            response = requests.post(f"{BASE_URL}/cameras", json=camera_data)
            if response.status_code == 200:
                camera_id = response.json()["id"]
                camera_id_str = "test-camera-1"
                print(f"创建测试摄像头，ID: {camera_id}, 标识: {camera_id_str}")
                
                # 测试摄像头管理
                test_cameras(barn_id, pen_id)
                
                # 测试其他功能
                test_camera_configs(barn_id, pen_id, camera_id_str)
                test_events(barn_id, pen_id, camera_id_str)
    
    print("\n测试完成！")