from flask import Blueprint, render_template, send_file, jsonify, url_for, flash, redirect
from datetime import datetime, timedelta
from src.authentication import user_details
from src.database.models.users import User
from src.utils import static_folder

home_route = Blueprint('home', __name__)


@home_route.get('/get-time')
async def get_time():
    # Get the current server time
    current_time = datetime.utcnow()

    # Convert the datetime object to a string
    current_time_str = current_time.strftime("%Y-%m-%d %H:%M:%S.%f")


    # Return the current time as a JSON response
    return jsonify({'time': current_time_str})




@home_route.get("/")
@user_details
async def get_home(user: User | None):

    social_url = url_for('home.get_home', _external=True)
    context = dict(user=user, social_url=social_url)
    return render_template('index.html', **context)
