from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    USER_AGENT: str
    GOOGLE_SEARCH_URL: str
    MAX_RESULTS: int

    class Config:
        env_file = ".env"

settings = Settings()
