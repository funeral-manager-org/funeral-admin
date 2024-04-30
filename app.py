from src.main import create_app
from src.config import config_instance
import threading

# Create the Flask app, chat_io, and message_loop
app, chat_io, message_controller = create_app(config=config_instance())


def run_message_loop():
    message_controller.loop.run_forever()


# Start the message loop in a separate thread
message_thread = threading.Thread(target=run_message_loop, daemon=True)
message_thread.start()

if __name__ == '__main__':
    # Run the Flask app
    app.run(debug=True, port=8000)
