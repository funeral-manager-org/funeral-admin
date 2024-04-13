import requests
from flask import Flask
from src.controller import Controllers, error_handler
from src.database.models.game import GameDataInternal
from src.database.models.market import SellerAccount, BuyerAccount, MainAccountsCredentials, MarketMainAccounts, \
    AccountOffers
from src.database.models.users import User
from src.database.sql.market import SellerAccountORM, BuyerAccountORM, MainAccountsCredentialsORM, \
    MarketMainAccountsORM, AccountOffersORM


class MarketController(Controllers):

    def __init__(self):
        super().__init__()

    def init_app(self, app: Flask):
        super().init_app(app=app)

    @error_handler
    async def activate_seller_account(self, user: User, activate: bool) -> SellerAccount:
        with self.get_session() as session:
            # Check if seller account exists for the user
            seller_account_orm = session.query(SellerAccountORM).filter(SellerAccountORM.uid == user.uid).first()

            if isinstance(seller_account_orm, SellerAccountORM):
                # If account exists, update activation status
                seller_account_orm.account_activated = activate
                session.merge(seller_account_orm)
            else:
                # If account doesn't exist, create a new one and activate it
                seller_account_orm = SellerAccountORM(uid=user.uid, account_activated=True)
                session.add(seller_account_orm)

            session.commit()  # Commit changes to the database

            # Return the corresponding SellerAccount object
            return SellerAccount(**seller_account_orm.to_dict()) if seller_account_orm else SellerAccount(
                uid=user.uid, account_activated=True)

    @error_handler
    async def activate_buyer_account(self, user: User, activate: bool):
        with self.get_session() as session:
            buyer_account_orm: BuyerAccountORM = session.query(BuyerAccountORM).filter(
                BuyerAccountORM.uid == user.uid).first()

            if isinstance(buyer_account_orm, BuyerAccountORM):
                buyer_account_orm.account_activated = activate

                session.merge(buyer_account_orm)
            else:
                buyer_account_orm = BuyerAccountORM(uid=user.uid, account_activated=True)
                session.add(buyer_account_orm)

            session.commit()

            return BuyerAccount(**buyer_account_orm.to_dict()) if buyer_account_orm else BuyerAccount(uid=user.uid,
                                                                                                      account_activated=True)

    @error_handler
    async def get_buyer_account(self, uid: str) -> BuyerAccount:
        with self.get_session() as session:
            buyer_account_orm = session.query(BuyerAccountORM).filter(BuyerAccountORM.uid == uid).first()
            if isinstance(buyer_account_orm, BuyerAccountORM):
                return BuyerAccount(**buyer_account_orm.to_dict())

            buyer_account = BuyerAccount(uid=uid)
            session.add(BuyerAccountORM(**buyer_account.dict()))
            session.commit()
            return buyer_account

    @error_handler
    async def get_seller_account(self, uid: str) -> SellerAccount:
        with self.get_session() as session:
            seller_account_orm = session.query(SellerAccountORM).filter(SellerAccountORM.uid == uid).first()
            if isinstance(seller_account_orm, SellerAccountORM):
                return SellerAccount(**seller_account_orm.to_dict())
            seller_account = SellerAccount(uid=uid)
            session.add(SellerAccountORM(**seller_account.dict()))
            session.commit()
            return seller_account

    @error_handler
    async def approved_for_market(self, uid: str, is_approved: bool = False):
        """
            On Approval the selle rating will start at 5
        :param uid:
        :param is_approved:
        :return:
        """
        with self.get_session() as session:
            seller_account_orm = session.query(SellerAccountORM).filter(SellerAccountORM.uid == uid).first()
            if isinstance(seller_account_orm, SellerAccountORM):
                seller_account_orm.account_verified = is_approved
                seller_account_orm.seller_rating = 5

                session.merge(seller_account_orm)

                session.commit()
                return True
            return False

    @error_handler
    async def add_game_account_credentials(self, game_account: MainAccountsCredentials):
        """

        :param game_account:
        :return:
        """
        with self.get_session() as session:
            account_creds_orm = session.query(MainAccountsCredentialsORM).filter(
                MainAccountsCredentialsORM.account_email == game_account.account_email).first()
            if isinstance(account_creds_orm, MainAccountsCredentialsORM):
                return None

            session.add(MainAccountsCredentialsORM(**game_account.dict()))
            session.commit()
            return game_account

    @error_handler
    async def add_account_market_listing(self,
                                         market_account: MarketMainAccounts,
                                         account_credentials: MainAccountsCredentials):
        """
            :param market_account:
            :param account_data:
            :param account_credentials:
            :return:
        """
        with self.get_session() as session:
            listed_account_orm = session.query(MarketMainAccountsORM).filter_by(game_id=market_account.game_id).first()
            if isinstance(listed_account_orm, MarketMainAccountsORM):
                return None
            new_listing_orm = MarketMainAccountsORM(**market_account.dict())

            session.add(new_listing_orm)
            session.commit()
            return market_account

    @error_handler
    async def get_listed_account(self, listing_id: str) -> MarketMainAccounts | None:
        """

        :param listing_id:
        :return:
        """
        with self.get_session() as session:

            listed_account_orm = session.query(MarketMainAccountsORM).filter(
                MarketMainAccountsORM.listing_id==listing_id).first()

            if isinstance(listed_account_orm, MarketMainAccountsORM):
                return MarketMainAccounts(**listed_account_orm.to_dict())
            return None

    @error_handler
    async def get_public_listed_accounts(self) -> list[MarketMainAccounts]:
        """

        :return:
        """
        with self.get_session() as session:
            listed_accounts = session.query(MarketMainAccountsORM).filter(
                MarketMainAccountsORM.listing_active == True).all()

            return [MarketMainAccounts(**account.to_dict()) for account in listed_accounts
                    if isinstance(account, MarketMainAccountsORM)]

    async def get_user_listed_accounts(self, uid: str) -> list[MarketMainAccounts]:
        with self.get_session() as session:
            listed_accounts = session.query(MarketMainAccountsORM).filter(
                MarketMainAccountsORM.uid == uid).all()
            return [MarketMainAccounts(**account.to_dict()) for account in listed_accounts
                    if isinstance(account, MarketMainAccountsORM)]

    async def get_listed_account_by_listing_id(self, listing_id: str) -> MarketMainAccounts | None:
        """

        :param listing_id:
        :return:
        """

        with self.get_session() as session:
            listed_account_orm = session.query(MarketMainAccountsORM).filter(
                MarketMainAccountsORM.listing_id == listing_id).first()
            if isinstance(listed_account_orm, MarketMainAccountsORM):
                return MarketMainAccounts(**listed_account_orm.to_dict())
            return None

    async def update_listed_account(self, listed_account: MarketMainAccounts):
        """

        :param listed_account:
        :return:
        """
        with self.get_session() as session:
            listing_id = listed_account.listing_id
            listed_account_orm = session.query(MarketMainAccountsORM).filter(
                MarketMainAccountsORM.listing_id == listing_id).first()
            if isinstance(listed_account_orm, MarketMainAccountsORM):
                # Update the attributes of the ORM object with the new values
                listed_account_orm.uid = listed_account.uid
                listed_account_orm.total_gold_cards = listed_account.total_gold_cards
                listed_account_orm.total_hero_tokens = listed_account.total_hero_tokens
                listed_account_orm.total_skins = listed_account.total_skins
                listed_account_orm.gold_sets_vehicles = listed_account.gold_sets_vehicles
                listed_account_orm.gold_sets_fighters = listed_account.gold_sets_fighters
                listed_account_orm.gold_sets_shooters = listed_account.gold_sets_shooters
                listed_account_orm.bane_blade_sets = listed_account.bane_blade_sets
                listed_account_orm.fighter_units_level = listed_account.fighter_units_level
                listed_account_orm.shooter_units_level = listed_account.shooter_units_level
                listed_account_orm.vehicle_units_level = listed_account.vehicle_units_level
                listed_account_orm.state_season = listed_account.state_season
                listed_account_orm.season_heroes = listed_account.season_heroes
                listed_account_orm.sp_heroes = listed_account.sp_heroes
                listed_account_orm.universal_sp_medals = listed_account.universal_sp_medals
                listed_account_orm.amount_spent_packages = listed_account.amount_spent_packages
                listed_account_orm.vip_shop = listed_account.vip_shop
                listed_account_orm.energy_lab_level = listed_account.energy_lab_level
                listed_account_orm.energy_lab_password = listed_account.energy_lab_password
                listed_account_orm.listing_active = listed_account.listing_active
                listed_account_orm.is_bought = listed_account.is_bought
                listed_account_orm.in_negotiation = listed_account.in_negotiation

                # Commit the changes to the database
                session.commit()
                return listed_account
            return None


    async def create_offer(self, account_offers: AccountOffers) -> AccountOffers | None:
        with self.get_session() as session:
            account_offer_orm = session.query(AccountOffersORM).filter(AccountOffersORM.offer_id == account_offers.offer_id).first()
            if isinstance(account_offer_orm, AccountOffersORM):
                return None
            session.add(AccountOffersORM(**account_offers.dict()))
            session.commit()

            return account_offers