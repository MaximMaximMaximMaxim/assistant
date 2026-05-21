from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openrouter_api_key: str
    analytics_base_url: str = "https://api.ustyantsevmd.ru"


settings = Settings()