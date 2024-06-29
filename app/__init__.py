from fastapi import FastAPI
from loguru import logger

from app.core.exceptions import SettingNotFound
from app.core.init_app import (
    init_menus,
    init_superuser,
    make_middlewares,
    register_db,
    register_exceptions,
    register_routers, init_scheduler,
)
from app.db.redis import init_redis_pool, close_redis_pool, get_redis

try:
    from app.settings.config import settings
except ImportError:
    raise SettingNotFound("Can not import settings")


def create_app() -> FastAPI:
    logger.warning("开始创建app")
    app = FastAPI(
        title=settings.APP_TITLE,
        description=settings.APP_DESCRIPTION,
        version=settings.VERSION,
        openapi_url="/openapi.json",
        middleware=make_middlewares(),
    )
    register_db(app)
    register_exceptions(app)
    register_routers(app, prefix="/api")
    logger.success("创建app成功")
    return app


app = create_app()


@app.on_event("startup")
async def startup_event():
    # 在应用启动时执行的初始化任务 固定写法
    logger.info("app启动初始化任务")
    await init_superuser()
    await init_menus()
    await init_scheduler(app)
    await init_redis_pool()  # 初始化 Redis 连接池
    app.state.redis = await get_redis()
    logger.success("Redis 连接已建立")


@app.on_event("shutdown")
async def shutdown_event():
    # 在应用关闭时执行的清理任务
    logger.warning("测试服务关闭-shutdown")
    await close_redis_pool()  # 关闭 Redis 连接池
    logger.warning("Redis 连接已关闭")
