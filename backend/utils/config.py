from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    APP_NAME: str = "NutriPlan AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Supabase
    SUPABASE_URL: str
    SUPABASE_SERVICE_ROLE_KEY: str
    SUPABASE_JWT_SECRET: str
    SUPABASE_STORAGE_BUCKET: str = "patient-documents"

    # Database (Supabase PostgreSQL direct connection)
    DATABASE_URL: str

    # Redis / Celery
    REDIS_URL: str = "redis://redis:6379/0"

    # OpenAI
    OPENAI_API_KEY: str = ""

    # Mistral
    MISTRAL_API_KEY: str = ""

    # Pinecone
    PINECONE_API_KEY: str = ""
    PINECONE_INDEX_NAME: str = "nutriplan-patients"
    VECTOR_BACKEND: str = "pgvector"  # "pinecone" | "pgvector"

    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 60


settings = Settings()
