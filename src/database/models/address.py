import uuid
from pydantic import BaseModel, Field


class Address(BaseModel):
    """
    Represents an address.

    Attributes:
    - address_id (str): The unique ID of the address.
    - street (str): The street address.
    - city (str): The city.
    - state (str): The state.
    - postal_code (str): The postal code.
    - country (str): The country.
    """

    address_id: str = Field(default_factory=lambda: str(uuid.uuid4()),
                            description="The unique ID of the address.")
    street: str
    city: str
    state: str
    postal_code: str
    country: str
