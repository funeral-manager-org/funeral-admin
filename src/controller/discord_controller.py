import random

from flask import Flask

from src.controller import Controllers, error_handler
from src.database.models.support_chat import ChatMessage, ChatUser
from src.database.sql.support_chat import ChatMessageORM, ChatUserORM


class DiscordController(Controllers):
    def __init__(self):
        super().__init__()

    def init_app(self, app: Flask):
        super().init_app(app=app)

    async def get_lss_notices(self):
        """
            interface with this website discord channel that contains
            notices from LSS
        :return:
        """
        pass
