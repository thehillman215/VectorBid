# VectorBid

An AI-powered pilot scheduling platform that streamlines aviation professionals' bid package management through intelligent administrative tools and secure document handling.

## Quick Start

1. **Start the application**:
   ```bash
   # Application runs automatically on Replit
   # Access at: https://your-repl-name.replit.app
   ```

2. **Admin access** (requires Bearer token):
   ```bash
   curl -H "Authorization: Bearer YOUR_TOKEN" \
        https://your-repl-name.replit.app/admin/
   ```

## Project Structure

```
📁 VectorBid/
├── 🔧 src/                    # Source code
│   ├── core/                  # Core application (Flask app, models)
│   ├── api/                   # Routes and admin endpoints
│   ├── auth/                  # Authentication system
│   ├── lib/                   # Business logic and utilities
│   └── ui/                    # Templates and frontend
├── 🧪 tests/                  # Test suites
│   ├── e2e/                   # End-to-end tests
│   ├── legacy/                # Archived tests
│   └── fixtures/              # Test data
├── 📁 bids/                   # Bid package storage
├── 📚 docs/                   # Documentation
├── 🗄️ archive/                # Historical files
├── 🔧 main.py                 # Application entry point
├── 📋 replit.md               # Project configuration
└── 📄 README.md               # This file
```

## Features

### For Pilots
- **AI Trip Ranking**: Upload schedules, get intelligent trip recommendations
- **Natural Language Preferences**: "I prefer weekends off and short layovers"
- **Profile Management**: Airline, base, equipment, seniority tracking
- **Export Results**: CSV download of ranked trips

### For Administrators
- **Secure Upload**: Bearer token protected bid package uploads  
- **Validation Preview**: One-click parsing verification
- **Multi-format Support**: PDF, CSV, TXT schedule parsing
- **Metadata Management**: File storage with comprehensive metadata

### Technical Features
- **Multi-format Parsing**: Handles complex airline bid packages
- **GPT-4o Integration**: Advanced AI-powered trip analysis
- **Replit Auth**: Secure OAuth2 authentication
- **PostgreSQL**: Robust data storage with SQLAlchemy ORM
- **Responsive Design**: Mobile-first Bootstrap interface

## API Endpoints

### Main Application
- `GET /` - Main dashboard
- `POST /analyze_bid_package` - AI trip analysis
- `GET /results` - View ranked results
- `GET /how-to` - User guide

### Admin (Bearer Token Required)
- `GET /admin/` - Admin dashboard
- `POST /admin/upload-bid` - Upload bid packages
- `GET /admin/validate-bid/<month>` - Validate package
- `GET /admin/preview-bid/<month>` - Preview validation

## Configuration

### Environment Variables
```bash
DATABASE_URL=postgresql://...     # PostgreSQL connection
SECRET_KEY=your-secret-key       # Flask session encryption
ADMIN_BEARER_TOKEN=admin-token   # Admin API authentication
OPENAI_API_KEY=sk-...           # OpenAI API access
```

### Database Setup
The application automatically creates required tables on startup using SQLAlchemy migrations.

## Development

### Adding New Features
1. **Models**: Add to `src/core/models.py`
2. **Routes**: Add to `src/api/routes.py` or `src/api/admin.py`
3. **Business Logic**: Add to `src/lib/`
4. **Templates**: Add to `src/ui/templates/`

### Testing
```bash
# Run all tests
python -m pytest tests/

# Run specific test suite
python -m pytest tests/e2e/

# Run with coverage
python -m pytest tests/ --cov=src/
```

### File Organization Guidelines
- **src/core/**: Database models, Flask app factory
- **src/api/**: HTTP routes and request handlers
- **src/auth/**: Authentication and authorization
- **src/lib/**: Reusable business logic
- **src/ui/**: Frontend templates and assets
- **tests/**: All test files with clear categorization
- **archive/**: Historical files, samples, old documentation

## Architecture

### Key Design Decisions
- **Factory Pattern**: Modular Flask application creation
- **Service Layer**: Business logic separated from routes
- **Dual Database**: PostgreSQL for complex data, Replit DB for profiles
- **AI Integration**: GPT-4o for natural language trip analysis
- **Security First**: Bearer tokens, OAuth2, input validation

### Data Flow
1. User authenticates via Replit Auth
2. Profile stored in Replit DB
3. Admin uploads bid packages via secure API
4. Multi-layered parser extracts trip data
5. GPT-4o analyzes and ranks trips
6. Results displayed with export options

## Contributing

1. Follow the established directory structure
2. Add tests for new features
3. Update documentation for API changes
4. Use type hints for Python code
5. Follow Flask best practices

## Support

For technical issues or feature requests, refer to the project documentation in `docs/DESIGN.md` for detailed architectural information.

---

**Built with**: Flask, PostgreSQL, OpenAI GPT-4o, Replit Auth, Bootstrap