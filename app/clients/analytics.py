import httpx

from tenacity import retry
from tenacity import stop_after_attempt
from tenacity import wait_exponential


class AnalyticsClient:

    def __init__(self, base_url: str):
        self.client = httpx.AsyncClient(
            base_url=base_url,
            timeout=30,
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def query(self, endpoint: str, params: dict):
        response = await self.client.get(
            endpoint,
            params=params,
        )

        response.raise_for_status()

        return response.json()