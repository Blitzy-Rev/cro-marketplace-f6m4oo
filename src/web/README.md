# Molecular Data Management and CRO Integration Platform - Frontend

Frontend web application for the Molecular Data Management and CRO Integration Platform, a cloud-based application designed to revolutionize small molecule drug discovery workflows for small to mid-cap pharmaceutical companies.

## Technology Stack

- React 18+ with TypeScript 4.9+
- Material UI 5.0+ for component library
- Redux Toolkit 1.9+ for state management
- React Query 4.0+ for data fetching
- D3.js 7.0+ for data visualization
- ChemDoodle Web 9.0+ for molecular visualization
- Vite 4.0+ for build tooling
- Jest and React Testing Library for testing

## Project Structure

```
src/
├── api/              # API client functions
├── assets/           # Static assets and theme
├── components/       # Reusable UI components
│   ├── auth/         # Authentication components
│   ├── common/       # Common UI elements
│   ├── cro/          # CRO-related components
│   ├── document/     # Document handling components
│   ├── layout/       # Layout components
│   ├── library/      # Library management components
│   ├── molecule/     # Molecule visualization components
│   ├── results/      # Results display components
│   └── submission/   # Submission workflow components
├── constants/        # Application constants
├── contexts/         # React contexts
├── features/         # Redux slices by feature
├── hooks/            # Custom React hooks
├── pages/            # Page components
├── routes/           # Routing configuration
├── store/            # Redux store configuration
├── types/            # TypeScript type definitions
├── utils/            # Utility functions
└── App.tsx           # Root component
```

## Getting Started

### Prerequisites

- Node.js 18+ and npm 8+
- Git

### Installation

1. Clone the repository
2. Navigate to the frontend directory: `cd src/web`
3. Install dependencies: `npm install`
4. Copy the example environment file: `cp .env.example .env.local`
5. Update environment variables in `.env.local`

### Development

Start the development server:

```bash
npm run dev
```

The application will be available at http://localhost:3000 with hot module replacement enabled.

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build locally
- `npm run test` - Run tests
- `npm run test:watch` - Run tests in watch mode
- `npm run test:coverage` - Run tests with coverage report
- `npm run lint` - Lint code
- `npm run lint:fix` - Lint and fix code
- `npm run format` - Format code with Prettier
- `npm run typecheck` - Check TypeScript types
- `npm run analyze` - Analyze bundle size

## Code Style and Quality

This project follows strict code quality standards:

- TypeScript for type safety
- ESLint for code linting
- Prettier for code formatting
- Husky for pre-commit hooks
- lint-staged for running linters on staged files

Pre-commit hooks will automatically run linting and formatting on staged files.

## Testing

We use Jest and React Testing Library for testing. Tests are located next to the components they test in `__tests__` directories.

Run tests with:

```bash
npm run test
```

For test coverage:

```bash
npm run test:coverage
```

## Building for Production

To create a production build:

```bash
npm run build
```

The build artifacts will be stored in the `dist/` directory.

You can preview the production build locally:

```bash
npm run preview
```

## Docker

The frontend can be built and run using Docker:

```bash
# Build the image
docker build -t molecule-flow-frontend .

# Run the container
docker run -p 80:80 molecule-flow-frontend
```

The Dockerfile uses a multi-stage build process for optimal image size and security.

## Environment Variables

The following environment variables can be configured:

- `VITE_API_BASE_URL` - Base URL for API requests
- `VITE_AUTH_DOMAIN` - Authentication domain
- `VITE_AUTH_CLIENT_ID` - Authentication client ID
- `VITE_WEBSOCKET_URL` - WebSocket server URL
- `VITE_CHEMDOODLE_LICENSE` - ChemDoodle license key (optional)

Environment variables must be prefixed with `VITE_` to be accessible in the frontend code.

## Key Features

- Interactive molecule visualization with ChemDoodle Web
- Drag-and-drop CSV file upload with column mapping
- Property filtering and sorting for molecules
- Library management with drag-and-drop organization
- CRO submission workflow with multi-step forms
- Document management with preview and e-signature
- Results visualization with interactive charts
- Real-time notifications via WebSockets

## Browser Support

The application supports modern browsers:

- Chrome (latest 2 versions)
- Firefox (latest 2 versions)
- Safari (latest 2 versions)
- Edge (latest 2 versions)

Internet Explorer is not supported.

## Accessibility

The application is designed to meet WCAG 2.1 AA standards:

- Proper semantic HTML
- ARIA attributes where necessary
- Keyboard navigation support
- Color contrast compliance
- Screen reader compatibility

## Integration with Backend

The frontend communicates with the backend API using Axios. API client functions are organized in the `src/api` directory.

WebSocket connections are used for real-time notifications and updates, particularly for CRO communication and long-running processes.

## Deployment

The frontend can be deployed to various environments:

- Static hosting (S3 + CloudFront)
- Docker container on ECS
- Traditional web servers (Nginx, Apache)

Refer to the deployment documentation in `/deployment` for detailed instructions.

## Contributing

Please follow the contribution guidelines in the root README.md when contributing to this project.

## License

This project is licensed under the terms specified in the LICENSE file at the root of the repository.