from enum import Enum

from pydantic import BaseModel, Field
from datetime import datetime

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
    message: str
    to_branch: str
    recipient_type: str
    date_time_composed: str = Field(default_factory=date_time)
    date_time_sent: str | None
    is_delivered: bool = Field(default=False)
