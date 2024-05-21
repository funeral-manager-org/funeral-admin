from flask import Flask
from src.controller import Controllers


class CoversController(Controllers):
    """
        cover controller is responsible
        with creating reports for employees so they know
        where to keep their attention in the company

    """

    def __init__(self):
        super().__init__()

    def init_app(self, app: Flask):
        """
            pass
        :param app:
        :return:
        """
        super().init_app(app=app)
