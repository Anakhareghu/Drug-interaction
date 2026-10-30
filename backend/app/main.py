from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router as data_router
from app.api.auth_routes import router as auth_router
from app.core.config import settings

def get_application() -> FastAPI:
    application = FastAPI(
        title=settings.PROJECT_NAME,
        openapi_url=f"{settings.API_V1_STR}/openapi.json"
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Auth routes
    application.include_router(auth_router, prefix=settings.API_V1_STR)
    # Research data routes
    application.include_router(data_router, prefix=settings.API_V1_STR)

    return application

app = get_application()
