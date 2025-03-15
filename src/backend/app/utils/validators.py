"""
Validators Module

This module provides utility functions for data validation across the Molecular Data Management 
and CRO Integration Platform. It includes validators for various data types, formats, and
domain-specific validations for molecules, properties, and other entities.
"""

import re
import uuid
import datetime
from email_validator import validate_email as email_validator_func, EmailNotValidError
from typing import Any, Dict, List, Optional, Union

from ..constants.molecule_properties import PROPERTY_RANGES, STANDARD_PROPERTIES, PropertyType
from ..constants.error_messages import VALIDATION_ERRORS
from ..core.exceptions import ValidationException
from .smiles import validate_smiles

# Regular expression patterns
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
UUID_REGEX = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")


def validate_required(value: Any, field_name: str, raise_exception: bool = True) -> bool:
    """
    Validates that a required field has a value.
    
    Args:
        value: The value to validate
        field_name: Name of the field being validated (for error messages)
        raise_exception: Whether to raise an exception if validation fails
        
    Returns:
        True if validation passes, False otherwise
        
    Raises:
        ValidationException: If validation fails and raise_exception is True
    """
    if value is None or (isinstance(value, str) and value.strip() == ""):
        if raise_exception:
            raise ValidationException(
                message=VALIDATION_ERRORS["REQUIRED_FIELD"],
                validation_errors=[{
                    "field": field_name,
                    "message": VALIDATION_ERRORS["REQUIRED_FIELD"]
                }]
            )
        return False
    return True


def validate_string(
    value: str,
    field_name: str,
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
    pattern: Optional[str] = None,
    raise_exception: bool = True
) -> bool:
    """
    Validates string format and length constraints.
    
    Args:
        value: The string to validate
        field_name: Name of the field being validated (for error messages)
        min_length: Minimum allowed length
        max_length: Maximum allowed length
        pattern: Regular expression pattern to match
        raise_exception: Whether to raise an exception if validation fails
        
    Returns:
        True if validation passes, False otherwise
        
    Raises:
        ValidationException: If validation fails and raise_exception is True
    """
    # Check if value is None (if required, should be caught by validate_required)
    if value is None:
        if raise_exception:
            raise ValidationException(
                message=VALIDATION_ERRORS["INVALID_FORMAT"],
                validation_errors=[{
                    "field": field_name,
                    "message": "Value must be a string"
                }]
            )
        return False
    
    # Check if value is a string
    if not isinstance(value, str):
        if raise_exception:
            raise ValidationException(
                message=VALIDATION_ERRORS["INVALID_FORMAT"],
                validation_errors=[{
                    "field": field_name,
                    "message": "Value must be a string"
                }]
            )
        return False
    
    # Check minimum length
    if min_length is not None and len(value) < min_length:
        if raise_exception:
            raise ValidationException(
                message=VALIDATION_ERRORS["VALUE_TOO_SHORT"],
                validation_errors=[{
                    "field": field_name,
                    "message": f"Value must be at least {min_length} characters"
                }]
            )
        return False
    
    # Check maximum length
    if max_length is not None and len(value) > max_length:
        if raise_exception:
            raise ValidationException(
                message=VALIDATION_ERRORS["VALUE_TOO_LONG"],
                validation_errors=[{
                    "field": field_name,
                    "message": f"Value must be at most {max_length} characters"
                }]
            )
        return False
    
    # Check pattern if provided
    if pattern is not None:
        if not re.match(pattern, value):
            if raise_exception:
                raise ValidationException(
                    message=VALIDATION_ERRORS["INVALID_FORMAT"],
                    validation_errors=[{
                        "field": field_name,
                        "message": "Value does not match the required format"
                    }]
                )
            return False
    
    return True


def validate_numeric(
    value: Union[int, float],
    field_name: str,
    min_value: Optional[Union[int, float]] = None,
    max_value: Optional[Union[int, float]] = None,
    raise_exception: bool = True
) -> bool:
    """
    Validates numeric value constraints.
    
    Args:
        value: The numeric value to validate
        field_name: Name of the field being validated (for error messages)
        min_value: Minimum allowed value
        max_value: Maximum allowed value
        raise_exception: Whether to raise an exception if validation fails
        
    Returns:
        True if validation passes, False otherwise
        
    Raises:
        ValidationException: If validation fails and raise_exception is True
    """
    # Check if value is None (if required, should be caught by validate_required)
    if value is None:
        if raise_exception:
            raise ValidationException(
                message=VALIDATION_ERRORS["INVALID_FORMAT"],
                validation_errors=[{
                    "field": field_name,
                    "message": "Value must be a number"
                }]
            )
        return False
    
    # Check if value is a number
    if not isinstance(value, (int, float)):
        if raise_exception:
            raise ValidationException(
                message=VALIDATION_ERRORS["INVALID_FORMAT"],
                validation_errors=[{
                    "field": field_name,
                    "message": "Value must be a number"
                }]
            )
        return False
    
    # Check minimum value
    if min_value is not None and value < min_value:
        if raise_exception:
            raise ValidationException(
                message=VALIDATION_ERRORS["VALUE_OUT_OF_RANGE"],
                validation_errors=[{
                    "field": field_name,
                    "message": f"Value must be at least {min_value}"
                }]
            )
        return False
    
    # Check maximum value
    if max_value is not None and value > max_value:
        if raise_exception:
            raise ValidationException(
                message=VALIDATION_ERRORS["VALUE_OUT_OF_RANGE"],
                validation_errors=[{
                    "field": field_name,
                    "message": f"Value must be at most {max_value}"
                }]
            )
        return False
    
    return True


def validate_email(
    value: str,
    field_name: str,
    raise_exception: bool = True
) -> bool:
    """
    Validates email address format.
    
    Args:
        value: The email address to validate
        field_name: Name of the field being validated (for error messages)
        raise_exception: Whether to raise an exception if validation fails
        
    Returns:
        True if validation passes, False otherwise
        
    Raises:
        ValidationException: If validation fails and raise_exception is True
    """
    # Check if value is None (if required, should be caught by validate_required)
    if value is None:
        if raise_exception:
            raise ValidationException(
                message=VALIDATION_ERRORS["INVALID_EMAIL"],
                validation_errors=[{
                    "field": field_name,
                    "message": "Email address is required"
                }]
            )
        return False
    
    # Check if value is a string
    if not isinstance(value, str):
        if raise_exception:
            raise ValidationException(
                message=VALIDATION_ERRORS["INVALID_EMAIL"],
                validation_errors=[{
                    "field": field_name,
                    "message": "Email address must be a string"
                }]
            )
        return False
    
    # Validate email format using email_validator library
    try:
        email_validator_func(value)
        return True
    except EmailNotValidError:
        if raise_exception:
            raise ValidationException(
                message=VALIDATION_ERRORS["INVALID_EMAIL"],
                validation_errors=[{
                    "field": field_name,
                    "message": "Invalid email address format"
                }]
            )
        return False


def validate_uuid(
    value: str,
    field_name: str,
    raise_exception: bool = True
) -> bool:
    """
    Validates UUID format.
    
    Args:
        value: The UUID string to validate
        field_name: Name of the field being validated (for error messages)
        raise_exception: Whether to raise an exception if validation fails
        
    Returns:
        True if validation passes, False otherwise
        
    Raises:
        ValidationException: If validation fails and raise_exception is True
    """
    # Check if value is None (if required, should be caught by validate_required)
    if value is None:
        if raise_exception:
            raise ValidationException(
                message=VALIDATION_ERRORS["INVALID_UUID"],
                validation_errors=[{
                    "field": field_name,
                    "message": "UUID is required"
                }]
            )
        return False
    
    # Check if value is a string
    if not isinstance(value, str):
        if raise_exception:
            raise ValidationException(
                message=VALIDATION_ERRORS["INVALID_UUID"],
                validation_errors=[{
                    "field": field_name,
                    "message": "UUID must be a string"
                }]
            )
        return False
    
    # Try to parse as UUID
    try:
        uuid.UUID(value)
        return True
    except ValueError:
        if raise_exception:
            raise ValidationException(
                message=VALIDATION_ERRORS["INVALID_UUID"],
                validation_errors=[{
                    "field": field_name,
                    "message": "Invalid UUID format"
                }]
            )
        return False


def validate_date(
    value: Union[str, datetime.date, datetime.datetime],
    field_name: str,
    format_str: Optional[str] = "%Y-%m-%d",
    min_date: Optional[datetime.date] = None,
    max_date: Optional[datetime.date] = None,
    raise_exception: bool = True
) -> bool:
    """
    Validates date format and constraints.
    
    Args:
        value: The date to validate (string, date, or datetime)
        field_name: Name of the field being validated (for error messages)
        format_str: Date format string for parsing string dates
        min_date: Minimum allowed date
        max_date: Maximum allowed date
        raise_exception: Whether to raise an exception if validation fails
        
    Returns:
        True if validation passes, False otherwise
        
    Raises:
        ValidationException: If validation fails and raise_exception is True
    """
    # Check if value is None (if required, should be caught by validate_required)
    if value is None:
        if raise_exception:
            raise ValidationException(
                message=VALIDATION_ERRORS["INVALID_DATE"],
                validation_errors=[{
                    "field": field_name,
                    "message": "Date is required"
                }]
            )
        return False
    
    # Parse date if string is provided
    date_value = None
    if isinstance(value, str):
        try:
            date_value = datetime.datetime.strptime(value, format_str).date()
        except ValueError:
            if raise_exception:
                raise ValidationException(
                    message=VALIDATION_ERRORS["INVALID_DATE"],
                    validation_errors=[{
                        "field": field_name,
                        "message": f"Invalid date format, expected: {format_str}"
                    }]
                )
            return False
    elif isinstance(value, datetime.datetime):
        date_value = value.date()
    elif isinstance(value, datetime.date):
        date_value = value
    else:
        if raise_exception:
            raise ValidationException(
                message=VALIDATION_ERRORS["INVALID_DATE"],
                validation_errors=[{
                    "field": field_name,
                    "message": "Value must be a date, datetime, or properly formatted string"
                }]
            )
        return False
    
    # Check minimum date
    if min_date is not None and date_value < min_date:
        if raise_exception:
            raise ValidationException(
                message=VALIDATION_ERRORS["PAST_DATE_REQUIRED"],
                validation_errors=[{
                    "field": field_name,
                    "message": f"Date must be on or after {min_date.isoformat()}"
                }]
            )
        return False
    
    # Check maximum date
    if max_date is not None and date_value > max_date:
        if raise_exception:
            raise ValidationException(
                message=VALIDATION_ERRORS["FUTURE_DATE_REQUIRED"],
                validation_errors=[{
                    "field": field_name,
                    "message": f"Date must be on or before {max_date.isoformat()}"
                }]
            )
        return False
    
    return True


def validate_property_value(
    value: Any,
    property_name: str,
    property_type: PropertyType,
    raise_exception: bool = True
) -> bool:
    """
    Validates a molecular property value based on its type and constraints.
    
    Args:
        value: The property value to validate
        property_name: Name of the property
        property_type: Type of the property (from PropertyType enum)
        raise_exception: Whether to raise an exception if validation fails
        
    Returns:
        True if validation passes, False otherwise
        
    Raises:
        ValidationException: If validation fails and raise_exception is True
    """
    # Skip validation if value is None (required check should be handled elsewhere)
    if value is None:
        return True
    
    # Get property constraints if available
    property_range = None
    if property_name in PROPERTY_RANGES:
        property_range = PROPERTY_RANGES[property_name]
    
    if property_type == PropertyType.STRING:
        # String validation
        if not isinstance(value, str):
            if raise_exception:
                raise ValidationException(
                    message=VALIDATION_ERRORS["INVALID_FORMAT"],
                    validation_errors=[{
                        "field": property_name,
                        "message": "Property value must be a string"
                    }]
                )
            return False
        
        # Check if this is a SMILES property that needs special validation
        if property_name == "smiles":
            if not validate_smiles(value):
                if raise_exception:
                    raise ValidationException(
                        message=VALIDATION_ERRORS["INVALID_FORMAT"],
                        validation_errors=[{
                            "field": property_name,
                            "message": "Invalid SMILES string"
                        }]
                    )
                return False
            
        return True
    
    elif property_type == PropertyType.NUMERIC:
        # Numeric validation
        if not isinstance(value, (int, float)):
            if raise_exception:
                raise ValidationException(
                    message=VALIDATION_ERRORS["INVALID_FORMAT"],
                    validation_errors=[{
                        "field": property_name,
                        "message": "Property value must be a number"
                    }]
                )
            return False
        
        # Check range if available
        if property_range:
            min_value = property_range.get("min")
            max_value = property_range.get("max")
            
            if min_value is not None and value < min_value:
                if raise_exception:
                    raise ValidationException(
                        message=VALIDATION_ERRORS["VALUE_OUT_OF_RANGE"],
                        validation_errors=[{
                            "field": property_name,
                            "message": f"Value must be at least {min_value}"
                        }]
                    )
                return False
            
            if max_value is not None and value > max_value:
                if raise_exception:
                    raise ValidationException(
                        message=VALIDATION_ERRORS["VALUE_OUT_OF_RANGE"],
                        validation_errors=[{
                            "field": property_name,
                            "message": f"Value must be at most {max_value}"
                        }]
                    )
                return False
        
        return True
    
    elif property_type == PropertyType.INTEGER:
        # Integer validation
        if not isinstance(value, int):
            if raise_exception:
                raise ValidationException(
                    message=VALIDATION_ERRORS["INVALID_FORMAT"],
                    validation_errors=[{
                        "field": property_name,
                        "message": "Property value must be an integer"
                    }]
                )
            return False
        
        # Check range if available
        if property_range:
            min_value = property_range.get("min")
            max_value = property_range.get("max")
            
            if min_value is not None and value < min_value:
                if raise_exception:
                    raise ValidationException(
                        message=VALIDATION_ERRORS["VALUE_OUT_OF_RANGE"],
                        validation_errors=[{
                            "field": property_name,
                            "message": f"Value must be at least {min_value}"
                        }]
                    )
                return False
            
            if max_value is not None and value > max_value:
                if raise_exception:
                    raise ValidationException(
                        message=VALIDATION_ERRORS["VALUE_OUT_OF_RANGE"],
                        validation_errors=[{
                            "field": property_name,
                            "message": f"Value must be at most {max_value}"
                        }]
                    )
                return False
        
        return True
    
    elif property_type == PropertyType.BOOLEAN:
        # Boolean validation
        if not isinstance(value, bool):
            if raise_exception:
                raise ValidationException(
                    message=VALIDATION_ERRORS["INVALID_FORMAT"],
                    validation_errors=[{
                        "field": property_name,
                        "message": "Property value must be a boolean"
                    }]
                )
            return False
        
        return True
    
    # If property type is not recognized
    if raise_exception:
        raise ValidationException(
            message=VALIDATION_ERRORS["INVALID_PROPERTY_TYPE"],
            validation_errors=[{
                "field": property_name,
                "message": f"Unsupported property type: {property_type}"
            }]
        )
    return False


def validate_molecule_properties(
    properties: Dict[str, Any],
    raise_exception: bool = True
) -> bool:
    """
    Validates a dictionary of molecular properties.
    
    Args:
        properties: Dictionary of property name -> value pairs
        raise_exception: Whether to raise an exception if validation fails
        
    Returns:
        True if validation passes, False otherwise
        
    Raises:
        ValidationException: If validation fails and raise_exception is True
    """
    if not properties:
        if raise_exception:
            raise ValidationException(
                message="No properties provided",
                validation_errors=[{
                    "field": "properties",
                    "message": "At least one property must be provided"
                }]
            )
        return False
    
    validation_errors = []
    
    # Validate each property
    for prop_name, prop_value in properties.items():
        # Skip validation if property value is None
        if prop_value is None:
            continue
        
        # Get property definition if it's a standard property
        property_def = STANDARD_PROPERTIES.get(prop_name)
        
        if property_def:
            property_type = property_def["property_type"]
            
            try:
                if not validate_property_value(prop_value, prop_name, property_type, raise_exception=False):
                    validation_errors.append({
                        "field": prop_name,
                        "message": f"Invalid value for property {prop_name}"
                    })
            except Exception as e:
                validation_errors.append({
                    "field": prop_name,
                    "message": str(e)
                })
    
    if validation_errors and raise_exception:
        raise ValidationException(
            message="Invalid property values",
            validation_errors=validation_errors
        )
    
    return len(validation_errors) == 0


def validate_csv_column_mapping(
    column_mapping: Dict[str, str],
    raise_exception: bool = True
) -> bool:
    """
    Validates CSV column mapping configuration.
    
    Args:
        column_mapping: Dictionary mapping CSV columns to property names
        raise_exception: Whether to raise an exception if validation fails
        
    Returns:
        True if validation passes, False otherwise
        
    Raises:
        ValidationException: If validation fails and raise_exception is True
    """
    if not column_mapping:
        if raise_exception:
            raise ValidationException(
                message="Column mapping is required",
                validation_errors=[{
                    "field": "column_mapping",
                    "message": "At least one column must be mapped"
                }]
            )
        return False
    
    validation_errors = []
    
    # Check for required SMILES mapping
    if "smiles" not in column_mapping.values():
        validation_errors.append({
            "field": "column_mapping",
            "message": "SMILES column mapping is required"
        })
    
    # Validate that all mapped properties exist in standard properties
    for csv_col, prop_name in column_mapping.items():
        if prop_name not in STANDARD_PROPERTIES and not prop_name.startswith("custom_"):
            validation_errors.append({
                "field": "column_mapping",
                "message": f"Unknown property: {prop_name}"
            })
    
    if validation_errors and raise_exception:
        raise ValidationException(
            message="Invalid column mapping",
            validation_errors=validation_errors
        )
    
    return len(validation_errors) == 0


def validate_smiles_string(
    smiles: str,
    raise_exception: bool = True
) -> bool:
    """
    Validates a SMILES string using the smiles module.
    
    Args:
        smiles: SMILES string to validate
        raise_exception: Whether to raise an exception if validation fails
        
    Returns:
        True if validation passes, False otherwise
        
    Raises:
        ValidationException: If validation fails and raise_exception is True
    """
    if not validate_smiles(smiles):
        if raise_exception:
            raise ValidationException(
                message=VALIDATION_ERRORS["INVALID_FORMAT"],
                validation_errors=[{
                    "field": "smiles",
                    "message": "Invalid SMILES string"
                }]
            )
        return False
    return True


def validate_list(
    value: List[Any],
    field_name: str,
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
    raise_exception: bool = True
) -> bool:
    """
    Validates a list with optional length constraints.
    
    Args:
        value: The list to validate
        field_name: Name of the field being validated (for error messages)
        min_length: Minimum allowed length
        max_length: Maximum allowed length
        raise_exception: Whether to raise an exception if validation fails
        
    Returns:
        True if validation passes, False otherwise
        
    Raises:
        ValidationException: If validation fails and raise_exception is True
    """
    # Check if value is None (if required, should be caught by validate_required)
    if value is None:
        if raise_exception:
            raise ValidationException(
                message=VALIDATION_ERRORS["INVALID_FORMAT"],
                validation_errors=[{
                    "field": field_name,
                    "message": "Value must be a list"
                }]
            )
        return False
    
    # Check if value is a list
    if not isinstance(value, list):
        if raise_exception:
            raise ValidationException(
                message=VALIDATION_ERRORS["INVALID_FORMAT"],
                validation_errors=[{
                    "field": field_name,
                    "message": "Value must be a list"
                }]
            )
        return False
    
    # Check minimum length
    if min_length is not None and len(value) < min_length:
        if raise_exception:
            raise ValidationException(
                message=VALIDATION_ERRORS["VALUE_TOO_SHORT"],
                validation_errors=[{
                    "field": field_name,
                    "message": f"List must contain at least {min_length} item(s)"
                }]
            )
        return False
    
    # Check maximum length
    if max_length is not None and len(value) > max_length:
        if raise_exception:
            raise ValidationException(
                message=VALIDATION_ERRORS["VALUE_TOO_LONG"],
                validation_errors=[{
                    "field": field_name,
                    "message": f"List must contain at most {max_length} item(s)"
                }]
            )
        return False
    
    return True


def validate_dict(
    value: Dict[Any, Any],
    field_name: str,
    required_keys: Optional[List[str]] = None,
    allowed_keys: Optional[List[str]] = None,
    raise_exception: bool = True
) -> bool:
    """
    Validates a dictionary with optional key constraints.
    
    Args:
        value: The dictionary to validate
        field_name: Name of the field being validated (for error messages)
        required_keys: List of keys that must be present
        allowed_keys: List of allowed keys (if provided, other keys are not allowed)
        raise_exception: Whether to raise an exception if validation fails
        
    Returns:
        True if validation passes, False otherwise
        
    Raises:
        ValidationException: If validation fails and raise_exception is True
    """
    # Check if value is None (if required, should be caught by validate_required)
    if value is None:
        if raise_exception:
            raise ValidationException(
                message=VALIDATION_ERRORS["INVALID_FORMAT"],
                validation_errors=[{
                    "field": field_name,
                    "message": "Value must be a dictionary"
                }]
            )
        return False
    
    # Check if value is a dictionary
    if not isinstance(value, dict):
        if raise_exception:
            raise ValidationException(
                message=VALIDATION_ERRORS["INVALID_FORMAT"],
                validation_errors=[{
                    "field": field_name,
                    "message": "Value must be a dictionary"
                }]
            )
        return False
    
    validation_errors = []
    
    # Check required keys
    if required_keys:
        for key in required_keys:
            if key not in value:
                validation_errors.append({
                    "field": f"{field_name}.{key}",
                    "message": f"Required key '{key}' is missing"
                })
    
    # Check allowed keys
    if allowed_keys:
        for key in value:
            if key not in allowed_keys:
                validation_errors.append({
                    "field": f"{field_name}.{key}",
                    "message": f"Key '{key}' is not allowed"
                })
    
    if validation_errors and raise_exception:
        raise ValidationException(
            message="Invalid dictionary",
            validation_errors=validation_errors
        )
    
    return len(validation_errors) == 0