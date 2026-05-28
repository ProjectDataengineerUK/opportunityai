import asyncio
from models import RawJob
from config import AppConfig
from agents.sources.remoteok import RemoteOKSource
from agents.sources.remotive import RemotiveSource
from agents.sources.freelancer import FreelancerSource

ACCEPTED_LANGUAGES = {"pt", "en"}


class Collector:
    def __init__(self, config: AppConfig):
        self.config = config

    async def collect_all(self) -> list[RawJob]:
        tasks = []
        if self.config.sources.remoteok:
            tasks.append(RemoteOKSource().fetch())
        if self.config.sources.remotive:
            tasks.append(RemotiveSource().fetch())
        if self.config.sources.freelancer:
            tasks.append(FreelancerSource(self.config.freelancer_token).fetch())

        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_jobs: list[RawJob] = []
        for result in results:
            if isinstance(result, Exception):
                print(f"[collector] source error: {result}")
                continue
            all_jobs.extend(result)

        return self._filter(all_jobs)

    def _filter(self, jobs: list[RawJob]) -> list[RawJob]:
        filtered = []
        min_budget = self.config.user_profile.get("min_budget_usd", 0)

        for job in jobs:
            if job.language not in ACCEPTED_LANGUAGES:
                continue
            if job.budget_min is not None and job.budget_max is None:
                if job.budget_min < min_budget:
                    continue
            filtered.append(job)

        return filtered
