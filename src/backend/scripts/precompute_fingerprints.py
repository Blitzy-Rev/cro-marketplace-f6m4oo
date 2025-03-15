#!/usr/bin/env python3
"""
Fingerprint Precomputation Script

This script precomputes and stores molecular fingerprints for all molecules in the
database. This improves performance for similarity searches, clustering, and other
operations that rely on molecular fingerprints by avoiding on-the-fly generation.

Usage:
    python precompute_fingerprints.py [options]

Options:
    --fingerprint-types TYPE1,TYPE2  Fingerprint types to compute (default: morgan,maccs,rdkit)
    --batch-size SIZE                Number of molecules to process in each batch (default: 1000)
    --force                          Force recomputation of existing fingerprints
    --verbose                        Enable verbose logging
"""

import argparse
import logging
import sys
import time
import pickle
from uuid import uuid4

import sqlalchemy as sa
from tqdm import tqdm  # version: 4.64.0
import numpy as np  # version: 1.23.0

from ..app.db.session import db_session, engine
from ..app.models.molecule import Molecule
from ..app.utils.rdkit_utils import smiles_to_mol
from ..app.utils.chem_fingerprints import (
    FINGERPRINT_TYPES, 
    get_morgan_fingerprint,
    get_maccs_fingerprint,
    get_rdkit_fingerprint
)
from ..app.core.config import settings

# Configure logger
logger = logging.getLogger(__name__)

# Default fingerprint types if none specified
DEFAULT_FINGERPRINT_TYPES = ['morgan', 'maccs', 'rdkit']

# Default parameters for fingerprint generation
FINGERPRINT_PARAMETERS = {
    "morgan": {"radius": 2, "n_bits": 2048},
    "rdkit": {"min_path": 1, "max_path": 7, "n_bits": 2048}
}


def setup_logging():
    """Configure logging for the script."""
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )
    # Add console handler
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console.setFormatter(formatter)
    logger.addHandler(console)


def parse_arguments():
    """Parse command-line arguments for the script."""
    parser = argparse.ArgumentParser(
        description="Precompute and store molecular fingerprints for database molecules."
    )
    parser.add_argument(
        "--fingerprint-types",
        type=str,
        help=f"Comma-separated list of fingerprint types to compute. Available types: {', '.join(FINGERPRINT_TYPES.keys())}",
        default=",".join(DEFAULT_FINGERPRINT_TYPES)
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        help="Number of molecules to process in each batch",
        default=1000
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force recomputation of existing fingerprints"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    return parser.parse_args()


def create_fingerprint_table():
    """Create or verify the fingerprint table in the database."""
    try:
        # Check if table exists
        inspector = sa.inspect(engine)
        if inspector.has_table("molecule_fingerprint"):
            logger.info("Fingerprint table already exists")
            return
        
        # Create table if it doesn't exist
        metadata = sa.MetaData()
        fingerprint_table = sa.Table(
            "molecule_fingerprint",
            metadata,
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("molecule_id", sa.String(36), sa.ForeignKey("molecule.id"), nullable=False),
            sa.Column("fingerprint_type", sa.String(50), nullable=False),
            sa.Column("fingerprint_data", sa.LargeBinary, nullable=False),
            sa.Column("parameters", sa.JSON, nullable=True),
            sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
            sa.UniqueConstraint("molecule_id", "fingerprint_type", name="uq_molecule_fingerprint")
        )
        
        # Create indexes for efficient querying
        sa.Index("ix_molecule_fingerprint_molecule_id", fingerprint_table.c.molecule_id)
        sa.Index("ix_molecule_fingerprint_fingerprint_type", fingerprint_table.c.fingerprint_type)
        
        # Create the table
        metadata.create_all(engine)
        logger.info("Created fingerprint table")
    except Exception as e:
        logger.error(f"Error creating fingerprint table: {str(e)}")
        raise


def get_molecules_without_fingerprints(fingerprint_types, force=False):
    """Get molecules that don't have specified fingerprint types computed."""
    try:
        # If force recomputation, return all molecules with SMILES
        if force:
            with engine.connect() as conn:
                result = conn.execute(sa.text("""
                    SELECT id, smiles FROM molecule
                    WHERE smiles IS NOT NULL
                """))
                return [(str(row[0]), row[1]) for row in result]
        
        # Otherwise, find molecules that need at least one fingerprint type
        with engine.connect() as conn:
            molecules_to_process = []
            
            # Get all molecules with SMILES
            result = conn.execute(sa.text("""
                SELECT id, smiles FROM molecule
                WHERE smiles IS NOT NULL
            """))
            
            for row in result:
                mol_id = str(row[0])
                smiles = row[1]
                
                # Check if this molecule needs any fingerprint type
                for fp_type in fingerprint_types:
                    # See if this fingerprint exists
                    count_result = conn.execute(sa.text("""
                        SELECT COUNT(*) FROM molecule_fingerprint
                        WHERE molecule_id = :mol_id AND fingerprint_type = :fp_type
                    """), {"mol_id": mol_id, "fp_type": fp_type})
                    
                    count = count_result.scalar()
                    
                    if count == 0:
                        # This molecule needs this fingerprint type
                        molecules_to_process.append((mol_id, smiles))
                        break  # No need to check other fingerprint types
        
        return molecules_to_process
    except Exception as e:
        logger.error(f"Error getting molecules without fingerprints: {str(e)}")
        return []


def compute_and_store_fingerprint(molecule_id, smiles, fingerprint_type, parameters):
    """Compute and store a fingerprint for a molecule."""
    try:
        # Convert SMILES to RDKit molecule
        mol = smiles_to_mol(smiles)
        if mol is None:
            logger.warning(f"Failed to convert SMILES to molecule: {smiles}")
            return False
        
        # Generate fingerprint based on type
        if fingerprint_type == "morgan":
            fingerprint = get_morgan_fingerprint(
                mol, 
                radius=parameters.get("radius", 2),
                n_bits=parameters.get("n_bits", 2048)
            )
        elif fingerprint_type == "maccs":
            fingerprint = get_maccs_fingerprint(mol)
        elif fingerprint_type == "rdkit":
            fingerprint = get_rdkit_fingerprint(
                mol,
                min_path=parameters.get("min_path", 1),
                max_path=parameters.get("max_path", 7),
                n_bits=parameters.get("n_bits", 2048)
            )
        else:
            logger.warning(f"Unsupported fingerprint type: {fingerprint_type}")
            return False
        
        # Serialize fingerprint
        fingerprint_binary = pickle.dumps(fingerprint)
        
        # Store fingerprint in database
        fingerprint_id = str(uuid4())
        
        with engine.connect() as conn:
            # Check if this fingerprint already exists
            result = conn.execute(sa.text("""
                SELECT id FROM molecule_fingerprint
                WHERE molecule_id = :molecule_id AND fingerprint_type = :fingerprint_type
            """), {
                "molecule_id": molecule_id,
                "fingerprint_type": fingerprint_type
            })
            
            existing_id = next((row[0] for row in result), None)
            
            if existing_id:
                # Update existing fingerprint
                conn.execute(sa.text("""
                    UPDATE molecule_fingerprint
                    SET fingerprint_data = :fingerprint_data,
                        parameters = :parameters,
                        created_at = CURRENT_TIMESTAMP
                    WHERE id = :id
                """), {
                    "id": existing_id,
                    "fingerprint_data": fingerprint_binary,
                    "parameters": parameters
                })
            else:
                # Insert new fingerprint
                conn.execute(sa.text("""
                    INSERT INTO molecule_fingerprint
                    (id, molecule_id, fingerprint_type, fingerprint_data, parameters)
                    VALUES (:id, :molecule_id, :fingerprint_type, :fingerprint_data, :parameters)
                """), {
                    "id": fingerprint_id,
                    "molecule_id": molecule_id,
                    "fingerprint_type": fingerprint_type,
                    "fingerprint_data": fingerprint_binary,
                    "parameters": parameters
                })
            
            conn.commit()
        
        return True
    except Exception as e:
        logger.error(f"Error computing fingerprint for molecule {molecule_id}: {str(e)}")
        return False


def process_molecules_batch(molecules, fingerprint_types):
    """Process a batch of molecules to compute and store fingerprints."""
    success_count = 0
    error_count = 0
    
    for molecule_id, smiles in molecules:
        for fp_type in fingerprint_types:
            # Get parameters for fingerprint type
            parameters = FINGERPRINT_PARAMETERS.get(fp_type, {})
            
            # Compute and store fingerprint
            success = compute_and_store_fingerprint(molecule_id, smiles, fp_type, parameters)
            
            if success:
                success_count += 1
            else:
                error_count += 1
    
    return success_count, error_count


def main():
    """Main function to run the fingerprint precomputation script."""
    # Set up logging
    setup_logging()
    
    # Parse command-line arguments
    args = parse_arguments()
    
    # Set log level based on verbosity
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)
    
    # Parse fingerprint types
    fingerprint_types = [fp.strip() for fp in args.fingerprint_types.split(",")]
    
    # Validate fingerprint types
    valid_types = []
    for fp_type in fingerprint_types:
        if fp_type in FINGERPRINT_TYPES:
            valid_types.append(fp_type)
        else:
            logger.warning(f"Ignoring unsupported fingerprint type: {fp_type}")
    
    if not valid_types:
        logger.error("No valid fingerprint types specified")
        return 1
    
    # Log configuration
    logger.info(f"Computing fingerprint types: {', '.join(valid_types)}")
    logger.info(f"Batch size: {args.batch_size}")
    logger.info(f"Force recomputation: {args.force}")
    
    # Create fingerprint table if it doesn't exist
    create_fingerprint_table()
    
    # Get molecules without fingerprints
    start_time = time.time()
    molecules = get_molecules_without_fingerprints(valid_types, args.force)
    logger.info(f"Found {len(molecules)} molecules to process")
    
    # Process molecules in batches
    total_success = 0
    total_error = 0
    
    if not molecules:
        logger.info("No molecules to process")
        return 0
    
    # Split molecules into batches
    batches = [molecules[i:i + args.batch_size] for i in range(0, len(molecules), args.batch_size)]
    
    # Process batches with progress bar
    with tqdm(total=len(molecules) * len(valid_types), desc="Computing fingerprints") as pbar:
        for batch in batches:
            success, error = process_molecules_batch(batch, valid_types)
            total_success += success
            total_error += error
            pbar.update(len(batch) * len(valid_types))
    
    # Log results
    elapsed_time = time.time() - start_time
    logger.info(f"Fingerprint computation completed in {elapsed_time:.2f} seconds")
    logger.info(f"Successfully computed {total_success} fingerprints")
    logger.info(f"Failed to compute {total_error} fingerprints")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())