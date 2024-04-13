import datetime

from src.controller import Controllers, error_handler
from src.database.models.email_service import EmailService, EmailSubscriptions
from src.database.models.users import User
from src.database.sql.email_service import EmailServiceORM, EmailSubscriptionsORM


class EmailController(Controllers):
    def __init__(self):
        super().__init__()

    def init_app(self, app):
        super().init_app(app=app)

    async def create_email_subscription(self, email_service: EmailService) -> EmailService:
        with self.get_session() as session:
            email_services = session.query(EmailServiceORM).filter(EmailServiceORM.uid == email_service.uid,
                                                                   EmailServiceORM.subscription_active == False).all()
            for email_service_ in email_services:
                session.delete(email_service_)
            session.commit()

            email_service_orm = EmailServiceORM(**email_service.dict())
            session.add(email_service_orm)

            session.commit()
            return email_service

    async def generate_emails(self, email_stub: str, total_emails: int) -> list[str]:
        emails = []
        for i in range(1, total_emails + 1):
            email = f"f{i}.{email_stub}@last-shelter.vip"
            emails.append(email)
        return emails

    async def create_email_addresses(self, email_service: EmailService):
        """
            this Utility will create email addresses based on the information on the Email Service
            which was created during activation of the email service
        :param email_service:
        :return:
        """
        email_list = await self.generate_emails(email_stub=email_service.email_stub,
                                                total_emails=email_service.total_emails)
        with self.get_session() as session:
            for email in email_list:
                try:
                    session.add(EmailSubscriptionsORM(
                        subscription_id=email_service.subscription_id,
                        email_address=email,
                        map_to=email_service.email,
                        is_used=False,
                        date_used=None
                    ))
                except Exception as e:
                    print(str(e))
                    pass
            session.commit()
        return email_list

    @error_handler
    async def activation_email_service(self, user: User, activate: bool) -> EmailService | None:
        with self.get_session() as session:
            email_service_orm = session.query(EmailServiceORM).filter(EmailServiceORM.uid == user.uid).first()
            if isinstance(email_service_orm, EmailServiceORM):
                email_service_orm.subscription_active = activate
                email_service = EmailService(**email_service_orm.to_dict())
                session.merge(email_service_orm)
                session.commit()

                return email_service
            return None

    @error_handler
    async def get_email_service(self, user: User) -> EmailService | None:
        with self.get_session() as session:
            email_service_orm = session.query(EmailServiceORM).filter(EmailServiceORM.uid == user.uid).first()
            if isinstance(email_service_orm, EmailServiceORM):
                return EmailService(**email_service_orm.to_dict())
            else:

                return None

    async def get_email_service_subscription(self, subscription_id: str) -> list[EmailSubscriptions]:
        """

        :param user:
        :return:
        """
        with self.get_session() as session:
            email_subscription_orm = session.query(EmailSubscriptionsORM).filter(
                EmailSubscriptionsORM.subscription_id == subscription_id).all()
            return [EmailSubscriptions(**sub.to_dict()) for sub in email_subscription_orm if
                    isinstance(sub, EmailSubscriptionsORM)]

    @error_handler
    async def get_all_active_subscriptions(self) -> list[EmailService]:
        with self.get_session() as session:
            email_services_orm = session.query(EmailServiceORM).filter(
                EmailServiceORM.subscription_running == False).all()
            return [EmailService(**email_orm.to_dict()) for email_orm in email_services_orm if email_orm]

    @error_handler
    async def email_used(self, email: str):
        with self.get_session() as session:
            email_subscription_orm = session.query(EmailSubscriptionsORM).filter(
                EmailSubscriptionsORM.email == email).first()
            if isinstance(email_subscription_orm, EmailSubscriptionsORM):
                email_subscription_orm.is_used = True
                email_subscription_orm.date_used = datetime.date.today()
                session.merge(email_subscription_orm)
                session.commit()
                return True
            return False

    async def return_mappings(self) -> dict[str, str]:
        """
            this method will be called only by cloudflare
        :return:
        """
        mappings = {}
        with self.get_session() as session:
            email_subscriptions_list = session.query(EmailSubscriptionsORM).all()
            subs_list = [EmailSubscriptions(**subscript.to_dict()) for subscript in email_subscriptions_list if
                         isinstance(subscript, EmailSubscriptionsORM)]
            for subscript in subs_list:
                mappings[subscript.email_address] = subscript.map_to
        return mappings

    async def map_to(self, email: str) -> str | None:
        """
            this method is called to resolve a single email address
        :param email:
        :return:
        """
        with self.get_session() as session:
            email_subscription = session.query(EmailSubscriptionsORM).filter(
                EmailSubscriptionsORM.email_address == email).first()
            if isinstance(email_subscription, EmailSubscriptionsORM):
                return email_subscription.email_address
            return None

    async def email_stub_exist(self, email_stub: str):
        """

        :param email_stub:
        :return:
        """
        with self.get_session() as session:
            email_subscription_orm = session.query(EmailServiceORM.email_stub == email_stub).first()
            return isinstance(email_subscription_orm, EmailServiceORM)
