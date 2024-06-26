from flask import Flask

from src.database.sql.support import TicketORM, TicketMessageORM
from src.database.models.support import Ticket, TicketMessage
from src.controller.messaging_controller import MessagingController
from src.controller import Controllers


class SupportController(Controllers):

    def __init__(self):
        super().__init__()

    def init_app(self, app: Flask, messaging_controller: MessagingController):
        super().init_app(app=app)

    async def create_support_ticket(self, ticket: Ticket):
        """

        :param ticket:
        :return:
        """
        with self.get_session() as session:
            session.add(TicketORM(**ticket.dict(exclude={'messages'})))

            return ticket

    async def add_ticket_message(self, ticket_message: TicketMessage):
        """

        :return:
        """
        with self.get_session() as session:
            ticket_orm = session.query(TicketORM).filter_by(ticket_id=ticket_message.ticket_id).first()
            if isinstance(ticket_orm, TicketORM):
                session.add(TicketMessageORM(**ticket_message.dict()))

            return ticket_message

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
