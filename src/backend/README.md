# Molecular Data Management and CRO Integration Platform - Backend

Backend services for the Molecular Data Management and CRO Integration Platform, a cloud-based application designed to revolutionize small molecule drug discovery workflows for small to mid-cap pharmaceutical companies.

## Technology Stack

- Python 3.10+
- FastAPI
- PostgreSQL 15+
- RDKit for cheminformatics
- Celery for background processing
- Redis for caching and message queue
- AWS services (S3, SQS, Cognito)

## Project Structure

```
app/
├── api/              # API endpoints
│   └── api_v1/       # API version 1
├── constants/        # Application constants
├── core/             # Core functionality
├── crud/             # Database CRUD operations
├── db/               # Database models and session
├── integrations/     # External service integrations
├── middleware/       # Request/response middleware
├── models/           # SQLAlchemy models
├── schemas/          # Pydantic schemas
├── services/         # Business logic
├── tasks/            # Background tasks
└── utils/            # Utility functions
```

## Getting Started

### Prerequisites

- Python 3.10+
- Docker and Docker Compose
- PostgreSQL 15+
- RDKit

### Environment Setup

1. Clone the repository
2. Navigate to the backend directory: `cd src/backend`
3. Copy the example environment file: `cp .env.example .env`
4. Update the environment variables in `.env`

### Installation

#### Using Docker

```bash
docker-compose up -d
```

#### Manual Setup

1. Create a virtual environment: `python -m venv venv`
2. Activate the virtual environment: `source venv/bin/activate` (Linux/Mac) or `venv\Scripts\activate` (Windows)
3. Install dependencies: `pip install -r requirements.txt`
4. Run database migrations: `alembic upgrade head`
5. Start the application: `uvicorn app.main:app --reload`

## Development

### Code Style

This project follows PEP 8 guidelines. We use the following tools for code quality:

- Black for code formatting
- isort for import sorting
- Flake8 for linting
- mypy for type checking

Run the following commands before committing:

```bash
black app tests
isort app tests
flake8 app tests
mypy app
```

### Testing

We use pytest for testing. Run tests with:

```bash
pytest
```

For test coverage:

```bash
pytest --cov=app tests/
```

## API Documentation

Once the application is running, you can access the API documentation at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

The OpenAPI specification is also available at http://localhost:8000/openapi.json

## Key Features

- CSV molecular data ingestion with SMILES validation
- Molecule library management
- AI property prediction integration
- CRO submission workflow
- Secure document exchange
- Results tracking and visualization
- Role-based access control

## Database Migrations

We use Alembic for database migrations. To create a new migration:

```bash
alembic revision --autogenerate -m "Description of changes"
```

To apply migrations:

```bash
alembic upgrade head
```

## Background Tasks

Background tasks are handled by Celery with Redis as the message broker. To start the Celery worker:

```bash
celery -A app.tasks.worker worker --loglevel=info
```

## Deployment

The application is designed to be deployed as Docker containers on AWS ECS. Refer to the deployment documentation in `/deployment` for detailed instructions.

## Security Considerations

- All API endpoints are protected with JWT authentication
- Role-based access control for different user types
- Data encryption at rest and in transit
- Comprehensive audit logging for compliance
- Input validation for all API requests
- Rate limiting to prevent abuse

## Compliance

This application is designed to comply with 21 CFR Part 11 requirements for electronic records and signatures in pharmaceutical research.

## License

Proprietary and confidential. Unauthorized copying or distribution is prohibited.