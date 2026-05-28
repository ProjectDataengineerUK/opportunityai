import httpx
from models import RawJob

FREELANCER_API = "https://www.freelancer.com/api/projects/0.1/projects/"
TARGET_JOBS = [3, 7, 9]  # Python, AI/ML, Data Science job IDs on Freelancer


class FreelancerSource:
    def __init__(self, token: str):
        self.token = token

    async def fetch(self) -> list[RawJob]:
        if not self.token:
            return []

        headers = {
            "freelancer-oauth-v1": self.token,
            "Content-Type": "application/json",
        }
        params = {
            "job_details": True,
            "jobs[]": TARGET_JOBS,
            "limit": 50,
            "sort_field": "time_updated",
            "reverse_sort": True,
            "full_description": True,
        }

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(FREELANCER_API, headers=headers, params=params)
            resp.raise_for_status()

        data = resp.json()
        projects = data.get("result", {}).get("projects", [])

        results = []
        for project in projects:
            budget = project.get("budget", {})
            budget_min = budget.get("minimum")
            budget_max = budget.get("maximum")
            currency = project.get("currency", {}).get("code", "USD")

            results.append(RawJob(
                external_id=f"freelancer:{project.get('id', '')}",
                source="freelancer",
                title=project.get("title", ""),
                description=project.get("description", ""),
                budget_min=float(budget_min) if budget_min else None,
                budget_max=float(budget_max) if budget_max else None,
                budget_currency=currency,
                url=f"https://www.freelancer.com/projects/{project.get('seo_url', project.get('id', ''))}",
                language="en",
                raw_data=project,
            ))

        return results
