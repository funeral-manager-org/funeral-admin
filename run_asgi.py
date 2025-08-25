# run_asgi.py
from src.main import create_app
from src.config import config_instance

app, message_controller, notifications_controller, subscriptions_controller = create_app(
    config=config_instance()
)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:create_app()",  # if using factory, call it with quotes
        host="0.0.0.0",
        port=8000,
        reload=True,  # optional, for dev autoreload
        log_level="info",
    )
