import uuid
from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, Field, Extra


class GameAccountTypes(Enum):
    Farm = "Farm"
    Main = "Main"
    Flag = "Flag"
    Alt = "Alt"


class GameAuth(BaseModel):
    game_id: str
    game_email: str
    game_password: str
    game_pin: str | None


class GameIDS(BaseModel):
    game_id_list: list[str]


class GameDataInternal(BaseModel):
    uid: str
    game_id: str
    game_uid: str
    account_type: str
    base_level: int
    state: int
    base_name: str
    power: int
    last_login_time: datetime

    @classmethod
    def from_json(cls, data, game_id: str, uid: str):
        return cls(
            uid=uid,
            game_id=game_id,
            game_uid=data.get('gameUid'),
            account_type='Farm',
            base_level=int(data.get('level')),
            state=data.get('sid'),  # Assuming 'result' corresponds to 'state' in GameDataInternal
            base_name=data.get('name'),
            power=int(data.get('power')),
            last_login_time=datetime.strptime(data.get('lastTime'), "%Y-%m-%d %H:%M:%S")
        )


class GiftCode(BaseModel):
    code: str
    number_days_valid: int

    class Config:
        extra = Extra.ignore


class GiftCodeOut(BaseModel):
    code: str
    number_days_valid: int
    is_valid: bool
    date_submitted: date


class RedeemCodes(BaseModel):
    id: str
    game_id: str
    code: str


def today():
    return datetime.today()


def create_id():
    return str(uuid.uuid4())


class GiftCodesSubscriptions(BaseModel):
    uid: str
    subscription_id: str = Field(default_factory=create_id)
    base_limit: int
    amount_paid: int
    remaining_codes: int = Field(default=30)
    date_created: date = Field(default_factory=today)
    subscription_active: bool = Field(default=False)

    @property
    def is_valid(self):
        return (self.remaining_codes > 0) and self.subscription_active
