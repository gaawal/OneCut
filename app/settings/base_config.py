import os
import typing

from pydantic_settings import BaseSettings

from app.settings import movies_config


class BaseSettings(BaseSettings):
    VERSION: str = "0.1.0"
    APP_TITLE: str = "Vue FastAPI Admin"
    PROJECT_NAME: str = "Vue FastAPI Admin"
    APP_DESCRIPTION: str = "Description"

    CORS_ORIGINS: typing.List = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: typing.List = ["*"]
    CORS_ALLOW_HEADERS: typing.List = ["*"]

    DEBUG: bool = True
    DB_URL: str = "sqlite://db.sqlite3"
    DB_CONNECTIONS: dict = {
        "default": {
            "engine": "tortoise.backends.sqlite",
            "db_url": DB_URL,
            "credentials": {
                "host": "",
                "port": "",
                "user": "",
                "password": "",
                "database": "",
            },
        },
    }

    PROJECT_ROOT: str = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    BASE_DIR: str = os.path.abspath(os.path.join(PROJECT_ROOT, os.pardir))
    LOGS_ROOT: str = os.path.join(BASE_DIR, "app/logs")
    SECRET_KEY: str = "3488a63e1765035d386f05409663f55c83bfae3b3c61a932744b20ad14244dcf"  # openssl rand -hex 32
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 day
    TORTOISE_ORM: dict = {
        "connections": {
            "sqlite": {
                "engine": "tortoise.backends.sqlite",
                "credentials": {"file_path": f"{BASE_DIR}/db.sqlite3"},
            }
        },
        "apps": {
            "models": {
                "models": ["app.models","aerich.models"],# aerich.models是必须写的，写了之后会去找到对应的模型类然后创建一个迁移记录表。
                "default_connection": "sqlite",
            },
        },
        "use_tz": False,
        "timezone": "Asia/Shanghai",
    }
    DATETIME_FORMAT: str = "%Y-%m-%d %H:%M:%S"

    _redis_host = movies_config.app.get("redis_host", "localhost")
    _redis_port = movies_config.app.get("redis_port", 6379)
    _redis_db = movies_config.app.get("redis_db", 0)
    _redis_password = movies_config.app.get("redis_password", None)

    _enable_redis:bool = movies_config.app.get("enable_redis", False)
    max_concurrent_tasks:int = movies_config.app.get("max_concurrent_tasks", 5)
    REDIS_URL: str = f"redis://:{_redis_password}@{_redis_host}:{_redis_port}/{_redis_db}"


base_settings = BaseSettings()
TORTOISE_ORM = base_settings.TORTOISE_ORM
