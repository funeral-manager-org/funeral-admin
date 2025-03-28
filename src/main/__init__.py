from flask import Flask

from src.cache.caching import Caching
from src.controller.encryptor import Encryptor
from src.emailer import SendMail
from src.utils import format_with_grouping, friendlytimestamp, friendly_calendar, basename_filter

system_cache = Caching()
encryptor = Encryptor()
send_mail = SendMail()

from src.controller.auth import UserController
from src.controller.company_controller import CompanyController
from src.controller.employees_controller import EmployeesController
from src.controller.covers_controller import CoversController
from src.controller.paypal_controller import PayPalController
from src.controller.payfast_controller import PayfastController
from src.controller.chat_controller import ChatController
from src.controller.messaging_controller import MessagingController
from src.controller.notifications_controller import NotificationsController
from src.controller.subscriptions_controller import SubscriptionsController
from src.controller.system_controller import SystemController

from src.controller.support_controller import SupportController

# from src.firewall import Firewall

user_controller = UserController()
company_controller = CompanyController()
employee_controller = EmployeesController()

covers_controller = CoversController()
paypal_controller = PayPalController()
payfast_controller = PayfastController()
chat_controller = ChatController()
messaging_controller = MessagingController()
notifications_controller = NotificationsController()
subscriptions_controller = SubscriptionsController()
system_controller = SystemController()
support_controller = SupportController()


# chat_io = SocketIO()


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
    from src.routes.policies import policy_route
    from src.routes.messaging import messaging_route
    from src.routes.subscriptions import subscriptions_route
    from src.routes.billing import billing_route
    from src.routes.system import system_route

    from src.routes.documents import documents_route

    from src.routes.support import support_route

    routes = [auth_route, home_route, company_route, employee_route, covers_route, clients_route, policy_route,
              messaging_route, subscriptions_route, billing_route, support_route, system_route, documents_route]

    for route in routes:
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
    app.jinja_env.filters['days_ago'] = friendly_calendar
    app.jinja_env.filters['basename'] = basename_filter


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
        system_cache.init_app(app=app)
        encryptor.init_app(app=app)
        # chat_io.init_app(app)
        user_controller.init_app(app=app)
        company_controller.init_app(app=app)
        employee_controller.init_app(app=app)

        paypal_controller.init_app(app=app, config_instance=config)
        payfast_controller.init_app(app=app, settings=config)
        chat_controller.init_app(app=app)
        system_controller.init_app(app=app)

        # application engines
        messaging_controller.init_app(app=app, settings=config, emailer=send_mail)

        covers_controller.init_app(app=app, messaging_controller=messaging_controller)
        support_controller.init_app(app=app, messaging_controller=messaging_controller)

        notifications_controller.init_app(app=app,
                                          messaging_controller=messaging_controller,
                                          company_controller=company_controller,
                                          user_controller=user_controller)

        subscriptions_controller.init_app(app=app, messaging_controller=messaging_controller,
                                          company_controller=company_controller,
                                          user_controller=user_controller)

    # return app, chat_io, messaging_controller
    return app, messaging_controller, notifications_controller, subscriptions_controller
