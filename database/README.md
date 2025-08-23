# VectorBid Database Project

**Separate database project for VectorBid contract management and authentication**

## Overview

This database project handles:
- Pilot authentication and user management
- Contract rules storage and versioning
- FAR 117 regulatory compliance data
- Audit trails and security logging
- Performance-optimized rule lookups

## Architecture

```
VectorBid-Database/
├── migrations/           # Database schema migrations
├── schemas/             # SQL schema definitions
├── seeds/               # Default data (FAR 117, sample contracts)
├── indexes/             # Database indexes for performance
├── triggers/            # Database triggers for auditing
├── views/               # Optimized views for common queries
└── tests/               # Database integration tests
```

## Requirements

- PostgreSQL 14+
- Alembic for migrations
- Full audit trail capability
- High-performance rule lookups
- Multi-tenant airline support
- Comprehensive security model

## Getting Started

See individual README files in each directory for setup instructions.

## Security Considerations

- All pilot data encrypted at rest
- Comprehensive audit logging
- Role-based access control
- No direct database access in production