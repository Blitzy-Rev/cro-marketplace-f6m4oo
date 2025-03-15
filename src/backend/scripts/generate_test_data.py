#!/usr/bin/env python
"""
Test Data Generator

This script generates synthetic test data for the Molecular Data Management and CRO Integration Platform.
It creates users, molecules, libraries, CRO services, and submissions for development and testing purposes.
"""

import argparse
import logging
import random
import uuid
from datetime import datetime, timedelta
from tqdm import tqdm

# Internal imports
from ..app.db.session import db_session
from ..app.models.user import User
from ..app.models.molecule import Molecule
from ..app.models.library import Library
from ..app.models.cro_service import CROService, ServiceType
from ..app.models.submission import Submission
from ..app.constants.submission_status import SubmissionStatus
from ..app.constants.user_roles import (
    SYSTEM_ADMIN, PHARMA_ADMIN, PHARMA_SCIENTIST, CRO_ADMIN, CRO_TECHNICIAN
)
from ..app.utils.smiles import validate_smiles
from ..app.utils.rdkit_utils import calculate_basic_properties

# Set up logger
logger = logging.getLogger(__name__)

# Sample SMILES strings for test molecules
SAMPLE_SMILES = [
    "CC(C)CCO",  # isopentyl alcohol
    "c1ccccc1",  # benzene
    "CCN(CC)CC",  # triethylamine
    "CC(=O)OC1=CC=CC=C1C(=O)O",  # aspirin
    "CN1C=NC2=C1C(=O)N(C(=O)N2C)C",  # caffeine
    "C1=CC=C(C=C1)C(=O)O",  # benzoic acid
    "CC(C)CC1=CC=C(C=C1)C(C)C(=O)O",  # ibuprofen
    "CC1=C(C=C(C=C1)S(=O)(=O)N)CC(C(=O)O)N",  # sulfamethoxazole
    "CC(=O)OC1=CC=CC=C1C(=O)O",  # aspirin (duplicate)
    "CN1C=NC2=C1C(=O)N(C(=O)N2C)C"  # caffeine (duplicate)
]

# Default password for test users
DEFAULT_PASSWORD = "password123"


def setup_logging():
    """Configure logging for the script."""
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    console_handler = logging.StreamHandler()
    logger.addHandler(console_handler)
    logger.setLevel(logging.INFO)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Generate test data for the Molecular Data Management and CRO Integration Platform'
    )
    parser.add_argument('--users', type=int, default=10, help='Number of users to create')
    parser.add_argument('--molecules', type=int, default=100, help='Number of molecules to create')
    parser.add_argument('--libraries', type=int, default=5, help='Number of libraries to create')
    parser.add_argument('--services', type=int, default=3, help='Number of CRO services to create')
    parser.add_argument('--submissions', type=int, default=5, help='Number of submissions to create')
    parser.add_argument('--clean', action='store_true', help='Clean existing test data before generation')
    
    return parser.parse_args()


def clean_database():
    """Clean existing test data from the database."""
    try:
        # Delete submissions first (due to foreign key constraints)
        db_session.query(Submission).delete()
        
        # Delete libraries
        db_session.query(Library).delete()
        
        # Delete molecules
        db_session.query(Molecule).delete()
        
        # Delete CRO services
        db_session.query(CROService).delete()
        
        # Delete test users (keep any with 'real' in their email to preserve real users)
        db_session.query(User).filter(~User.email.contains('real')).delete()
        
        db_session.commit()
        logger.info("Database cleaned successfully")
    except Exception as e:
        db_session.rollback()
        logger.error(f"Error cleaning database: {e}")


def create_test_users(count):
    """Create test users with different roles."""
    users = []
    
    # Create one system admin
    system_admin = User(
        email="admin@example.com",
        full_name="System Administrator",
        role=SYSTEM_ADMIN,
        organization_name="System"
    )
    system_admin.set_password(DEFAULT_PASSWORD)
    users.append(system_admin)
    
    # Create one pharma admin
    pharma_admin = User(
        email="pharma_admin@example.com",
        full_name="Pharma Administrator",
        role=PHARMA_ADMIN,
        organization_name="PharmaCorp"
    )
    pharma_admin.set_password(DEFAULT_PASSWORD)
    users.append(pharma_admin)
    
    # Create pharma scientists
    scientist_count = max(1, count // 3)
    for i in range(scientist_count):
        scientist = User(
            email=f"scientist{i+1}@example.com",
            full_name=f"Scientist {i+1}",
            role=PHARMA_SCIENTIST,
            organization_name="PharmaCorp"
        )
        scientist.set_password(DEFAULT_PASSWORD)
        users.append(scientist)
    
    # Create one CRO admin
    cro_admin = User(
        email="cro_admin@example.com",
        full_name="CRO Administrator",
        role=CRO_ADMIN,
        organization_name="TestCRO Inc."
    )
    cro_admin.set_password(DEFAULT_PASSWORD)
    users.append(cro_admin)
    
    # Create CRO technicians
    tech_count = max(1, count // 3)
    for i in range(tech_count):
        technician = User(
            email=f"technician{i+1}@example.com",
            full_name=f"Technician {i+1}",
            role=CRO_TECHNICIAN,
            organization_name="TestCRO Inc."
        )
        technician.set_password(DEFAULT_PASSWORD)
        users.append(technician)
    
    # Add all users to the database
    db_session.add_all(users)
    db_session.commit()
    
    logger.info(f"Created {len(users)} test users")
    return users


def create_test_molecules(count, created_by):
    """Create test molecules with properties."""
    molecules = []
    
    # Use sample SMILES as a base
    available_smiles = [s for s in SAMPLE_SMILES if validate_smiles(s)]
    unique_smiles = list(set(available_smiles))  # Remove duplicates
    
    # If we need more molecules than we have unique samples,
    # we'll just reuse them with a suffix to make them unique
    all_smiles = []
    for i in range(count):
        base_smiles = unique_smiles[i % len(unique_smiles)]
        if i < len(unique_smiles):
            all_smiles.append(base_smiles)
        else:
            # Add a suffix to make it unique (in a real scenario, we would generate valid SMILES)
            # For test data, we'll just append a character that should still validate
            modified = f"{base_smiles}C"  # Append a carbon atom
            if validate_smiles(modified):
                all_smiles.append(modified)
            else:
                all_smiles.append(base_smiles)  # Fallback to original if modified is invalid
    
    # Create molecules in batches
    batch_size = 50
    for i in range(0, len(all_smiles), batch_size):
        batch = []
        batch_smiles = all_smiles[i:i+batch_size]
        
        for smiles in tqdm(batch_smiles, desc=f"Creating molecules (batch {i//batch_size + 1})"):
            try:
                # Create molecule from SMILES
                molecule = Molecule.from_smiles(smiles, created_by.id)
                batch.append(molecule)
                molecules.append(molecule)
            except Exception as e:
                logger.warning(f"Error creating molecule with SMILES {smiles}: {e}")
                continue
        
        # Add batch to database
        if batch:
            db_session.add_all(batch)
            db_session.commit()
    
    logger.info(f"Created {len(molecules)} test molecules")
    return molecules


def create_test_libraries(count, users, molecules):
    """Create test molecule libraries."""
    libraries = []
    
    # Get pharma users
    pharma_users = [u for u in users if u.role in (PHARMA_ADMIN, PHARMA_SCIENTIST)]
    if not pharma_users:
        logger.warning("No pharma users found to create libraries")
        return []
    
    # Create libraries
    for i in range(count):
        # Select a random pharma user as owner
        owner = random.choice(pharma_users)
        
        # Create library
        library = Library(
            name=f"Test Library {i+1}",
            description=f"A test library with random molecules #{i+1}",
            owner_id=owner.id,
            organization_id=None  # No organization for test data
        )
        
        # Add to database
        db_session.add(library)
        db_session.flush()  # Get library ID without committing
        
        # Add random molecules to the library
        molecule_count = min(len(molecules), random.randint(5, 20))
        library_molecules = random.sample(molecules, molecule_count)
        
        for molecule in library_molecules:
            library.add_molecule(molecule, owner.id)
        
        libraries.append(library)
    
    # Commit all changes
    db_session.commit()
    
    logger.info(f"Created {len(libraries)} test libraries")
    return libraries


def create_test_cro_services(count):
    """Create test CRO services."""
    services = []
    
    # Create services with different service types
    service_types = list(ServiceType)
    
    for i in range(count):
        # Select a service type, cycling through available types
        service_type = service_types[i % len(service_types)]
        
        # Set random price and turnaround time
        base_price = round(random.uniform(500, 5000), 2)
        turnaround_days = random.randint(5, 30)
        
        # Create service
        service = CROService.create(
            name=f"{service_type.name} Service {i+1}",
            provider="TestCRO Inc.",
            service_type=service_type,
            base_price=base_price,
            typical_turnaround_days=turnaround_days,
            description=f"Test {service_type.name.lower()} service for testing molecules",
            price_currency="USD",
            specifications={
                "assay_type": service_type.name.lower().replace('_', ' '),
                "min_quantity": "10mg",
                "preferred_concentration": "10µM"
            }
        )
        
        services.append(service)
    
    # Add to database
    db_session.add_all(services)
    db_session.commit()
    
    logger.info(f"Created {len(services)} test CRO services")
    return services


def create_test_submissions(count, users, molecules, services):
    """Create test CRO submissions."""
    submissions = []
    
    # Get pharma users
    pharma_users = [u for u in users if u.role in (PHARMA_ADMIN, PHARMA_SCIENTIST)]
    if not pharma_users:
        logger.warning("No pharma users found to create submissions")
        return []
    
    # Get CRO services
    if not services:
        logger.warning("No CRO services found to create submissions")
        return []
    
    # Create submissions
    for i in range(count):
        # Select a random pharma user as creator
        creator = random.choice(pharma_users)
        
        # Select a random CRO service
        service = random.choice(services)
        
        # Create submission
        submission = Submission.create(
            name=f"Test Submission {i+1}",
            created_by=creator.id,
            cro_service_id=service.id,
            description=f"Test submission #{i+1} for {service.name}"
        )
        
        # Add to database to get an ID
        db_session.add(submission)
        db_session.flush()
        
        # Add random molecules
        molecule_count = min(len(molecules), random.randint(3, 10))
        submission_molecules = random.sample(molecules, molecule_count)
        
        for molecule in submission_molecules:
            submission.add_molecule(molecule.id)
        
        # Set random status
        status_options = [
            SubmissionStatus.DRAFT.value,
            SubmissionStatus.SUBMITTED.value,
            SubmissionStatus.PENDING_REVIEW.value,
            SubmissionStatus.PRICING_PROVIDED.value,
            SubmissionStatus.APPROVED.value,
            SubmissionStatus.IN_PROGRESS.value
        ]
        random_status = random.choice(status_options)
        submission.update_status(random_status)
        
        # Add pricing if in appropriate status
        if random_status in [SubmissionStatus.PRICING_PROVIDED.value, SubmissionStatus.APPROVED.value, SubmissionStatus.IN_PROGRESS.value]:
            # Set random price based on service base price and number of molecules
            price = round(service.base_price * (1 + (molecule_count * 0.1)), 2)
            submission.set_pricing(price, "USD", service.typical_turnaround_days)
        
        submissions.append(submission)
    
    # Commit changes
    db_session.commit()
    
    logger.info(f"Created {len(submissions)} test submissions")
    return submissions


def main():
    """Main function to generate test data."""
    # Set up logging
    setup_logging()
    
    # Parse arguments
    args = parse_args()
    
    # Clean database if requested
    if args.clean:
        clean_database()
    
    # Create test users
    users = create_test_users(args.users)
    
    # Get a pharma admin for creating molecules
    pharma_admin = next((u for u in users if u.role == PHARMA_ADMIN), None)
    if not pharma_admin:
        pharma_admin = users[0]  # Fallback to first user
    
    # Create test molecules
    molecules = create_test_molecules(args.molecules, pharma_admin)
    
    # Create test libraries
    libraries = create_test_libraries(args.libraries, users, molecules)
    
    # Create test CRO services
    services = create_test_cro_services(args.services)
    
    # Create test submissions
    submissions = create_test_submissions(args.submissions, users, molecules, services)
    
    logger.info("Test data generation complete")
    return 0


if __name__ == "__main__":
    exit(main())