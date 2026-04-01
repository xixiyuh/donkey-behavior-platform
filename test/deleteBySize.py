import sqlite3
from pathlib import Path
from PIL import Image

PROJECT_ROOT = Path("/var/www/realtime-detector")
DB_PATH = PROJECT_ROOT / "data" / "farm.db"

MIN_WIDTH = 80
MIN_HEIGHT = 80

def delete_small_screenshot_events():
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    cursor.execute("SELECT id, screenshot FROM mating_events")
    rows = cursor.fetchall()

    ids_to_delete = []

    for event_id, screenshot in rows:
        if not screenshot:
            continue

        # 数据库存的是 /static/xxx 这种 URL 路径，要拼到项目根目录
        img_path = PROJECT_ROOT / screenshot.lstrip("/")

        if not img_path.exists():
            print(f"[跳过] id={event_id} 图片不存在: {img_path}")
            continue

        try:
            with Image.open(img_path) as img:
                width, height = img.size

            if width < MIN_WIDTH or height < MIN_HEIGHT:
                print(f"[待删除] id={event_id}, size={width}x{height}, path={img_path}")
                ids_to_delete.append(event_id)

        except Exception as e:
            print(f"[跳过] id={event_id} 图片读取失败: {img_path}, error={e}")

    if not ids_to_delete:
        print("没有需要删除的记录")
        conn.close()
        return 0

    placeholders = ",".join("?" for _ in ids_to_delete)
    delete_sql = f"DELETE FROM mating_events WHERE id IN ({placeholders})"
    cursor.execute(delete_sql, ids_to_delete)

    deleted_count = cursor.rowcount
    conn.commit()
    conn.close()

    print(f"成功删除 {deleted_count} 条截图尺寸小于 {MIN_WIDTH}x{MIN_HEIGHT} 的事件记录")
    return deleted_count

if __name__ == "__main__":
    delete_small_screenshot_events()
