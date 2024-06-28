from flask import Flask

from src.controller import Controllers, error_handler
from src.controller.messaging_controller import MessagingController
from src.database.models.support import Ticket, TicketMessage, TicketStatus
from src.database.sql.support import TicketORM, TicketMessageORM
from src.database.sql.user import UserORM


class SupportController(Controllers):

    def __init__(self):
        super().__init__()

    def init_app(self, app: Flask, messaging_controller: MessagingController):
        super().init_app(app=app)

    @error_handler
    async def create_support_ticket(self, ticket: Ticket):
        """

        :param ticket:
        :return:
        """
        with self.get_session() as session:
            session.add(TicketORM(**ticket.dict(exclude={'messages'})))

            return ticket

    @error_handler
    async def add_ticket_message(self, ticket_message: TicketMessage):
        """

        :return:
        """
        with self.get_session() as session:
            ticket_orm = session.query(TicketORM).filter_by(ticket_id=ticket_message.ticket_id).first()
            if isinstance(ticket_orm, TicketORM):
                session.add(TicketMessageORM(**ticket_message.dict()))

            return ticket_message

    @error_handler
    async def ticket_set_status(self, ticket_id: str, status: str):
        """

        :param ticket_id:
        :param status:
        :return:
        """
        with self.get_session() as session:
            ticket_orm = session.query(TicketORM).filter_by(ticket_id=ticket_id).first()
            if isinstance(ticket_orm, TicketORM):
                ticket_orm.status = status

    @error_handler
    async def get_user_support_tickets(self, uid: str) -> list[Ticket]:
        """
        Get all support tickets for a specific user, including their messages.

        :param uid: User ID
        :return: List of Ticket objects
        """
        with self.get_session() as session:
            # Query to join TicketORM and TicketMessageORM and filter by user ID
            tickets_with_messages = (
                session.query(TicketORM)
                .outerjoin(TicketMessageORM, TicketORM.ticket_id == TicketMessageORM.ticket_id)
                .filter(TicketORM.user_id == uid)
                .all()
            )

            # Transform the result into a list of Ticket objects
            return [Ticket(**ticket_orm.to_dict()) for ticket_orm in tickets_with_messages if
                    isinstance(ticket_orm, TicketORM)]

    @error_handler
    async def get_support_ticket_by_ticket_id(self, ticket_id: str) -> Ticket | None:
        """
            return ticket with messages
        :param ticket_id:
        :return:
        """
        with self.get_session() as session:
            ticket_orm = (
                session.query(TicketORM)
                .outerjoin(TicketMessageORM, TicketORM.ticket_id == TicketMessageORM.ticket_id)
                .filter(TicketORM.ticket_id == ticket_id).first()
            )

            return Ticket(**ticket_orm.to_dict()) if isinstance(ticket_orm, TicketORM) else None

    @error_handler
    async def get_uid_tags(self, support_ticket: Ticket) -> dict[str, str]:
        """
            :param support_ticket:
            :return:
        """
        with self.get_session() as session:
            uid_name_tag = {}
            for message in support_ticket.messages:
                user_orm: UserORM = session.query(UserORM).filter_by(uid=message.sender_id).first()
                uid_name_tag[user_orm.uid] = user_orm.email

            return uid_name_tag

    @error_handler
    async def load_unresolved_tickets(self) -> list[Ticket]:
        """

        :return:
        """
        with self.get_session() as session:
            unresolved_tickets_orm_list = (session.query(TicketORM)
                                           .outerjoin(TicketMessageORM,
                                                      TicketORM.ticket_id == TicketMessageORM.ticket_id)
                                           .filter(TicketORM.status.in_(TicketStatus.UN_RESOLVED())).all())

            return [Ticket(**ticket_orm.to_dict()) for ticket_orm in unresolved_tickets_orm_list
                    if isinstance(ticket_orm, TicketORM)]
