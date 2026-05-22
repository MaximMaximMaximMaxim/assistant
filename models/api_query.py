from pydantic import BaseModel, Field


class AnalyticsQuery(BaseModel):
    reasoning: str
    endpoint: str
    params: dict = Field(default_factory=dict)
