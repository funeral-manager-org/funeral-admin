from src.main import create_app
from src.config import config_instance

app, chat_io = create_app(config=config_instance())

if __name__ == '__main__':
    # chat_io.run(app, port=5000, debug=True)
    app.run(debug=True)
