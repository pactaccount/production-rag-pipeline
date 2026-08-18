from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    GEMINI_API_KEY: str
    COHERE_API_KEY: str
    LLAMA_CLOUD_API_KEY: str
    QDRANT_URL: str
    QDRANT_API_KEY: str
    PHOENIX_PORT: int = 6006

    class Config:
        env_file = ".env"

settings = Settings()
