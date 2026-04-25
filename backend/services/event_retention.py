from pathlib import Path
from typing import Optional

from backend.database import get_db_connection
import modules.config as C

DEFAULT_EVENT_RETENTION_MONTHS = getattr(C, "EVENT_RETENTION_MONTHS", 3)


def _is_within_base_dir(path: Path, base_dir: Path) -> bool:
    try:
        path.resolve().relative_to(base_dir.resolve())
        return True
    except ValueError:
        return False


def _resolve_screenshot_path(screenshot: Optional[str]) -> Optional[Path]:
    if not screenshot:
        return None

    screenshot_path = str(screenshot).strip()
    if not screenshot_path:
        return None

    if screenshot_path.startswith(("http://", "https://")):
        return None

    normalized = screenshot_path.replace("\\", "/")
    candidate = Path(normalized)

    if candidate.is_absolute():
        resolved = candidate.resolve()
        return resolved if _is_within_base_dir(resolved, C.BASE_DIR) else None

    resolved = (C.BASE_DIR / normalized.lstrip("/")).resolve()
    return resolved if _is_within_base_dir(resolved, C.BASE_DIR) else None


def cleanup_expired_mating_events(retention_months: int = DEFAULT_EVENT_RETENTION_MONTHS) -> dict:
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT id, screenshot, start_time
            FROM mating_events
            WHERE start_time < DATE_SUB(NOW(), INTERVAL %s MONTH)
            """,
            (retention_months,),
        )
        expired_events = cursor.fetchall()

        deleted_files = 0
        missing_files = 0
        skipped_files = 0
        file_errors = 0

        for event in expired_events:
            screenshot_path = _resolve_screenshot_path(event.get("screenshot"))
            if screenshot_path is None:
                if event.get("screenshot"):
                    skipped_files += 1
                continue

            if not screenshot_path.exists():
                missing_files += 1
                continue

            try:
                screenshot_path.unlink()
                deleted_files += 1
            except Exception:
                file_errors += 1

        cursor.execute(
            """
            DELETE FROM mating_events
            WHERE start_time < DATE_SUB(NOW(), INTERVAL %s MONTH)
            """,
            (retention_months,),
        )
        deleted_events = cursor.rowcount
        conn.commit()

        return {
            "retention_months": retention_months,
            "expired_events": len(expired_events),
            "deleted_events": deleted_events,
            "deleted_files": deleted_files,
            "missing_files": missing_files,
            "skipped_files": skipped_files,
            "file_errors": file_errors,
        }
    finally:
        conn.close()
