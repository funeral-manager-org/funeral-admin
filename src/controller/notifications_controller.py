from flask import Flask

from src.controller import error_handler, Controllers
from src.database.models.notifications import NotificationsModel, Notification
from src.database.sql.notifications import NotificationORM


class NotificationsController(Controllers):

    def __init__(self):
        super().__init__()

    def init_app(self, app: Flask):
        super().init_app(app=app)

    @error_handler
    async def get_user_notifications(self, uid: str) -> NotificationsModel | None:
        """

        :param user_id:
        :return:
        """
        with self.get_session() as session:
            notifications: list[NotificationORM] = session.query(NotificationORM).filter(
                NotificationORM.uid == uid).all()
            notifications_ = [Notification(**notification.dict()) for notification in notifications]
            if notifications_:
                notifications_list: NotificationsModel = NotificationsModel(**dict(notifications=notifications_))
                return notifications_list
            return None
