# run_asgi.py
from src.main import create_app
from src.config import config_instance

# Create the async Flask app
app, message_controller, notifications_controller, subscriptions_controller = create_app(
    config=config_instance()
)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,                  # pass the actual ASGI app object
        host="0.0.0.0",
        port=8000,
        reload=True,          # dev autoreload
        log_level="info",
    )
