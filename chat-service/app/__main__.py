import uvicorn

from app.main import get_app

if __name__ == "__main__":
    app = get_app()
    uvicorn.run(app, host="localhost", port=8000)
