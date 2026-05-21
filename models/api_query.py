from pydantic import BaseModel, Field


class AnalyticsQuery(BaseModel):
    endpoint: str
    params: dict = Field(default_factory=dict)
    reasoning: str
