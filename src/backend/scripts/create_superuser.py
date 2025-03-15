#!/usr/bin/env python3
"""
Creates a superuser account for the Molecular Data Management and CRO Integration Platform.

This script allows system administrators to create a superuser with full system privileges
during initial setup or for administrative purposes.

Usage:
    python create_superuser.py --email admin@example.com --full-name "Admin User" [--password "Password123!"]
    
If password is not provided, it will be prompted securely.
"""

import argparse  # standard library
import getpass  # standard library
import sys  # standard library
import logging  # standard library
import uuid  # standard library

# Internal imports
from ..app.db.session import db_session
from ..app.models.user import User
from ..app.schemas.user import UserCreate
from ..app.crud.crud_user import user
from ..app.constants.user_roles import SYSTEM_ADMIN
from ..app.core.security import validate_password

# Configure logger
logger = logging.getLogger(__name__)


def setup_argparse():
    """
    Set up command-line argument parser.
    
    Returns:
        argparse.ArgumentParser: Configured argument parser
    """
    parser = argparse.ArgumentParser(
        description="Create a superuser for the Molecular Data Management and CRO Integration Platform"
    )
    
    parser.add_argument(
        "--email", 
        required=True, 
        help="Email address for the superuser"
    )
    
    parser.add_argument(
        "--full-name", 
        required=True, 
        help="Full name of the superuser"
    )
    
    parser.add_argument(
        "--password", 
        required=False, 
        help="Password for the superuser (if not provided, will be prompted)"
    )
    
    return parser


def create_superuser(email: str, full_name: str, password: str) -> User:
    """
    Create a superuser with provided details.
    
    Args:
        email: Email address for the superuser
        full_name: Full name of the superuser
        password: Password for the superuser
        
    Returns:
        User: Created superuser instance
        
    Raises:
        ValueError: If user with email already exists or password is invalid
    """
    # Check if user with email already exists
    existing_user = user.get_by_email(email)
    if existing_user:
        raise ValueError(f"User with email {email} already exists")
    
    # Validate password complexity
    if not validate_password(password):
        raise ValueError(
            "Password must be at least 12 characters long and include "
            "uppercase, lowercase, number, and special characters"
        )
    
    # Create user data with UserCreate schema
    user_data = UserCreate(
        email=email,
        full_name=full_name,
        password=password,
        role=SYSTEM_ADMIN
    )
    
    # Create user with superuser privileges
    superuser = user.create(user_data)
    
    # Set superuser flag directly (not part of UserCreate schema)
    superuser.is_superuser = True
    db_session.add(superuser)
    db_session.commit()
    
    logger.info(f"Superuser {email} created successfully")
    return superuser


def main() -> int:
    """
    Main function to parse arguments and create superuser.
    
    Returns:
        int: Exit code (0 for success, 1 for error)
    """
    # Configure basic logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Parse command-line arguments
    parser = setup_argparse()
    args = parser.parse_args()
    
    # Extract email and full_name from arguments
    email = args.email
    full_name = args.full_name
    
    # Get password or prompt securely if not provided
    password = args.password
    if not password:
        password = getpass.getpass("Enter password for superuser: ")
        password_confirm = getpass.getpass("Confirm password: ")
        
        if password != password_confirm:
            logger.error("Passwords do not match")
            return 1
    
    try:
        # Create superuser
        superuser = create_superuser(email, full_name, password)
        logger.info(f"Superuser created: {superuser.email} (ID: {superuser.id})")
        return 0
    except ValueError as e:
        logger.error(f"Error creating superuser: {str(e)}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error creating superuser: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())