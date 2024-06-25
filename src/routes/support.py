from datetime import datetime
from random import randint

from flask import Blueprint, render_template, url_for, flash, redirect, request
from pydantic import ValidationError

from src.database.models.support import TicketPriority, TicketTypes
from src.database.models.companies import EmployeeDetails
from src.database.models.messaging import SMSCompose, RecipientTypes, EmailCompose, SMSInbox, SMSSettings
from src.database.models.covers import ClientPersonalInformation
from src.authentication import login_required, user_details
from src.database.models.users import User
from src.main import company_controller, messaging_controller

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
