from sqlalchemy import Column, String, Boolean, inspect, Integer

from src.database.constants import NAME_LEN
from src.database.sql import Base, engine


class JobORM(Base):
    __tablename__ = "lss_jobs"
    job_id: str = Column(String(NAME_LEN), primary_key=True)
    email: str = Column(String(255))
    job_completed: bool = Column(Boolean)
    job_in_progress: bool = Column(Boolean)
    file_index: int = Column(Integer)
    password_found: str | None = Column(String(NAME_LEN), nullable=True)


    @classmethod
    def create_if_not_table(cls):
        if not inspect(engine).has_table(cls.__tablename__):
            Base.metadata.create_all(bind=engine)

    @classmethod
    def delete_table(cls):
        if inspect(engine).has_table(cls.__tablename__):
            cls.__table__.drop(bind=engine)


    def to_dict(self):
        return {
            "job_id": self.job_id,
            "email": self.email,
            "job_completed": self.job_completed,
            "job_in_progress": self.job_in_progress,
            "file_index": self.file_index,
            "password_found": self.password_found
        }
