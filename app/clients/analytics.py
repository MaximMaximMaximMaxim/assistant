import httpx

from tenacity import retry
from tenacity import retry_if_exception
from tenacity import stop_after_attempt
from tenacity import wait_exponential


def _is_retryable_error(exc: BaseException) -> bool:
    if isinstance(exc, httpx.HTTPStatusError):
        status_code = exc.response.status_code
        return status_code == 429 or status_code >= 500
    return isinstance(exc, httpx.TransportError)


class AnalyticsClient:

    def __init__(self, base_url: str):
        self.client = httpx.AsyncClient(
            base_url=base_url,
            timeout=30,
        )

    @retry(
        retry=retry_if_exception(_is_retryable_error),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def query(self, endpoint: str, params: dict):
        response = await self.client.get(
            endpoint,
            params=params,
        )

        response.raise_for_status()

        return response.json()
