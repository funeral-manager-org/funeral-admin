import uuid
from datetime import date, datetime
from enum import Enum

from flask import url_for
from pydantic import BaseModel, Field, Extra


class SellerAccount(BaseModel):
    """
        A Strcuture needed for Sellers to sell their Farms
    """
    uid: str
    # A Rating of 1 to 10 Based on Feedback
    seller_rating: int = Field(default=0)
    seller_name: str | None
    promotional_content: str | None
    account_verified: bool = Field(default=False)
    # Farms, Accounts and Skins
    total_items_sold: int = Field(default=0)
    # Amount Sold in Dollars
    total_amount_sold: int = Field(default=0)
    account_activated: bool = Field(default=False)


class BuyerAccount(BaseModel):
    uid: str
    buyer_rating: int = Field(default=0)  # A Rating of 1 to 10 Based on Feedback
    buyer_name: str | None  # Name of the Buyer , Could Also be a nickname
    account_verified: bool = Field(default=False)

    total_accounts_bought: int = Field(default=0)
    total_skins_bought: int = Field(default=0)

    total_amount_spent: int = Field(default=0)  # Amount Spent in Dollars
    amount_in_escrow: int = Field(default=0)  # Amount the buyer puts in Escrow to secure a sale
    account_activated: bool = Field(default=False)


#################################################################################################

class FarmSale(BaseModel):
    uid: str  # ID of the user selling the Farm
    package_id: str  # ID of the Packaged Deal

    state: int
    average_base_level: int
    total_farms: int
    total_bought: int = Field(default=0)
    item_price: int
    package_price: int
    farm_manager_available: bool
    image_url: str
    accounts_verified: bool
    notes: str

    def farms_remaining(self):
        return self.total_farms - self.total_bought


class FarmResources(BaseModel):
    """
        Average Resources Per Farm
    """
    package_id: str
    total_iron: int
    total_wood: int
    total_oil: int
    total_food: int
    total_money: int


class FarmIDS(BaseModel):
    """
        List of Farms Being Sold
    """
    package_id: str
    uid: str
    game_id: str
    game_uid: str
    base_level: int
    state: int
    base_name: str
    base_level: int
    power: int


class FarmCredentials(BaseModel):
    game_id: str
    account_email: str
    password: str
    pin: str | None


#################################################################################################

def create_id():
    return str(uuid.uuid4())


def default_listing_image():
    return url_for('static', filename='images/lss/base.jpg')


class MarketMainAccounts(BaseModel):
    """
        A Structure that allows users to sell Main Accounts
    """
    listing_id: str = Field(default_factory=create_id)
    uid: str  # ID of the user making the Account Sale
    game_id: str
    game_uid: str
    # The State number the Account is in
    state: int
    # Base Level of the Account
    base_level: int
    # Price for the Account
    item_price: int

    image_url: str = Field(default_factory=default_listing_image)

    total_gold_cards: int = Field(default=0)
    total_hero_tokens: int = Field(default=0)
    total_skins: int = Field(default=0)

    gold_sets_vehicles = Field(default=0)
    gold_sets_fighters = Field(default=0)
    gold_sets_shooters = Field(default=0)
    bane_blade_sets = Field(default=0)

    fighter_units_level = Field(default=7)
    shooter_units_level = Field(default=7)
    vehicle_units_level = Field(default=7)

    state_season: int = Field(default=1)
    season_heroes: int = Field(default=0)
    sp_heroes: int = Field(default=0)
    universal_sp_medals: int = Field(default=0)

    amount_spent_packages: int = Field(default=0)  # Amount Spent on Packages
    vip_shop: bool = Field(default=False)
    energy_lab_level: int = Field(default=1)
    energy_lab_password: str | None

    listing_active: bool = Field(default=False)
    in_negotiation: bool = Field(default=False)
    is_bought: bool = Field(default=False)


class MainAccountsCredentials(BaseModel):
    """
        Verification should verify also the Game ID
    """
    game_id: str
    account_email: str
    account_password: str
    account_pin: str
    is_verified: bool = Field(default=False)


class AccountOffers(BaseModel):
    offer_id: str = Field(default_factory=create_id)
    listing_id: str
    buyer_uid: str
    seller_uid: str
    offer_amount: int
    asking_amount: int
    offer_notes: str
    offer_accepted: bool = Field(default=False)
    date_accepted: date | None
