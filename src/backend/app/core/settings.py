"""
Settings module for the Molecular Data Management and CRO Integration Platform.

This module defines application settings using Pydantic's BaseSettings for environment
variable loading, validation, and type conversion. It provides a centralized configuration
interface that is used throughout the application.
"""

import os
import secrets
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse

from pydantic import (  # pydantic version: ^2.0.0
    BaseSettings,
    Field,
    validator,
    SecretStr,
)
from dotenv import load_dotenv  # python-dotenv version: ^1.0.0

from .constants import (
    PROJECT_NAME,
    VERSION,
    API_V1_STR,
    get_environment,
    is_development,
)

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables from .env file if it exists
env_path = Path(".") / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
    logger.info(f"Loaded environment variables from {env_path}")


class Settings(BaseSettings):
    """
    Application settings with environment variable loading and validation using Pydantic BaseSettings.
    
    This class defines all configuration settings for the application and provides methods
    to access grouped settings for specific components.
    """
    
    # Environment
    ENV: str = Field(default_factory=get_environment)
    DEBUG: bool = Field(default=False)
    
    # API
    API_V1_STR: str = Field(default=API_V1_STR)
    PROJECT_NAME: str = Field(default=PROJECT_NAME)
    VERSION: str = Field(default=VERSION)
    
    # Security
    SECRET_KEY: SecretStr = Field(default="")
    BACKEND_CORS_ORIGINS: List[str] = Field(default=["http://localhost:3000", "https://localhost:3000"])
    
    # Database
    DATABASE_URL: str = Field(default="postgresql://postgres:postgres@localhost:5432/molecule_db")
    DATABASE_MAX_CONNECTIONS: int = Field(default=20)
    DATABASE_POOL_SIZE: int = Field(default=5)
    DATABASE_POOL_OVERFLOW: int = Field(default=10)
    
    # Redis
    REDIS_URL: str = Field(default="redis://localhost:6379/0")
    
    # AWS/S3
    S3_BUCKET_NAME: str = Field(default="moleculeflow-data")
    AWS_REGION: str = Field(default="us-east-1")
    AWS_ACCESS_KEY_ID: SecretStr = Field(default="")
    AWS_SECRET_ACCESS_KEY: SecretStr = Field(default="")
    
    # AI Engine Integration
    AI_ENGINE_API_URL: str = Field(default="https://ai-prediction-engine.example.com/v1")
    AI_ENGINE_API_KEY: SecretStr = Field(default="")
    
    # DocuSign Integration
    DOCUSIGN_INTEGRATION_KEY: str = Field(default="")
    DOCUSIGN_USER_ID: str = Field(default="")
    DOCUSIGN_BASE_URL: str = Field(default="https://demo.docusign.net/restapi")
    
    # Email
    SMTP_HOST: str = Field(default="smtp.example.com")
    SMTP_PORT: int = Field(default=587)
    SMTP_USER: str = Field(default="")
    SMTP_PASSWORD: SecretStr = Field(default="")
    EMAILS_FROM_EMAIL: str = Field(default="noreply@moleculeflow.com")
    EMAILS_FROM_NAME: str = Field(default=PROJECT_NAME)
    
    # Authentication
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7)
    
    # Monitoring
    SENTRY_DSN: str = Field(default="")
    LOG_LEVEL: str = Field(default="INFO")
    
    # Pagination
    PAGINATION_DEFAULT_PAGE: int = Field(default=1)
    PAGINATION_DEFAULT_PAGE_SIZE: int = Field(default=50)
    PAGINATION_MAX_PAGE_SIZE: int = Field(default=100)

    @classmethod
    def model_config(cls) -> Dict[str, Any]:
        """
        Pydantic model configuration for environment variable loading.
        
        Returns:
            Dict[str, Any]: Configuration dictionary
        """
        return {
            "env_prefix": "",  # No prefix for environment variables
            "case_sensitive": True,  # Case sensitive environment variables
            "extra": "ignore",  # Ignore extra fields
        }

    @validator("SECRET_KEY")
    def validate_secret_key(cls, v: SecretStr) -> SecretStr:
        """
        Validate that SECRET_KEY is set and has sufficient length.
        
        Args:
            v (SecretStr): Secret key value
            
        Returns:
            SecretStr: Validated secret key
        """
        secret_key = v.get_secret_value() if v else ""
        
        if not secret_key and is_development():
            # Generate a random secret key for development
            secret_key = secrets.token_urlsafe(32)
            logger.warning("Generated random SECRET_KEY for development environment")
            return SecretStr(secret_key)
        
        if not secret_key:
            raise ValueError("SECRET_KEY must be set in production environments")
        
        if len(secret_key) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
            
        return v

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def validate_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        """
        Parse and validate CORS origins from string to list.
        
        Args:
            v (Union[str, List[str]]): CORS origins as string or list
            
        Returns:
            List[str]: List of validated CORS origins
        """
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    def get_database_connection_parameters(self) -> Dict[str, Any]:
        """
        Get database connection parameters as a dictionary.
        
        Returns:
            Dict[str, Any]: Database connection parameters
        """
        return {
            "url": self.DATABASE_URL,
            "max_connections": self.DATABASE_MAX_CONNECTIONS,
            "pool_size": self.DATABASE_POOL_SIZE,
            "max_overflow": self.DATABASE_POOL_OVERFLOW,
        }

    def get_redis_connection_parameters(self) -> Dict[str, Any]:
        """
        Get Redis connection parameters as a dictionary.
        
        Returns:
            Dict[str, Any]: Redis connection parameters
        """
        url = urlparse(self.REDIS_URL)
        
        # Parse password from URL if present
        password = None
        if url.password:
            password = url.password
            
        # Get database number from path
        db = 0
        if url.path and len(url.path) > 1:
            db = int(url.path.replace("/", ""))
        
        return {
            "host": url.hostname or "localhost",
            "port": url.port or 6379,
            "password": password,
            "db": db,
            "ssl": url.scheme == "rediss",
        }

    def get_aws_credentials(self) -> Dict[str, Any]:
        """
        Get AWS credentials as a dictionary.
        
        Returns:
            Dict[str, Any]: AWS credentials
        """
        return {
            "region": self.AWS_REGION,
            "access_key_id": self.AWS_ACCESS_KEY_ID.get_secret_value() if self.AWS_ACCESS_KEY_ID else None,
            "secret_access_key": self.AWS_SECRET_ACCESS_KEY.get_secret_value() if self.AWS_SECRET_ACCESS_KEY else None,
            "s3_bucket_name": self.S3_BUCKET_NAME,
        }

    def get_ai_engine_credentials(self) -> Dict[str, Any]:
        """
        Get AI Engine API credentials as a dictionary.
        
        Returns:
            Dict[str, Any]: AI Engine API credentials
        """
        return {
            "api_url": self.AI_ENGINE_API_URL,
            "api_key": self.AI_ENGINE_API_KEY.get_secret_value() if self.AI_ENGINE_API_KEY else None,
        }

    def get_docusign_credentials(self) -> Dict[str, Any]:
        """
        Get DocuSign credentials as a dictionary.
        
        Returns:
            Dict[str, Any]: DocuSign credentials
        """
        return {
            "integration_key": self.DOCUSIGN_INTEGRATION_KEY,
            "user_id": self.DOCUSIGN_USER_ID,
            "base_url": self.DOCUSIGN_BASE_URL,
        }

    def get_email_settings(self) -> Dict[str, Any]:
        """
        Get email settings as a dictionary.
        
        Returns:
            Dict[str, Any]: Email settings
        """
        return {
            "smtp_host": self.SMTP_HOST,
            "smtp_port": self.SMTP_PORT,
            "smtp_user": self.SMTP_USER,
            "smtp_password": self.SMTP_PASSWORD.get_secret_value() if self.SMTP_PASSWORD else None,
            "from_email": self.EMAILS_FROM_EMAIL,
            "from_name": self.EMAILS_FROM_NAME,
        }


# Create a settings instance to be imported by other modules
settings = Settings()