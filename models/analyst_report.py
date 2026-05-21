from pydantic import BaseModel


class AnalystReport(BaseModel):
    is_complete: bool
    missing_info: list[str]
    analysis: str
