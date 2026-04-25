from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")


def _get_env(name: str, default: str) -> str:
    return os.getenv(name, default)


def _get_int_env(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None or raw_value == "":
        return default
    return int(raw_value)


def _get_bool_env(name: str, default: bool) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None or raw_value == "":
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


def _get_list_env(name: str, default: list[str]) -> list[str]:
    raw_value = os.getenv(name)
    if raw_value is None or raw_value.strip() == "":
        return default
    return [item.strip() for item in raw_value.split(",") if item.strip()]


def _get_path_env(name: str, default: Path) -> Path:
    raw_value = os.getenv(name)
    if raw_value is None or raw_value.strip() == "":
        return default
    path = Path(raw_value)
    if not path.is_absolute():
        path = BASE_DIR / path
    return path


APP_ENV = _get_env("APP_ENV", "local").strip().lower()
IS_PRODUCTION = APP_ENV == "production"


@dataclass(frozen=True)
class Settings:
    app_env: str = APP_ENV
    app_host: str = _get_env("APP_HOST", "127.0.0.1")
    app_port: int = _get_int_env("APP_PORT", 8080)
    debug: bool = _get_bool_env("DEBUG", not IS_PRODUCTION)
    log_level: str = _get_env("LOG_LEVEL", "INFO")

    db_host: str = _get_env("DB_HOST", "127.0.0.1")
    db_port: int = _get_int_env("DB_PORT", 3306)
    db_user: str = _get_env("DB_USER", "root")
    db_password: str = _get_env("DB_PASSWORD", "123456")
    db_name: str = _get_env("DB_NAME", "farm")
    db_charset: str = _get_env("DB_CHARSET", "utf8mb4")

    allowed_origins: list[str] = None

    upload_dir: Path = _get_path_env("UPLOAD_DIR", BASE_DIR / "uploads")
    image_max_upload_size: int = _get_int_env("IMAGE_MAX_UPLOAD_SIZE", 10 * 1024 * 1024)
    video_max_upload_size: int = _get_int_env("VIDEO_MAX_UPLOAD_SIZE", 500 * 1024 * 1024)

    def __post_init__(self):
        default_origins = [] if IS_PRODUCTION else ["http://localhost:5173", "http://127.0.0.1:5173"]
        object.__setattr__(self, "allowed_origins", _get_list_env("ALLOWED_ORIGINS", default_origins))


settings = Settings()
