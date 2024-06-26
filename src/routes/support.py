from flask import Blueprint, render_template, request, redirect, url_for, flash
from pydantic import ValidationError

from src.authentication import user_details, login_required
from src.database.models.support import TicketPriority, TicketTypes, NewTicketForm, Ticket, TicketMessage, \
    create_ticket_id
from src.database.models.users import User
from src.logger import init_logger
from src.main import support_controller

support_route = Blueprint('support', __name__)
support_logger = init_logger("support_logger")


@support_route.get('/support')
@login_required
async def get_support(user: User):
    """

    :param user:
    :return:
    """

    context: dict[str, dict[any, any] | str | list[str]] = dict(user=user) if user and user.email else dict()

    ticket_priority_list = TicketPriority.priority_list()
    ticket_types_list = TicketTypes.ticket_types_list()
    previous_tickets = await support_controller.get_user_support_tickets(uid=user.uid)
    context.update(ticket_priority_list=ticket_priority_list,
                   ticket_types_list=ticket_types_list,
                   previous_tickets=previous_tickets)

    return render_template('support/support.html', **context)

@support_route.get('/support/ticket/<string:ticket_id>')
@login_required
async def view_ticket(user: User, ticket_id: str):
    """

    :param user:
    :param ticket_id:
    :return:
    """
    context: dict[str, dict[any, any] | str | list[str]] = dict(user=user) if user and user.email else dict()
    support_ticket = await support_controller.get_support_ticket_by_ticket_id(ticket_id=ticket_id)

    context.update(support_ticket=support_ticket)

    return render_template('support/view_ticket.html', **context)



@support_route.post('/support/ticket-create')
@login_required
async def do_create_ticket(user: User):
    """

    :param user:
    :return:
    """
    try:
        new_ticket = NewTicketForm(**request.form)
    except ValidationError as e:
        support_logger.error(str(e))
        flash(message="Please fill in all the details to create ticket", category="danger")
        return redirect(url_for('support.get_support'))

    ticket, ticket_message = await create_ticket(new_ticket, user)

    ticket: Ticket = await support_controller.create_support_ticket(ticket=ticket)
    ticket_message: TicketMessage = await support_controller.add_ticket_message(ticket_message=ticket_message)
    message = "Successfully created ticket"
    ticket_id = f"Ticket ID : {ticket.ticket_id}"
    flash(message=message, category="success")
    flash(message=ticket_id, category="success")
    return redirect(url_for('support.get_support'))


async def create_ticket(new_ticket: NewTicketForm, user: User) -> tuple[Ticket, TicketMessage]:
    ticket_id = create_ticket_id()
    ticket_message: TicketMessage = TicketMessage(message=new_ticket.message, sender_id=user.uid,
                                                  ticket_id=ticket_id)
    messages = [ticket_message]
    ticket = Ticket(**new_ticket.dict(), messages=messages, ticket_id=ticket_id, user_id=user.uid)
    return ticket, ticket_message




