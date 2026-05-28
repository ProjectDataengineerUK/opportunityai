import httpx
from models import RawJob

REMOTEOK_URL = "https://remoteok.com/api"
TARGET_TAGS = {"python", "ai", "machine-learning", "data", "backend", "automation", "llm", "nlp"}


class RemoteOKSource:
    async def fetch(self) -> list[RawJob]:
        headers = {"User-Agent": "OpportunityAI/1.0"}
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(REMOTEOK_URL, headers=headers)
            resp.raise_for_status()

        jobs = resp.json()
        # First item is metadata, skip it
        if jobs and isinstance(jobs[0], dict) and "legal" in jobs[0]:
            jobs = jobs[1:]

        results = []
        for job in jobs:
            if not isinstance(job, dict):
                continue
            tags = {t.lower() for t in job.get("tags", [])}
            if not tags.intersection(TARGET_TAGS):
                continue

            salary_min = None
            if job.get("salary_min"):
                try:
                    salary_min = float(job["salary_min"])
                except (ValueError, TypeError):
                    pass

            results.append(RawJob(
                external_id=f"remoteok:{job.get('id', job.get('slug', ''))}",
                source="remoteok",
                title=job.get("position", ""),
                description=job.get("description", ""),
                budget_min=salary_min,
                budget_currency="USD",
                url=job.get("url", ""),
                language="en",
                raw_data=job,
            ))

        return results
