from fastapi import FastAPI

from app.api import router


def get_app():
    app = FastAPI(
        title="User Service",
        description="User Profile and Contact Management Microservice",
    )
    app.include_router(router)

    return app


app = get_app()
