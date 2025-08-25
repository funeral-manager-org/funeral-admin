# src/asgi.py
from src.main import create_app
from src.config import config_instance

app, message_controller, notifications_controller, subscriptions_controller = create_app(config=config_instance())
