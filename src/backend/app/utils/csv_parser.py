"""
CSV Parser Module

Provides utilities for parsing, validating, and processing CSV files containing molecular data.
This module is a core component of the CSV Molecular Data Ingestion feature, enabling users to
upload and process large datasets of molecules with their associated properties.
"""

import os
import io
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union, Any, Tuple, Callable

# Internal imports
from ..core.exceptions import CSVException, MoleculeException
from ..constants.error_messages import CSV_ERRORS, MOLECULE_ERRORS
from ..constants.molecule_properties import STANDARD_PROPERTIES, REQUIRED_PROPERTIES, PropertyType
from .smiles import validate_smiles
from .validators import validate_property_value

# Maximum allowed CSV file size in MB
MAX_FILE_SIZE_MB = 100

# Maximum allowed number of molecules in a CSV file
MAX_MOLECULES = 500000

# Default number of rows to show in preview
DEFAULT_PREVIEW_ROWS = 5

# Default chunk size for processing large CSV files
DEFAULT_CHUNK_SIZE = 10000


def parse_csv_file(file_path: str, column_mapping: Optional[Dict[str, str]] = None, validate_data: bool = True) -> pd.DataFrame:
    """
    Parse a CSV file into a pandas DataFrame with basic validation.
    
    Args:
        file_path: Path to the CSV file
        column_mapping: Optional mapping of CSV columns to system properties
        validate_data: Whether to validate required columns
        
    Returns:
        DataFrame containing the parsed CSV data
        
    Raises:
        CSVException: If CSV validation fails
    """
    # Check if file exists and is accessible
    if not os.path.isfile(file_path):
        raise CSVException(
            message=f"File not found: {file_path}",
            file_name=os.path.basename(file_path)
        )
    
    # Check file size
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    if file_size_mb > MAX_FILE_SIZE_MB:
        raise CSVException(
            message=CSV_ERRORS["FILE_TOO_LARGE"],
            file_name=os.path.basename(file_path),
            details={"size_mb": file_size_mb, "max_size_mb": MAX_FILE_SIZE_MB}
        )
    
    try:
        # Try to read CSV file into pandas DataFrame
        df = pd.read_csv(file_path)
    except Exception as e:
        raise CSVException(
            message=CSV_ERRORS["INVALID_CSV_FORMAT"],
            file_name=os.path.basename(file_path),
            details={"error": str(e)}
        )
    
    # Check if DataFrame is empty
    if df.empty:
        raise CSVException(
            message=CSV_ERRORS["EMPTY_FILE"],
            file_name=os.path.basename(file_path)
        )
    
    # Check if number of rows exceeds maximum allowed
    if len(df) > MAX_MOLECULES:
        raise CSVException(
            message=CSV_ERRORS["TOO_MANY_ROWS"],
            file_name=os.path.basename(file_path),
            details={"row_count": len(df), "max_rows": MAX_MOLECULES}
        )
    
    # If column mapping is provided, apply it
    if column_mapping:
        try:
            df = map_csv_columns(df, column_mapping)
        except CSVException as e:
            # Re-raise with file name
            raise CSVException(
                message=e.message,
                file_name=os.path.basename(file_path),
                details=e.details
            )
    
    # Validate required columns if needed
    if validate_data:
        try:
            validate_csv_columns(df)
        except CSVException as e:
            # Re-raise with file name
            raise CSVException(
                message=e.message,
                file_name=os.path.basename(file_path),
                details=e.details
            )
    
    return df


def validate_csv_columns(df: pd.DataFrame, required_columns: Optional[List[str]] = None) -> bool:
    """
    Validate that CSV contains required columns, especially SMILES.
    
    Args:
        df: DataFrame containing CSV data
        required_columns: List of required column names
        
    Returns:
        True if validation passes
        
    Raises:
        CSVException: If validation fails
    """
    if required_columns is None:
        required_columns = ['smiles']
    
    # Check required columns
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        if 'smiles' in missing_columns:
            raise CSVException(
                message=CSV_ERRORS["MISSING_SMILES_COLUMN"],
                details={"missing_columns": missing_columns}
            )
        else:
            raise CSVException(
                message=CSV_ERRORS["MISSING_REQUIRED_COLUMN"],
                details={"missing_columns": missing_columns}
            )
    
    # Check for duplicate column names
    duplicate_columns = [col for col in df.columns if list(df.columns).count(col) > 1]
    if duplicate_columns:
        raise CSVException(
            message=CSV_ERRORS["DUPLICATE_COLUMN_NAMES"],
            details={"duplicate_columns": list(set(duplicate_columns))}
        )
    
    return True


def map_csv_columns(df: pd.DataFrame, column_mapping: Dict[str, str]) -> pd.DataFrame:
    """
    Map CSV columns to standard system properties.
    
    Args:
        df: DataFrame containing CSV data
        column_mapping: Dictionary mapping CSV column names to system property names
        
    Returns:
        DataFrame with renamed columns
        
    Raises:
        CSVException: If mapping validation fails
    """
    # Validate mapping contains required SMILES column
    if 'smiles' not in column_mapping.values():
        raise CSVException(
            message=CSV_ERRORS["MISSING_SMILES_COLUMN"],
            details={"mapped_properties": list(column_mapping.values())}
        )
    
    # Validate all columns in mapping exist in DataFrame
    missing_columns = [col for col in column_mapping.keys() if col not in df.columns]
    if missing_columns:
        raise CSVException(
            message=CSV_ERRORS["INVALID_COLUMN_MAPPING"],
            details={"missing_columns": missing_columns}
        )
    
    # Create reverse mapping (CSV column name to property name)
    rename_dict = {csv_col: prop_name for csv_col, prop_name in column_mapping.items()}
    
    # Apply mapping
    return df.rename(columns=rename_dict)


def get_column_mapping_suggestions(df: pd.DataFrame) -> Dict[str, str]:
    """
    Generate suggested column mappings based on column names and content.
    
    Args:
        df: DataFrame containing CSV data
        
    Returns:
        Dictionary mapping CSV columns to suggested system properties
    """
    suggestions = {}
    
    # Create lowercase versions of column names for case-insensitive matching
    lowercase_columns = {col.lower(): col for col in df.columns}
    
    # Common SMILES column names
    smiles_names = ['smiles', 'structure', 'molecule', 'mol', 'smi', 'canonical_smiles']
    
    # Try to find SMILES column
    for name in smiles_names:
        if name in lowercase_columns:
            suggestions[lowercase_columns[name]] = 'smiles'
            break
    
    # Match other standard properties
    for prop_name, prop_info in STANDARD_PROPERTIES.items():
        if prop_name == 'smiles':
            continue  # Already handled above
            
        display_name = prop_info['display_name'].lower()
        if display_name in lowercase_columns:
            suggestions[lowercase_columns[display_name]] = prop_name
            continue
            
        # Try to match with column name
        if prop_name in lowercase_columns:
            suggestions[lowercase_columns[prop_name]] = prop_name
            continue
    
    # For columns with numeric data, suggest property types based on content analysis
    for col in df.columns:
        if col in suggestions.keys():
            continue  # Skip already mapped columns
            
        # Check if column contains numeric data
        if pd.api.types.is_numeric_dtype(df[col]):
            # Column could be molecular weight, logP, etc.
            # Make suggestions based on column name patterns
            col_lower = col.lower()
            
            if any(term in col_lower for term in ['weight', 'mw']):
                suggestions[col] = 'molecular_weight'
            elif any(term in col_lower for term in ['logp', 'log_p', 'log p']):
                suggestions[col] = 'logp'
            elif any(term in col_lower for term in ['solubility', 'sol']):
                suggestions[col] = 'solubility'
            elif any(term in col_lower for term in ['tpsa', 'polar surface', 'surface area']):
                suggestions[col] = 'tpsa'
            elif any(term in col_lower for term in ['mp', 'melting', 'melting point']):
                suggestions[col] = 'melting_point'
            elif any(term in col_lower for term in ['ic50', 'ic_50', 'ic 50']):
                suggestions[col] = 'ic50'
            elif any(term in col_lower for term in ['ec50', 'ec_50', 'ec 50']):
                suggestions[col] = 'ec50'
    
    return suggestions


def validate_csv_data(df: pd.DataFrame, column_mapping: Dict[str, str]) -> Tuple[bool, List[Dict[str, Any]]]:
    """
    Validate the content of CSV data, especially SMILES strings.
    
    Args:
        df: DataFrame containing CSV data
        column_mapping: Dictionary mapping CSV column names to system property names
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    smiles_column = None
    
    # Find the CSV column mapped to SMILES
    for csv_col, prop_name in column_mapping.items():
        if prop_name == 'smiles':
            smiles_column = csv_col
            break
    
    if not smiles_column:
        return False, [{"row": None, "message": CSV_ERRORS["MISSING_SMILES_COLUMN"]}]
    
    # Validate SMILES strings
    for idx, row in df.iterrows():
        smiles = row[smiles_column]
        
        # Skip NaN/None values
        if pd.isna(smiles):
            errors.append({
                "row": idx,
                "col": smiles_column,
                "message": MOLECULE_ERRORS["INVALID_SMILES"],
                "value": None
            })
            continue
        
        # Validate SMILES
        if not validate_smiles(str(smiles)):
            errors.append({
                "row": idx,
                "col": smiles_column,
                "message": MOLECULE_ERRORS["INVALID_SMILES"],
                "value": smiles
            })
    
    # Validate other properties based on their expected types
    for csv_col, prop_name in column_mapping.items():
        if prop_name == 'smiles':
            continue  # Already validated above
            
        # Get property type if it's a standard property
        prop_type = None
        if prop_name in STANDARD_PROPERTIES:
            prop_type = STANDARD_PROPERTIES[prop_name]['property_type']
        
        # Custom properties are assumed to be strings if not otherwise specified
        if not prop_type and prop_name.startswith('custom_'):
            continue
        
        # Skip properties with unknown types
        if not prop_type:
            continue
            
        # Validate property values
        for idx, row in df.iterrows():
            value = row[csv_col]
            
            # Skip NaN/None values
            if pd.isna(value):
                continue
                
            try:
                validate_property_value(value, prop_name, prop_type, raise_exception=True)
            except Exception as e:
                errors.append({
                    "row": idx,
                    "col": csv_col,
                    "message": str(e),
                    "value": value
                })
    
    return len(errors) == 0, errors


def get_csv_preview(file_path: str, num_rows: int = DEFAULT_PREVIEW_ROWS) -> Dict[str, Any]:
    """
    Get a preview of CSV data for display in the UI.
    
    Args:
        file_path: Path to the CSV file
        num_rows: Number of preview rows to return
        
    Returns:
        Dictionary containing headers and preview rows
    """
    try:
        # Read a limited number of rows
        df = pd.read_csv(file_path, nrows=num_rows)
        
        # Extract headers
        headers = list(df.columns)
        
        # Convert to list of dictionaries for easy JSON serialization
        rows = df.fillna('').to_dict(orient='records')
        
        return {
            "headers": headers,
            "rows": rows,
            "total_rows": len(pd.read_csv(file_path, usecols=[0])),  # Estimate total rows efficiently
            "preview_rows": len(rows)
        }
    except Exception as e:
        raise CSVException(
            message=CSV_ERRORS["PARSING_ERROR"],
            file_name=os.path.basename(file_path),
            details={"error": str(e)}
        )


def process_csv_in_chunks(
    file_path: str,
    column_mapping: Dict[str, str],
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    process_function: Callable[[pd.DataFrame], Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Process large CSV files in chunks to manage memory usage.
    
    Args:
        file_path: Path to the CSV file
        column_mapping: Dictionary mapping CSV column names to system property names
        chunk_size: Number of rows to process in each chunk
        process_function: Function to process each valid chunk
        
    Returns:
        Dictionary with processing results and statistics
    """
    processed_rows = 0
    successful_rows = 0
    errors = []
    results = []
    
    try:
        # Check file size
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if file_size_mb > MAX_FILE_SIZE_MB:
            raise CSVException(
                message=CSV_ERRORS["FILE_TOO_LARGE"],
                file_name=os.path.basename(file_path),
                details={"size_mb": file_size_mb, "max_size_mb": MAX_FILE_SIZE_MB}
            )
        
        # Create CSV reader with chunking
        csv_reader = pd.read_csv(file_path, chunksize=chunk_size)
        
        for chunk_idx, chunk in enumerate(csv_reader):
            try:
                # Apply column mapping
                mapped_chunk = map_csv_columns(chunk, column_mapping)
                
                # Validate chunk data
                is_valid, chunk_errors = validate_csv_data(mapped_chunk, column_mapping)
                
                # Add errors with chunk information
                for error in chunk_errors:
                    # Adjust row index to account for chunking
                    if 'row' in error and error['row'] is not None:
                        error['row'] = chunk_idx * chunk_size + error['row']
                    errors.append(error)
                
                # Process valid rows
                valid_rows = len(mapped_chunk) - len(chunk_errors)
                successful_rows += valid_rows
                
                # Call process function with valid data if there are any valid rows
                if valid_rows > 0:
                    # Filter out rows with errors if needed
                    if chunk_errors:
                        error_indices = [e['row'] for e in chunk_errors if 'row' in e and e['row'] is not None]
                        valid_chunk = mapped_chunk.drop(index=error_indices)
                    else:
                        valid_chunk = mapped_chunk
                    
                    # Process the valid chunk
                    chunk_result = process_function(valid_chunk)
                    results.append(chunk_result)
                
                # Update processed rows count
                processed_rows += len(chunk)
                
            except Exception as e:
                errors.append({
                    "chunk": chunk_idx,
                    "message": str(e),
                    "rows": f"{chunk_idx * chunk_size}-{(chunk_idx + 1) * chunk_size - 1}"
                })
        
        # Combine results and return summary
        return {
            "total_rows": processed_rows,
            "successful_rows": successful_rows,
            "error_count": len(errors),
            "errors": errors,
            "results": results
        }
        
    except Exception as e:
        raise CSVException(
            message=CSV_ERRORS["PARSING_ERROR"],
            file_name=os.path.basename(file_path),
            details={"error": str(e)}
        )


class CSVProcessor:
    """
    Class for handling CSV file processing with validation and mapping.
    """
    
    def __init__(self, file_path: str):
        """
        Initialize the CSV processor.
        
        Args:
            file_path: Path to the CSV file
        """
        self._file_path = file_path
        self._df = None
        self._column_mapping = {}
        self._invalid_rows = []
        self._summary = {}
        self._processed = False
    
    def load_csv(self) -> bool:
        """
        Load CSV file into memory with basic validation.
        
        Returns:
            True if loading was successful
        
        Raises:
            CSVException: If CSV validation fails
        """
        try:
            self._df = parse_csv_file(self._file_path, validate_data=False)
            return True
        except Exception as e:
            raise e
    
    def set_column_mapping(self, column_mapping: Dict[str, str]) -> bool:
        """
        Set the column mapping for CSV processing.
        
        Args:
            column_mapping: Dictionary mapping CSV column names to system property names
            
        Returns:
            True if mapping is valid
            
        Raises:
            CSVException: If mapping validation fails
        """
        if self._df is None:
            raise CSVException(
                message="CSV file not loaded",
                file_name=os.path.basename(self._file_path)
            )
        
        # Validate mapping
        missing_columns = [col for col in column_mapping.keys() if col not in self._df.columns]
        if missing_columns:
            raise CSVException(
                message=CSV_ERRORS["INVALID_COLUMN_MAPPING"],
                file_name=os.path.basename(self._file_path),
                details={"missing_columns": missing_columns}
            )
        
        # Validate SMILES column is mapped
        if 'smiles' not in column_mapping.values():
            raise CSVException(
                message=CSV_ERRORS["MISSING_SMILES_COLUMN"],
                file_name=os.path.basename(self._file_path)
            )
        
        self._column_mapping = column_mapping
        return True
    
    def get_mapping_suggestions(self) -> Dict[str, str]:
        """
        Generate suggested column mappings based on column names and content.
        
        Returns:
            Dictionary mapping CSV columns to suggested system properties
            
        Raises:
            CSVException: If CSV file not loaded
        """
        if self._df is None:
            raise CSVException(
                message="CSV file not loaded",
                file_name=os.path.basename(self._file_path)
            )
        
        return get_column_mapping_suggestions(self._df)
    
    def process(self, validate_data: bool = True) -> bool:
        """
        Process the CSV file using the provided column mapping.
        
        Args:
            validate_data: Whether to validate SMILES and other properties
            
        Returns:
            True if processing was successful
            
        Raises:
            CSVException: If processing fails
        """
        if self._df is None:
            raise CSVException(
                message="CSV file not loaded",
                file_name=os.path.basename(self._file_path)
            )
        
        if not self._column_mapping:
            raise CSVException(
                message=CSV_ERRORS["COLUMN_MAPPING_REQUIRED"],
                file_name=os.path.basename(self._file_path)
            )
        
        # Apply column mapping
        try:
            mapped_df = map_csv_columns(self._df, self._column_mapping)
            self._df = mapped_df
        except CSVException as e:
            raise e
        
        # Validate data if required
        if validate_data:
            is_valid, errors = validate_csv_data(self._df, self._column_mapping)
            self._invalid_rows = errors
            
            # Calculate processing summary
            total_rows = len(self._df)
            invalid_rows = len(self._invalid_rows)
            valid_rows = total_rows - invalid_rows
            
            self._summary = {
                "total_rows": total_rows,
                "valid_rows": valid_rows,
                "invalid_rows": invalid_rows,
                "invalid_percentage": (invalid_rows / total_rows) * 100 if total_rows > 0 else 0,
                "mapped_columns": len(self._column_mapping)
            }
        
        self._processed = True
        return True
    
    def get_invalid_rows(self) -> List[Dict[str, Any]]:
        """
        Get list of invalid rows with error details.
        
        Returns:
            List of invalid rows with error information
            
        Raises:
            CSVException: If CSV not processed yet
        """
        if not self._processed:
            raise CSVException(
                message="CSV not processed yet",
                file_name=os.path.basename(self._file_path)
            )
        
        return self._invalid_rows
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary of CSV processing results.
        
        Returns:
            Summary statistics of processing results
            
        Raises:
            CSVException: If CSV not processed yet
        """
        if not self._processed:
            raise CSVException(
                message="CSV not processed yet",
                file_name=os.path.basename(self._file_path)
            )
        
        return self._summary
    
    def get_preview(self, num_rows: int = DEFAULT_PREVIEW_ROWS) -> Dict[str, Any]:
        """
        Get a preview of the CSV data.
        
        Args:
            num_rows: Number of preview rows to return
            
        Returns:
            Preview data including headers and sample rows
            
        Raises:
            CSVException: If CSV not loaded
        """
        if self._df is None:
            raise CSVException(
                message="CSV file not loaded",
                file_name=os.path.basename(self._file_path)
            )
        
        preview_df = self._df.head(num_rows)
        
        return {
            "headers": list(preview_df.columns),
            "rows": preview_df.fillna('').to_dict(orient='records'),
            "total_rows": len(self._df),
            "preview_rows": len(preview_df)
        }
    
    def get_processed_data(self) -> pd.DataFrame:
        """
        Get the processed DataFrame with mapped columns.
        
        Returns:
            Processed DataFrame
            
        Raises:
            CSVException: If CSV not processed yet
        """
        if not self._processed:
            raise CSVException(
                message="CSV not processed yet",
                file_name=os.path.basename(self._file_path)
            )
        
        return self._df
    
    def get_valid_molecules(self) -> pd.DataFrame:
        """
        Get only the valid molecule rows as a DataFrame.
        
        Returns:
            DataFrame with only valid molecules
            
        Raises:
            CSVException: If CSV not processed yet
        """
        if not self._processed:
            raise CSVException(
                message="CSV not processed yet",
                file_name=os.path.basename(self._file_path)
            )
        
        if not self._invalid_rows:
            return self._df
        
        # Get indices of invalid rows
        invalid_indices = [error['row'] for error in self._invalid_rows 
                           if 'row' in error and error['row'] is not None]
        
        # Filter out invalid rows
        valid_df = self._df.drop(index=invalid_indices)
        
        return valid_df