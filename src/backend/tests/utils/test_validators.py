import pytest
import uuid
import datetime
import re

from ../../app/utils/validators import (
    validate_required,
    validate_string,
    validate_numeric,
    validate_email,
    validate_uuid,
    validate_date,
    validate_property_value,
    validate_molecule_properties,
    validate_csv_column_mapping,
    validate_smiles_string,
    validate_list,
    validate_dict
)
from ../../app/core/exceptions import ValidationException
from ../../app/constants/error_messages import VALIDATION_ERRORS
from ../../app/constants/molecule_properties import PropertyType, STANDARD_PROPERTIES, PROPERTY_RANGES

# Test data for validation tests
VALID_EMAILS = ["user@example.com", "test.user@example.co.uk", "user+tag@example.org", "user.name@subdomain.example.com"]
INVALID_EMAILS = ["user@", "@example.com", "user@example", "user@.com", "user@example..com", "", None]
VALID_UUIDS = ["123e4567-e89b-12d3-a456-426614174000", "00000000-0000-0000-0000-000000000000", "a8098c1a-f86e-11da-bd1a-00112444be1e"]
INVALID_UUIDS = ["123e4567", "123e4567-e89b-12d3-a456", "123e4567-e89b-12d3-a456-42661417400Z", "123e4567-e89b-12d3-a456-4266141740001", "", None]
VALID_SMILES = ["C", "CC", "CCO", "c1ccccc1", "CC(=O)O", "C1CCCCC1", "N#C", "CCN(CC)CC"]
INVALID_SMILES = ["X", "C:C", "C(C", "1CCCCC1", "C%C", "C##C", "C1CC2", "", None]

@pytest.mark.parametrize("value", ["test", 0, False, [], {}, 42, 3.14])
def test_validate_required_valid(value):
    """Tests that validate_required correctly identifies non-empty values."""
    assert validate_required(value, "field_name", raise_exception=False)


@pytest.mark.parametrize("value", [None, ""])
def test_validate_required_invalid(value):
    """Tests that validate_required correctly identifies empty values."""
    assert not validate_required(value, "field_name", raise_exception=False)


@pytest.mark.parametrize("value", [None, ""])
def test_validate_required_exception(value):
    """Tests that validate_required raises ValidationException when specified."""
    with pytest.raises(ValidationException) as excinfo:
        validate_required(value, "field_name", raise_exception=True)
    assert VALIDATION_ERRORS["REQUIRED_FIELD"] in str(excinfo.value)


def test_validate_string_valid():
    """Tests that validate_string correctly validates strings with various constraints."""
    # Basic string validation
    assert validate_string("test", "field_name", raise_exception=False)
    
    # With minimum length
    assert validate_string("test", "field_name", min_length=2, raise_exception=False)
    
    # With maximum length
    assert validate_string("test", "field_name", max_length=10, raise_exception=False)
    
    # With both min and max length
    assert validate_string("test", "field_name", min_length=2, max_length=10, raise_exception=False)
    
    # With pattern
    assert validate_string("ABC123", "field_name", pattern=r"^[A-Z0-9]+$", raise_exception=False)


def test_validate_string_invalid():
    """Tests that validate_string correctly identifies invalid strings."""
    # Non-string values
    assert not validate_string(None, "field_name", raise_exception=False)
    assert not validate_string(123, "field_name", raise_exception=False)
    
    # Too short
    assert not validate_string("a", "field_name", min_length=2, raise_exception=False)
    
    # Too long
    assert not validate_string("abcdef", "field_name", max_length=5, raise_exception=False)
    
    # Doesn't match pattern
    assert not validate_string("abc", "field_name", pattern=r"^[A-Z]+$", raise_exception=False)


def test_validate_string_exception():
    """Tests that validate_string raises ValidationException when specified."""
    # Non-string value
    with pytest.raises(ValidationException) as excinfo:
        validate_string(123, "field_name", raise_exception=True)
    assert VALIDATION_ERRORS["INVALID_FORMAT"] in str(excinfo.value)
    
    # Too short
    with pytest.raises(ValidationException) as excinfo:
        validate_string("a", "field_name", min_length=2, raise_exception=True)
    assert VALIDATION_ERRORS["VALUE_TOO_SHORT"] in str(excinfo.value)
    
    # Too long
    with pytest.raises(ValidationException) as excinfo:
        validate_string("abcdef", "field_name", max_length=5, raise_exception=True)
    assert VALIDATION_ERRORS["VALUE_TOO_LONG"] in str(excinfo.value)
    
    # Doesn't match pattern
    with pytest.raises(ValidationException) as excinfo:
        validate_string("abc", "field_name", pattern=r"^[A-Z]+$", raise_exception=True)
    assert VALIDATION_ERRORS["INVALID_FORMAT"] in str(excinfo.value)


def test_validate_numeric_valid():
    """Tests that validate_numeric correctly validates numeric values with various constraints."""
    # Basic numeric validation
    assert validate_numeric(42, "field_name", raise_exception=False)
    assert validate_numeric(3.14, "field_name", raise_exception=False)
    
    # With minimum value
    assert validate_numeric(10, "field_name", min_value=5, raise_exception=False)
    
    # With maximum value
    assert validate_numeric(10, "field_name", max_value=15, raise_exception=False)
    
    # With both min and max value
    assert validate_numeric(10, "field_name", min_value=5, max_value=15, raise_exception=False)


def test_validate_numeric_invalid():
    """Tests that validate_numeric correctly identifies invalid numeric values."""
    # Non-numeric values
    assert not validate_numeric(None, "field_name", raise_exception=False)
    assert not validate_numeric("123", "field_name", raise_exception=False)
    
    # Below minimum
    assert not validate_numeric(3, "field_name", min_value=5, raise_exception=False)
    
    # Above maximum
    assert not validate_numeric(20, "field_name", max_value=15, raise_exception=False)


def test_validate_numeric_exception():
    """Tests that validate_numeric raises ValidationException when specified."""
    # Non-numeric value
    with pytest.raises(ValidationException) as excinfo:
        validate_numeric("123", "field_name", raise_exception=True)
    assert VALIDATION_ERRORS["INVALID_FORMAT"] in str(excinfo.value)
    
    # Below minimum
    with pytest.raises(ValidationException) as excinfo:
        validate_numeric(3, "field_name", min_value=5, raise_exception=True)
    assert VALIDATION_ERRORS["VALUE_OUT_OF_RANGE"] in str(excinfo.value)
    
    # Above maximum
    with pytest.raises(ValidationException) as excinfo:
        validate_numeric(20, "field_name", max_value=15, raise_exception=True)
    assert VALIDATION_ERRORS["VALUE_OUT_OF_RANGE"] in str(excinfo.value)


@pytest.mark.parametrize("email", VALID_EMAILS)
def test_validate_email_valid(email):
    """Tests that validate_email correctly validates email addresses."""
    assert validate_email(email, "email", raise_exception=False)


@pytest.mark.parametrize("email", INVALID_EMAILS)
def test_validate_email_invalid(email):
    """Tests that validate_email correctly identifies invalid email addresses."""
    assert not validate_email(email, "email", raise_exception=False)


@pytest.mark.parametrize("email", INVALID_EMAILS)
def test_validate_email_exception(email):
    """Tests that validate_email raises ValidationException when specified."""
    with pytest.raises(ValidationException) as excinfo:
        validate_email(email, "email", raise_exception=True)
    assert VALIDATION_ERRORS["INVALID_EMAIL"] in str(excinfo.value)


@pytest.mark.parametrize("uuid_str", VALID_UUIDS)
def test_validate_uuid_valid(uuid_str):
    """Tests that validate_uuid correctly validates UUID strings."""
    assert validate_uuid(uuid_str, "uuid", raise_exception=False)


@pytest.mark.parametrize("uuid_str", INVALID_UUIDS)
def test_validate_uuid_invalid(uuid_str):
    """Tests that validate_uuid correctly identifies invalid UUID strings."""
    assert not validate_uuid(uuid_str, "uuid", raise_exception=False)


@pytest.mark.parametrize("uuid_str", INVALID_UUIDS)
def test_validate_uuid_exception(uuid_str):
    """Tests that validate_uuid raises ValidationException when specified."""
    with pytest.raises(ValidationException) as excinfo:
        validate_uuid(uuid_str, "uuid", raise_exception=True)
    assert VALIDATION_ERRORS["INVALID_UUID"] in str(excinfo.value)


def test_validate_date_valid():
    """Tests that validate_date correctly validates date values with various constraints."""
    today = datetime.datetime.now().date()
    yesterday = today - datetime.timedelta(days=1)
    tomorrow = today + datetime.timedelta(days=1)
    
    # Date objects
    assert validate_date(today, "date", raise_exception=False)
    
    # Datetime objects
    assert validate_date(datetime.datetime.now(), "date", raise_exception=False)
    
    # String dates
    assert validate_date("2023-05-01", "date", raise_exception=False)
    
    # With format string
    assert validate_date("05/01/2023", "date", format_str="%m/%d/%Y", raise_exception=False)
    
    # With min_date
    assert validate_date(today, "date", min_date=yesterday, raise_exception=False)
    
    # With max_date
    assert validate_date(today, "date", max_date=tomorrow, raise_exception=False)
    
    # With both min and max date
    assert validate_date(today, "date", min_date=yesterday, max_date=tomorrow, raise_exception=False)


def test_validate_date_invalid():
    """Tests that validate_date correctly identifies invalid date values."""
    today = datetime.datetime.now().date()
    yesterday = today - datetime.timedelta(days=1)
    tomorrow = today + datetime.timedelta(days=1)
    
    # Non-date values
    assert not validate_date(None, "date", raise_exception=False)
    assert not validate_date(123, "date", raise_exception=False)
    
    # Invalid string format
    assert not validate_date("not-a-date", "date", raise_exception=False)
    
    # Before min_date
    assert not validate_date(yesterday, "date", min_date=today, raise_exception=False)
    
    # After max_date
    assert not validate_date(tomorrow, "date", max_date=today, raise_exception=False)


def test_validate_date_exception():
    """Tests that validate_date raises ValidationException when specified."""
    today = datetime.datetime.now().date()
    yesterday = today - datetime.timedelta(days=1)
    tomorrow = today + datetime.timedelta(days=1)
    
    # Non-date value
    with pytest.raises(ValidationException) as excinfo:
        validate_date(123, "date", raise_exception=True)
    assert VALIDATION_ERRORS["INVALID_DATE"] in str(excinfo.value)
    
    # Invalid string format
    with pytest.raises(ValidationException) as excinfo:
        validate_date("not-a-date", "date", raise_exception=True)
    assert VALIDATION_ERRORS["INVALID_DATE"] in str(excinfo.value)
    
    # Before min_date
    with pytest.raises(ValidationException) as excinfo:
        validate_date(yesterday, "date", min_date=today, raise_exception=True)
    assert VALIDATION_ERRORS["PAST_DATE_REQUIRED"] in str(excinfo.value)
    
    # After max_date
    with pytest.raises(ValidationException) as excinfo:
        validate_date(tomorrow, "date", max_date=today, raise_exception=True)
    assert VALIDATION_ERRORS["FUTURE_DATE_REQUIRED"] in str(excinfo.value)


def test_validate_property_value_valid():
    """Tests that validate_property_value correctly validates property values based on type."""
    # String property
    assert validate_property_value("C", "smiles", PropertyType.STRING, raise_exception=False)
    
    # Numeric property
    assert validate_property_value(100.5, "molecular_weight", PropertyType.NUMERIC, raise_exception=False)
    
    # Integer property
    assert validate_property_value(5, "num_rings", PropertyType.INTEGER, raise_exception=False)
    
    # Boolean property
    assert validate_property_value(True, "is_active", PropertyType.BOOLEAN, raise_exception=False)


def test_validate_property_value_invalid():
    """Tests that validate_property_value correctly identifies invalid property values."""
    # Invalid string property
    assert not validate_property_value(123, "smiles", PropertyType.STRING, raise_exception=False)
    
    # Invalid numeric property
    assert not validate_property_value("not a number", "molecular_weight", PropertyType.NUMERIC, raise_exception=False)
    
    # Invalid integer property
    assert not validate_property_value(5.5, "num_rings", PropertyType.INTEGER, raise_exception=False)
    
    # Invalid boolean property
    assert not validate_property_value("yes", "is_active", PropertyType.BOOLEAN, raise_exception=False)
    
    # Value outside range (if property has range defined)
    assert not validate_property_value(3000, "molecular_weight", PropertyType.NUMERIC, raise_exception=False)


def test_validate_property_value_exception():
    """Tests that validate_property_value raises ValidationException when specified."""
    # Invalid string property
    with pytest.raises(ValidationException) as excinfo:
        validate_property_value(123, "smiles", PropertyType.STRING, raise_exception=True)
    assert VALIDATION_ERRORS["INVALID_FORMAT"] in str(excinfo.value)
    
    # Invalid numeric property
    with pytest.raises(ValidationException) as excinfo:
        validate_property_value("not a number", "molecular_weight", PropertyType.NUMERIC, raise_exception=True)
    assert VALIDATION_ERRORS["INVALID_FORMAT"] in str(excinfo.value)
    
    # Value outside range
    with pytest.raises(ValidationException) as excinfo:
        validate_property_value(3000, "molecular_weight", PropertyType.NUMERIC, raise_exception=True)
    assert VALIDATION_ERRORS["VALUE_OUT_OF_RANGE"] in str(excinfo.value)


def test_validate_molecule_properties_valid():
    """Tests that validate_molecule_properties correctly validates a set of molecular properties."""
    properties = {
        "smiles": "CCO",
        "molecular_weight": 46.07,
        "logp": 0.5,
        "num_rings": 0
    }
    assert validate_molecule_properties(properties, raise_exception=False)


def test_validate_molecule_properties_invalid():
    """Tests that validate_molecule_properties correctly identifies invalid property sets."""
    # Invalid molecular weight (outside range)
    properties1 = {
        "smiles": "CCO",
        "molecular_weight": 3000,
        "logp": 0.5
    }
    assert not validate_molecule_properties(properties1, raise_exception=False)
    
    # Invalid property type
    properties2 = {
        "smiles": "CCO",
        "molecular_weight": "not a number",
        "logp": 0.5
    }
    assert not validate_molecule_properties(properties2, raise_exception=False)


def test_validate_molecule_properties_exception():
    """Tests that validate_molecule_properties raises ValidationException when specified."""
    # Invalid molecular weight
    properties = {
        "smiles": "CCO",
        "molecular_weight": 3000,
        "logp": 0.5
    }
    with pytest.raises(ValidationException) as excinfo:
        validate_molecule_properties(properties, raise_exception=True)
    assert "Invalid property values" in str(excinfo.value)


def test_validate_csv_column_mapping_valid():
    """Tests that validate_csv_column_mapping correctly validates column mappings."""
    # Valid mapping with smiles
    mapping1 = {
        "Column1": "smiles",
        "Column2": "molecular_weight",
        "Column3": "logp"
    }
    assert validate_csv_column_mapping(mapping1, raise_exception=False)
    
    # Valid mapping with custom property
    mapping2 = {
        "Column1": "smiles",
        "Column2": "molecular_weight",
        "Column3": "custom_property"
    }
    assert validate_csv_column_mapping(mapping2, raise_exception=False)


def test_validate_csv_column_mapping_invalid():
    """Tests that validate_csv_column_mapping correctly identifies invalid column mappings."""
    # Missing smiles
    mapping1 = {
        "Column1": "molecular_weight",
        "Column2": "logp"
    }
    assert not validate_csv_column_mapping(mapping1, raise_exception=False)
    
    # Empty mapping
    mapping2 = {}
    assert not validate_csv_column_mapping(mapping2, raise_exception=False)
    
    # Mapping to non-existent properties
    mapping3 = {
        "Column1": "smiles",
        "Column2": "nonexistent_property"
    }
    assert not validate_csv_column_mapping(mapping3, raise_exception=False)


def test_validate_csv_column_mapping_exception():
    """Tests that validate_csv_column_mapping raises ValidationException when specified."""
    # Missing smiles
    mapping = {
        "Column1": "molecular_weight",
        "Column2": "logp"
    }
    with pytest.raises(ValidationException) as excinfo:
        validate_csv_column_mapping(mapping, raise_exception=True)
    assert "SMILES column mapping is required" in str(excinfo.value)


@pytest.mark.parametrize("smiles", VALID_SMILES)
def test_validate_smiles_string_valid(smiles):
    """Tests that validate_smiles_string correctly validates SMILES strings."""
    assert validate_smiles_string(smiles, raise_exception=False)


@pytest.mark.parametrize("smiles", INVALID_SMILES)
def test_validate_smiles_string_invalid(smiles):
    """Tests that validate_smiles_string correctly identifies invalid SMILES strings."""
    assert not validate_smiles_string(smiles, raise_exception=False)


@pytest.mark.parametrize("smiles", INVALID_SMILES)
def test_validate_smiles_string_exception(smiles):
    """Tests that validate_smiles_string raises ValidationException when specified."""
    with pytest.raises(ValidationException) as excinfo:
        validate_smiles_string(smiles, raise_exception=True)
    assert VALIDATION_ERRORS["INVALID_FORMAT"] in str(excinfo.value)


def test_validate_list_valid():
    """Tests that validate_list correctly validates lists with various constraints."""
    # Basic list validation
    assert validate_list([1, 2, 3], "field_name", raise_exception=False)
    
    # With minimum length
    assert validate_list([1, 2, 3], "field_name", min_length=2, raise_exception=False)
    
    # With maximum length
    assert validate_list([1, 2, 3], "field_name", max_length=5, raise_exception=False)
    
    # With both min and max length
    assert validate_list([1, 2, 3], "field_name", min_length=2, max_length=5, raise_exception=False)


def test_validate_list_invalid():
    """Tests that validate_list correctly identifies invalid lists."""
    # Non-list values
    assert not validate_list(None, "field_name", raise_exception=False)
    assert not validate_list("not a list", "field_name", raise_exception=False)
    
    # Too short
    assert not validate_list([1], "field_name", min_length=2, raise_exception=False)
    
    # Too long
    assert not validate_list([1, 2, 3, 4, 5, 6], "field_name", max_length=5, raise_exception=False)


def test_validate_list_exception():
    """Tests that validate_list raises ValidationException when specified."""
    # Non-list value
    with pytest.raises(ValidationException) as excinfo:
        validate_list("not a list", "field_name", raise_exception=True)
    assert VALIDATION_ERRORS["INVALID_FORMAT"] in str(excinfo.value)
    
    # Too short
    with pytest.raises(ValidationException) as excinfo:
        validate_list([1], "field_name", min_length=2, raise_exception=True)
    assert VALIDATION_ERRORS["VALUE_TOO_SHORT"] in str(excinfo.value)
    
    # Too long
    with pytest.raises(ValidationException) as excinfo:
        validate_list([1, 2, 3, 4, 5, 6], "field_name", max_length=5, raise_exception=True)
    assert VALIDATION_ERRORS["VALUE_TOO_LONG"] in str(excinfo.value)


def test_validate_dict_valid():
    """Tests that validate_dict correctly validates dictionaries with various constraints."""
    # Basic dict validation
    assert validate_dict({"key": "value"}, "field_name", raise_exception=False)
    
    # With required keys
    assert validate_dict({"key1": "value1", "key2": "value2"}, "field_name", required_keys=["key1"], raise_exception=False)
    
    # With allowed keys
    assert validate_dict({"key1": "value1"}, "field_name", allowed_keys=["key1", "key2"], raise_exception=False)
    
    # With both required and allowed keys
    assert validate_dict({"key1": "value1", "key2": "value2"}, "field_name", required_keys=["key1"], allowed_keys=["key1", "key2"], raise_exception=False)


def test_validate_dict_invalid():
    """Tests that validate_dict correctly identifies invalid dictionaries."""
    # Non-dict values
    assert not validate_dict(None, "field_name", raise_exception=False)
    assert not validate_dict("not a dict", "field_name", raise_exception=False)
    
    # Missing required keys
    assert not validate_dict({"key2": "value2"}, "field_name", required_keys=["key1"], raise_exception=False)
    
    # Keys not in allowed list
    assert not validate_dict({"key3": "value3"}, "field_name", allowed_keys=["key1", "key2"], raise_exception=False)


def test_validate_dict_exception():
    """Tests that validate_dict raises ValidationException when specified."""
    # Non-dict value
    with pytest.raises(ValidationException) as excinfo:
        validate_dict("not a dict", "field_name", raise_exception=True)
    assert VALIDATION_ERRORS["INVALID_FORMAT"] in str(excinfo.value)
    
    # Missing required keys
    with pytest.raises(ValidationException) as excinfo:
        validate_dict({"key2": "value2"}, "field_name", required_keys=["key1"], raise_exception=True)
    assert "Required key" in str(excinfo.value)
    
    # Keys not in allowed list
    with pytest.raises(ValidationException) as excinfo:
        validate_dict({"key3": "value3"}, "field_name", allowed_keys=["key1", "key2"], raise_exception=True)
    assert "Key 'key3' is not allowed" in str(excinfo.value)