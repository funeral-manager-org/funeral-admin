from flask import Flask
from flask_socketio import SocketIO
from src.controller.encryptor import Encryptor

from src.emailer import SendMail

from src.utils import format_with_grouping, friendlytimestamp

encryptor = Encryptor()
send_mail = SendMail()

from src.controller.auth import UserController
from src.controller.company_controller import  CompanyController
from src.controller.paypal_controller import PayPalController
from src.controller.chat_controller import ChatController



# from src.firewall import Firewall

user_controller = UserController()
company_controller = CompanyController()
paypal_controller = PayPalController()
chat_controller = ChatController()



chat_io = SocketIO()

# firewall = Firewall()
def _add_blue_prints(app: Flask):
    """
        this function adds blueprints
    :param app:
    :return:
    """
    from src.routes.home import home_route
    from src.routes.auth import auth_route
    from src.routes.company import company_route
    from src.routes.employees import employee_route
    from src.routes.covers import covers_route
    from src.routes.clients import clients_route


    for route in [auth_route, home_route, company_route, employee_route, covers_route, clients_route]:
        app.register_blueprint(route)


def _add_filters(app: Flask):
    """
        **add_filters**
            filters allows formatting from models to user readable format
    :param app:
    :return:
    """
    app.jinja_env.filters['number'] = format_with_grouping
    app.jinja_env.filters['time'] = friendlytimestamp


def create_app(config):
    from src.utils import template_folder, static_folder
    app: Flask = Flask(__name__)
    app.template_folder = template_folder()
    app.static_folder = static_folder()
    app.config['SECRET_KEY'] = config.SECRET_KEY
    app.config['BASE_URL'] = "https://funeral-manager.org"

    with app.app_context():
        from src.main.bootstrapping import bootstrapper
        bootstrapper()
        # firewall.init_app(app=app)

        _add_blue_prints(app)
        _add_filters(app)
        encryptor.init_app(app=app)
        chat_io.init_app(app)
        user_controller.init_app(app=app)
        company_controller.init_app(app=app)
        paypal_controller.init_app(app=app, config_instance=config)
        chat_controller.init_app(app=app)

    return app, chat_io



