# Contributing to OpenSNS

Thank you for your interest in contributing to OpenSNS. This guide will help you get started.

## How to Contribute

There are many ways to contribute:

- **Report bugs** — Open an issue with clear reproduction steps
- **Fix bugs** — Pick up open issues labeled `good first issue` or `help wanted`
- **Add features** — Propose new features via an issue before starting work
- **Improve documentation** — Fix typos, clarify explanations, add examples
- **Review pull requests** — Help review code and provide feedback

Before starting significant work, please open an issue to discuss your approach. This helps avoid duplicate effort and ensures your contribution aligns with the project's direction.

## Development Setup

### Prerequisites

- Python 3.11+
- Node.js 18+ and Bun
- Docker (optional, for containerized setup)

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your settings

uvicorn app.main:app --reload
```

The backend API will be available at `http://localhost:8000` with documentation at `/docs`.

### Frontend Setup

```bash
cd frontend
bun install
cp .env.example .env.local

bun dev
```

The frontend will be available at `http://localhost:3000`.

### Docker Setup (Alternative)

```bash
# Copy and configure environment
cp .env.example .env

# Generate required secrets
# JWT_SECRET_KEY and API_KEY_ENCRYPTION_KEY are required
# Generate with: openssl rand -hex 32

# Start all services
docker compose up -d
```

## Code Style

### Backend (Python)

- Use type hints for all function signatures
- Write async functions where appropriate (`async def`)
- Follow PEP 8 style guidelines
- Run the linter before committing:

```bash
cd backend && ruff check app/
```

### Frontend (TypeScript)

- Use strict TypeScript settings
- Follow the existing component patterns
- Use the path alias `@/*` for imports from `src/`
- Run the linter before committing:

```bash
cd frontend && bun lint
```

## Testing

All contributions should include tests where applicable.

### Backend Tests

```bash
cd backend && pytest -v
```

### Frontend Tests

```bash
cd frontend && bun test
```

### E2E Tests

```bash
cd frontend && bun e2e
```

Make sure all tests pass before submitting a pull request.

## Pull Request Process

1. **Fork the repository** and create your branch from `main`
2. **Make your changes** following the code style guidelines
3. **Add or update tests** as needed
4. **Run the test suite** and ensure everything passes
5. **Update documentation** if your changes affect usage or setup
6. **Submit your pull request** with a clear description of the changes

### PR Guidelines

- Keep changes focused and atomic
- One logical change per pull request
- Write clear commit messages that explain the "why" not just the "what"
- Reference any related issues using `Fixes #123` or `Closes #456`
- Respond to review feedback promptly and professionally

Pull requests require review from at least one maintainer before merging.

## Reporting Bugs

When reporting bugs, please include:

- **Clear description** — What happened vs. what you expected
- **Steps to reproduce** — Minimal steps that trigger the issue
- **Environment details** — OS, Python/Node versions, browser if relevant
- **Error messages** — Full stack traces or console output
- **Screenshots** — If applicable, visual evidence of the issue

Check existing issues first to avoid duplicates. If you find a similar issue, add a comment with any new information.

## License

By contributing to OpenSNS, you agree that your contributions will be licensed under the MIT License.
