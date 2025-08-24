"""
Application configuration
"""
import os
from typing import List
from pydantic import BaseSettings

class Settings(BaseSettings):
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # Project
    PROJECT_ID: str = "california-motion-writer"
    REGION: str = "us-central1"
    
    # Database
    DB_HOST: str = os.getenv("DB_HOST", "/cloudsql/california-motion-writer:us-central1:app-sql")
    DB_NAME: str = os.getenv("DB_NAME", "appdb")
    DB_USER: str = os.getenv("DB_USER", "appuser")
    DB_PASSWORD_SECRET: str = os.getenv("DB_PASSWORD_SECRET", "motion-db-password")
    
    # API Settings
    API_V1_PREFIX: str = "/api/v1"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "development-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "https://motion-api-mlcaanldqq-uc.a.run.app"
    ]
    
    # Pub/Sub
    PUBSUB_TOPIC: str = os.getenv("PUBSUB_TOPIC", "app-events")
    
    # Storage
    GCS_BUCKET: str = "california-motion-writer-documents"
    
    # Vertex AI
    VERTEX_AI_LOCATION: str = "us-central1"
    VERTEX_AI_MODEL: str = "gemini-1.5-flash"
    
    # Vector Search
    INDEX_ID: str = "8771272646722584576"
    INDEX_ENDPOINT_ID: str = "1505347966657888256"
    
    class Config:
        case_sensitive = True

settings = Settings()