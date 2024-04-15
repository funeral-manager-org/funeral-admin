import uuid
from datetime import datetime
from pydantic import BaseModel, Field, Extra

import random


def create_id() -> str:
    return str(uuid.uuid4())


class Job(BaseModel):
    job_id: str = Field(default_factory=create_id)
    email: str
    job_completed: bool = Field(default=False)
    job_in_progress: bool = Field(default=False)
    file_index: int = Field(default=0)
    password_found: str | None


