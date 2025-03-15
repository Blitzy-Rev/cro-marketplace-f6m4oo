"""
Package initialization file for the Molecular Data Management and CRO Integration Platform.

This module initializes the backend application package, sets up logging, and exposes
key components to be imported by other modules. It serves as the entry point for the
backend application and establishes the overall package structure.
"""

import logging  # standard library

from .core.logging import setup_logging
from .core.config import load_environment_variables, settings

# Set up a logger for this module
logger = logging.getLogger(__name__)

# Define package version
__version__ = "1.0.0"

def initialize_app():
    """
    Initialize the application by setting up logging and environment variables.
    
    This function should be called at application startup to ensure proper
    configuration before any other operations are performed. It loads environment
    variables and configures the logging system according to the application settings.
    """
    # Load environment variables from .env file
    load_environment_variables()
    
    # Configure application logging with the appropriate log level
    setup_logging(settings.LOG_LEVEL)
    
    # Log application initialization
    logger.info(f"Initializing {settings.PROJECT_NAME} v{__version__}")
    logger.info(f"Environment: {settings.ENV}")