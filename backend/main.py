from fastapi import FastAPI

from backend.integration.ml_backend import MLBackend, PackageMLBackend
from backend.interaction.routes import router


def create_app(ml_backend: MLBackend | None = None) -> FastAPI:
    app = FastAPI(
        title="机器学习理论与实践交互平台",
        version="0.1.0",
        description="Thin HTTP interaction layer over the independent ml_core package.",
    )
    app.state.ml_backend = ml_backend or PackageMLBackend()
    app.include_router(router)
    return app


app = create_app()
