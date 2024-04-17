from flask import Blueprint, render_template, send_file, jsonify, url_for, flash, redirect
from datetime import datetime, timedelta
from src.authentication import user_details, admin_login, login_required
from src.database.models.users import User
from src.utils import static_folder

company_route = Blueprint('company', __name__)


@company_route.get('/admin')
@login_required
async def get_admin(user: User):
    """

    :return:
    """
    context = dict(user=user)
    return render_template('admin/admin.html', **context)
