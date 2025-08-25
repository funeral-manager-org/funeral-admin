import threading
from src.main import create_app
from src.config import config_instance

app, message_controller, notifications_controller, subscriptions_controller = create_app(config=config_instance())

def run_loops():
    loops = [
        message_controller.loop,
        notifications_controller.loop,
        subscriptions_controller.loop
    ]
    for loop in loops:
        loop.run_forever()

if __name__ == "__main__":
    loop_threads = threading.Thread(target=run_loops, daemon=True)
    loop_threads.start()
    loop_threads.join()
