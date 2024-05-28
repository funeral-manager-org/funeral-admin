from src.main import create_app
from src.config import config_instance
import threading

# Create the Flask app, chat_io, and message_loop
app, chat_io, message_controller, notifications_controller, subscriptions_controller = create_app(
    config=config_instance())


# app, chat_io, message_controller = create_app(config=config_instance())

def run_loops():
    """running message loops"""
    loops = [
        message_controller.loop,
        notifications_controller.loop,
        subscriptions_controller.loop
    ]
    for loop in loops:
        loop.run_forever()


if __name__ == '__main__':
    # Run the Flask app
    # Start the message loop in a separate thread
    loop_threads = threading.Thread(target=run_loops, daemon=True)

    loop_threads.start()

    app.run(debug=True, port=8000)
