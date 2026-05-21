from pydantic import BaseModel


class AnalyticsQuery(BaseModel):
    endpoint: str
    params: dict
    reasoning: str