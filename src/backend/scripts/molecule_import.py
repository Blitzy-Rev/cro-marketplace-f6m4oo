"""
Command-line script for importing molecular data from CSV files into the Molecular Data Management platform.
This script provides a standalone utility for batch importing molecules outside of the web application context, with options for library assignment, property mapping, and validation.
"""

import argparse  # standard library
import sys  # standard library
import os  # standard library
import logging  # standard library
import json  # standard library
import uuid  # standard library
from typing import Dict, List, Optional, Any  # standard library

# Internal imports
from ..app.utils.csv_parser import CSVProcessor  # version: check in src/backend/app/utils/csv_parser.py
from ..app.services.molecule_service import molecule_service  # version: check in src/backend/app/services/molecule_service.py
from ..app.services.library_service import library_service  # version: check in src/backend/app/services/library_service.py
from ..app.db.session import get_db  # version: check in src/backend/app/db/session.py
from ..app.core.exceptions import CSVException, MoleculeException, LibraryException  # version: check in src/backend/app/core/exceptions.py
from ..app.constants.molecule_properties import STANDARD_PROPERTIES  # version: check in src/backend/app/constants/molecule_properties.py
from ..app.constants.molecule_properties import PREDICTABLE_PROPERTIES  # version: check in src/backend/app/constants/molecule_properties.py

# Initialize logger
logger = logging.getLogger(__name__)


def setup_logging(verbose: bool) -> None:
    """Configure logging for the script

    Args:
        verbose: If True, set logging level to DEBUG, otherwise INFO
    """
    # Configure logging format with timestamp, level, and message
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO, format=log_format)

    # Add console handler to logger
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(log_format))
    logger.addHandler(console_handler)


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments for the script

    Returns:
        argparse.Namespace: Parsed command-line arguments
    """
    # Create ArgumentParser with description
    parser = argparse.ArgumentParser(description='Import molecular data from a CSV file into the Molecular Data Management platform.')

    # Add argument for CSV file path (required)
    parser.add_argument('csv_file', type=str, help='Path to the CSV file containing molecular data')

    # Add argument for column mapping file path (optional)
    parser.add_argument('--mapping_file', type=str, help='Path to a JSON file containing column mappings')

    # Add argument for library ID to add molecules to (optional)
    parser.add_argument('--library_id', type=str, help='UUID of the library to add the imported molecules to')

    # Add argument for user ID who is importing the molecules (required)
    parser.add_argument('--user_id', type=str, required=True, help='UUID of the user performing the import')

    # Add argument for output file to save results (optional)
    parser.add_argument('--output_file', type=str, help='Path to a file to save the import results as JSON')

    # Add flag for AI prediction of properties
    parser.add_argument('--predict_properties', action='store_true', help='Request AI prediction of properties after import')

    # Add flag for verbose logging
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging (DEBUG level)')

    # Add flag for dry run (validate only, don't import)
    parser.add_argument('--dry_run', action='store_true', help='Perform a dry run (validate only, do not import)')

    # Parse and return arguments
    return parser.parse_args()


def load_column_mapping(mapping_file: Optional[str], csv_processor: CSVProcessor) -> Dict[str, str]:
    """Load column mapping from a JSON file or generate suggestions

    Args:
        mapping_file: Path to the JSON file containing column mappings
        csv_processor: CSVProcessor instance

    Returns:
        Dict[str, str]: Column mapping dictionary
    """
    if mapping_file:
        # Load JSON from file
        try:
            with open(mapping_file, 'r') as f:
                column_mapping = json.load(f)
        except FileNotFoundError:
            logger.error(f"Mapping file not found: {mapping_file}")
            raise
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in mapping file: {mapping_file}")
            raise
    else:
        # Get mapping suggestions from csv_processor
        column_mapping = csv_processor.get_mapping_suggestions()

    # Log the mapping being used
    logger.info(f"Using column mapping: {column_mapping}")

    # Return the column mapping dictionary
    return column_mapping


def save_results(results: Dict[str, Any], output_file: str) -> bool:
    """Save import results to a JSON file

    Args:
        results: Dictionary containing import results
        output_file: Path to the output file

    Returns:
        bool: True if saved successfully, False otherwise
    """
    try:
        # Open output_file for writing
        with open(output_file, 'w') as f:
            # Serialize results to JSON with pretty formatting
            json.dump(results, f, indent=4)

        # Log success message
        logger.info(f"Import results saved to: {output_file}")
        return True
    except Exception as e:
        logger.error(f"Error saving results to file: {e}")
        return False


def main() -> int:
    """Main function to run the molecule import script

    Returns:
        int: Exit code (0 for success, non-zero for error)
    """
    # Parse command-line arguments
    args = parse_arguments()

    # Setup logging based on verbose flag
    setup_logging(args.verbose)

    # Log script start with arguments
    logger.info(f"Starting molecule import script with arguments: {args}")

    try:
        # Create database session
        db = next(get_db())

        # Create CSVProcessor instance and load CSV file
        csv_processor = CSVProcessor(args.csv_file)
        csv_processor.load_csv()

        # Load column mapping from file or generate suggestions
        column_mapping = load_column_mapping(args.mapping_file, csv_processor)

        # Set column mapping for CSV processing
        csv_processor.set_column_mapping(column_mapping)

        # Process CSV data with validation
        csv_processor.process()

        # If dry run, log validation results and exit
        if args.dry_run:
            summary = csv_processor.get_summary()
            logger.info(f"Dry run completed. Validation summary: {summary}")
            return 0

        # Process CSV file using molecule_service
        import_results = molecule_service.process_csv_file(
            file_path=args.csv_file,
            column_mapping=column_mapping,
            created_by=uuid.UUID(args.user_id),
            db=db
        )

        # If library_id provided, add molecules to library
        if args.library_id:
            library_id = uuid.UUID(args.library_id)
            molecule_ids = [molecule.id for molecule in import_results['created']]
            molecule_service.add_to_library(
                library_id=library_id,
                molecule_ids=molecule_ids,
                added_by=uuid.UUID(args.user_id),
                db=db
            )

        # If predict_properties flag set, request AI predictions
        if args.predict_properties:
            molecule_ids = [molecule.id for molecule in import_results['created']]
            molecule_service.batch_predict_properties(
                molecule_ids=molecule_ids,
                properties=PREDICTABLE_PROPERTIES,
                db=db
            )

        # If output_file provided, save results to file
        if args.output_file:
            save_results(import_results, args.output_file)

        # Log import summary statistics
        logger.info(f"Import completed. Summary: {import_results}")
        return 0

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except CSVException as e:
        logger.error(f"CSV processing error: {e}")
        return 1
    except MoleculeException as e:
        logger.error(f"Molecule error: {e}")
        return 1
    except LibraryException as e:
        logger.error(f"Library error: {e}")
        return 1
    except AIEngineException as e:
        logger.error(f"AI Engine error: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Value error: {e}")
        return 1
    except Exception as e:
        logger.exception(f"An unexpected error occurred: {e}")
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())