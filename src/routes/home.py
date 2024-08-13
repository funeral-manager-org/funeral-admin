from flask import Blueprint, render_template, url_for

from src.authentication import user_details
from src.database.models.users import User

home_route = Blueprint('home', __name__)


@home_route.get("/")
@user_details
async def get_home(user: User | None):

    social_url = url_for('home.get_home', _external=True)
    context = dict(user=user, social_url=social_url)
    return render_template('index.html', **context)
