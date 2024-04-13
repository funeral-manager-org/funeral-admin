import time
import uuid

from flask import Flask, render_template
from pydantic import ValidationError
from sqlalchemy import or_

from src.controller import error_handler, UnauthorizedError, Controllers
from src.database.models.profile import Profile, ProfileUpdate
from src.database.models.users import User, CreateUser, UserUpdate, PayPal
from src.database.sql.user import UserORM, ProfileORM, PayPalORM
from src.emailer import EmailModel
from src.main import send_mail
import requests


class UserController(Controllers):

    def __init__(self):
        super().__init__()

        self._time_limit = 360
        self._verification_tokens: dict[str, int | dict[str, str | int]] = {}
        self.profiles: dict[str, Profile] = {}
        self.users: dict[str, User] = {}
        self._game_data_url: str = 'https://gslls.im30app.com/gameservice/web_getserverbyname.php'

    def init_app(self, app: Flask):
        super().init_app(app=app)

    async def _get_game_data(self, game_id: str, lang: str = 'en') -> dict[str, str | int]:
        """

        :param game_id:
        :param lang:
        :return:
        """
        _params = {'name': game_id, 'lang': lang}
        response = requests.get(url=self._game_data_url, params=_params)
        game_data = response.json()
        print("Game Data 1")
        print(game_data)
        if 'allianceabbr' in game_data:
            # Rename the key from 'allianceabbr' to 'allianceabr'
            game_data['allianceabr'] = game_data.pop('allianceabbr')
        if 'headimgurl' in game_data:
            game_data['headimgurl'] = game_data.pop('headimgurl')

        if 'result' in game_data:
            game_data['result'] = game_data.pop('result')

        return game_data

    async def manage_users_dict(self, new_user: User):
        # Check if the user instance already exists in the dictionary
        self.users[new_user.uid] = new_user

    async def manage_profiles(self, new_profile: Profile):
        self.profiles[new_profile.uid] = new_profile

    @error_handler
    async def get_profile_by_uid(self, uid: str) -> Profile | None:
        """
        Get the profile for the given user ID.

        :param uid: The user ID for which to retrieve the profile.
        :return: The Profile instance corresponding to the user ID if found, else None.
        """
        # Check if the profile is available in the cache (profiles dictionary)
        # if uid in self.profiles:
        #     self.logger.info("Fetching profile from dict {} ")
        #     return self.profiles.get(uid)

        # Fetch the profile data from the database
        with self.get_session() as session:

            profile_orm = session.query(ProfileORM).filter(ProfileORM.uid == uid).first()
            # If the profile_orm is not found, return None
            if not profile_orm:
                # game_data = await self._get_game_data(game_id=profile_orm.game_id)
                # profile = Profile(**game_data, uid=uid)
                # profile_orm = ProfileORM(**profile.dict())
                # session.add(profile_orm)
                # session.commit()
                profile = Profile(uid=uid)
            else:
                # Convert ProfileORM to Profile object
                profile = Profile(**profile_orm.to_dict())

            # Cache the profile in the dictionary for future use
            self.profiles[uid] = profile
        return profile

    @error_handler
    async def update_profile(self, updated_profile: ProfileUpdate) -> Profile | None:
        """
        :param updated_profile:
        :return:
        """
        with self.get_session() as session:
            original_profile: ProfileORM = session.query(ProfileORM).filter(
                ProfileORM.uid == updated_profile.uid).first()

            if isinstance(original_profile, ProfileORM):
                print(original_profile.to_dict())
                original_profile.main_game_id = updated_profile.main_game_id
                original_profile.profile_name = updated_profile.profile_name
                original_profile.notes = updated_profile.notes
                original_profile.currency = updated_profile.currency
                session.merge(original_profile)
                profile = Profile(**original_profile.to_dict())
                session.commit()
                self.profiles[profile.uid] = profile
                return profile
            return None

    @error_handler
    async def delete_profile(self, game_id: str) -> bool:
        """
        Delete a profile from the database.

        :param game_id:

        :return: True if the profile was successfully deleted, False otherwise.
        """
        with self.get_session() as session:
            # Find the profile with the given UID
            profile_to_delete: ProfileORM = session.query(ProfileORM).filter(ProfileORM.main_game_id == game_id).first()
            if isinstance(profile_to_delete, ProfileORM):
                print(f"Profile to Delete {profile_to_delete.to_dict()}")
                # Delete the profile from the session
                session.delete(profile_to_delete)
                # Commit the transaction to permanently delete the profile from the database
                session.commit()

                return True
            else:
                return False

    @error_handler
    async def create_profile(self, main_game_id: str, uid: str) -> Profile:
        """

        :param main_game_id:
        :param uid:

        :return:
        """
        with self.get_session() as session:
            profile_orm: ProfileORM = session.query(ProfileORM).filter(ProfileORM.uid == uid).first()

            if not isinstance(profile_orm, ProfileORM):
                profile_: dict[str, str] = await self._get_game_data(game_id=main_game_id)
                print(profile_)

                profile: Profile = Profile(uid=uid, main_game_id=main_game_id, profile_name=profile_.get('name'))
                profile_orm: ProfileORM = ProfileORM(**profile.dict())

                session.add(profile_orm)
                session.commit()
                self.profiles[profile.uid] = profile
                return profile

            return Profile(**profile_orm.to_dict())

    @error_handler
    async def add_paypal(self, user: User, paypal_email: str) -> PayPal | None:
        """

        :param user:
        :param paypal_email:
        :return:
        """
        paypal_email = paypal_email.strip().lower()
        if not paypal_email:
            return None

        with self.get_session() as session:
            paypal_account = session.query(PayPalORM).filter(PayPalORM.paypal_email == paypal_email).first()
            if isinstance(paypal_account, PayPalORM):
                if paypal_account.uid == user.uid:
                    paypal_account.paypal_email = paypal_email
                    paypal_account.uid = user.uid
                    session.merge(paypal_account)
                    session.commit()
                    return PayPal(**paypal_account.to_dict())
                else:
                    return None

            paypal_account: PayPalORM = session.query(PayPalORM).filter(PayPalORM.uid == user.uid).first()
            if isinstance(paypal_account, PayPalORM):
                paypal_account.paypal_email = paypal_email
                paypal_account_ = PayPal(**paypal_account.to_dict())
                session.merge(paypal_account_)
                session.commit()

                return paypal_account_

            paypal_orm = PayPalORM(paypal_email=paypal_email, uid=user.uid)
            paypal_account_ = PayPal(**paypal_orm.to_dict())
            session.add(paypal_orm)
            session.commit()
            return paypal_account_

    @error_handler
    async def get_paypal_account(self, uid: str) -> PayPal | None:
        with self.get_session() as session:
            paypal_account: PayPalORM = session.query(PayPalORM).filter(PayPalORM.uid == uid).first()
            print("PAYPAL ACCOUNT")
            print(paypal_account)
            if isinstance(paypal_account, PayPalORM):
                return PayPal(**paypal_account.to_dict())
            return None

    async def is_token_valid(self, token: str) -> bool:
        """
        **is_token_valid**
            Checks if the password reset token is valid based on the elapsed time.
        :param token: The password reset token to validate.
        :return: True if the token is valid, False otherwise.
        """
        if token in set(self._verification_tokens.keys()):
            timestamp: int = self._verification_tokens[token]
            current_time: int = int(time.time())
            elapsed_time = current_time - timestamp
            return elapsed_time < self._time_limit

        return False

    @error_handler
    async def get(self, uid: str) -> dict[str, str] | None:
        """
        :param uid:
        :return:
        """
        if not uid:
            return None
        # if uid in self.users:
        #     return self.users[uid].dict()

        with self.get_session() as session:
            user_data: UserORM = session.query(UserORM).filter(UserORM.uid == uid).first()
            return user_data.to_dict()

    @error_handler
    async def get_by_email(self, email: str) -> User | None:
        """
            **get_by_email**
        :param email:
        :return:
        """
        if not email:
            return None
        # for user in self.users.values():
        #     if user.email.casefold() == email.casefold():
        #         return user

        with self.get_session() as session:
            user_data: UserORM = session.query(UserORM).filter(UserORM.email == email.casefold()).first()

            return User(**user_data.to_dict()) if user_data else None

    @error_handler
    async def send_password_reset(self, email: str) -> dict[str, str] | None:
        """
        Sends a password reset email to the specified email address.

        :param email: The email address to send the password reset email to.
        :return: A dictionary containing the result of the email sending operation, or None if an error occurred.
        """
        # TODO please complete the method to send the password reset email
        password_reset_subject: str = "last-shelter.vip Password Reset Request"
        # Assuming you have a function to generate the password reset link
        password_reset_link: str = self.generate_password_reset_link(email)

        html = f"""
        <html>
        <body>
            <h2>Last Shelter VIP Password Reset</h2>
            <p>Hello,</p>
            <p>We received a password reset request for your https://last-shelter.vip account. 
            Please click the link below to reset your password:</p>
            <a href="{password_reset_link}">{password_reset_link}</a>
            <p>If you didn't request a password reset, you can ignore this email.</p>
            <p>Thank you,</p>
            <p>The Rental Manager Team</p>
        </body>
        </html>
        """

        email_template = dict(to_=email, subject_=password_reset_subject, html_=html)
        await send_mail.send_mail_resend(email=EmailModel(**email_template))

        return email_template

    def generate_password_reset_link(self, email: str) -> str:
        """
        Generates a password reset link for the specified email.

        :param email: The email address for which to generate the password reset link.
        :return: The password reset link.
        """
        token = str(uuid.uuid4())  # Assuming you have a function to generate a random token
        self._verification_tokens[token] = int(time.time())
        password_reset_link = f"https://last-shelter.vip/admin/reset-password?token={token}&email={email}"

        return password_reset_link

    async def post(self, user: CreateUser) -> User | None:
        """

        :param user:
        :return:
        """
        with self.get_session() as session:
            user_data: UserORM = session.query(UserORM).filter(or_(UserORM.uid == user.uid,
                                                                   UserORM.email == user.email)).first()
            if user_data:
                return None

            new_user: UserORM = UserORM(**user.to_dict())
            session.add(new_user)
            new_user_dict = new_user.to_dict()
            session.commit()
            _user_data = User(**new_user_dict) if isinstance(new_user, UserORM) else None
            self.users[_user_data.uid] = _user_data
            return _user_data

    @error_handler
    async def put(self, user: User) -> dict[str, str] | None:
        with self.get_session() as session:
            user_data: UserORM = session.query(UserORM).filter_by(uid=user.uid).first()
            if not user_data:
                return None

            # Update user_data with the values from the user Pydantic BaseModel
            for field in user_data.__table__.columns.keys():
                if hasattr(user, field):
                    setattr(user_data, field, getattr(user, field))

            # Save the updated user_data back to the session
            session.add(user_data)
            session.commit()
            self.users[user_data.uid] = user_data
            return user_data.to_dict()

    @error_handler
    async def login(self, email: str, password: str) -> User | None:
        with self.get_session() as session:
            print(f"Email : {email}")
            user_data: UserORM = session.query(UserORM).filter(UserORM.email == email).first()
            try:
                if user_data:
                    user: User = User(**user_data.to_dict())
                else:
                    return None
            except ValidationError as e:
                raise UnauthorizedError(description="Cannot Login User please check your login details")
            return user if user.is_login(password=password) else None

    @error_handler
    async def send_verification_email(self, user: User) -> None:
        """
        Sends a verification email to the specified user.

        :param user: The user to send the verification email to.
        """
        token = str(uuid.uuid4())  # Assuming you have a function to generate a verification token
        verification_link = f"https://last-shelter.vip/dashboard/verify-email?token={token}&email={user.email}"
        self._verification_tokens[token] = dict(email=user.email, timestamp=int(time.time()))
        # Render the email template
        email_html = render_template("email_templates/verification_email.html", user=user,
                                     verification_link=verification_link)

        msg = EmailModel(subject_="last-shelter.vip Email Verification",
                         to_=user.email,
                         html_=email_html)

        await send_mail.send_mail_resend(email=msg)

    @error_handler
    async def verify_email(self, email: str, token: str) -> bool:
        """
            **verify_email**
        :param email:
        :param token:
        :return:
        """
        if email is None:
            return False
        if token is None:
            return False
        if token not in self._verification_tokens:
            return False

        _data: dict[str, str | int] = self._verification_tokens[token]

        current_time: int = int(time.time())
        elapsed_time = current_time - int(_data.get('timestamp', 0))
        return (elapsed_time < self._time_limit) and (email.casefold() == _data.get('email'))

    @error_handler
    async def get_all_accounts(self) -> list[User]:
        with self.get_session() as session:
            accounts_list = session.query(UserORM).all()
            return [User(**account.to_dict()) for account in accounts_list if account]

    @error_handler
    async def get_account_by_uid(self, uid: str) -> User | None:
        with self.get_session() as session:
            account_orm = session.query(UserORM).filter(UserORM.uid == uid).first()
            if isinstance(account_orm, UserORM):
                return User(**account_orm.to_dict())
            return None
