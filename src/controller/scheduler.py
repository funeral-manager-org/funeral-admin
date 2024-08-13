import asyncio
from datetime import datetime, timedelta


class Scheduler:
    def __init__(self):
        self.tasks = []

    async def schedule(self, routine, interval):
        """
        Schedule a routine to run at specified intervals.

        :param routine: The routine to be scheduled.
        :param interval: The interval at which the routine should run (in seconds).
        """
        while True:
            await routine()
            await asyncio.sleep(interval)

    async def run_at_specific_time(self, routine, days, hour, minute, second=0):
        """
        Schedule a routine to run at a specific time of the day.

        :param routine: The routine to be scheduled.
        :param hour: The hour at which the routine should run.
        :param minute: The minute at which the routine should run.
        :param second: The second at which the routine should run (default is 0).
        """
        while True:
            now = datetime.now()
            next_run = now.replace(hour=hour, minute=minute, second=second)
            if now > next_run:
                next_run += timedelta(days=days)

            await asyncio.sleep((next_run - datetime.now()).total_seconds())
            await routine()

    async def run_every_minute(self, routine):
        """
        Schedule a routine to run every minute.

        :param routine: The routine to be scheduled.
        """
        await self.schedule(routine, 60)  # 60 seconds = 1 minute

    async def run_every_hour(self, routine):
        """
        Schedule a routine to run every hour.

        :param routine: The routine to be scheduled.
        """
        await self.schedule(routine, 3600)  # 3600 seconds = 1 hour

    async def run_every_day(self, routine):
        """
        Schedule a routine to run every day.

        :param routine: The routine to be scheduled.
        """
        await self.run_at_specific_time(routine, days=1, hour=0, minute=0)  # Run at midnight

    async def run_every_week(self, routine):
        """
        Schedule a routine to run every week.

        :param routine: The routine to be scheduled.
        """
        await self.run_at_specific_time(routine, days=7, hour=9, minute=0, second=0)  # Run at midnight on Sunday
