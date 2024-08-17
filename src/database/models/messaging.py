from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field
from datetime import datetime

from src.database.models import ID_LEN
from src.utils import create_id


def date_time() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class RecipientTypes(Enum):
    EMPLOYEES = "Employees"
    CLIENTS = "Policy Holders"
    LAPSED_POLICY = "Lapsed Policy - Policy Holders"

    @classmethod
    def get_fields(cls):
        """Return a list of field names."""
        return [field.value for field in cls]


class SMSCompose(BaseModel):

    message_id: str = Field(default_factory=create_id)
    reference: Optional[str] = Field(default=None)
    message: str = Field(min_length=2, max_length=255)
    from_cell: Optional[str] = Field(default=None, min_length=10, max_length=16)
    to_cell: Optional[str] = Field(default=None, min_length=10, max_length=16)
    to_branch: str = Field(min_length=ID_LEN, max_length=ID_LEN)
    recipient_type: str
    date_time_composed: str = Field(default_factory=date_time)
    date_time_sent: Optional[str] =  Field(default=None)
    is_delivered: bool = Field(default=False)
    client_responded: bool = Field(default=False)

    @property
    def to_cell_za(self):
        """Return South African international format from a ten-digit cell number."""
        if self.to_cell and self.to_cell.startswith("0") and len(self.to_cell) == 10:
            return f"+27{self.to_cell[1:]}"
        return self.to_cell

    @property
    def from_cell_za(self):
        """ South African international format of the from number:return:"""
        if self.from_cell and self.from_cell.startswith("0") and len(self.from_cell) == 10:
            return f"+27{self.from_cell[1:]}"
        return self.from_cell

class SMSInbox(BaseModel):

    message_id: str = Field(default_factory=create_id)
    to_branch: str
    parent_reference: Optional[str] = Field(default=None)
    from_cell: Optional[str] = None
    is_response: bool = Field(default=True)
    previous_history: Optional[str] = Field(default=None)
    message: str
    date_time_received: str = Field(default_factory=date_time)
    is_read: bool = Field(default=False)


class EmailCompose(BaseModel):
    """
        email compose
    """
    message_id: str = Field(default_factory=create_id)
    reference: Optional[str] = Field(default=None)
    from_email: Optional[str] = Field(default=None)
    to_email: Optional[str] = Field(default=None)
    subject: str
    message: str
    to_branch: Optional[str] = Field(default=None)
    recipient_type: str
    is_sent: bool = Field(default=False)
    date_time_sent: Optional[str] = Field(default=None)


class SMSSettings(BaseModel):
    company_id: str
    enable_sms_notifications: bool = Field(default=False)
    enable_sms_campaigns: bool = Field(default=False)
    sms_signature: str
    policy_lapsed_notifications: bool = Field(default=False)
    upcoming_payments_notifications: bool = Field(default=False)
    policy_paid_notifications: bool = Field(default=False)
    claims_notifications: bool = Field(default=False)
