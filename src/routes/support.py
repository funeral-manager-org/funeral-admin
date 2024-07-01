from flask import Blueprint, render_template, request, redirect, url_for, flash
from pydantic import ValidationError

from src.authentication import user_details, login_required, admin_login
from src.database.models.support import TicketPriority, TicketTypes, NewTicketForm, Ticket, TicketMessage, \
    create_ticket_id, TicketStatus
from src.database.models.users import User
from src.logger import init_logger
from src.main import support_controller

support_route = Blueprint('support', __name__)
support_logger = init_logger("support_logger")


async def create_ticket(new_ticket: NewTicketForm, user: User) -> tuple[Ticket, TicketMessage]:
    ticket_id = create_ticket_id()
    ticket_message: TicketMessage = TicketMessage(message=new_ticket.message, sender_id=user.uid,
                                                  ticket_id=ticket_id)
    messages = [ticket_message]
    ticket = Ticket(**new_ticket.dict(), messages=messages, ticket_id=ticket_id, user_id=user.uid)
    return ticket, ticket_message


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
    support_ticket: Ticket = await support_controller.get_support_ticket_by_ticket_id(ticket_id=ticket_id)
    support_logger.info(f"Support Ticket : {support_ticket}")
    uid_email_tags: dict[str, str] = await support_controller.get_uid_tags(support_ticket=support_ticket)
    context.update(support_ticket=support_ticket.dict(), uid_email_tags=uid_email_tags)

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


@support_route.post('/support/ticket-response/<string:ticket_id>')
@login_required
async def respond_to_ticket(user: User, ticket_id: str):
    """

    :param user:
    :param ticket_id:
    :return:
    """
    message: str = request.form.get('message')
    new_message: TicketMessage = TicketMessage(ticket_id=ticket_id, sender_id=user.uid, message=message)
    ticket_message: TicketMessage = await support_controller.add_ticket_message(ticket_message=new_message)
    await support_controller.ticket_set_status(ticket_id=ticket_id, status=TicketStatus.IN_PROGRESS.value)

    flash(message="response successfully sent", category="danger")
    return redirect(url_for('support.get_support'))


@support_route.post('/support/ticket-resolve/<string:ticket_id>')
@login_required
async def resolve_ticket(user: User, ticket_id: str):
    """

    :param user:
    :param ticket_id:
    :return:
    """
    await support_controller.ticket_set_status(ticket_id=ticket_id, status=TicketStatus.RESOLVED.value)

    flash(message="Ticket Status Successfully changed to resolved", category="danger")
    return redirect(url_for('support.view_ticket', ticket_id=ticket_id))


@support_route.post('/support/ticket-close/<string:ticket_id>')
@login_required
async def close_ticket(user: User, ticket_id: str):
    """
        **close_ticket**

    :param user:
    :param ticket_id:
    :return:
    """
    await support_controller.ticket_set_status(ticket_id=ticket_id, status=TicketStatus.CLOSED.value)

    flash(message="Ticket Successfully Closed", category="danger")
    return redirect(url_for('support.view_ticket', ticket_id=ticket_id))


# Admin Section
@support_route.get('/admin/support/unresolved')
@admin_login
async def admin_unresolved_support_tickets(user: User):
    """

    :param user:
    :return:
    """
    unresolved_tickets: list[Ticket] = await support_controller.load_unresolved_tickets()
    context = dict(user=user, unresolved_tickets=unresolved_tickets)
    return render_template('support/admin/support.html', **context)

