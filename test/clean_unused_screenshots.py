import sqlite3
import shutil
from pathlib import Path

PROJECT_ROOT = Path("/var/www/realtime-detector")
DB_PATH = PROJECT_ROOT / "data" / "farm.db"
SCREENSHOT_DIR = PROJECT_ROOT / "static" / "mating_screenshots"
TRASH_DIR = PROJECT_ROOT / "static" / "mating_screenshots_trash"

def move_unused_screenshots():
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    cursor.execute("SELECT screenshot FROM mating_events WHERE screenshot IS NOT NULL AND screenshot != ''")
    rows = cursor.fetchall()
    conn.close()

    referenced_files = {Path(screenshot).name for (screenshot,) in rows if screenshot}
    TRASH_DIR.mkdir(parents=True, exist_ok=True)

    moved_count = 0

    for file_path in SCREENSHOT_DIR.iterdir():
        if not file_path.is_file():
            continue
        if file_path.name not in referenced_files:
            target = TRASH_DIR / file_path.name
            shutil.move(str(file_path), str(target))
            print(f"[已移动] {file_path} -> {target}")
            moved_count += 1

    print(f"成功移动 {moved_count} 个未引用文件到 {TRASH_DIR}")

if __name__ == "__main__":
    move_unused_screenshots()