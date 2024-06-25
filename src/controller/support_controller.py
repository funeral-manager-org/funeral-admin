from flask import Flask

from flask import Flask

from src.controller import Controllers, error_handler
from src.database.models.companies import Company
from src.database.models.subscriptions import Subscriptions
from src.database.sql.companies import CompanyORM
from src.database.sql.subscriptions import SubscriptionsORM


class SupportController(Controllers):

    def __init__(self):
        super().__init__()

    def init_app(self, app: Flask):
        super().init_app(app=app)

    