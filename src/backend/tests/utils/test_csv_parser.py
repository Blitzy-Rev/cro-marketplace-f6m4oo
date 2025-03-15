"""
Unit tests for the CSV parser utility module that handles parsing, validation, and processing
of CSV files containing molecular data. These tests ensure the reliability of the CSV
Molecular Data Ingestion feature.
"""

import pytest
import pandas as pd
import numpy as np
import os
import tempfile
import io
from unittest import mock

# Internal imports
from ../../app/utils/csv_parser import (
    parse_csv_file,
    validate_csv_columns,
    map_csv_columns,
    get_column_mapping_suggestions,
    validate_csv_data,
    get_csv_preview,
    process_csv_in_chunks,
    CSVProcessor,
    MAX_FILE_SIZE_MB,
    MAX_MOLECULES
)
from ../../app/core/exceptions import CSVException
from ../../app/constants/error_messages import CSV_ERRORS, FILE_TOO_LARGE, INVALID_CSV_FORMAT, EMPTY_FILE, TOO_MANY_ROWS, MISSING_REQUIRED_COLUMN, MISSING_SMILES_COLUMN
from ../../app/constants/molecule_properties import STANDARD_PROPERTIES


def create_test_csv_file(content):
    """Helper function to create a temporary CSV file for testing."""
    temp_file = tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.csv')
    temp_file.write(content)
    temp_file.flush()
    temp_file.close()
    return temp_file.name


class TestParseCSVFile:
    """Test cases for the parse_csv_file function."""
    
    def test_parse_valid_csv(self):
        """Test parsing a valid CSV file."""
        csv_content = "smiles,molecular_weight,logp\nCC(C)CCO,88.15,1.2\nc1ccccc1,78.11,2.1\n"
        temp_file = create_test_csv_file(csv_content)
        
        try:
            df = parse_csv_file(temp_file)
            assert isinstance(df, pd.DataFrame)
            assert list(df.columns) == ["smiles", "molecular_weight", "logp"]
            assert len(df) == 2
            assert df.iloc[0]["smiles"] == "CC(C)CCO"
            assert df.iloc[0]["molecular_weight"] == 88.15
        finally:
            os.unlink(temp_file)
    
    def test_parse_invalid_csv_format(self):
        """Test parsing a CSV file with invalid format."""
        csv_content = "Invalid CSV content"
        temp_file = create_test_csv_file(csv_content)
        
        try:
            with pytest.raises(CSVException) as excinfo:
                parse_csv_file(temp_file)
            assert CSV_ERRORS["INVALID_CSV_FORMAT"] in str(excinfo.value)
        finally:
            os.unlink(temp_file)
            
    def test_parse_empty_csv(self):
        """Test parsing an empty CSV file."""
        csv_content = ""
        temp_file = create_test_csv_file(csv_content)
        
        try:
            with pytest.raises(CSVException) as excinfo:
                parse_csv_file(temp_file)
            assert CSV_ERRORS["EMPTY_FILE"] in str(excinfo.value)
        finally:
            os.unlink(temp_file)
            
    def test_parse_file_too_large(self, mocker):
        """Test parsing a CSV file that exceeds the size limit."""
        csv_content = "smiles,molecular_weight,logp\nCC(C)CCO,88.15,1.2\n"
        temp_file = create_test_csv_file(csv_content)
        
        try:
            # Mock os.path.getsize to return a value larger than MAX_FILE_SIZE_MB
            mocker.patch('os.path.getsize', return_value=(MAX_FILE_SIZE_MB + 1) * 1024 * 1024)
            
            with pytest.raises(CSVException) as excinfo:
                parse_csv_file(temp_file)
            assert CSV_ERRORS["FILE_TOO_LARGE"] in str(excinfo.value)
        finally:
            os.unlink(temp_file)
            
    def test_parse_too_many_rows(self, mocker):
        """Test parsing a CSV file with too many rows."""
        csv_content = "smiles,molecular_weight,logp\nCC(C)CCO,88.15,1.2\n"
        temp_file = create_test_csv_file(csv_content)
        
        try:
            # Mock pandas.read_csv to return a DataFrame with more rows than MAX_MOLECULES
            mock_df = pd.DataFrame({
                "smiles": ["CC(C)CCO"] * (MAX_MOLECULES + 1),
                "molecular_weight": [88.15] * (MAX_MOLECULES + 1),
                "logp": [1.2] * (MAX_MOLECULES + 1)
            })
            mocker.patch('pandas.read_csv', return_value=mock_df)
            
            with pytest.raises(CSVException) as excinfo:
                parse_csv_file(temp_file)
            assert CSV_ERRORS["TOO_MANY_ROWS"] in str(excinfo.value)
        finally:
            os.unlink(temp_file)
            
    def test_parse_with_column_mapping(self):
        """Test parsing a CSV file with column mapping."""
        csv_content = "structure,MW,LogP\nCC(C)CCO,88.15,1.2\nc1ccccc1,78.11,2.1\n"
        temp_file = create_test_csv_file(csv_content)
        
        try:
            column_mapping = {
                "structure": "smiles",
                "MW": "molecular_weight",
                "LogP": "logp"
            }
            df = parse_csv_file(temp_file, column_mapping=column_mapping)
            assert isinstance(df, pd.DataFrame)
            assert list(df.columns) == ["smiles", "molecular_weight", "logp"]
            assert len(df) == 2
            assert df.iloc[0]["smiles"] == "CC(C)CCO"
            assert df.iloc[0]["molecular_weight"] == 88.15
        finally:
            os.unlink(temp_file)


class TestValidateCSVColumns:
    """Test cases for the validate_csv_columns function."""
    
    def test_validate_with_required_columns(self):
        """Test validation with all required columns present."""
        df = pd.DataFrame({
            "smiles": ["CC(C)CCO", "c1ccccc1"],
            "molecular_weight": [88.15, 78.11],
            "logp": [1.2, 2.1]
        })
        
        assert validate_csv_columns(df, required_columns=["smiles", "molecular_weight"])
        
    def test_validate_missing_required_column(self):
        """Test validation with a missing required column."""
        df = pd.DataFrame({
            "molecular_weight": [88.15, 78.11],
            "logp": [1.2, 2.1]
        })
        
        with pytest.raises(CSVException) as excinfo:
            validate_csv_columns(df, required_columns=["smiles", "molecular_weight"])
        assert CSV_ERRORS["MISSING_REQUIRED_COLUMN"] in str(excinfo.value)
        
    def test_validate_missing_smiles_column(self):
        """Test validation with missing SMILES column."""
        df = pd.DataFrame({
            "molecular_weight": [88.15, 78.11],
            "logp": [1.2, 2.1]
        })
        
        with pytest.raises(CSVException) as excinfo:
            validate_csv_columns(df)
        assert CSV_ERRORS["MISSING_SMILES_COLUMN"] in str(excinfo.value)
        
    def test_validate_duplicate_column_names(self):
        """Test validation with duplicate column names."""
        # Create DataFrame with duplicate column names
        df = pd.DataFrame(columns=["smiles", "molecular_weight", "molecular_weight"])
        
        with pytest.raises(CSVException) as excinfo:
            validate_csv_columns(df)
        assert CSV_ERRORS["DUPLICATE_COLUMN_NAMES"] in str(excinfo.value)


class TestMapCSVColumns:
    """Test cases for the map_csv_columns function."""
    
    def test_map_valid_columns(self):
        """Test mapping valid columns."""
        df = pd.DataFrame({
            "structure": ["CC(C)CCO", "c1ccccc1"],
            "MW": [88.15, 78.11],
            "LogP": [1.2, 2.1]
        })
        
        column_mapping = {
            "structure": "smiles",
            "MW": "molecular_weight",
            "LogP": "logp"
        }
        
        mapped_df = map_csv_columns(df, column_mapping)
        assert list(mapped_df.columns) == ["smiles", "molecular_weight", "logp"]
        
    def test_map_missing_smiles_column(self):
        """Test mapping without SMILES column mapping."""
        df = pd.DataFrame({
            "structure": ["CC(C)CCO", "c1ccccc1"],
            "MW": [88.15, 78.11],
            "LogP": [1.2, 2.1]
        })
        
        column_mapping = {
            "MW": "molecular_weight",
            "LogP": "logp"
        }
        
        with pytest.raises(CSVException) as excinfo:
            map_csv_columns(df, column_mapping)
        assert CSV_ERRORS["MISSING_SMILES_COLUMN"] in str(excinfo.value)
        
    def test_map_nonexistent_column(self):
        """Test mapping a column that doesn't exist in the DataFrame."""
        df = pd.DataFrame({
            "structure": ["CC(C)CCO", "c1ccccc1"],
            "MW": [88.15, 78.11]
        })
        
        column_mapping = {
            "structure": "smiles",
            "MW": "molecular_weight",
            "LogP": "logp"  # This column doesn't exist
        }
        
        with pytest.raises(CSVException) as excinfo:
            map_csv_columns(df, column_mapping)
        assert CSV_ERRORS["INVALID_COLUMN_MAPPING"] in str(excinfo.value)


class TestGetColumnMappingSuggestions:
    """Test cases for the get_column_mapping_suggestions function."""
    
    def test_suggest_standard_columns(self):
        """Test suggestions for standard column names."""
        df = pd.DataFrame({
            "smiles": ["CC(C)CCO", "c1ccccc1"],
            "molecular_weight": [88.15, 78.11],
            "logp": [1.2, 2.1]
        })
        
        suggestions = get_column_mapping_suggestions(df)
        assert suggestions.get("smiles") == "smiles"
        assert suggestions.get("molecular_weight") == "molecular_weight"
        assert suggestions.get("logp") == "logp"
        
    def test_suggest_case_insensitive(self):
        """Test case-insensitive column name matching."""
        df = pd.DataFrame({
            "SMILES": ["CC(C)CCO", "c1ccccc1"],
            "Molecular_Weight": [88.15, 78.11],
            "LogP": [1.2, 2.1]
        })
        
        suggestions = get_column_mapping_suggestions(df)
        assert suggestions.get("SMILES") == "smiles"
        assert suggestions.get("Molecular_Weight") == "molecular_weight"
        assert suggestions.get("LogP") == "logp"
        
    def test_suggest_by_content(self):
        """Test suggestions based on column content."""
        df = pd.DataFrame({
            "compound_structure": ["CC(C)CCO", "c1ccccc1"],
            "weight": [88.15, 78.11],
            "partition_coefficient": [1.2, 2.1]
        })
        
        suggestions = get_column_mapping_suggestions(df)
        assert suggestions.get("weight") == "molecular_weight"
        
    def test_suggest_smiles_variants(self):
        """Test suggestions for various SMILES column name variants."""
        # Test different SMILES column variants
        df1 = pd.DataFrame({"structure": ["CC(C)CCO"]})
        df2 = pd.DataFrame({"molecule": ["CC(C)CCO"]})
        df3 = pd.DataFrame({"canonical_smiles": ["CC(C)CCO"]})
        
        suggestions1 = get_column_mapping_suggestions(df1)
        suggestions2 = get_column_mapping_suggestions(df2)
        suggestions3 = get_column_mapping_suggestions(df3)
        
        assert suggestions1.get("structure") == "smiles"
        assert suggestions2.get("molecule") == "smiles"
        assert suggestions3.get("canonical_smiles") == "smiles"


class TestValidateCSVData:
    """Test cases for the validate_csv_data function."""
    
    def test_validate_valid_data(self):
        """Test validation of valid CSV data."""
        df = pd.DataFrame({
            "smiles_col": ["CC(C)CCO", "c1ccccc1"],
            "mw_col": [88.15, 78.11],
            "logp_col": [1.2, 2.1]
        })
        
        column_mapping = {
            "smiles_col": "smiles",
            "mw_col": "molecular_weight",
            "logp_col": "logp"
        }
        
        is_valid, errors = validate_csv_data(df, column_mapping)
        assert is_valid
        assert len(errors) == 0
        
    def test_validate_invalid_smiles(self):
        """Test validation with invalid SMILES strings."""
        df = pd.DataFrame({
            "smiles_col": ["CC(C)CCO", "invalid_smiles"],
            "mw_col": [88.15, 78.11]
        })
        
        column_mapping = {
            "smiles_col": "smiles",
            "mw_col": "molecular_weight"
        }
        
        is_valid, errors = validate_csv_data(df, column_mapping)
        assert not is_valid
        assert len(errors) > 0
        assert errors[0]["col"] == "smiles_col"
        
    def test_validate_invalid_property_values(self):
        """Test validation with invalid property values."""
        df = pd.DataFrame({
            "smiles_col": ["CC(C)CCO", "c1ccccc1"],
            "mw_col": [88.15, -10]  # Negative molecular weight is invalid
        })
        
        column_mapping = {
            "smiles_col": "smiles",
            "mw_col": "molecular_weight"
        }
        
        is_valid, errors = validate_csv_data(df, column_mapping)
        assert not is_valid
        assert len(errors) > 0
        assert errors[0]["col"] == "mw_col"
        
    def test_validate_missing_smiles_column(self):
        """Test validation without a SMILES column."""
        df = pd.DataFrame({
            "mw_col": [88.15, 78.11],
            "logp_col": [1.2, 2.1]
        })
        
        column_mapping = {
            "mw_col": "molecular_weight",
            "logp_col": "logp"
        }
        
        with pytest.raises(CSVException) as excinfo:
            validate_csv_data(df, column_mapping)
        assert CSV_ERRORS["MISSING_SMILES_COLUMN"] in str(excinfo.value)


class TestGetCSVPreview:
    """Test cases for the get_csv_preview function."""
    
    def test_get_preview_default_rows(self):
        """Test getting preview with default number of rows."""
        csv_content = "smiles,molecular_weight,logp\nCC(C)CCO,88.15,1.2\nc1ccccc1,78.11,2.1\nCCN(CC)CC,101.19,0.8\n"
        temp_file = create_test_csv_file(csv_content)
        
        try:
            preview = get_csv_preview(temp_file)
            assert "headers" in preview
            assert "rows" in preview
            assert len(preview["headers"]) == 3
            assert len(preview["rows"]) <= 5  # DEFAULT_PREVIEW_ROWS is 5
        finally:
            os.unlink(temp_file)
            
    def test_get_preview_custom_rows(self):
        """Test getting preview with custom number of rows."""
        csv_content = "smiles,molecular_weight,logp\n" + "\n".join([f"CC(C)CCO,{i},1.2" for i in range(10)])
        temp_file = create_test_csv_file(csv_content)
        
        try:
            preview = get_csv_preview(temp_file, num_rows=3)
            assert len(preview["rows"]) == 3
        finally:
            os.unlink(temp_file)
            
    def test_get_preview_file_not_found(self):
        """Test preview with nonexistent file."""
        with pytest.raises(FileNotFoundError):
            get_csv_preview("nonexistent_file.csv")


class TestProcessCSVInChunks:
    """Test cases for the process_csv_in_chunks function."""
    
    def test_process_in_chunks(self, mocker):
        """Test processing CSV in chunks."""
        csv_content = "smiles,molecular_weight,logp\n" + "\n".join([f"CC(C)CCO,{i},1.2" for i in range(100)])
        temp_file = create_test_csv_file(csv_content)
        
        try:
            # Mock process function
            process_mock = mocker.Mock(return_value={"processed": True})
            column_mapping = {"smiles": "smiles", "molecular_weight": "molecular_weight", "logp": "logp"}
            
            result = process_csv_in_chunks(temp_file, column_mapping, chunk_size=20, process_function=process_mock)
            
            assert "total_rows" in result
            assert "successful_rows" in result
            assert "error_count" in result
            assert "results" in result
            
            # Check that the process function was called for each chunk
            assert process_mock.call_count == 5  # 100 rows / 20 chunk size = 5 chunks
        finally:
            os.unlink(temp_file)
            
    def test_process_with_errors(self, mocker):
        """Test processing with validation errors."""
        csv_content = "smiles,molecular_weight,logp\nCC(C)CCO,88.15,1.2\ninvalid_smiles,78.11,2.1\n"
        temp_file = create_test_csv_file(csv_content)
        
        try:
            # Mock process function
            process_mock = mocker.Mock(return_value={"processed": True})
            column_mapping = {"smiles": "smiles", "molecular_weight": "molecular_weight", "logp": "logp"}
            
            result = process_csv_in_chunks(temp_file, column_mapping, chunk_size=10, process_function=process_mock)
            
            assert result["error_count"] > 0
            assert result["successful_rows"] < result["total_rows"]
        finally:
            os.unlink(temp_file)
            
    def test_process_empty_file(self, mocker):
        """Test processing an empty CSV file."""
        csv_content = ""
        temp_file = create_test_csv_file(csv_content)
        
        try:
            # Mock process function
            process_mock = mocker.Mock(return_value={"processed": True})
            column_mapping = {"smiles": "smiles", "molecular_weight": "molecular_weight", "logp": "logp"}
            
            with pytest.raises(CSVException) as excinfo:
                process_csv_in_chunks(temp_file, column_mapping, chunk_size=10, process_function=process_mock)
            assert CSV_ERRORS["EMPTY_FILE"] in str(excinfo.value)
        finally:
            os.unlink(temp_file)


class TestCSVProcessor:
    """Test cases for the CSVProcessor class."""
    
    def test_load_csv(self):
        """Test loading a CSV file."""
        csv_content = "smiles,molecular_weight,logp\nCC(C)CCO,88.15,1.2\nc1ccccc1,78.11,2.1\n"
        temp_file = create_test_csv_file(csv_content)
        
        try:
            processor = CSVProcessor(temp_file)
            assert processor.load_csv()
            
            # Check internal DataFrame
            preview = processor.get_preview()
            assert len(preview["rows"]) == 2
            assert "smiles" in preview["headers"]
        finally:
            os.unlink(temp_file)
            
    def test_set_column_mapping(self):
        """Test setting column mapping."""
        csv_content = "structure,MW,LogP\nCC(C)CCO,88.15,1.2\nc1ccccc1,78.11,2.1\n"
        temp_file = create_test_csv_file(csv_content)
        
        try:
            processor = CSVProcessor(temp_file)
            processor.load_csv()
            
            column_mapping = {
                "structure": "smiles",
                "MW": "molecular_weight",
                "LogP": "logp"
            }
            
            assert processor.set_column_mapping(column_mapping)
        finally:
            os.unlink(temp_file)
            
    def test_get_mapping_suggestions(self):
        """Test getting column mapping suggestions."""
        csv_content = "smiles,molecular_weight,logp\nCC(C)CCO,88.15,1.2\nc1ccccc1,78.11,2.1\n"
        temp_file = create_test_csv_file(csv_content)
        
        try:
            processor = CSVProcessor(temp_file)
            processor.load_csv()
            
            suggestions = processor.get_mapping_suggestions()
            assert suggestions.get("smiles") == "smiles"
            assert suggestions.get("molecular_weight") == "molecular_weight"
            assert suggestions.get("logp") == "logp"
        finally:
            os.unlink(temp_file)
            
    def test_process(self):
        """Test processing the CSV data."""
        csv_content = "smiles,molecular_weight,logp\nCC(C)CCO,88.15,1.2\nc1ccccc1,78.11,2.1\n"
        temp_file = create_test_csv_file(csv_content)
        
        try:
            processor = CSVProcessor(temp_file)
            processor.load_csv()
            
            column_mapping = {
                "smiles": "smiles",
                "molecular_weight": "molecular_weight",
                "logp": "logp"
            }
            
            processor.set_column_mapping(column_mapping)
            assert processor.process()
            
            # Check processed data
            processed_data = processor.get_processed_data()
            assert isinstance(processed_data, pd.DataFrame)
            assert len(processed_data) == 2
        finally:
            os.unlink(temp_file)
            
    def test_get_invalid_rows(self):
        """Test getting invalid rows after processing."""
        csv_content = "smiles,molecular_weight,logp\nCC(C)CCO,88.15,1.2\ninvalid_smiles,78.11,2.1\n"
        temp_file = create_test_csv_file(csv_content)
        
        try:
            processor = CSVProcessor(temp_file)
            processor.load_csv()
            
            column_mapping = {
                "smiles": "smiles",
                "molecular_weight": "molecular_weight",
                "logp": "logp"
            }
            
            processor.set_column_mapping(column_mapping)
            processor.process()
            
            invalid_rows = processor.get_invalid_rows()
            assert len(invalid_rows) > 0
            assert invalid_rows[0]["col"] == "smiles"
        finally:
            os.unlink(temp_file)
            
    def test_get_summary(self):
        """Test getting processing summary."""
        csv_content = "smiles,molecular_weight,logp\nCC(C)CCO,88.15,1.2\ninvalid_smiles,78.11,2.1\nCCN(CC)CC,101.19,0.8\n"
        temp_file = create_test_csv_file(csv_content)
        
        try:
            processor = CSVProcessor(temp_file)
            processor.load_csv()
            
            column_mapping = {
                "smiles": "smiles",
                "molecular_weight": "molecular_weight",
                "logp": "logp"
            }
            
            processor.set_column_mapping(column_mapping)
            processor.process()
            
            summary = processor.get_summary()
            assert "total_rows" in summary
            assert "valid_rows" in summary
            assert "invalid_rows" in summary
            assert summary["total_rows"] == 3
            assert summary["invalid_rows"] >= 1
        finally:
            os.unlink(temp_file)
            
    def test_get_preview(self):
        """Test getting data preview."""
        csv_content = "smiles,molecular_weight,logp\n" + "\n".join([f"CC(C)CCO,{i},1.2" for i in range(10)])
        temp_file = create_test_csv_file(csv_content)
        
        try:
            processor = CSVProcessor(temp_file)
            processor.load_csv()
            
            preview = processor.get_preview(num_rows=3)
            assert len(preview["rows"]) == 3
            assert preview["total_rows"] == 10
        finally:
            os.unlink(temp_file)
            
    def test_get_processed_data(self):
        """Test getting processed data."""
        csv_content = "smiles,molecular_weight,logp\nCC(C)CCO,88.15,1.2\nc1ccccc1,78.11,2.1\n"
        temp_file = create_test_csv_file(csv_content)
        
        try:
            processor = CSVProcessor(temp_file)
            processor.load_csv()
            
            column_mapping = {
                "smiles": "smiles",
                "molecular_weight": "molecular_weight",
                "logp": "logp"
            }
            
            processor.set_column_mapping(column_mapping)
            processor.process()
            
            data = processor.get_processed_data()
            assert isinstance(data, pd.DataFrame)
            assert len(data) == 2
            assert list(data.columns) == ["smiles", "molecular_weight", "logp"]
        finally:
            os.unlink(temp_file)
            
    def test_get_valid_molecules(self):
        """Test getting only valid molecules."""
        csv_content = "smiles,molecular_weight,logp\nCC(C)CCO,88.15,1.2\ninvalid_smiles,78.11,2.1\nCCN(CC)CC,101.19,0.8\n"
        temp_file = create_test_csv_file(csv_content)
        
        try:
            processor = CSVProcessor(temp_file)
            processor.load_csv()
            
            column_mapping = {
                "smiles": "smiles",
                "molecular_weight": "molecular_weight",
                "logp": "logp"
            }
            
            processor.set_column_mapping(column_mapping)
            processor.process()
            
            valid_molecules = processor.get_valid_molecules()
            assert isinstance(valid_molecules, pd.DataFrame)
            assert len(valid_molecules) < 3  # Should exclude the invalid row
        finally:
            os.unlink(temp_file)