import uuid
from datetime import datetime, timedelta

from sqlalchemy import Column, String, inspect, ForeignKey, Boolean, func, Integer, Date, DateTime, Text

from src.database.constants import ID_LEN, NAME_LEN
from src.database.sql import Base, engine


class SellerAccountORM(Base):
    __tablename__ = "seller_account"
    uid: str = Column(String(ID_LEN), primary_key=True)
    seller_rating: int = Column(Integer)
    seller_name: str = Column(String(NAME_LEN))
    promotional_content: str = Column(Text)
    account_verified: bool = Column(Boolean)
    total_items_sold: int = Column(Integer)

    total_amount_sold: int = Column(Integer)
    account_activated: bool = Column(Boolean)

    @classmethod
    def create_if_not_table(cls):
        if not inspect(engine).has_table(cls.__tablename__):
            Base.metadata.create_all(bind=engine)

    @classmethod
    def delete_table(cls):
        if inspect(engine).has_table(cls.__tablename__):
            cls.__table__.drop(bind=engine)

    def to_dict(self):
        return {
            'uid': self.uid,
            'seller_rating': self.seller_rating,
            'seller_name': self.seller_name,
            'promotional_content': self.promotional_content,
            'account_verified': self.account_verified,
            'total_items_sold': self.total_items_sold,
            'total_amount_sold': self.total_amount_sold,
            'account_activated': self.account_activated
        }


class BuyerAccountORM(Base):
    __tablename__ = "buyer_account"
    uid: str = Column(String(ID_LEN), primary_key=True)
    buyer_rating: int = Column(Integer)
    buyer_name: int = Column(String(NAME_LEN))
    account_verified: bool = Column(Boolean)

    total_accounts_bought: int = Column(Integer)
    total_skins_bought: int = Column(Integer)

    total_amount_spent: int = Column(Integer)
    amount_in_escrow: int = Column(Integer)
    account_activated: bool = Column(Boolean)

    @classmethod
    def create_if_not_table(cls):
        if not inspect(engine).has_table(cls.__tablename__):
            Base.metadata.create_all(bind=engine)

    @classmethod
    def delete_table(cls):
        if inspect(engine).has_table(cls.__tablename__):
            cls.__table__.drop(bind=engine)

    def to_dict(self):
        return {
            'uid': self.uid,
            'buyer_rating': self.buyer_rating,
            'buyer_name': self.buyer_name,
            'account_verified': self.account_verified,
            'total_accounts_bought': self.total_accounts_bought,
            'total_skins_bought': self.total_skins_bought,
            'total_amount_spent': self.total_amount_spent,
            'amount_in_escrow': self.amount_in_escrow,
            'account_activated': self.account_activated
        }


class FarmSaleORM(Base):
    __tablename__ = "farm_sales"
    uid: str = Column(String(ID_LEN))
    package_id: str = Column(String(ID_LEN), primary_key=True)

    state: int = Column(Integer)
    average_base_level: int = Column(Integer)
    total_farms: int = Column(Integer)
    total_bought: int = Column(Integer)
    item_price: int = Column(Integer)
    package_price: int = Column(Integer)
    farm_manager_available: bool = Column(Boolean)
    image_url: str = Column(String(255))
    accounts_verified: bool = Column(Boolean)
    notes: str = Column(String(255))

    @classmethod
    def create_if_not_table(cls):
        if not inspect(engine).has_table(cls.__tablename__):
            Base.metadata.create_all(bind=engine)

    @classmethod
    def delete_table(cls):
        if inspect(engine).has_table(cls.__tablename__):
            cls.__table__.drop(bind=engine)

    def to_dict(self):
        return {
            "uid": self.uid,
            "package_id": self.package_id,
            "state": self.state,
            "average_base_level": self.average_base_level,
            "total_farms": self.total_farms,
            "total_bought": self.total_bought,
            "item_price": self.item_price,
            "package_price": self.package_price,
            "farm_manager_available": self.farm_manager_available,
            "image_url": self.image_url,
            "accounts_verified": self.accounts_verified,
            "notes": self.notes
        }


class FarmResourcesORM(Base):
    __tablename__ = "farm_resources"
    package_id: str = Column(String(ID_LEN), primary_key=True)
    total_iron: int = Column(Integer)
    total_wood: int = Column(Integer)
    total_oil: int = Column(Integer)
    total_food: int = Column(Integer)
    total_money: int = Column(Integer)

    @classmethod
    def create_if_not_table(cls):
        if not inspect(engine).has_table(cls.__tablename__):
            Base.metadata.create_all(bind=engine)

    @classmethod
    def delete_table(cls):
        if inspect(engine).has_table(cls.__tablename__):
            cls.__table__.drop(bind=engine)

    def to_dict(self):
        return {
            "package_id": self.package_id,
            "total_iron": self.total_iron,
            "total_wood": self.total_wood,
            "total_oil": self.total_oil,
            "total_food": self.total_food,
            "total_money": self.total_money
        }


class FarmIDORM(Base):
    __tablename__ = "farm_id"
    package_id: str = Column(String(NAME_LEN))
    uid: str = Column(String(NAME_LEN))
    game_id: str = Column(String(NAME_LEN), primary_key=True)
    game_uid: str = Column(String(NAME_LEN))
    base_level: int = Column(Integer)
    state: int = Column(Integer)
    base_name: str = Column(String(NAME_LEN))

    power: int = Column(Integer)

    @classmethod
    def create_if_not_table(cls):
        if not inspect(engine).has_table(cls.__tablename__):
            Base.metadata.create_all(bind=engine)

    @classmethod
    def delete_table(cls):
        if inspect(engine).has_table(cls.__tablename__):
            cls.__table__.drop(bind=engine)

    def to_dict(self):
        return {
            "package_id": self.package_id,
            "uid": self.uid,
            "game_id": self.game_id,
            "game_uid": self.game_uid,
            "base_level": self.base_level,
            "state": self.state,
            "base_name": self.base_name,
            "power": self.power
        }


class FarmCredentialsORM(Base):
    __tablename__ = "farm_credentials"
    game_id: str = Column(String(ID_LEN), primary_key=True)
    account_email: str = Column(String(255))
    password: str = Column(String(NAME_LEN))
    pin: str = Column(String(NAME_LEN), nullable=True)

    @classmethod
    def create_if_not_table(cls):
        if not inspect(engine).has_table(cls.__tablename__):
            Base.metadata.create_all(bind=engine)

    @classmethod
    def delete_table(cls):
        if inspect(engine).has_table(cls.__tablename__):
            cls.__table__.drop(bind=engine)

    def to_dict(self):
        return {
            "game_id": self.game_id,
            "account_email": self.account_email,
            "password": self.password,
            "pin": self.pin
        }


class MainAccountsCredentialsORM(Base):
    __tablename__ = "market_accounts_creds"
    game_id: str = Column(String(ID_LEN), primary_key=True)
    account_email: str = Column(String(255))
    account_password: str = Column(String(NAME_LEN))
    account_pin: str = Column(String(NAME_LEN))
    is_verified: bool = Column(Boolean)


    @classmethod
    def create_if_not_table(cls):
        if not inspect(engine).has_table(cls.__tablename__):
            Base.metadata.create_all(bind=engine)

    @classmethod
    def delete_table(cls):
        if inspect(engine).has_table(cls.__tablename__):
            cls.__table__.drop(bind=engine)

    def to_dict(self):
        return {
            "game_id": self.game_id,
            "account_email": self.account_email,
            "account_password": self.account_password,
            "account_pin": self.account_pin,
            "is_verified": self.is_verified,
        }


class MarketMainAccountsORM(Base):
    """
    ORM Model for listing accounts in the market place
    """
    __tablename__ = 'main_accounts_market'
    listing_id = Column(String(NAME_LEN), primary_key=True)
    uid = Column(String(NAME_LEN))  # ID of the user making the Account Sale
    game_id = Column(String(NAME_LEN))
    game_uid = Column(String(NAME_LEN))
    state = Column(Integer)  # The State number the Account is in
    base_level = Column(Integer)  # Base Level of the Account
    item_price = Column(Integer)  # Price for the Account

    image_url = Column(String(255))

    total_gold_cards = Column(Integer)
    total_hero_tokens = Column(Integer)
    total_skins = Column(Integer)

    gold_sets_vehicles = Column(Integer)
    gold_sets_fighters = Column(Integer)
    gold_sets_shooters = Column(Integer)
    bane_blade_sets = Column(Integer)

    fighter_units_level = Column(Integer)
    shooter_units_level = Column(Integer)
    vehicle_units_level = Column(Integer)

    state_season = Column(Integer)
    season_heroes = Column(Integer)
    sp_heroes = Column(Integer)
    universal_sp_medals = Column(Integer)

    amount_spent_packages = Column(Integer)  # Amount Spent on Packages
    vip_shop = Column(Boolean)
    energy_lab_level = Column(Integer)
    energy_lab_password = Column(String(12))

    listing_active = Column(Boolean)
    in_negotiation = Column(Boolean)
    is_bought = Column(Boolean)


    @classmethod
    def create_if_not_table(cls):
        if not inspect(engine).has_table(cls.__tablename__):
            Base.metadata.create_all(bind=engine)

    @classmethod
    def delete_table(cls):
        if inspect(engine).has_table(cls.__tablename__):
            cls.__table__.drop(bind=engine)

    def to_dict(self):
        return {
            "listing_id": self.listing_id,
            "uid": self.uid,
            "game_id": self.game_id,
            "game_uid": self.game_uid,
            "state": self.state,
            "base_level": self.base_level,
            "item_price": self.item_price,
            "image_url": self.image_url,
            "total_gold_cards": self.total_gold_cards,
            "total_hero_tokens": self.total_hero_tokens,
            "total_skins": self.total_skins,
            "gold_sets_vehicles": self.gold_sets_vehicles,
            "gold_sets_fighters": self.gold_sets_fighters,
            "gold_sets_shooters": self.gold_sets_shooters,
            "bane_blade_sets": self.bane_blade_sets,
            "fighter_units_level": self.fighter_units_level,
            "shooter_units_level": self.shooter_units_level,
            "vehicle_units_level": self.vehicle_units_level,
            "state_season": self.state_season,
            "season_heroes": self.season_heroes,
            "sp_heroes": self.sp_heroes,
            "universal_sp_medals": self.universal_sp_medals,
            "amount_spent_packages": self.amount_spent_packages,
            "vip_shop": self.vip_shop,
            "energy_lab_level": self.energy_lab_level,
            "energy_lab_password": self.energy_lab_password,
            "listing_active": self.listing_active,
            "in_negotiation": self.in_negotiation,
            "is_bought": self.is_bought
        }


class AccountOffersORM(Base):
    __tablename__ = "account_offers"
    offer_id = Column(String(NAME_LEN), primary_key=True)
    listing_id = Column(String(NAME_LEN))
    buyer_uid = Column(String(NAME_LEN))
    seller_uid = Column(String(NAME_LEN))
    offer_amount = Column(Integer)
    asking_amount = Column(Integer)
    offer_notes = Column(String(255))
    offer_accepted = Column(Boolean)
    date_accepted = Column(Date)

    @classmethod
    def create_if_not_table(cls):
        if not inspect(engine).has_table(cls.__tablename__):
            Base.metadata.create_all(bind=engine)

    @classmethod
    def delete_table(cls):
        if inspect(engine).has_table(cls.__tablename__):
            cls.__table__.drop(bind=engine)

    def to_dict(self):
        return {
            "offer_id": self.offer_id,
            "buyer_uid": self.buyer_uid,
            "listing_id": self.listing_id,
            "seller_uid": self.seller_uid,
            "offer_amount": self.offer_amount,
            "asking_amount": self.asking_amount,
            "offer_notes": self.offer_notes,
            "offer_accepted": self.offer_accepted,
            "date_accepted": self.date_accepted
        }
