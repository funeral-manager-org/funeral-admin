from flask import Blueprint, render_template

from flask import Blueprint, render_template

from src.authentication import user_details
from src.database.models.support import TicketPriority, TicketTypes
from src.database.models.users import User

support_route = Blueprint('support', __name__)


@support_route.get('/support')
@user_details
async def get_support(user: User):
    """

    :param user:
    :return:
    """

    context: dict[str, dict[any, any] | str | list[str]] = dict(user=user) if user and user.email else dict()

    ticket_priority_list = TicketPriority.priority_list()
    ticket_types_list = TicketTypes.ticket_types_list()

    context.update(ticket_priority_list=ticket_priority_list,
                   ticket_types_list=ticket_types_list)

    return render_template('support/support.html', **context)


@support_route.post('/support/ticket-create')
@user_details
async def do_create_ticket(user: User):
    """

    :param user:
    :return:
    """
    pass
