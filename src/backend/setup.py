import os
from setuptools import setup, find_packages
from app import __version__

# Read long description from README
README = open('README.md', 'r', encoding='utf-8').read()

# Read requirements
REQUIREMENTS = open('requirements.txt', 'r', encoding='utf-8').read().splitlines()

def get_requirements():
    """Parse requirements.txt file to get package dependencies."""
    return [line.strip() for line in REQUIREMENTS if line.strip() and not line.strip().startswith('#')]

setup(
    name="molecular-platform-backend",
    version=__version__,
    description="Molecular Data Management and CRO Integration Platform",
    long_description=README,
    long_description_content_type="text/markdown",
    author="Pharmaceutical Research Team",
    author_email="platform@moleculardata.example.com",
    url="https://github.com/organization/molecular-platform",
    packages=find_packages(include=["app", "app.*"]),
    package_data={
        "app": ["static/*", "templates/*", "alembic.ini", "alembic/*"],
    },
    include_package_data=True,
    install_requires=get_requirements(),
    python_requires=">=3.10",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Chemistry",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
    ],
    entry_points={
        "console_scripts": [
            "molecule-service=app.main:run_app",
            "molecule-worker=app.worker:run_worker",
        ],
    },
)