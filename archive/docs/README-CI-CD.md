# VectorBid CI/CD Pipeline Documentation

This document describes the comprehensive GitHub Actions CI/CD pipeline implemented for VectorBid, an AI-powered pilot schedule bidding assistant.

## Overview

The CI/CD pipeline provides automated testing, code quality checks, security scanning, and Docker image packaging with every code push and pull request.

## Pipeline Components

### 1. GitHub Actions Workflows

#### Main CI/CD Pipeline (`.github/workflows/ci-cd.yml`)
A comprehensive multi-stage pipeline that includes:

**Test Stage:**
- PostgreSQL service container for database testing
- Python 3.11 environment setup
- System dependency installation (libpq-dev, gcc)
- Python dependency management with pip caching
- Linting with ruff (syntax errors, code style, formatting)
- Test execution with pytest and coverage reporting
- Codecov integration for coverage visualization

**Security Stage:**
- Bandit security scanning for Python code vulnerabilities
- Artifact upload for security scan results
- High and medium severity issue detection

**Build Stage:**
- Docker image building with BuildKit
- GitHub Container Registry (GHCR) integration
- Multi-platform image support with caching
- Automatic tagging with commit SHA and branch names
- Build metadata injection (commit SHA, build date)

**Deployment Stages:**
- Conditional staging deployment (develop branch)
- Conditional production deployment (main branch)
- Environment protection rules

**Notification Stage:**
- Success/failure notifications
- Comprehensive result reporting

#### Basic CI Pipeline (`.github/workflows/ci.yml`)
A streamlined version focusing on essential checks:
- Fast linting and testing
- PostgreSQL integration testing
- Essential security scanning
- Suitable for development branches

### 2. Docker Configuration

#### Dockerfile Features
```dockerfile
# Multi-stage build optimization
# Python 3.11 slim base image
# Non-root user security
# Health check implementation
# Build argument support for metadata
# Production-ready gunicorn configuration
```

**Security Features:**
- Non-root user execution (vectorbid:vectorbid)
- Minimal attack surface with slim image
- Health check endpoint monitoring
- Build metadata for traceability

**Performance Optimizations:**
- Layer caching for dependencies
- Multi-worker gunicorn setup
- Request handling optimizations
- Connection pooling configuration

#### .dockerignore
Comprehensive exclusion list for:
- Development files (.git, .idea, .vscode)
- Python artifacts (__pycache__, *.pyc)
- Test and documentation files
- CI/CD configuration files
- Temporary and log files

### 3. Code Quality Tools

#### Ruff Configuration (pyproject.toml)
**Linting Rules:**
- E: pycodestyle errors
- W: pycodestyle warnings  
- F: pyflakes (undefined variables, imports)
- I: isort (import sorting)
- B: flake8-bugbear (likely bugs)
- C4: flake8-comprehensions
- UP: pyupgrade (modern Python features)

**Formatting:**
- 88 character line length
- Automatic import sorting
- Per-file rule customization

#### Pytest Configuration
**Test Discovery:**
- Automatic test file detection (test_*.py)
- Markers for test categorization (slow, integration)
- Coverage reporting with exclusions
- Strict marker enforcement

**Coverage Settings:**
- Source code coverage measurement
- Exclusion of test files and utilities
- Missing line reporting
- Configurable thresholds

#### Bandit Security Scanning
**Security Checks:**
- SQL injection detection
- Hardcoded secrets scanning
- Insecure dependencies
- Code execution vulnerabilities

**Configuration:**
- Medium and high severity focus
- Test file exclusions
- Custom rule skipping where appropriate

### 4. Environment Configuration

#### Test Environment
```yaml
DATABASE_URL: postgresql://postgres:postgres@localhost:5432/vectorbid_test
SECRET_KEY: test-secret-key-for-github-actions
ADMIN_BEARER_TOKEN: test-admin-token-for-github-actions
FLASK_ENV: testing
```

#### Production Environment Variables
- `OPENAI_API_KEY`: AI service authentication
- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: Flask session encryption
- `ADMIN_BEARER_TOKEN`: Admin API authentication

## Workflow Triggers

### Automatic Triggers
- **Push to main branch**: Full CI/CD with production deployment
- **Push to develop branch**: Full CI/CD with staging deployment
- **Pull requests to main**: Complete testing and validation
- **Manual triggers**: Workflow dispatch support

### Branch Protection
- Require status checks to pass
- Require up-to-date branches
- Require review from code owners
- Automatic deployment on merge

## Docker Image Strategy

### Image Tagging
- `latest`: Latest main branch build
- `main-{SHA}`: Production builds with commit SHA
- `develop-{SHA}`: Development builds with commit SHA
- `{branch}-{SHA}`: Feature branch builds

### Registry Integration
- **GitHub Container Registry (GHCR)**: Primary registry
- **Automatic authentication**: Using GITHUB_TOKEN
- **Public/private visibility**: Configurable per repository
- **Retention policies**: Automatic cleanup of old images

## Test Strategy

### Unit Tests
- **Admin API Tests**: Authentication, validation, file upload
- **Parser Tests**: Schedule file processing (PDF, CSV, TXT)
- **Model Tests**: Database operations and relationships
- **Route Tests**: HTTP endpoint behavior

### Integration Tests
- **Database Integration**: PostgreSQL with real schemas
- **External API Mocking**: OpenAI service integration
- **File Processing**: Real schedule file parsing
- **Authentication Flow**: Complete OAuth integration

### Test Fixtures
- **Dummy PDF Files**: Sample bid packet documents
- **Database Fixtures**: Test data for models
- **Environment Setup**: Isolated test configurations
- **Mock Services**: External dependency simulation

## Deployment Architecture

### Staging Environment
- **Branch**: develop
- **Database**: Staging PostgreSQL instance
- **Environment**: staging
- **Domain**: staging.vectorbid.app (example)

### Production Environment
- **Branch**: main
- **Database**: Production PostgreSQL instance
- **Environment**: production  
- **Domain**: vectorbid.app (example)

### Rollback Strategy
- **Image versioning**: All builds tagged with commit SHA
- **Database migrations**: Reversible schema changes
- **Environment variables**: Version-controlled configurations
- **Health checks**: Automatic failure detection

## Monitoring and Observability

### Build Monitoring
- **GitHub Actions**: Build status and logs
- **Codecov**: Test coverage trends
- **GHCR**: Image vulnerability scanning
- **Bandit**: Security issue tracking

### Application Monitoring
- **Health checks**: Container health endpoints
- **Logging**: Structured application logs
- **Metrics**: Performance and usage metrics
- **Alerts**: Failure notification system

## Security Considerations

### Secret Management
- **GitHub Secrets**: Encrypted environment variables
- **Runtime Secrets**: Environment variable injection
- **Least Privilege**: Minimal permission grants
- **Rotation**: Regular secret updates

### Image Security
- **Non-root execution**: Restricted container privileges
- **Minimal base**: Reduced attack surface
- **Dependency scanning**: Vulnerability detection
- **Security policies**: Container runtime restrictions

### Code Security
- **Static analysis**: Bandit security scanning
- **Dependency audit**: Package vulnerability checks
- **Secret detection**: Hardcoded credential prevention
- **Code review**: Manual security review process

## Usage Examples

### Running Tests Locally
```bash
# Install dependencies
pip install -r requirements.txt

# Run linting
ruff check . --select=E9,F63,F7,F82
ruff format --check .

# Run security scan
bandit -r . -ll --exclude tests/

# Run tests with coverage
pytest tests/ -v --cov=. --cov-report=term-missing
```

### Building Docker Image
```bash
# Build with metadata
docker build -t vectorbid:latest \
  --build-arg COMMIT_SHA=$(git rev-parse HEAD) \
  --build-arg BUILD_DATE=$(date -Iseconds) .

# Run container
docker run -p 5000:5000 \
  -e DATABASE_URL="postgresql://..." \
  -e SECRET_KEY="your-secret-key" \
  vectorbid:latest
```

### Manual Deployment
```bash
# Tag and push image
docker tag vectorbid:latest ghcr.io/username/vectorbid:v1.0.0
docker push ghcr.io/username/vectorbid:v1.0.0

# Deploy to production
kubectl set image deployment/vectorbid \
  vectorbid=ghcr.io/username/vectorbid:v1.0.0
```

## Performance Metrics

### Build Performance
- **Average build time**: ~8-12 minutes
- **Test execution**: ~2-3 minutes
- **Docker build**: ~3-5 minutes
- **Parallel job execution**: Test, security, build stages

### Resource Usage
- **GitHub Actions minutes**: ~10-15 per full pipeline run
- **Storage**: ~500MB per Docker image
- **Bandwidth**: Optimized with layer caching
- **Compute**: 2-core runners for standard workflows

## Troubleshooting

### Common Issues
1. **Test failures**: Check database connectivity and environment variables
2. **Build failures**: Verify dependency versions and system requirements
3. **Security alerts**: Review bandit reports and update vulnerable dependencies
4. **Deployment failures**: Check container health and resource availability

### Debug Commands
```bash
# Check test logs
pytest tests/ -v -s --tb=long

# Validate Docker build
docker build --no-cache -t debug-build .

# Security scan details
bandit -r . -f json -o security-report.json
```

This comprehensive CI/CD pipeline ensures VectorBid maintains high code quality, security standards, and deployment reliability throughout the development lifecycle.