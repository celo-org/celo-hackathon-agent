# Contributing to AI Project Analyzer

Thank you for your interest in contributing to AI Project Analyzer! This guide will help you get started.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Package Structure](#package-structure)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Documentation](#documentation)
- [Pull Request Process](#pull-request-process)
- [Release Process](#release-process)

## Code of Conduct

This project adheres to a code of conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.

## Getting Started

### Prerequisites

- **Python 3.11+** with [uv](https://github.com/astral-sh/uv)
- **Node.js 18+** with npm
- **Docker** (for containerized development)
- **Git**

### Quick Setup

```bash
# Clone the repository
git clone <repository-url>
cd ai-project-analyzer

# Set up development environment
./scripts/dev-setup.sh

# Start development services
./scripts/docker-dev.sh up
```

### Manual Setup

```bash
# Install packages
./scripts/install.sh

# Configure environment
cp config/env.development .env
# Edit .env and add your API keys

# Start services manually
./start.sh --dev
```

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-description
# or
git checkout -b docs/documentation-update
```

### 2. Make Changes

Follow our [coding standards](#coding-standards) and ensure your changes:

- Are well-tested
- Include appropriate documentation
- Follow the existing code style
- Don't break existing functionality

### 3. Test Your Changes

```bash
# Run all tests
./scripts/test.sh --coverage

# Run specific package tests
./scripts/test.sh --package core

# Run tests in Docker
./scripts/test.sh --docker

# Run linting
./scripts/test.sh --lint

# Run security tests
./scripts/test.sh --security
```

### 4. Commit Your Changes

We use conventional commits:

```bash
# Format: type(scope): description
git commit -m "feat(core): add new analysis engine"
git commit -m "fix(api): resolve authentication issue"
git commit -m "docs(readme): update installation guide"
git commit -m "test(cli): add integration tests"
```

**Types:**

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Test changes
- `chore`: Build/tooling changes
- `perf`: Performance improvements
- `ci`: CI/CD changes

### 5. Push and Create PR

```bash
git push origin your-branch-name
```

Then create a pull request using our [PR template](.github/PULL_REQUEST_TEMPLATE.md).

## Package Structure

```
packages/
├── core/           # Core business logic
│   ├── src/        # Source code
│   ├── tests/      # Tests
│   └── README.md   # Package documentation
├── cli/            # Command-line interface
├── api/            # REST API server
└── frontend/       # React frontend
```

### Core Package

Contains the main analysis logic, repository fetching, and LLM integration.

**Key Files:**

- `analyzer.py`: Main analysis engine
- `fetcher.py`: Repository content fetching
- `reporter.py`: Report generation
- `config.py`: Configuration management

### CLI Package

Command-line interface for batch analysis and automation.

### API Package

FastAPI server with user management, background processing, and database integration.

### Frontend Package

React application with TypeScript, providing a modern web interface.

## Coding Standards

### Python

- **Code Style**: We use [Ruff](https://github.com/astral-sh/ruff) for linting and formatting
- **Type Hints**: Required for all functions
- **Docstrings**: Google-style docstrings for all public functions
- **Line Length**: 100 characters maximum
- **Imports**: Grouped and sorted (handled by Ruff)

```python
def analyze_repository(url: str, model: str = "gemini-2.5-flash") -> AnalysisResult:
    """Analyze a GitHub repository using the specified LLM model.

    Args:
        url: GitHub repository URL
        model: LLM model to use for analysis

    Returns:
        Analysis result containing scores and insights

    Raises:
        InvalidURLError: If the repository URL is invalid
        AnalysisError: If analysis fails
    """
    # Implementation here
```

### TypeScript/React

- **Code Style**: ESLint + Prettier configuration
- **Components**: Functional components with hooks
- **File Naming**: PascalCase for components, camelCase for utilities
- **Exports**: Named exports preferred over default exports

```typescript
interface RepositoryAnalysisProps {
  repositoryUrl: string;
  onAnalysisComplete: (result: AnalysisResult) => void;
}

export const RepositoryAnalysis: React.FC<RepositoryAnalysisProps> = ({
  repositoryUrl,
  onAnalysisComplete,
}) => {
  // Component implementation
};
```

### General Guidelines

- **Error Handling**: Always handle errors gracefully
- **Logging**: Use appropriate log levels
- **Security**: Never commit secrets or API keys
- **Performance**: Consider performance implications of changes
- **Accessibility**: Follow accessibility best practices in frontend

## Testing

### Test Organization

```
packages/[package]/tests/
├── unit/           # Unit tests
├── integration/    # Integration tests
├── performance/    # Performance tests
└── fixtures/       # Test data and fixtures
```

### Writing Tests

#### Python Tests (pytest)

```python
import pytest
from src.analyzer import analyze_repository

def test_analyze_repository_success():
    """Test successful repository analysis."""
    result = analyze_repository("https://github.com/owner/repo")
    assert result.status == "success"
    assert result.score > 0

def test_analyze_repository_invalid_url():
    """Test analysis with invalid URL."""
    with pytest.raises(InvalidURLError):
        analyze_repository("invalid-url")
```

#### Frontend Tests (Jest/React Testing Library)

```typescript
import { render, screen } from "@testing-library/react";
import { RepositoryAnalysis } from "./RepositoryAnalysis";

test("renders repository analysis component", () => {
  render(
    <RepositoryAnalysis
      repositoryUrl="https://github.com/owner/repo"
      onAnalysisComplete={jest.fn()}
    />
  );

  expect(screen.getByText(/analyze repository/i)).toBeInTheDocument();
});
```

### Running Tests

```bash
# All tests with coverage
./scripts/test.sh --coverage

# Specific package
./scripts/test.sh --package core

# Integration tests
./scripts/test.sh --integration

# Docker-based testing
./scripts/test.sh --docker
```

## Documentation

### Code Documentation

- **Python**: Google-style docstrings
- **TypeScript**: JSDoc comments
- **README files**: Each package should have comprehensive README

### API Documentation

- **API Endpoints**: Documented in OpenAPI/Swagger format
- **Auto-generated**: Available at `/docs` when API server is running

### User Documentation

- **Getting Started**: Clear setup instructions
- **Examples**: Real-world usage examples
- **Troubleshooting**: Common issues and solutions

## Pull Request Process

### Before Submitting

1. **Rebase**: Ensure your branch is up-to-date with main
2. **Test**: All tests pass locally
3. **Lint**: Code follows style guidelines
4. **Documentation**: Updates included if needed

### PR Requirements

- [ ] **Title**: Clear, descriptive title
- [ ] **Description**: Detailed description of changes
- [ ] **Tests**: New tests for new functionality
- [ ] **Documentation**: Updated documentation
- [ ] **Breaking Changes**: Clearly marked and documented

### Review Process

1. **Automated Checks**: CI/CD pipeline must pass
2. **Code Review**: At least one maintainer review
3. **Testing**: Manual testing if required
4. **Approval**: Maintainer approval required for merge

### After Merge

- **Cleanup**: Delete feature branch
- **Monitor**: Watch for any issues in production
- **Follow-up**: Address any post-merge feedback

## Release Process

### Versioning

We use [Semantic Versioning](https://semver.org/):

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Steps

1. **Update Version**: Update version in `pyproject.toml` files
2. **Update Changelog**: Document changes in `CHANGELOG.md`
3. **Create Release**: Tag and create GitHub release
4. **Deploy**: Automated deployment via CI/CD
5. **Announce**: Notify users of new release

## Getting Help

### Resources

- **Documentation**: Check package README files
- **Examples**: Look at existing code and tests
- **Issues**: Search existing GitHub issues
- **Discussions**: Use GitHub Discussions for questions

### Contact

- **GitHub Issues**: For bug reports and feature requests
- **GitHub Discussions**: For questions and general discussion
- **Email**: [maintainer-email] for security issues

## Recognition

Contributors will be recognized in:

- **README.md**: Contributors section
- **Release Notes**: Highlighting major contributions
- **GitHub**: Contributor recognition features

Thank you for contributing to AI Project Analyzer! 🚀
