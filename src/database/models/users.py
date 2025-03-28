import uuid
from enum import Enum

from pydantic import BaseModel, Field, Extra

from src.main import encryptor


class UserType(str, Enum):
    ADMIN = 'admin'
    GAMER = 'gamer'


class User(BaseModel):
    """
    Represents the details of a user.

    Attributes:
    - uid (str): The ID of the user.
    - company_id (str): The ID of the company_id associated with the user.
    - is_tenant (bool): Indicates if the user is a tenant.
    - tenant_id (str): The ID of the tenant associated with the user.
    - user_type (UserType): The type of user.
    - username (str): The username of the user.
    - password (str | None): The password of the user.
    - email (str): The email address of the user.
    - full_name (str): The full name of the user.
    - contact_number (str): The contact number of the user.
    """
    uid: str
    branch_id: str | None = Field(default=None)
    company_id: str | None = Field(default=None)
    username: str | None = Field(default=None)
    password_hash: str
    email: str

    account_verified: bool = Field(default=False)

    is_system_admin: bool = Field(default=False)
    is_company_admin: bool = Field(default=False)
    is_employee: bool = Field(default=False)
    is_client: bool = Field(default=False)

    class Config:
        from_attributes = True

    def __str__(self):
        return f"User(uid={self.uid}, branch_id={self.branch_id}, company_id={self.company_id}, username={self.username}, email={self.email})"

    def __repr__(self):
        return f"User(uid='{self.uid}', branch_id='{self.branch_id}', company_id='{self.company_id}', username='{self.username}', email='{self.email}', account_verified={self.account_verified}, is_system_admin={self.is_system_admin}, is_company_admin={self.is_company_admin}, is_employee={self.is_employee}, is_client={self.is_client})"

    def __bool__(self) -> bool:
        return bool(self.uid) and bool(self.username) and bool(self.password_hash)

    def is_login(self, password: str) -> bool:
        """

        :param password:
        :return:
        """
        return encryptor.compare_hashes(hash=self.password_hash, password=password)

    def __eq__(self, other):
        """
        Compare two User instances based on their uid only.

        :param other: The other User instance to compare.
        :return: True if uid of both instances is the same, False otherwise.
        """
        if not isinstance(other, User):
            return False
        return self.uid == other.uid

    @property
    def can_access_employee_record(self):
        """will allow employee or admin to access employee file only if it's an employee and account is verified"""
        return (self.is_employee or self.is_company_admin) and self.account_verified

    def can_edit_employee_record(self, company_id: str):
        return (self.company_id == company_id) and self.is_company_admin

class CreateUser(BaseModel):
    uid: str
    username: str | None = Field(default=None)
    password: str
    email: str
    account_verified: bool = Field(default=False)

    is_system_admin: bool = Field(default=False)
    is_company_admin: bool = Field(default=False)
    is_employee: bool = Field(default=False)
    is_client: bool = Field(default=False)

    @property
    def password_hash(self):
        return encryptor.create_hash(password=self.password)

    def to_dict(self) -> dict[str, str | bool]:
        dict_ = self.dict(exclude={'password'})
        dict_.update(dict(password_hash=self.password_hash))
        return dict_


class PasswordResetUser(BaseModel):
    uid: str
    username: str | None = Field(default=None)
    password: str
    email: str
    account_verified: bool = Field(default=False)

    is_system_admin: bool = Field(default=False)
    is_company_admin: bool = Field(default=False)
    is_employee: bool = Field(default=False)
    is_client: bool = Field(default=False)

    @property
    def password_hash(self):
        return encryptor.create_hash(password=self.password)

    def to_dict(self) -> dict[str, str | bool]:
        dict_ = self.dict(exclude={'password'})
        dict_.update(dict(password_hash=self.password_hash))
        return dict_


class UserUpdate(BaseModel):
    uid: str
    username: str | None = Field(default=None)
    email: str
    account_verified: bool = Field(default=False)

    is_system_admin: bool = Field(default=False)
    is_company_admin: bool = Field(default=False)
    is_employee: bool = Field(default=False)
    is_client: bool = Field(default=False)

    class Config:
        extra = Extra.ignore


class PayPal(BaseModel):
    uid: str
    paypal_email: str

    class Config:
        extra = Extra.ignore
