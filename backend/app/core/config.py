from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "CargoPulse AI"
    APP_VERSION: str ="0.1.0"
    DEBUG: bool = True
    API_PREFIX: str = "/api"

settings = Settings()

# Later this will contain things like:

# DATABASE_URL
# JWT_SECRET
# OPENAI_API_KEY
# HF_TOKEN
# MLFLOW_TRACKING_URI