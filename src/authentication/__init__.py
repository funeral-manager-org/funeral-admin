from functools import wraps

from flask import request, redirect, url_for, flash

from src.logger import init_logger
from src.database.models.users import User
from src.database.sql import Session
from src.database.sql.user import UserORM
from src.main import system_cache

cached_ttl = system_cache.cached_ttl
auth_logger = init_logger('auth_logger')
# Your route handlers go here
@cached_ttl(ttl=60 * 30)
async def get_user_details(uid: str) -> User:
    """Get the details for a user by their ID."""

    # Assuming you have a database session and engine configured
    with Session() as session:
        # Perform the query to retrieve the user based on the uid
        user = session.query(UserORM).filter(UserORM.uid == uid).first()
        return User(**user.to_dict()) if user else None


def login_required(route_function):
    @wraps(route_function)
    async def decorated_function(*args, **kwargs):
        auth_cookie = request.cookies.get('auth')
        if auth_cookie:
            # Assuming you have a function to retrieve the user details based on the uid
            user = await get_user_details(auth_cookie)
            try:
                if user:
                    return await route_function(user, *args, **kwargs)  # Inject user as a parameter
                flash(message="User may not be Authorized or Logged In", category="danger")
                return redirect(url_for('home.get_home'))
            except TypeError as e:
                auth_logger.error(str(e))
                _mess = f'Error making request please try again later {str(e)}'
                flash(message=_mess, category="danger")
                return redirect(url_for('home.get_home'))
        return redirect(url_for('auth.get_auth'))  # Redirect to login page if not logged in

    return decorated_function


# noinspection DuplicatedCode
def admin_login(route_function):
    """used to authenticate company admins only """

    @wraps(route_function)
    async def decorated_function(*args, **kwargs):
        auth_cookie = request.cookies.get('auth')
        if auth_cookie:
            # Assuming you have a function to retrieve the user details based on the uid
            user = await get_user_details(auth_cookie)
            try:
                if user and user.company_id and user.is_company_admin:
                    return await route_function(user, *args, **kwargs)  # Inject user as a parameter
                flash(message="User may not be Authorized or Logged In", category="danger")
                return redirect(url_for('home.get_home'))
            except TypeError as e:
                flash(message='Error making request please try again later', category="danger")
                return redirect(url_for('home.get_home'))
        return redirect(url_for('auth.get_auth'))  # Redirect to login page if not logged in

    return decorated_function


# noinspection DuplicatedCode
def system_login(route_function):
    """used to authenticate system admin"""

    @wraps(route_function)
    async def decorated_function(*args, **kwargs):
        auth_cookie = request.cookies.get('auth')
        if auth_cookie:
            # Assuming you have a function to retrieve the user details based on the uid
            user = await get_user_details(auth_cookie)
            try:
                if user and user.is_system_admin:
                    return await route_function(user, *args, **kwargs)  # Inject user as a parameter
                flash(message="User may not be Authorized or Logged In", category="danger")
                return redirect(url_for('home.get_home'))
            except TypeError as e:
                flash(message='Error making request please try again later', category="danger")
                return redirect(url_for('home.get_home'))
        return redirect(url_for('auth.get_auth'))  # Redirect to login page if not logged in

    return decorated_function


def user_details(route_function):
    @wraps(route_function)
    async def decorated_function(*args, **kwargs):
        uid = request.cookies.get('auth')
        user: User | None = await get_user_details(uid=uid) if uid else None
        return await route_function(user, *args, **kwargs)

    return decorated_function
