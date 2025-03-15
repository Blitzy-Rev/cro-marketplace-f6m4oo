# Molecular Data Management and CRO Integration Platform Development Setup

This guide provides comprehensive instructions for setting up the development environment for the Molecular Data Management and CRO Integration Platform, a cloud-based application designed to revolutionize small molecule drug discovery workflows.

## Prerequisites

### System Requirements

- **CPU**: Minimum 4 cores recommended (8 preferred for optimal performance)
- **RAM**: Minimum 8GB (16GB+ recommended for RDKit and molecule processing)
- **Disk Space**: Minimum 20GB free space
- **Operating System**: 
  - Linux (Ubuntu 20.04+, CentOS 8+)
  - macOS (10.15+)
  - Windows 10+ with WSL2 recommended for Docker workflow

### Required Software

| Software | Version | Purpose |
|----------|---------|---------|
| Docker | 24.0+ | Container runtime for development environment |
| Docker Compose | 2.0+ | Multi-container orchestration |
| Git | 2.0+ | Version control system |
| Python | 3.10+ | Backend programming language |
| Node.js | 18.0+ | Frontend JavaScript runtime |
| PostgreSQL | 15.0+ | Database for development |
| RDKit | 2023.03+ | Cheminformatics library for molecule processing |
| AWS CLI | 2.0+ | Command-line interface for AWS services |

### Recommended Tools

- **IDEs**: VS Code, PyCharm, WebStorm
- **Database Tools**: DBeaver, pgAdmin
- **API Testing**: Postman, Insomnia
- **Git GUI**: GitKraken, SourceTree

## Docker-based Setup

The Docker-based setup is the recommended approach as it ensures consistent environments across all developers.

### Docker Installation

1. Install Docker and Docker Compose following the official documentation:
   - [Docker Installation](https://docs.docker.com/get-docker/)
   - [Docker Compose Installation](https://docs.docker.com/compose/install/)

2. Verify the installation:
   ```bash
   docker --version
   docker-compose --version
   ```

3. Configure Docker resources:
   - Minimum 4GB RAM
   - Minimum 2 CPUs
   - Minimum 20GB disk space

### Environment Configuration

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd molecular-data-platform
   ```

2. Create environment files:
   ```bash
   # Backend environment
   cp src/backend/.env.example src/backend/.env

   # Frontend environment
   cp src/web/.env.example src/web/.env.local
   ```

3. Configure environment variables:

   The default configuration in the example files should work for most development scenarios. Key variables include:

   **Backend `.env`**:
   ```
   DATABASE_URL=postgresql://postgres:postgres@database:5432/molecule_platform
   REDIS_URL=redis://redis:6379/0
   AI_ENGINE_API_URL=http://mock-ai-engine:5000/api
   ```

   **Frontend `.env.local`**:
   ```
   VITE_API_BASE_URL=http://localhost:8000/api/v1
   ```

### Running the Application

1. Start all services:
   ```bash
   docker-compose up -d
   ```

2. Verify all services are running:
   ```bash
   docker-compose ps
   ```

3. Access the applications:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

4. View service logs:
   ```bash
   docker-compose logs -f <service-name>
   ```
   Where `<service-name>` can be: frontend, backend, molecule_service, worker, database, redis, or mock-ai-engine.

5. Stop all services:
   ```bash
   docker-compose down
   ```

## Backend Setup

For developers who prefer to run the backend services directly on their local machine:

### Python Environment

1. Install Python 3.10+ from [python.org](https://www.python.org/downloads/)

2. Create and activate a virtual environment:
   ```bash
   cd src/backend
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Database Setup

1. Install PostgreSQL 15+ following the [official documentation](https://www.postgresql.org/download/)

2. Create a database for the project:
   ```bash
   # Connect to PostgreSQL
   psql -U postgres
   
   # Create database
   CREATE DATABASE molecule_platform;
   \q
   ```

3. Install database client libraries if needed:
   - Ubuntu/Debian: `sudo apt-get install libpq-dev python3-dev`
   - macOS: `brew install postgresql`
   - Windows: Included in PostgreSQL installer

### RDKit Installation

RDKit is critical for molecular data processing. Installation via conda is strongly recommended:

1. Install Miniconda from [conda.io](https://docs.conda.io/en/latest/miniconda.html)

2. Create a conda environment with RDKit:
   ```bash
   conda create -n molecule-platform python=3.10
   conda activate molecule-platform
   conda install -c conda-forge rdkit=2023.03
   ```

3. Install the Python dependencies within this conda environment:
   ```bash
   pip install -r requirements.txt
   ```

### Running the Backend

1. Configure environment variables in `.env`:
   ```
   DATABASE_URL=postgresql://postgres:password@localhost:5432/molecule_platform
   REDIS_URL=redis://localhost:6379/0
   ```

2. Run database migrations:
   ```bash
   alembic upgrade head
   ```

3. Start the FastAPI application:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

4. In separate terminal windows, start additional services:
   ```bash
   # Celery worker
   celery -A app.tasks.celery_app worker --loglevel=info
   
   # Molecule Service
   python -m app.services.molecule_service --debug
   
   # Mock AI Engine (optional - for development without external AI service)
   python -m app.services.mock_ai_engine --host 0.0.0.0 --port 5000
   ```

## Frontend Setup

For developers who prefer to run the frontend directly on their local machine:

### Node.js Environment

1. Install Node.js 18+ from [nodejs.org](https://nodejs.org/)

2. Verify the installation:
   ```bash
   node --version
   npm --version
   ```

### Dependencies Installation

1. Navigate to the frontend directory:
   ```bash
   cd src/web
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

### Running the Frontend

1. Configure environment in `.env.local`:
   ```
   VITE_API_BASE_URL=http://localhost:8000/api/v1
   ```

2. Start the development server:
   ```bash
   npm run dev
   ```

3. The application will be available at http://localhost:3000

## Infrastructure Setup

For developers working on infrastructure components:

### Terraform Installation

1. Install Terraform 1.5+ following the [official documentation](https://developer.hashicorp.com/terraform/downloads)

2. Verify the installation:
   ```bash
   terraform --version
   ```

### AWS CLI Configuration

1. Install AWS CLI 2.0+ following the [official documentation](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)

2. Configure AWS credentials:
   ```bash
   aws configure
   ```

3. Enter your AWS Access Key ID, Secret Access Key, default region, and output format when prompted.

### Local Infrastructure Testing

1. Navigate to the infrastructure directory:
   ```bash
   cd infrastructure
   ```

2. Initialize Terraform:
   ```bash
   terraform init
   ```

3. Create a local tfvars file for development:
   ```bash
   cp terraform.tfvars.example terraform.dev.tfvars
   ```

4. Test the configuration:
   ```bash
   terraform plan -var-file=terraform.dev.tfvars
   ```

## IDE Configuration

### VS Code Setup

1. Install VS Code extensions:
   - Python
   - Pylance
   - ESLint
   - Prettier
   - Docker
   - Remote - Containers
   - GitLens

2. Configure workspace settings (`settings.json`):
   ```json
   {
     "python.linting.enabled": true,
     "python.linting.flake8Enabled": true,
     "python.linting.mypyEnabled": true,
     "python.formatting.provider": "black",
     "editor.formatOnSave": true,
     "editor.codeActionsOnSave": {
       "source.organizeImports": true,
       "source.fixAll.eslint": true
     },
     "typescript.tsdk": "node_modules/typescript/lib",
     "[python]": {
       "editor.defaultFormatter": "ms-python.black-formatter"
     },
     "[javascript][typescript][typescriptreact]": {
       "editor.defaultFormatter": "esbenp.prettier-vscode"
     }
   }
   ```

### PyCharm Setup

1. Open the backend directory as a project

2. Configure the Python interpreter:
   - Settings/Preferences > Project > Python Interpreter
   - Add interpreter, pointing to the virtual environment or conda environment

3. Configure code quality tools:
   - External Tools > Black formatter
   - External Tools > Flake8 linter

### WebStorm Setup

1. Open the frontend directory as a project

2. Configure ESLint:
   - Settings/Preferences > Languages & Frameworks > JavaScript > Code Quality Tools > ESLint
   - Enable ESLint and select automatic configuration

3. Configure Prettier:
   - Settings/Preferences > Languages & Frameworks > JavaScript > Prettier
   - Enable Prettier with automatic configuration

## Code Quality Tools

### Linting Tools

**Backend Linting**

```bash
# In src/backend directory
flake8 app tests
mypy app
bandit -r app
```

**Frontend Linting**

```bash
# In src/web directory
npm run lint
npm run typecheck
```

### Formatting Tools

**Backend Formatting**

```bash
# In src/backend directory
black app tests
isort app tests
```

**Frontend Formatting**

```bash
# In src/web directory
npm run format
```

### Static Analysis

**Backend Static Analysis**

```bash
# In src/backend directory
pytest --cov=app tests/
```

**Frontend Static Analysis**

```bash
# In src/web directory
npm run test
npm run analyze  # Bundle analysis
```

## Troubleshooting

### Common Issues

1. **Port Already in Use**
   - Find the process: `lsof -i :<port_number>`
   - Kill the process: `kill -9 <process_id>`
   - Or change the port in configuration

2. **Python Package Installation Failures**
   - Try using conda instead of pip for scientific packages
   - Install system dependencies as needed

3. **Module Not Found Errors**
   - Check that your virtual environment is activated
   - Verify the package is installed: `pip list | grep <package-name>`

### Docker Troubleshooting

1. **Containers Not Starting**
   - Check logs: `docker-compose logs <service-name>`
   - Ensure all required environment variables are set
   - Check for port conflicts

2. **Volume Mount Issues**
   - Check file permissions in mounted directories
   - Rebuild the container: `docker-compose up -d --build <service-name>`

3. **Network Issues**
   - Check if services can reach each other: `docker-compose exec <service-name> ping <other-service-name>`
   - Verify network configuration in docker-compose.yml

### Backend Troubleshooting

1. **RDKit Installation Issues**
   - Use conda for installation (recommended)
   - On Linux, install required system packages:
     ```bash
     sudo apt-get install -y build-essential python3-dev
     ```

2. **Database Connection Issues**
   - Verify PostgreSQL is running: `pg_isready`
   - Check connection string in `.env` file
   - Ensure the database exists: `psql -U postgres -l`

3. **Alembic Migration Errors**
   - Reset migrations if necessary:
     ```bash
     alembic downgrade base
     alembic upgrade head
     ```

### Frontend Troubleshooting

1. **Node.js Dependency Issues**
   - Remove node_modules and reinstall:
     ```bash
     rm -rf node_modules
     npm install
     ```
   - Clear npm cache: `npm cache clean --force`

2. **Build or TypeScript Errors**
   - Check for TypeScript errors: `npm run typecheck`
   - Update dependencies: `npm update`

3. **API Connection Issues**
   - Verify the backend is running
   - Check CORS configuration in backend
   - Ensure `VITE_API_BASE_URL` is correctly set