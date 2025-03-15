# Molecular Data Management and CRO Integration Platform Coding Standards

This document outlines the coding standards, style guidelines, and best practices for the Molecular Data Management and CRO Integration Platform. Adherence to these standards ensures code quality, maintainability, and consistency across the codebase.

## General Principles

### Code Readability

- Write clear, readable code that is easy to understand and maintain
- Prioritize readability over cleverness or excessive optimization
- Use consistent formatting throughout the codebase
- Keep functions and methods small and focused on a single responsibility
- Limit nesting levels (aim for a maximum of 3 levels)
- Use meaningful variable, function, and class names

### Code Organization

- Structure code logically by functionality and domain
- Follow the principle of least surprise in code organization
- Keep related code together (high cohesion)
- Minimize dependencies between modules (loose coupling)
- Organize files and folders in a consistent, intuitive manner
- Follow domain-driven design principles when organizing modules

### Naming Conventions

- Use descriptive, meaningful names for variables, functions, and classes
- Follow language-specific naming conventions (see language-specific sections)
- Be consistent with naming patterns throughout the codebase
- Use domain-specific terminology accurately and consistently
- Avoid abbreviations except for well-known ones (e.g., HTTP, URL)
- Prioritize clarity over brevity

### Documentation

- Document the purpose and behavior of code, not the implementation details
- Keep documentation up-to-date with code changes
- Document non-obvious design decisions and complex algorithms
- Include references to external resources where appropriate
- Document public APIs comprehensively
- Use inline comments sparingly and focus on explaining "why" not "what"

## Python Standards

### Style Guide

We follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) with some project-specific modifications. The project uses the following tools to enforce style:

- **Black**: For code formatting
- **isort**: For import sorting
- **flake8**: For style guide enforcement

Key style points:

- Line length: 100 characters maximum
- Indentation: 4 spaces (no tabs)
- Use snake_case for variables and function names
- Use CamelCase for class names
- Use ALL_CAPS for constants

Our Black configuration from pyproject.toml:

```toml
[tool.black]
line-length = 100
target-version = ["py310", "py311"]
include = "\\.pyi?$"
exclude = "/(\\.\\.+|venv|build|dist)/"
```

Our isort configuration from pyproject.toml:

```toml
[tool.isort]
profile = "black"
line_length = 100
multi_line_output = 3
include_trailing_comma = true
force_grid_wrap = 0
use_parentheses = true
ensure_newline_before_comments = true
```

### Type Annotations

We use static type hints following [PEP 484](https://www.python.org/dev/peps/pep-0484/) and validate them with mypy.

- All function parameters and return values must have type annotations
- Use appropriate collection types (List, Dict, Set, etc.)
- Use Optional[] for parameters that can be None
- Use Union[] (or | in Python 3.10+) for parameters that can be multiple types
- Add type annotations to class variables and instance attributes

Our mypy configuration from pyproject.toml:

```toml
[tool.mypy]
python_version = "3.10"
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = false
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_return_any = true
warn_unused_configs = true
```

Example:

```python
def calculate_molecular_weight(smiles: str, precision: int = 2) -> float:
    """Calculate the molecular weight for a given SMILES string."""
    # Implementation...
    return weight
```

### Docstrings

We follow the Google docstring format for documenting functions, classes, and modules.

Example:

```python
def validate_molecule(smiles: str) -> tuple[bool, Optional[str]]:
    """Validates if the given SMILES string represents a valid molecule.
    
    Args:
        smiles: The SMILES string to validate.
        
    Returns:
        A tuple containing a boolean indicating validity and an optional
        error message if the validation failed.
    
    Example:
        >>> validate_molecule("CC(=O)OC1=CC=CC=C1C(=O)O")
        (True, None)
        >>> validate_molecule("invalid_smiles")
        (False, "Invalid SMILES string")
    """
    # Implementation...
    return is_valid, error_message
```

### Testing

- Write unit tests for all functionality
- Use pytest as the testing framework
- Name test files with the prefix `test_`
- Name test functions with the prefix `test_`
- Test happy paths, edge cases, and error conditions
- Mock external dependencies
- Aim for 85% code coverage overall, with 95% for critical paths

### Imports Organization

Organize imports in the following order:

1. Standard library imports
2. Third-party library imports
3. Local application imports

Within each group, sort imports alphabetically. Use isort to automate this process.

Example:

```python
import json
import os
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.molecule import Molecule
```

## TypeScript/JavaScript Standards

### Style Guide

We follow a modified version of the [Airbnb JavaScript Style Guide](https://github.com/airbnb/javascript) with TypeScript-specific additions. The project uses the following tools to enforce style:

- **ESLint**: For code linting
- **Prettier**: For code formatting

Key style points:

- Line length: 100 characters maximum
- Indentation: 2 spaces (no tabs)
- Use camelCase for variables and function names
- Use PascalCase for classes and React components
- Use ALL_CAPS for constants
- Use single quotes for strings (unless the string contains single quotes)
- Always use semicolons

Our ESLint configuration extends multiple preset configurations as defined in .eslintrc.js:

```javascript
extends: [
  'eslint:recommended',
  'plugin:@typescript-eslint/recommended',
  'plugin:react/recommended',
  'plugin:react-hooks/recommended',
  'plugin:jsx-a11y/recommended',
  'plugin:import/errors',
  'plugin:import/warnings',
  'plugin:import/typescript',
  'plugin:jest/recommended',
  'prettier',
],
```

### Type Definitions

- Use TypeScript interfaces and types to define data structures
- Prefer interfaces for public APIs and types for internal use
- Avoid using `any` type when possible
- Use union types when a value can be one of several specific types
- Use generics to create reusable components and functions
- Export types that are part of the public API

Example:

```typescript
interface Molecule {
  id: string;
  smiles: string;
  inchiKey: string;
  molecularWeight?: number;
  logP?: number;
  properties: MoleculeProperty[];
}

type MoleculeProperty = {
  name: string;
  value: number | string;
  units?: string;
  source: 'predicted' | 'experimental';
};

export function getMoleculeById(id: string): Promise<Molecule> {
  // Implementation...
}
```

### JSDoc Comments

Use JSDoc comments to document functions, classes, and interfaces, especially for public APIs.

Example:

```typescript
/**
 * Fetches molecule data by its unique identifier.
 * 
 * @param id - The unique identifier of the molecule
 * @returns A promise that resolves to the molecule data
 * @throws {ApiError} When the molecule is not found or the server returns an error
 * 
 * @example
 * ```typescript
 * const molecule = await getMoleculeById('MOL-123');
 * console.log(molecule.smiles);
 * ```
 */
export async function getMoleculeById(id: string): Promise<Molecule> {
  // Implementation...
}
```

### Testing

- Write unit tests for all components and utilities
- Use Jest as the testing framework
- Use React Testing Library for testing React components
- Name test files with the suffix `.test.ts` or `.test.tsx`
- Test component rendering, user interactions, and edge cases
- Mock external dependencies and API calls
- Aim for 80% code coverage overall, with 90% for critical paths

### Imports Organization

Organize imports in the following order:

1. External imports (from node_modules)
2. Internal absolute imports (from project)
3. Internal relative imports (from same directory or parent/child directories)

Within each group, sort imports alphabetically. This is enforced via ESLint:

```javascript
'import/order': [
  'error',
  {
    groups: ['builtin', 'external', 'internal', 'parent', 'sibling', 'index'],
    'newlines-between': 'always',
    alphabetize: {
      order: 'asc',
      caseInsensitive: true,
    },
  },
],
```

Example:

```typescript
import React, { useEffect, useState } from 'react';
import { useQuery } from 'react-query';

import { API_ENDPOINTS } from '@/config/api';
import { useAuth } from '@/hooks/useAuth';
import { Molecule } from '@/types/molecule';

import { MoleculeCard } from './MoleculeCard';
import styles from './MoleculeList.module.css';
```

## React Standards

### Component Structure

- Prefer functional components with hooks over class components
- Use the following file structure for components:

```
ComponentName/
  index.ts            # Exports the component
  ComponentName.tsx   # Main component code
  ComponentName.test.tsx  # Component tests
  ComponentName.module.css  # Component styles (if using CSS modules)
  ComponentName.types.ts  # Component types (optional)
  useComponentLogic.ts  # Custom hook for complex logic (optional)
```

- Keep components focused on a single responsibility
- Extract reusable parts into separate components
- Use composition over inheritance

Example component:

```typescript
import React from 'react';

import { Button } from '@/components/common/Button';
import { useToast } from '@/hooks/useToast';
import { Molecule } from '@/types/molecule';

import styles from './MoleculeCard.module.css';

interface MoleculeCardProps {
  molecule: Molecule;
  onSelect?: (molecule: Molecule) => void;
  isSelected?: boolean;
}

export const MoleculeCard: React.FC<MoleculeCardProps> = ({
  molecule,
  onSelect,
  isSelected = false,
}) => {
  const { showToast } = useToast();
  
  const handleClick = () => {
    if (onSelect) {
      onSelect(molecule);
      showToast('Molecule selected', 'info');
    }
  };
  
  return (
    <div 
      className={`${styles.card} ${isSelected ? styles.selected : ''}`}
      onClick={handleClick}
    >
      <h3 className={styles.title}>{molecule.id}</h3>
      <div className={styles.structure}>
        {/* Molecule visualization */}
      </div>
      <div className={styles.properties}>
        <p>Molecular Weight: {molecule.molecularWeight} g/mol</p>
        <p>LogP: {molecule.logP}</p>
      </div>
      <Button onClick={handleClick}>
        {isSelected ? 'Deselect' : 'Select'}
      </Button>
    </div>
  );
};
```

### Hooks Usage

- Follow the [Rules of Hooks](https://reactjs.org/docs/hooks-rules.html)
- Use the appropriate hooks for each use case:
  - `useState` for component state
  - `useEffect` for side effects
  - `useContext` for context consumption
  - `useReducer` for complex state logic
  - `useMemo` and `useCallback` for performance optimization
- Create custom hooks to encapsulate and reuse stateful logic
- Ensure all dependencies are properly specified in dependency arrays

Example:

```typescript
import { useEffect, useState } from 'react';

import { fetchMoleculesByLibrary } from '@/api/molecules';
import { useDebouncedValue } from '@/hooks/useDebouncedValue';
import { Molecule } from '@/types/molecule';

export function useMoleculeSearch(libraryId: string, searchTerm: string) {
  const [molecules, setMolecules] = useState<Molecule[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  
  const debouncedSearchTerm = useDebouncedValue(searchTerm, 300);
  
  useEffect(() => {
    async function loadMolecules() {
      setIsLoading(true);
      setError(null);
      
      try {
        const result = await fetchMoleculesByLibrary(libraryId, debouncedSearchTerm);
        setMolecules(result);
      } catch (err) {
        setError(err instanceof Error ? err : new Error('Unknown error'));
      } finally {
        setIsLoading(false);
      }
    }
    
    loadMolecules();
  }, [libraryId, debouncedSearchTerm]);
  
  return { molecules, isLoading, error };
}
```

### Props and State

- Use interface definitions for component props
- Make props explicit and descriptive
- Provide default values for optional props
- Use destructuring to access props and state
- Keep state minimal and focused
- Use `useState` for simple state and `useReducer` for complex state
- Lift state up when needed for sharing between components
- Use context for deeply shared state
- Consider using state management libraries for complex applications

### Performance Optimization

- Use React's built-in performance optimization features:
  - `React.memo` for component memoization
  - `useMemo` for expensive calculations
  - `useCallback` for callback memoization
- Only optimize when necessary, based on profiling
- Use virtualization (e.g., `react-window` or `react-virtualized`) for long lists
- Split code into smaller chunks with dynamic imports
- Implement loading states and skeleton screens for better perceived performance
- Use appropriate keys for lists to optimize rendering

### Testing Components

- Test rendering and behavior, not implementation details
- Use React Testing Library to test components from a user perspective
- Write tests that mirror how users interact with components
- Test accessibility and keyboard navigation
- Use snapshot testing judiciously, focusing on small, stable components
- Test common user flows and edge cases
- Mock external dependencies and context providers

Example:

```typescript
import { render, screen, fireEvent } from '@testing-library/react';

import { Molecule } from '@/types/molecule';

import { MoleculeCard } from './MoleculeCard';

const mockMolecule: Molecule = {
  id: 'MOL-123',
  smiles: 'CC(=O)OC1=CC=CC=C1C(=O)O',
  inchiKey: 'BSYNRYMUTXBXSQ-UHFFFAOYSA-N',
  molecularWeight: 180.16,
  logP: 1.43,
  properties: []
};

describe('MoleculeCard', () => {
  it('renders molecule information correctly', () => {
    render(<MoleculeCard molecule={mockMolecule} />);
    
    expect(screen.getByText('MOL-123')).toBeInTheDocument();
    expect(screen.getByText('Molecular Weight: 180.16 g/mol')).toBeInTheDocument();
    expect(screen.getByText('LogP: 1.43')).toBeInTheDocument();
  });
  
  it('calls onSelect when clicked', () => {
    const onSelect = jest.fn();
    render(<MoleculeCard molecule={mockMolecule} onSelect={onSelect} />);
    
    fireEvent.click(screen.getByRole('button', { name: 'Select' }));
    
    expect(onSelect).toHaveBeenCalledWith(mockMolecule);
  });
  
  it('shows "Deselect" when selected', () => {
    render(<MoleculeCard molecule={mockMolecule} isSelected={true} />);
    
    expect(screen.getByRole('button', { name: 'Deselect' })).toBeInTheDocument();
  });
});
```

## Version Control Standards

### Branch Management

We follow a modified Git Flow branching model:

- `main`: Production-ready code
- `develop`: Integration branch for features
- `feature/*`: Feature branches
- `bugfix/*`: Bug fix branches
- `hotfix/*`: Emergency fixes for production
- `release/*`: Release preparation branches

Key principles:

- Branch from `develop` for new features
- Keep feature branches short-lived (ideally less than a week)
- Rebase feature branches on `develop` before creating a pull request
- Delete branches after merging

### Commit Guidelines

- Write clear, concise commit messages
- Use the imperative mood in commit messages (e.g., "Add feature" not "Added feature")
- Follow the conventional commits format:
  ```
  <type>(<scope>): <subject>
  
  <body>
  
  <footer>
  ```
- Common types: feat, fix, chore, docs, style, refactor, test, perf
- Include issue/ticket references in the footer
- Keep commits focused on a single logical change
- Don't commit commented code or debugging statements

Example:

```
feat(molecule-upload): add support for SDF file format

- Implement SDF file parsing with RDKit
- Add validation for SDF structures
- Update documentation with SDF examples

Closes #123
```

### Pull Request Process

1. Create a pull request from your feature branch to `develop`
2. Fill out the pull request template with:
   - Description of changes
   - Related issues
   - Testing procedures
   - Screenshots/videos (if applicable)
3. Request reviews from appropriate team members
4. Address all review comments
5. Ensure CI checks pass
6. Merge only after approval from at least one reviewer
7. Use squash merge to keep the history clean

### Change History Management

- Keep a CHANGELOG.md file updated following the [Keep a Changelog](https://keepachangelog.com/) format
- Update version numbers according to [Semantic Versioning](https://semver.org/)
- Tag releases with version numbers
- Document breaking changes clearly
- Include migration guides for major version changes

## Code Quality Tools

### Backend Tools

We use the following tools for backend code quality:

- **Black**: Code formatting
- **isort**: Import sorting
- **flake8**: Style guide enforcement and linting
- **mypy**: Static type checking
- **bandit**: Security linting
- **pytest**: Testing framework
- **pytest-cov**: Code coverage

Configuration is maintained in pyproject.toml. See the [Python Standards](#python-standards) section for specific configurations.

### Frontend Tools

We use the following tools for frontend code quality:

- **ESLint**: Code linting
- **Prettier**: Code formatting
- **TypeScript**: Static type checking
- **Jest**: Testing framework
- **React Testing Library**: Component testing
- **Cypress**: End-to-end testing

Configuration is maintained in .eslintrc.js, .prettierrc, and tsconfig.json.

### Pre-commit Hooks

We use pre-commit hooks to enforce code quality standards before committing:

```yaml
# .pre-commit-config.yaml
repos:
-   repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
    -   id: trailing-whitespace
    -   id: end-of-file-fixer
    -   id: check-yaml
    -   id: check-added-large-files

-   repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
    -   id: black

-   repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
    -   id: isort

-   repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
    -   id: flake8
        additional_dependencies: [flake8-bugbear]

-   repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.3.0
    hooks:
    -   id: mypy
        additional_dependencies: [types-requests]

-   repo: https://github.com/PyCQA/bandit
    rev: 1.7.5
    hooks:
    -   id: bandit
        args: ['-ll']

-   repo: https://github.com/pre-commit/mirrors-eslint
    rev: v8.43.0
    hooks:
    -   id: eslint
        files: \.(js|ts|tsx)$
        types: [file]
        additional_dependencies:
        -   eslint@8.43.0
        -   eslint-config-prettier@8.8.0
        -   @typescript-eslint/eslint-plugin@6.2.1
        -   @typescript-eslint/parser@6.2.1
        -   eslint-plugin-react@7.33.1
        -   eslint-plugin-react-hooks@4.6.0
        -   eslint-plugin-jsx-a11y@6.7.1
        -   eslint-plugin-import@2.28.0
        -   eslint-plugin-jest@27.2.3

-   repo: https://github.com/pre-commit/mirrors-prettier
    rev: v3.0.0
    hooks:
    -   id: prettier
        types_or: [javascript, typescript, jsx, tsx, css, json, yaml]
```

### CI Integration

The CI pipeline automatically runs code quality checks:

- Linting and formatting checks
- Static type checking
- Unit tests with coverage reporting
- Security scanning
- Build verification

Failed checks block the pull request from being merged.

## Code Review Process

### Review Checklist

Before approving a pull request, reviewers should check:

- [ ] Code follows project style guidelines
- [ ] New code has appropriate test coverage
- [ ] Documentation is updated
- [ ] No security vulnerabilities introduced
- [ ] Performance considerations addressed
- [ ] No unnecessary dependencies added
- [ ] Error handling is appropriate
- [ ] Edge cases are considered
- [ ] Code is maintainable and follows best practices
- [ ] CI checks pass

### Reviewer Responsibilities

- Provide constructive feedback
- Be specific about requested changes
- Respond to pull requests in a timely manner (ideally within 1 business day)
- Consider the big picture and the details
- Ensure code meets project standards
- Validate that the code works as intended
- Look for security and performance issues
- Share knowledge and explain suggestions

### Author Responsibilities

- Keep pull requests focused and reasonably sized
- Provide clear descriptions of changes
- Respond to feedback promptly
- Be open to suggestions and improvements
- Test changes thoroughly before requesting review
- Update the pull request based on feedback
- Thank reviewers for their time and input

### Review Etiquette

- Be respectful and professional
- Focus on the code, not the person
- Ask questions rather than making accusations
- Explain the reasoning behind suggestions
- Acknowledge good work and improvements
- Use a collaborative, not competitive, mindset
- Resolve discussions when addressed
- Use emoji reactions to acknowledge comments

## Quality Gates

### Automated Checks

All code must pass the following automated checks before merging:

- Linting and formatting rules
- Type checking
- Unit tests
- Integration tests (for backend API endpoints)
- Security scanning
- Build verification

These checks are enforced by the CI/CD pipeline.

### Code Coverage

The project maintains the following code coverage targets:

- Backend: 85% overall, 95% for critical paths
- Frontend: 80% overall, 90% for critical paths

Critical paths include:
- Molecule data processing and validation
- CRO submission workflows
- Authentication and authorization
- Data transformation between services

Coverage is measured using pytest-cov for backend and Jest for frontend.

### Security Scans

All code undergoes security scanning:

- **SonarQube**: For code quality and security issues
- **Bandit**: For Python security issues
- **npm audit**: For JavaScript dependency vulnerabilities
- **OWASP Dependency Check**: For known vulnerabilities in dependencies
- **Trivy**: For container image scanning

Security issues must be addressed before merging.

### Performance Checks

Critical components undergo performance checks:

- API response time checks for backend endpoints
- Bundle size analysis for frontend applications
- Database query performance monitoring
- Memory usage profiling for resource-intensive operations

## Documentation Standards

### Code Comments

- Use comments to explain why, not what (the code should be self-explanatory)
- Comment complex algorithms and non-obvious design decisions
- Keep comments up-to-date with code changes
- Use appropriate documentation tools (docstrings in Python, JSDoc in JavaScript/TypeScript)
- Don't comment out code; remove it (version control has the history)
- Follow language-specific comment conventions

### API Documentation

- Document all public APIs comprehensively
- Include:
  - Function/method purpose
  - Parameters and their types
  - Return values and their types
  - Exceptions/errors that can be thrown
  - Usage examples
- Use OpenAPI/Swagger for REST API documentation
- Generate API documentation automatically when possible

### README Files

Each repository and major component should have a README.md with:

- Project overview and purpose
- Installation instructions
- Configuration options
- Usage examples
- Development setup guide
- Testing instructions
- Contributing guidelines
- License information

### Technical Documentation

- Maintain high-level architecture documentation
- Document design decisions and trade-offs
- Keep documentation close to the code (e.g., in a `docs` directory)
- Use diagrams to illustrate complex systems and workflows
- Update documentation with each significant change
- Document environment setup and deployment procedures

## Code Coverage Standards

### Frontend Coverage Targets

| Component | Line Coverage | Branch Coverage | Function Coverage |
| --- | --- | --- | --- |
| UI Components | 80% | 75% | 85% |
| Utility Functions | 90% | 85% | 95% |
| API Services | 85% | 80% | 90% |
| State Management | 85% | 80% | 90% |
| Critical Components | 90% | 85% | 95% |

### Backend Coverage Targets

| Component | Line Coverage | Branch Coverage | Function Coverage |
| --- | --- | --- | --- |
| API Endpoints | 85% | 80% | 90% |
| Business Logic | 90% | 85% | 95% |
| Data Access | 85% | 80% | 90% |
| Utilities | 90% | 85% | 95% |
| Critical Services | 95% | 90% | 100% |

### Critical Path Coverage

Critical paths require higher code coverage:

- Molecule data processing pipeline
- CRO submission workflow
- Authentication and authorization
- Data import/export functionality
- Integration points with external services

These areas should maintain:
- 95% line coverage
- 90% branch coverage
- 100% function coverage

## Quality Metrics Standards

### Test Success Rate

- 100% pass rate required for production deployment
- >98% pass rate required for staging deployment
- <2% flaky test rate allowed in the test suite

Test flakiness is monitored and addressed regularly.

### Performance Thresholds

| Metric | Target | Critical Threshold |
| --- | --- | --- |
| API Response Time | P95 < 500ms | P99 < 1000ms |
| CSV Processing | <30s per 10K molecules | <60s per 10K molecules |
| UI Rendering | <200ms for initial load | <500ms for initial load |
| Database Queries | P95 < 100ms | P99 < 250ms |

Performance testing is integrated into the CI/CD pipeline for critical paths.

### Documentation Completeness

Documentation completeness is measured by:

- Public API documentation coverage (target: 100%)
- Code documentation coverage for complex functions (target: >90%)
- User-facing feature documentation (target: 100%)
- Architecture documentation up-to-date with implementation

Documentation quality is reviewed as part of the code review process.

---

## Development Environment Setup

To set up your development environment with all required code quality tools:

1. Install Python 3.10+ and Node.js 18+
2. Clone the repository
3. Install backend dependencies:
   ```bash
   cd src/backend
   pip install poetry
   poetry install
   ```
4. Install frontend dependencies:
   ```bash
   cd src/web
   npm install
   ```
5. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```
6. Configure your IDE with recommended extensions:
   - VSCode:
     - Python
     - Pylance
     - ESLint
     - Prettier
     - EditorConfig
     - GitLens
   - PyCharm:
     - Pylint
     - Black formatter
     - SonarLint

## Running Code Quality Checks

To run code quality checks locally:

### Backend

```bash
cd src/backend
# Format code
poetry run black .
poetry run isort .
# Lint code
poetry run flake8
# Type checking
poetry run mypy .
# Security scanning
poetry run bandit -r app
# Run tests with coverage
poetry run pytest --cov=app
```

### Frontend

```bash
cd src/web
# Lint code
npm run lint
# Format code
npm run format
# Type checking
npm run typecheck
# Run tests with coverage
npm run test:coverage
```

### Pre-commit

Run pre-commit on all files:
```bash
pre-commit run --all-files
```

Run pre-commit on staged files:
```bash
pre-commit run
```