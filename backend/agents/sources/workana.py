import html
import re
import httpx
from models import RawJob

# Workana não expõe API pública. A listagem de projetos é renderizada via JS,
# mas o mesmo endpoint responde JSON quando chamado como XHR (X-Requested-With).
WORKANA_URL = "https://www.workana.com/jobs"
CATEGORIES = ["it-programming"]
KEYWORDS = [
    "python", "ai", "ia", "machine learning", "ml", "data", "dados", "llm",
    "automation", "automação", "automacao", "backend", "fastapi", "api", "etl",
]
MAX_PAGES = 3

_TAG_RE = re.compile(r"<[^>]+>")
_NUM_RE = re.compile(r"\d[\d.]*")
_TITLE_ATTR_RE = re.compile(r'title="([^"]+)"')
_CURRENCY_RE = re.compile(r"\b([A-Z]{3})\b")
_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64)",
    "X-Requested-With": "XMLHttpRequest",
    "Accept": "application/json, text/javascript, */*; q=0.01",
}


def _strip_html(raw: str) -> str:
    text = html.unescape(_TAG_RE.sub(" ", raw or ""))
    return re.sub(r"\s+", " ", text).strip()


def _currency(text: str) -> str:
    match = _CURRENCY_RE.search(text)
    return match.group(1) if match else "USD"


def _parse_budget(budget: str) -> tuple[float | None, float | None, str | None]:
    """Workana budgets are localized strings, e.g.:
    'USD 500 - 1.000', 'Menos de USD 50', 'Mais de USD 3.000',
    'Menos de USD 15 / hora'. Dots are thousands separators.
    """
    if not budget:
        return None, None, None

    currency = _currency(budget)
    low = budget.lower()

    # Hourly rates aren't comparable to fixed-price thresholds — leave amounts empty.
    if "/" in budget or "hora" in low or "hour" in low:
        return None, None, currency

    nums = [float(n.replace(".", "")) for n in _NUM_RE.findall(budget)]
    if not nums:
        return None, None, currency
    if "menos" in low or "less" in low:
        return None, nums[0], currency
    if "mais" in low or "more" in low:
        return nums[0], None, currency
    if len(nums) >= 2:
        return nums[0], nums[1], currency
    return nums[0], None, currency


def _title(item: dict) -> str:
    raw = item.get("title", "")
    match = _TITLE_ATTR_RE.search(raw)
    if match:
        return html.unescape(match.group(1)).strip()
    return _strip_html(raw)


class WorkanaSource:
    async def fetch(self) -> list[RawJob]:
        items: list[dict] = []
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            for category in CATEGORIES:
                for page in range(1, MAX_PAGES + 1):
                    params = {"category": category, "language": "", "page": page}
                    resp = await client.get(WORKANA_URL, headers=_HEADERS, params=params)
                    resp.raise_for_status()
                    page_items = resp.json().get("results", {}).get("results", [])
                    if not page_items:
                        break
                    items.extend(page_items)

        return self._parse(items)

    @staticmethod
    def _parse(items: list[dict]) -> list[RawJob]:
        seen: set[str] = set()
        results: list[RawJob] = []
        for item in items:
            slug = item.get("slug")
            if not slug or slug in seen:
                continue

            title = _title(item)
            description = _strip_html(item.get("description", ""))
            haystack = f"{title} {description}".lower()
            if not any(kw in haystack for kw in KEYWORDS):
                continue

            budget_min, budget_max, currency = _parse_budget(item.get("budget", ""))
            seen.add(slug)
            results.append(RawJob(
                external_id=f"workana:{slug}",
                source="workana",
                title=title,
                description=description,
                budget_min=budget_min,
                budget_max=budget_max,
                budget_currency=currency,
                url=f"https://www.workana.com/job/{slug}",
                language="pt",
                raw_data=item,
            ))
        return results
