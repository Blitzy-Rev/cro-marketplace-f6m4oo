"""
Command-line script for seeding the database with initial data for the Molecular Data Management and CRO Integration Platform.
This script populates the database with essential reference data, sample molecules, libraries, and user accounts
for development and testing purposes.
"""

import argparse  # argparse - standard library
import logging  # logging - standard library
import sys  # sys - standard library
import os  # os - standard library
import uuid  # uuid - standard library
import datetime  # datetime - standard library
import random  # random - standard library
import csv  # csv - standard library

# Internal imports
from ..app.db.base import Base  # src/backend/app/db/base.py
from ..app.db.session import engine, db_session  # src/backend/app/db/session.py
from ..app.db.init_db import init_db, seed_db  # src/backend/app/db/init_db.py
from ..app.models.user import User  # src/backend/app/models/user.py
from ..app.models.molecule import Molecule, MoleculeProperty  # src/backend/app/models/molecule.py
from ..app.models.library import Library  # src/backend/app/models/library.py
from ..app.models.cro_service import CROService, ServiceType  # src/backend/app/models/cro_service.py
from ..app.utils.smiles import validate_smiles, get_inchi_key_from_smiles, get_molecular_formula_from_smiles  # src/backend/app/utils/smiles.py
from ..app.core.config import settings  # src/backend/app/core/config.py
from ..app.constants.user_roles import PHARMA_ADMIN, PHARMA_SCIENTIST, CRO_ADMIN, CRO_TECHNICIAN  # src/backend/app/constants/user_roles.py

# Configure logging
logger = logging.getLogger(__name__)

# Sample data
SAMPLE_SMILES = ["CC(C)CCO", "c1ccccc1", "CCN(CC)CC", "CC(=O)OC1=CC=CC=C1C(=O)O",
                 "C1=CC=C(C=C1)C(=O)O", "C1=CC=C2C(=C1)C=CC=C2", "C1=CN=CC=C1", "C1CCCCC1",
                 "CC(C)(C)C", "CCO"]

SAMPLE_USERS = [
    {'email': 'pharma_admin@example.com', 'full_name': 'Pharma Admin', 'password': 'password123', 'role': PHARMA_ADMIN, 'organization_name': 'PharmaCo'},
    {'email': 'scientist@example.com', 'full_name': 'Pharma Scientist', 'password': 'password123', 'role': PHARMA_SCIENTIST, 'organization_name': 'PharmaCo'},
    {'email': 'cro_admin@example.com', 'full_name': 'CRO Admin', 'password': 'password123', 'role': CRO_ADMIN, 'organization_name': 'BioCRO Inc.'},
    {'email': 'technician@example.com', 'full_name': 'CRO Technician', 'password': 'password123', 'role': CRO_TECHNICIAN, 'organization_name': 'BioCRO Inc.'}
]

SAMPLE_LIBRARIES = [
    {'name': 'High Potency Candidates', 'description': 'Molecules with high binding affinity'},
    {'name': 'Series A', 'description': 'First series of synthesized compounds'},
    {'name': 'Series B', 'description': 'Second series of synthesized compounds'},
    {'name': 'Fragments', 'description': 'Fragment-based screening compounds'},
    {'name': 'Leads', 'description': 'Lead compounds for further optimization'},
    {'name': 'Discarded', 'description': 'Compounds that failed initial screening'}
]


def setup_logging():
    """Configure logging for the script"""
    # Configure logging format
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_format)

    # Add console handler for log output
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(log_format))
    logger.addHandler(console_handler)


def parse_args():
    """Parse command-line arguments"""
    # Create ArgumentParser with description
    parser = argparse.ArgumentParser(description='Seed the database with initial data')

    # Add --reset flag to drop and recreate all tables
    parser.add_argument('--reset', action='store_true', help='Drop and recreate all tables')

    # Add --sample-data flag to include sample data
    parser.add_argument('--sample-data', action='store_true', help='Include sample data')

    # Add --sample-size argument to specify number of sample molecules
    parser.add_argument('--sample-size', type=int, default=10, help='Number of sample molecules to create')

    # Parse and return command-line arguments
    return parser.parse_args()


def reset_database():
    """Drop all tables and recreate the database schema"""
    # Log database reset operation
    logger.info("Resetting database: dropping all tables")

    # Drop all tables using Base.metadata.drop_all(engine)
    Base.metadata.drop_all(engine)

    # Create all tables using Base.metadata.create_all(engine)
    Base.metadata.create_all(engine)

    # Log successful database reset
    logger.info("Database reset completed successfully")


def create_sample_users():
    """Create sample user accounts for testing"""
    # Log creation of sample users
    logger.info("Creating sample users")

    # Initialize empty dictionary to store users
    users = {}

    # Iterate through SAMPLE_USERS list
    for user_data in SAMPLE_USERS:
        # For each user, check if user with email already exists
        existing_user = db_session.query(User).filter(User.email == user_data['email']).first()

        # If user doesn't exist, create new User object with provided details
        if not existing_user:
            new_user = User(
                email=user_data['email'],
                full_name=user_data['full_name'],
                role=user_data['role'],
                organization_name=user_data['organization_name']
            )

            # Set password using set_password method
            new_user.set_password(user_data['password'])

            # Add user to session and commit
            db_session.add(new_user)
            db_session.commit()

            # Add user to users dictionary with email as key
            users[new_user.email] = new_user

            # Log successful user creation
            logger.info(f"Created user: {new_user.email}")
        else:
            users[existing_user.email] = existing_user
            logger.info(f"User already exists: {existing_user.email}")

    # Return dictionary of created users
    return users


def create_sample_libraries(users):
    """Create sample molecule libraries for testing"""
    # Log creation of sample libraries
    logger.info("Creating sample libraries")

    # Initialize empty dictionary to store libraries
    libraries = {}

    # Get pharma admin user from users dictionary
    pharma_admin = users.get('pharma_admin@example.com')

    # Iterate through SAMPLE_LIBRARIES list
    for library_data in SAMPLE_LIBRARIES:
        # For each library, check if library with name already exists
        existing_library = db_session.query(Library).filter(Library.name == library_data['name']).first()

        # If library doesn't exist, create new Library object with provided details
        if not existing_library:
            new_library = Library(
                name=library_data['name'],
                description=library_data['description'],
                owner_id=pharma_admin.id
            )

            # Add library to session and commit
            db_session.add(new_library)
            db_session.commit()

            # Add library to libraries dictionary with name as key
            libraries[new_library.name] = new_library

            # Log successful library creation
            logger.info(f"Created library: {new_library.name}")
        else:
            libraries[existing_library.name] = existing_library
            logger.info(f"Library already exists: {existing_library.name}")

    # Return dictionary of created libraries
    return libraries


def create_sample_molecules(users, libraries, sample_size):
    """Create sample molecules and properties for testing"""
    # Log creation of sample molecules
    logger.info("Creating sample molecules")

    # Initialize empty list to store molecules
    molecules = []

    # Get pharma scientist user from users dictionary
    pharma_scientist = users.get('scientist@example.com')

    # Determine number of molecules to create (min of sample_size and len(SAMPLE_SMILES))
    count = min(sample_size, len(SAMPLE_SMILES))

    # Iterate through SAMPLE_SMILES up to count
    for i in range(count):
        smiles = SAMPLE_SMILES[i]

        # Validate using validate_smiles function
        if validate_smiles(smiles):
            # Generate InChI key using get_inchi_key_from_smiles
            inchi_key = get_inchi_key_from_smiles(smiles)

            # Check if molecule with InChI key already exists
            existing_molecule = db_session.query(Molecule).filter(Molecule.inchi_key == inchi_key).first()

            # If molecule doesn't exist, create new Molecule object
            if not existing_molecule:
                new_molecule = Molecule(
                    smiles=smiles,
                    inchi_key=inchi_key,
                    formula=get_molecular_formula_from_smiles(smiles),
                    molecular_weight=random.uniform(50, 500),
                    created_by=pharma_scientist.id
                )

                # Add molecule to session
                db_session.add(new_molecule)

                # Create MoleculeProperty objects for LogP, solubility, etc.
                logp = MoleculeProperty(molecule_id=new_molecule.id, name='LogP', value=random.uniform(-5, 5), source='calculated')
                solubility = MoleculeProperty(molecule_id=new_molecule.id, name='Solubility', value=random.uniform(0.1, 10), source='calculated')
                db_session.add_all([logp, solubility])

                # Randomly assign molecule to libraries
                for library_name in libraries:
                    if random.random() < 0.3:  # 30% chance of being in each library
                        libraries[library_name].molecules.append(new_molecule)

                # Commit session after each molecule
                db_session.commit()

                # Add molecule to molecules list
                molecules.append(new_molecule)

                # Log successful molecule creation
                logger.info(f"Created molecule: {smiles}")
            else:
                molecules.append(existing_molecule)
                logger.info(f"Molecule already exists: {smiles}")
        else:
            logger.warning(f"Invalid SMILES: {smiles}")

    # Return list of created molecules
    return molecules


def main():
    """Main function to execute the database seeding script"""
    # Set up logging
    setup_logging()

    # Parse command-line arguments
    args = parse_args()

    # Log script start with database URL
    logger.info(f"Starting database seeding script with database URL: {settings.DATABASE_URL}")

    try:
        # If --reset flag is set, reset the database
        if args.reset:
            reset_database()

        # Initialize database with init_db function
        init_db()

        # Seed database with basic data using seed_db function
        seed_db()

        # If --sample-data flag is set, create sample data
        if args.sample_data:
            # Create sample users
            users = create_sample_users()

            # Create sample libraries
            libraries = create_sample_libraries(users)

            # Create sample molecules with specified sample size
            create_sample_molecules(users, libraries, args.sample_size)

        # Log successful database seeding
        logger.info("Database seeding completed successfully")

        # Return 0 for success
        return 0
    except Exception as e:
        # Catch exceptions, log error, and return 1 for failure
        logger.error(f"Database seeding failed: {str(e)}")
        return 1


if __name__ == "__main__":
    # Execute main function and exit with appropriate code
    sys.exit(main())