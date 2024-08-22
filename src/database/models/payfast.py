

from pydantic import BaseModel, PositiveInt, Field

from src.database.constants import NAME_LEN


class PayFastPay(BaseModel):
    return_url: str
    cancel_url: str
    notify_url: str
    amount: PositiveInt
    item_name: str
    item_description: str
    company_id: str
    uid: str
    subscription_id: str


class PayFastData(BaseModel):
    merchant_id: str | None = Field(default=None)
    merchant_key: str | None = Field(default=None)
    return_url: str | None = Field(default=None)
    cancel_url: str | None = Field(default=None)
    notify_url: str | None = Field(default=None)
    item_name: str | None = Field(default=None)
    item_description: str | None = Field(default=None)
    company_id: str | None = Field(default=None)
    uid: str | None = Field(default=None)
    subscription_id: str | None = Field(default=None)
    amount: PositiveInt = Field(default=0)


