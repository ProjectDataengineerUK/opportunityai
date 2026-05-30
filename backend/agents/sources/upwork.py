import httpx
from models import RawJob

# Upwork só expõe dados via API GraphQL oficial, que exige OAuth2 (Bearer token).
# Sem token a fonte é inerte (retorna []), espelhando o comportamento do Freelancer.
UPWORK_GRAPHQL = "https://api.upwork.com/graphql"
SEARCH_EXPRESSION = (
    'python OR "machine learning" OR "artificial intelligence" '
    'OR "data engineering" OR automation OR LLM OR backend'
)

QUERY = """
query marketplaceJobPostingsSearch($filter: MarketplaceJobPostingsSearchFilter, $sort: [MarketplaceJobPostingSearchSortAttribute]) {
  marketplaceJobPostingsSearch(
    marketPlaceJobFilter: $filter
    searchType: USER_JOBS_SEARCH
    sortAttributes: $sort
  ) {
    totalCount
    edges {
      node {
        id
        title
        description
        ciphertext
        createdDateTime
        totalApplicants
        amount { rawValue currency }
        hourlyBudgetMin { rawValue currency }
        hourlyBudgetMax { rawValue currency }
        skills { name }
        client {
          totalSpent { rawValue }
          totalHires
          verificationStatus
        }
      }
    }
  }
}
"""


def _to_float(value) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


class UpworkSource:
    def __init__(self, token: str, org_id: str = ""):
        self.token = token
        self.org_id = org_id

    async def fetch(self) -> list[RawJob]:
        if not self.token:
            return []

        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        if self.org_id:
            headers["X-Upwork-API-TenantId"] = self.org_id

        payload = {
            "query": QUERY,
            "variables": {
                "filter": {
                    "searchExpression_eq": SEARCH_EXPRESSION,
                    "pagination_eq": {"after": "0", "first": 50},
                },
                "sort": [{"field": "RECENCY", "order": "DESC"}],
            },
        }

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(UPWORK_GRAPHQL, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        edges = (
            data.get("data", {})
            .get("marketplaceJobPostingsSearch", {})
            .get("edges", [])
        )
        return [self._parse_node(edge.get("node", {})) for edge in edges if edge.get("node")]

    @staticmethod
    def _parse_node(node: dict) -> RawJob:
        amount = node.get("amount") or {}
        hourly_min = node.get("hourlyBudgetMin") or {}
        hourly_max = node.get("hourlyBudgetMax") or {}

        fixed = _to_float(amount.get("rawValue"))
        if fixed:
            budget_min, budget_max = fixed, None
            currency = amount.get("currency") or "USD"
        else:
            budget_min = _to_float(hourly_min.get("rawValue"))
            budget_max = _to_float(hourly_max.get("rawValue"))
            currency = hourly_min.get("currency") or hourly_max.get("currency") or "USD"

        cipher = node.get("ciphertext") or node.get("id") or ""
        return RawJob(
            external_id=f"upwork:{node.get('id', cipher)}",
            source="upwork",
            title=node.get("title", ""),
            description=node.get("description", ""),
            budget_min=budget_min,
            budget_max=budget_max,
            budget_currency=currency,
            url=f"https://www.upwork.com/jobs/{cipher}",
            language="en",
            raw_data=node,
        )
