from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = 'gpt-4-0613'  # change as needed
    MONGO_URI: str | None = None
    DATABASE_NAME: str = 'accessibility_insights'
    REPORTS_COLLECTION: str = "ai_reports"
    SERVER_HOST: str = '0.0.0.0'
    SERVER_PORT: int = 8000

    model_config = SettingsConfigDict(env_file='.env')

settings = Settings()