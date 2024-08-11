import uuid

from pydantic import BaseModel, Field, validator

from utils import create_id


class Auth(BaseModel):
    email: str
    username: str | None
    password: str
    remember: str | None

    @validator('username')
    def convert_to_lower(cls, value):
        return value.lower()


class RegisterUser(BaseModel):
    uid: str = Field(default_factory=create_id)
    username: str | None
    email: str
    password: str
    terms: str

