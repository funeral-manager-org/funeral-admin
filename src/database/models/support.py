from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
from src.database.models.users import User
from src.utils import create_id


class TicketStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class TicketTypes(str, Enum):
    BILLING = "billing"
    COVERS = "covers"
    MESSAGING = "messaging"
    EMPLOYEES = "employees"
    PLANS = "plans"

    @classmethod
    def ticket_types_list(cls) -> list[str]:
        return [cls.BILLING.value, cls.COVERS.value, cls.MESSAGING.value, cls.EMPLOYEES.value, cls.PLANS.value]


class TicketPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

    @classmethod
    def priority_list(cls) -> list[str]:
        """

        :return:
        """
        return [cls.LOW.value, cls.MEDIUM.value, cls.HIGH.value, cls.URGENT.value]


class TicketMessage(BaseModel):
    message_id: str = Field(default_factory=create_id)
    ticket_id: str
    sender_id: str
    message: str
    created_at: datetime = Field(default=datetime.utcnow)


class Ticket(BaseModel):
    ticket_id: str = Field(default_factory=create_id)

    user_id: str

    assigned_to: str
    ticket_type: str
    subject: str

    status: str = Field(default=TicketStatus.OPEN.value)
    priority: str = Field(default=TicketPriority.MEDIUM.value)
    created_at: datetime = Field(default=datetime.utcnow)
    updated_at: datetime = Field(default=datetime.utcnow)

    messages: list[TicketMessage]
