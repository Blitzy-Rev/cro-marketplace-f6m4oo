"""
Central configuration module for the Molecular Data Management and CRO Integration Platform.

This module loads environment variables, initializes application settings, and provides a 
unified configuration interface for the entire application. It implements a Singleton pattern
to ensure consistent configuration access across all components.
"""

import os  # standard library
import pathlib  # standard library
import logging  # standard library
import logging.config  # standard library
import typing  # standard library
import secrets  # standard library

import dotenv  # python-dotenv ^1.0.0
import pydantic  # pydantic ^2.0.0
from pydantic_settings import BaseSettings  # pydantic-settings ^2.0.0

from .constants import (
    PROJECT_NAME,
    VERSION,
    API_V1_STR,
    get_environment,
    is_development,
)

# Set up basic logging
logger = logging.getLogger(__name__)

# Base directory for the application
BASE_DIR = pathlib.Path(__file__).resolve().parent.parent.parent


def get_env_file_path() -> pathlib.Path:
    """
    Determine the appropriate .env file path based on the current environment.
    
    Returns:
        pathlib.Path: Path to the environment file
    """
    environment = get_environment()
    env_file = f".env.{environment}"
    return BASE_DIR / env_file


def load_environment_variables() -> None:
    """
    Load environment variables from the appropriate .env file.
    
    This function should be called early in the application startup process
    to ensure environment variables are available for configuration.
    """
    env_file_path = get_env_file_path()
    if env_file_path.exists():
        dotenv.load_dotenv(env_file_path)
        logger.info(f"Loaded environment variables from {env_file_path}")
    else:
        logger.warning(f"No environment file found at {env_file_path}")


class Singleton(type):
    """
    Metaclass that implements the Singleton pattern to ensure only one instance of a class exists.
    """
    _instances = {}
    
    def __call__(cls, *args, **kwargs):
        """
        Override the __call__ method to implement the Singleton pattern.
        
        Args:
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
            
        Returns:
            object: The single instance of the class
        """
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Settings(BaseSettings, metaclass=Singleton):
    """
    Application settings with validation using Pydantic BaseSettings.
    
    This class represents all configuration settings for the application,
    loaded from environment variables with appropriate validation and typing.
    """
    # Core settings
    ENV: str = "development"
    DEBUG: bool = False
    SECRET_KEY: str
    API_V1_STR: str = API_V1_STR
    PROJECT_NAME: str = PROJECT_NAME
    VERSION: str = VERSION
    
    # CORS settings
    BACKEND_CORS_ORIGINS: list[str] = []
    
    # Database settings
    DATABASE_URL: str
    DATABASE_MAX_CONNECTIONS: int = 20
    DATABASE_POOL_SIZE: int = 5
    DATABASE_POOL_OVERFLOW: int = 10
    
    # Redis settings
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # AWS settings
    S3_BUCKET_NAME: str
    AWS_REGION: str = "us-east-1" 
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    
    # External service integrations
    AI_ENGINE_API_URL: str
    AI_ENGINE_API_KEY: str
    DOCUSIGN_INTEGRATION_KEY: str
    DOCUSIGN_USER_ID: str
    DOCUSIGN_BASE_URL: str
    
    # Email settings
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAILS_FROM_EMAIL: str = ""
    EMAILS_FROM_NAME: str = ""
    
    # Security settings
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Monitoring and logging
    SENTRY_DSN: str = ""
    LOG_LEVEL: str = "INFO"
    
    # Pagination settings
    PAGINATION_DEFAULT_PAGE: int = 1
    PAGINATION_DEFAULT_PAGE_SIZE: int = 50
    PAGINATION_MAX_PAGE_SIZE: int = 100
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }

    @pydantic.field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """
        Validate that SECRET_KEY is set and has sufficient length.
        
        In development mode, generates a random key if none is provided.
        
        Args:
            v: The secret key value
            
        Returns:
            str: Validated secret key
        """
        if v == "" and is_development():
            # Generate a secure random key for development
            return secrets.token_urlsafe(32)
        
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        
        return v
    
    @pydantic.field_validator("BACKEND_CORS_ORIGINS")
    @classmethod
    def validate_cors_origins(cls, v: typing.Any) -> list[str]:
        """
        Parse and validate CORS origins from string to list.
        
        Args:
            v: The CORS origins value
            
        Returns:
            list: List of validated CORS origins
        """
        if isinstance(v, str) and not v.startswith("["):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    def get_database_connection_parameters(self) -> dict:
        """
        Get database connection parameters as a dictionary.
        
        Returns:
            dict: Database connection parameters
        """
        return {
            "max_connections": self.DATABASE_MAX_CONNECTIONS,
            "pool_size": self.DATABASE_POOL_SIZE,
            "pool_overflow": self.DATABASE_POOL_OVERFLOW,
        }
    
    def configure_logging(self) -> None:
        """
        Configure application logging based on settings.
        
        Sets up logging with appropriate level, format, and handlers.
        """
        log_level = getattr(logging, self.LOG_LEVEL.upper(), logging.INFO)
        
        logging_config = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                },
            },
            "handlers": {
                "console": {
                    "level": log_level,
                    "class": "logging.StreamHandler",
                    "formatter": "standard",
                },
            },
            "loggers": {
                "": {
                    "handlers": ["console"],
                    "level": log_level,
                },
            },
        }
        
        logging.config.dictConfig(logging_config)
        logger.info(f"Logging configured with level: {self.LOG_LEVEL}")


# Initialize settings as early as possible
load_environment_variables()
settings = Settings()