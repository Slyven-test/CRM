from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import router as api_router
from app.settings import settings


def create_app() -> FastAPI:
    app = FastAPI(title="IA-CRM v2 API")
    app.include_router(api_router)

    if settings.cors_origins:
        origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=False,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    elif settings.environment in {"local", "dev"}:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
            allow_credentials=False,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    return app


app = create_app()
