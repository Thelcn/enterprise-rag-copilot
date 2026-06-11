from fastapi import FastAPI

from app.api.routes import router
from app.core.config import get_settings # 读取配置
from app.core.logging_config import configure_logging, get_logger


logger = get_logger(__name__)


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings)
    app = FastAPI(title=settings.service_name, version=settings.service_version)
    app.include_router(router)
    logger.info(
        "app_startup service=%s version=%s environment=%s",
        settings.service_name,
        settings.service_version,
        settings.environment,
    )
    return app


app = create_app()
