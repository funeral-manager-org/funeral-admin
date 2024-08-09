import random
from src.controller import Controllers, error_handler
from src.database.models.support_chat import ChatMessage, ChatUser
from src.database.sql.support_chat import ChatMessageORM, ChatUserORM


def create_colour(used_hexes: list[str]):
    count = 0
    while count < len(colours):
        chosen = random.choice(list(colours.values()))
        if chosen not in used_hexes:
            return chosen
        count += 1

    # Select a random color from the dictionary keys
    return random.choice(list(colours.values()))


colours = {
    "Red": "#FF0000",
    "Blue": "#0000FF",
    "Green": "#00FF00",
    "Yellow": "#FFFF00",
    "Purple": "#800080",
    "Orange": "#FFA500",
    "Pink": "#FFC0CB",
    "Brown": "#A52A2A",
    "Black": "#000000"}


class ChatController(Controllers):
    def __init__(self):
        super().__init__()
        self.user_colour = {}

    def init_app(self, app):
        super().init_app(app=app)

    def add_chat_message(self, message: ChatMessage):
        """
            Add Message to Database
        :param message:
        :return:
        """
        try:
            with self.get_session() as session:
                chat_message_orm = session.query(ChatMessageORM).filter(
                    ChatMessageORM.message_id == message.message_id).first()
                # TODO please consider saving a list of users in this class

                if isinstance(chat_message_orm, ChatMessageORM):
                    return message
                chat_message_orm = ChatMessageORM(uid=message.uid,
                                                  message_id=message.message_id,
                                                  text=message.text,
                                                  timestamp=message.timestamp)
                session.add(chat_message_orm)
                session.commit()
                used_hexes = list(self.user_colour.keys())
                if message.uid not in used_hexes:
                    self.user_colour[message.uid] = create_colour(used_hexes=used_hexes)

                message.user_colour = self.user_colour[message.uid]

                return message
        except Exception as e:
            print(f"An Error Occured  {str(e)}")
            return message

    @error_handler
    async def get_all_messages(self) -> list[ChatMessage]:
        """
            Get All Messages from database
        :return:
        """
        with self.get_session() as session:
            chat_messages_orm_list = session.query(ChatMessageORM).all()
            chat_users_orm_list = session.query(ChatUserORM).all()

            chat_users = [ChatUser(**user.to_dict()) for user in chat_users_orm_list]
            chat_messages = [ChatMessage(**message.to_dict()) for message in chat_messages_orm_list if
                             isinstance(message, ChatMessageORM)]

            proc_messages = []
            for message in chat_messages:
                used_hexes = list(self.user_colour.keys())
                if message.uid not in used_hexes:
                    self.user_colour[message.uid] = create_colour(used_hexes=used_hexes)

                message.user_colour = self.user_colour[message.uid]
                proc_messages.append(message)

            return proc_messages

    @error_handler
    async def get_all_users(self) -> list[str]:
        colours_reversed = {value: key for key, value in colours.items()}
        return [colours_reversed[_hex] for _hex in self.user_colour.values()]
