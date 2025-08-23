# VectorBid Database Architecture

**Comprehensive database design for pilot contract management and regulatory compliance**

## 🏗️ Architecture Overview

This database is designed as a **separate project** from the main VectorBid application, providing:

1. **Complete FAR 117 Regulatory Coverage** - All 25+ federal aviation rules
2. **Pilot-Driven Contract Management** - Community-sourced airline contracts
3. **Bulletproof Security** - Authentication, audit trails, encryption
4. **High Performance** - Optimized for rule lookups and contract queries
5. **Multi-Airline Support** - Extensible to any airline

## 📊 Schema Design

### Core Tables

```mermaid
erDiagram
    users ||--|| pilots : has
    pilots ||--o{ pilot_contract_assignments : assigned
    pilot_contracts ||--o{ pilot_contract_assignments : used_by
    pilot_contracts ||--o{ contract_rules : contains
    pilot_contracts ||--o{ contract_reviews : reviewed
    regulatory_rules ||--|| airlines : applies_to
    
    users {
        uuid id PK
        string email UK
        string password_hash
        string role
        timestamp created_at
    }
    
    pilots {
        uuid id PK
        uuid user_id FK
        string pilot_id UK
        string airline FK
        string base
        string seat
        jsonb equipment
        decimal seniority_percentile
    }
    
    pilot_contracts {
        uuid id PK
        string airline FK
        string contract_version UK
        string status
        uuid uploaded_by FK
        uuid approved_by FK
        text source_document
    }
    
    contract_rules {
        uuid id PK
        uuid contract_id FK
        string rule_id UK
        string category
        text description
        boolean is_hard_constraint
        decimal weight
    }
```

### Key Features

**1. Complete FAR 117 Coverage (25+ Rules)**
- Flight duty period limits by report time
- Maximum flight time limits (2-pilot, 3-pilot, augmented)
- Minimum rest requirements (10h standard, 12h time zones)
- Cumulative limits (100h/28days, 1000h/365days)
- Reserve duty, split duty, deadhead rules
- Consecutive night operations limits
- Airport standby and training exclusions

**2. Multi-Layered Security**
- Bcrypt password hashing
- JWT session management with revocation
- Row-level security policies
- Comprehensive audit logging
- Security event monitoring
- Role-based access control

**3. Performance Optimization**
- Strategic indexes on all query paths
- Materialized views for common operations
- JSONB indexes for metadata queries
- Full-text search on contract content
- Connection pooling ready

## 🚀 Deployment Architecture

### Development Setup
```bash
# Start database with Docker
cd database/
docker-compose up -d postgres redis

# Run migrations
docker-compose run --rm migrations alembic upgrade head

# Access PgAdmin (optional)
docker-compose --profile dev-tools up -d pgadmin
# Visit: http://localhost:8080
```

### Production Considerations
- **Managed Database**: Use AWS RDS PostgreSQL or equivalent
- **Connection Pooling**: PgBouncer for connection management
- **Backup Strategy**: Automated daily backups with point-in-time recovery
- **Monitoring**: Database performance monitoring (DataDog, New Relic)
- **Security**: VPC isolation, encrypted connections, credential rotation

## 🔐 Security Model

### Authentication Flow
1. **User Registration**: Email verification required
2. **Login**: JWT token issued, session tracked
3. **Authorization**: Role-based access (pilot, admin, approver)
4. **Session Management**: Tokens can be revoked, expire after 24h
5. **Audit Trail**: All actions logged with user context

### Data Protection
- **Encryption at Rest**: Database encryption enabled
- **Password Security**: Bcrypt with 12 rounds
- **PII Protection**: No sensitive data in logs
- **Access Control**: Row-level security for pilot data

## 📈 Performance Characteristics

### Expected Scale
- **Users**: 10,000+ pilots across multiple airlines
- **Contracts**: 100+ contract versions (5-10 per airline)
- **Rules**: 5,000+ individual contract rules
- **Queries**: 1,000+ rule lookups per second during peak

### Optimization Strategy
- **Rule Lookups**: Sub-millisecond response via indexes
- **Contract Queries**: Materialized views for complex joins
- **Full-Text Search**: Trigram indexes for contract text
- **Caching Layer**: Redis for frequently accessed rules

## 🔄 Integration with VectorBid App

### API Integration Pattern
```python
# In main VectorBid app
from database.client import DatabaseClient

class ContractService:
    def __init__(self):
        self.db = DatabaseClient()
    
    async def get_pilot_rules(self, pilot_id: str) -> List[ContractRule]:
        """Load all applicable rules for a pilot"""
        return await self.db.get_pilot_active_rules(pilot_id)
    
    async def validate_preferences(self, pilot_id: str, preferences: dict) -> ValidationResult:
        """Validate preferences against pilot's contract"""
        rules = await self.get_pilot_rules(pilot_id)
        return self.rule_engine.validate(preferences, rules)
```

### Environment Variables
```bash
# Main app configuration
DATABASE_URL=postgresql://vectorbid_app:password@localhost:5432/vectorbid
REDIS_URL=redis://:password@localhost:6379/0
JWT_SECRET_KEY=your-secret-key-here

# Database connection pool
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10
DB_POOL_TIMEOUT=30
```

## 🧪 Testing Strategy

### Database Testing Levels
1. **Unit Tests**: Individual table constraints and triggers
2. **Integration Tests**: Cross-table queries and views
3. **Performance Tests**: Rule lookup performance under load
4. **Security Tests**: Authentication and authorization
5. **Migration Tests**: Schema changes and data integrity

### Test Data Management
- **Fixtures**: Realistic test data for all airlines
- **Anonymization**: Production data scrubbing for testing
- **Seed Scripts**: Consistent test environment setup

## 🚀 Migration Strategy

### Version Control
- **Alembic Migrations**: All schema changes versioned
- **Rollback Support**: Every migration has down script
- **Environment Sync**: Dev/staging/prod schema consistency
- **Data Migrations**: Safe data transformations

### Deployment Process
1. **Backup Database**: Before any migration
2. **Run Migrations**: Alembic upgrade in transaction
3. **Verify Schema**: Automated schema validation
4. **Health Check**: Application connectivity test
5. **Rollback Plan**: Immediate rollback if issues

---

## ✅ Issue #2 Status: Database Architecture Complete

**What's Implemented:**
- ✅ Comprehensive PostgreSQL schema (12 core tables)
- ✅ Complete FAR 117 rule set (25+ regulations)
- ✅ Pilot contract management system
- ✅ Multi-airline support with metadata
- ✅ Security model with authentication tables
- ✅ Audit trail and monitoring capabilities
- ✅ Performance indexes and optimizations
- ✅ Docker development environment
- ✅ Alembic migration system

**Ready for Issue #3:** Security and authentication implementation can now begin with the solid database foundation in place.

**Database is production-ready for**:
- Storing all FAR 117 rules
- Managing pilot contracts and rules
- Supporting multiple airlines
- Scaling to thousands of pilots
- Comprehensive security and auditing