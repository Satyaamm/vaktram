# Contributing to Vaktram

Thank you for your interest in contributing to Vaktram! This guide will help you get started.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/your-username/vaktram.git`
3. Run setup: `bash infra/scripts/setup.sh`
4. Create a branch: `git checkout -b feature/your-feature`

## Project Structure

```
vaktram/
  apps/
    web/                  # Next.js frontend
    api/                  # FastAPI backend
    bot-service/          # Meeting bot service
    workers/
      transcription/      # Speech-to-text worker
      summarizer/         # LLM summarization worker
  packages/
    shared/               # Shared constants, types, utils
    db/                   # Database schema and seeds
    config/               # Shared configuration
  infra/
    docker/               # Dockerfiles
    scripts/              # Setup and utility scripts
  docs/                   # Documentation
  .github/workflows/      # CI/CD pipelines
```

## Development Workflow

### Branch Naming

- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation updates
- `refactor/description` - Code refactoring

### Commit Messages

Follow conventional commits:

```
feat: add semantic search endpoint
fix: handle empty transcript in summarizer
docs: update API documentation
refactor: extract audio processing into separate module
test: add unit tests for diarizer
```

### Pull Requests

1. Keep PRs focused on a single change
2. Write a clear description of what and why
3. Include tests for new functionality
4. Ensure CI passes (lint + tests)
5. Request review from a maintainer

## Code Standards

### Python

- Python 3.11+
- Type hints on all function signatures
- Docstrings for all public classes and functions
- Format with `black` (line length 100)
- Lint with `ruff`
- Sort imports with `isort`

### TypeScript

- Strict mode enabled
- ESLint + Prettier
- Functional components with hooks
- Server components by default (Next.js App Router)

### SQL

- Use snake_case for all identifiers
- Add indexes for frequently queried columns
- Write RLS policies for all new tables
- Include migration files for schema changes

## Testing

### Python Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=bot --cov-report=html

# Run specific test file
pytest tests/test_orchestrator.py
```

### Frontend Tests

```bash
cd apps/web
npm test
```

## Reporting Issues

- Use GitHub Issues
- Include steps to reproduce
- Include expected vs actual behavior
- Include environment details (OS, Python version, etc.)

## Code of Conduct

Be respectful, inclusive, and constructive. We follow the [Contributor Covenant](https://www.contributor-covenant.org/).
