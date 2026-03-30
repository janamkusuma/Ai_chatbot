from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET: str
    GOOGLE_MAPS_API_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120

    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str
    FRONTEND_BASE_URL: str
    
    ADMIN_EMAIL: str = ""
    
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASS: str = ""
    SMTP_FROM: str = "HealthBot AI <no-reply@example.com>"

    RESET_OTP_EXPIRE_MINUTES: int = 10

    # ✅ OpenRouter
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_MODEL: str = "openai/gpt-4o-mini"
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"

    # ✅ uploads
    UPLOAD_DIR: str = "uploads"
    
    # ✅ Vector backend switch: "pinecone" OR "faiss"
    VECTOR_BACKEND: str = "pinecone"

    # ✅ Pinecone
    PINECONE_API_KEY: str = ""
    PINECONE_INDEX: str = "healthbot-rag-1024"
    PINECONE_EMBED_MODEL: str = "llama-text-embed-v2"

    DATA_DIR: str = "data/medical_pdfs"
    PINECONE_NAMESPACE: str = "global-medical"



    model_config = {"env_file": ".env", "extra": "allow"}

settings = Settings()
