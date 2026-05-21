from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openrouter_api_key: str


settings = Settings()