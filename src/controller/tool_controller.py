import pickle

import aiocache
from flask import Flask

from src.controller import Controllers
from src.database.models.tool import Job
from src.database.sql.tool import JobORM


class ToolController(Controllers):
    def __init__(self):
        super().__init__()

    def init_app(self, app: Flask):
        """

        :param app:
        :return:
        """
        pass

    async def create_job(self, job: Job) -> Job | None:
        """

        :param email:
        :return:
        """
        with self.get_session() as session:
            job_orm = session.query(JobORM).filter(JobORM.email == job.email).first()
            if isinstance(job_orm, JobORM):
                return None

            session.add(JobORM(**job.dict()))
            session.commit()
            return job

    async def get_all_jobs(self) -> list[Job]:
        """

        :return:
        """
        with self.get_session() as session:
            job_list_orm = session.query(JobORM).all()
            return [Job(**job_orm.to_dict()) for job_orm in job_list_orm if isinstance(job_orm, JobORM)]

    @aiocache.cached(ttl=3600)
    async def get_job(self, job_id: str) -> Job | None:
        """

        :param job_id:
        :return:
        """
        with self.get_session() as session:
            job_orm = session.query(JobORM).filter(JobORM.job_id == job_id).first()
            if not isinstance(job_orm, JobORM):
                return None

            return Job(**job_orm.to_dict())

    async def update_job(self, job: Job) -> Job:
        with self.get_session() as session:
            job_orm = session.query(JobORM).filter(JobORM.job_id == job.job_id).first()
            if isinstance(job_orm, JobORM):
                job_orm.job_completed = job.job_completed
                job_orm.job_in_progress = job.job_in_progress
                job_orm.password_found = job.password_found
                job_orm.email = job.email
                job_orm.file_index = job.file_index

                session.commit()
            return job

    async def get_file(self, file_index: int) -> dict[str, str]:
        """

        :param file_index:
        :return:
        """
        password_filename = f"passwords-{file_index}.bin"
        passwords_dict = {}
        long_filename = f"src/tools/{password_filename}"
        with open(long_filename, "rb") as _file:
            while True:
                try:
                    batch = pickle.load(_file)
                    passwords_dict.update(batch)
                except EOFError:
                    break

        return passwords_dict
