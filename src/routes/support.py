from datetime import datetime
from random import randint

from flask import Blueprint, render_template, url_for, flash, redirect, request
from pydantic import ValidationError

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
    if user and user.email:
        context = dict(user=user)
    else:
        context = {}
        
    return render_template('support/support.html', **context)

        


