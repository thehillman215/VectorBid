# VectorBid Design Document

## Overview

VectorBid is an AI-powered pilot scheduling platform that streamlines aviation professionals' bid package management through intelligent administrative tools and secure document handling. The system helps airline pilots analyze and rank trip bids using OpenAI's GPT-4o model.

## Architecture

### Directory Structure

```
src/
├── core/           # Core application components
│   ├── app.py      # Flask application factory and configuration
│   ├── models.py   # Database models (SQLAlchemy)
│   └── extensions.py # Flask extensions configuration
├── api/            # API routes and handlers
│   ├── routes.py   # Main application routes
│   └── admin.py    # Admin API endpoints with Bearer auth
├── auth/           # Authentication modules
│   ├── replit_auth.py    # Replit OAuth integration
│   └── auth_helpers.py   # Authentication utilities
├── lib/            # Business logic and utilities
│   ├── services/         # Service layer
│   │   ├── bids.py      # Bid package management
│   │   └── db.py        # Database utilities
│   ├── schedule_parser/  # Multi-format schedule parsing
│   │   ├── pdf_parser.py
│   │   ├── csv_parser.py
│   │   └── txt_parser.py
│   ├── llm_service.py   # OpenAI GPT-4o integration
│   ├── bid_layers_*.py  # Advanced bid layering system
│   └── welcome/         # User onboarding flows
└── ui/             # User interface components
    └── templates/  # Jinja2 templates

tests/
├── e2e/           # End-to-end tests
├── legacy/        # Legacy test files
└── fixtures/      # Test data and fixtures

archive/
├── docs/          # Historical documentation
├── samples/       # Sample data files
└── test_files/    # Archived test files

bids/              # Bid package storage
├── metadata/      # Package metadata
└── *.pdf          # Stored bid packages
```

### Core Components

#### 1. Application Factory (`src/core/app.py`)
- Implements Flask application factory pattern
- Configures middleware, extensions, and error handlers
- Manages blueprint registration with fallback mechanisms
- Handles database initialization and table creation

#### 2. Database Models (`src/core/models.py`)
- **User**: Consolidated user model with authentication and pilot profile data
- **BidAnalysis**: Stores AI analysis results for trip rankings
- **BidPacket**: Manages monthly bid package PDFs
- **OAuth**: Handles Replit Auth token storage

#### 3. Authentication System (`src/auth/`)
- **replit_auth.py**: OAuth2 integration with Replit Auth
- **auth_helpers.py**: User session management and authorization decorators
- Supports secure Bearer token authentication for admin endpoints

#### 4. API Layer (`src/api/`)
- **routes.py**: Main application routes for pilot interactions
- **admin.py**: Administrative endpoints with Bearer token protection
- Handles file uploads, bid package validation, and user onboarding

#### 5. Business Logic (`src/lib/`)
- **services/bids.py**: Bid package storage and retrieval with metadata
- **services/db.py**: User profile management using Replit DB
- **schedule_parser/**: Multi-format parsing system for airline schedules
- **llm_service.py**: OpenAI GPT-4o integration for intelligent trip ranking

### Key Features

#### Bid Package Management
- Secure upload via Bearer token authentication
- Multi-format parsing (PDF, CSV, TXT)
- Metadata storage and validation
- One-click validation preview with parsing results

#### AI-Powered Trip Ranking
- Natural language preference input
- GPT-4o model integration for intelligent analysis
- Automated bid package matching based on pilot profiles
- Personalized trip recommendations

#### User Onboarding
- 3-step HTMX-powered wizard
- Predefined and custom flying style personas
- Profile completion tracking
- Automatic redirection for incomplete profiles

#### Enhanced Bid Layers System
- Advanced filtering and scoring
- Weekend preferences, layover optimization
- Trip length preferences
- Dynamic scoring algorithms

## Data Flow

1. **User Authentication**: Replit Auth handles OAuth flow
2. **Profile Management**: User data stored in Replit DB
3. **Bid Package Upload**: Admins upload via secure API
4. **Schedule Parsing**: Multi-layered parsing system extracts trip data
5. **AI Analysis**: GPT-4o ranks trips based on user preferences
6. **Results Display**: Ranked results with export capabilities

## Security

- Bearer token authentication for admin endpoints
- Secure token comparison using secrets.compare_digest()
- OAuth2 integration with Replit Auth
- Input validation and sanitization
- File type and size restrictions

## Database Strategy

- **PostgreSQL**: Main application data (complex relational data)
- **Replit DB**: User profiles (simplified key-value storage)
- **SQLAlchemy ORM**: Database abstraction and migrations

## Performance Considerations

- Lazy loading of PyMuPDF for PDF processing
- Connection pooling with pre-ping for database reliability
- Efficient file storage with metadata caching
- Modular architecture for scalable component loading

## Deployment

- Flask application with Gunicorn WSGI server
- Environment-based configuration
- Database migrations through SQLAlchemy
- Health check endpoints for monitoring

## Future Enhancements

- Real-time collaboration features
- Mobile-responsive interface improvements
- Advanced analytics and reporting
- Integration with additional airline systems
- Machine learning model training on historical data