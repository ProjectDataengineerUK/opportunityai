import httpx
from models import RawJob

REMOTIVE_URL = "https://remotive.com/api/remote-jobs"
CATEGORIES = ["software-dev", "data", "devops-sysadmin"]
KEYWORDS = ["python", "ai", "machine learning", "data", "llm", "automation", "backend", "fastapi"]


class RemotiveSource:
    async def fetch(self) -> list[RawJob]:
        results = []
        async with httpx.AsyncClient(timeout=30) as client:
            for category in CATEGORIES:
                resp = await client.get(REMOTIVE_URL, params={"category": category, "limit": 50})
                resp.raise_for_status()
                data = resp.json()
                for job in data.get("jobs", []):
                    title_desc = (job.get("title", "") + " " + job.get("description", "")).lower()
                    if not any(kw in title_desc for kw in KEYWORDS):
                        continue

                    salary_min = None
                    salary_raw = job.get("salary", "")
                    if salary_raw and "$" in salary_raw:
                        import re
                        nums = re.findall(r"\d+(?:,\d+)?(?:k)?", salary_raw.replace(",", ""))
                        if nums:
                            try:
                                val = float(nums[0].replace("k", "000"))
                                salary_min = val / 12 if val > 10000 else val
                            except ValueError:
                                pass

                    results.append(RawJob(
                        external_id=f"remotive:{job.get('id', '')}",
                        source="remotive",
                        title=job.get("title", ""),
                        description=job.get("description", ""),
                        budget_min=salary_min,
                        budget_currency="USD",
                        url=job.get("url", ""),
                        language="en",
                        raw_data=job,
                    ))

        seen = set()
        unique = []
        for r in results:
            if r.external_id not in seen:
                seen.add(r.external_id)
                unique.append(r)
        return unique
