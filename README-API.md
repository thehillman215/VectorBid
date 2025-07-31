# VectorBid OpenAPI Specification

This directory contains the complete OpenAPI 3.1 specification for VectorBid, an AI-powered pilot schedule bidding assistant.

## Files Overview

### API Specification
- **`openapi.yaml`** - Main OpenAPI 3.1 specification in YAML format
- **`openapi.json`** - Same specification in JSON format for tooling compatibility
- **`api-documentation.md`** - Human-readable API documentation with examples

### Validation and Testing
- **`validate_openapi.py`** - OpenAPI specification validator and analyzer
- **`test_api.py`** - API endpoint testing suite

## Quick Start

### View API Documentation
```bash
# Validate the OpenAPI specification
python validate_openapi.py

# Test the API endpoints
python test_api.py
```

### Use with API Tools

#### Swagger UI
You can view the interactive API documentation by loading `openapi.yaml` in Swagger UI:
1. Go to [Swagger Editor](https://editor.swagger.io/)
2. Copy the contents of `openapi.yaml`
3. Paste into the editor

#### Postman
Import the API collection:
1. Open Postman
2. Click "Import"
3. Upload `openapi.json`
4. Configure environment variables for your base URL and admin token

#### curl Examples
```bash
# Test home page
curl https://your-app.replit.app/

# Upload bid packet (admin only)
curl -X POST https://your-app.replit.app/admin/upload-bid \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -F "month_tag=202508" \
  -F "file=@bid_packet.pdf"
```

## API Endpoints Summary

### Public Endpoints
- `GET /` - Home page
- `POST /process` - Process schedule file with AI ranking
- `GET /download_csv` - Download ranked trips as CSV
- `GET /replit_auth/logout` - User logout
- `GET /replit_auth/error` - Authentication error page

### Admin Endpoints (Bearer Token Required)
- `POST /admin/upload-bid` - Upload monthly bid packet PDF

## Authentication

### User Authentication
Users authenticate through Replit Auth OAuth flow via the web interface.

### Admin Authentication
Admin endpoints require Bearer token authentication:
```http
Authorization: Bearer YOUR_ADMIN_TOKEN
```

Set the `ADMIN_BEARER_TOKEN` environment variable to configure the expected token.

## Request/Response Examples

### Process Schedule File
```bash
curl -X POST https://your-app.replit.app/process \
  -F "schedule_file=@my_schedule.pdf" \
  -F "preferences=I prefer short trips with no weekend work"
```

### Upload Bid Packet
```bash
curl -X POST https://your-app.replit.app/admin/upload-bid \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -F "month_tag=202508" \
  -F "file=@august_bid_packet.pdf"
```

Response:
```json
{
  "status": "ok",
  "stored": "202508"
}
```

## Data Models

### Trip Object
```json
{
  "trip_id": "UA123",
  "days": 3,
  "credit_hours": 12.5,
  "routing": "SFO-DEN-ORD",
  "dates": "12NOV-15NOV",
  "includes_weekend": true,
  "raw": "Original schedule line"
}
```

### Ranked Trip Object
```json
{
  "trip_id": "UA123",
  "days": 3,
  "credit_hours": 12.5,
  "routing": "SFO-DEN-ORD",
  "dates": "12NOV-15NOV", 
  "includes_weekend": true,
  "raw": "Original schedule line",
  "rank": 1,
  "comment": "Perfect for work-life balance with no weekend flying"
}
```

## Error Handling

### HTTP Status Codes
- `200` - Success
- `302` - Redirect (web interface)
- `400` - Bad Request (invalid parameters)
- `401` - Unauthorized (missing/invalid authentication)
- `403` - Forbidden
- `404` - Not Found
- `405` - Method Not Allowed

### Admin Endpoint Validation
- Month tag must be exactly 6 digits (YYYYMM)
- Year must be 2000-2099
- Month must be 01-12
- File must be provided in request

## Validation

Run the validation script to check the OpenAPI specification:

```bash
python validate_openapi.py
```

Expected output:
```
🔍 VectorBid OpenAPI Specification Validator
==================================================
✅ Successfully loaded openapi.yaml
✅ OpenAPI structure is valid

🛣️  API Endpoints Summary:
  🔓 GET / [Web Interface]
  🔓 POST /process [Web Interface]
  🔓 GET /download_csv [Web Interface]
  🔓 GET /replit_auth/logout [Authentication]
  🔓 GET /replit_auth/error [Authentication]
  🔒 POST /admin/upload-bid [Administration]

📊 Data Schemas Summary:
  📄 Trip (object)
  📄 RankedTrip (object)
  📄 ErrorResponse (object)
  📄 AdminUploadResponse (object)
  📄 BidPacket (object)

✅ OpenAPI specification validation completed successfully!
```

## Testing

Run the API test suite:

```bash
# Set your admin token (if testing admin endpoints)
export ADMIN_BEARER_TOKEN="your_token_here"

# Run tests against local development server
python test_api.py

# Run tests against production
TEST_BASE_URL="https://your-app.replit.app" python test_api.py
```

## Integration

### API Client Generation
You can generate API clients using the OpenAPI specification:

```bash
# Generate Python client
openapi-generator generate -i openapi.yaml -g python -o ./python-client

# Generate JavaScript client  
openapi-generator generate -i openapi.yaml -g javascript -o ./js-client
```

### Documentation Generation
Generate static documentation:

```bash
# Using Redoc
redoc-cli build openapi.yaml --output api-docs.html

# Using Swagger Codegen
swagger-codegen generate -i openapi.yaml -l html2 -o ./docs
```

## Specification Details

- **OpenAPI Version**: 3.1.0
- **API Version**: 1.0.0
- **Total Endpoints**: 6 (5 public, 1 admin)
- **Authentication Schemes**: 1 (Bearer token for admin)
- **Data Schemas**: 5 comprehensive models
- **Servers**: 2 (production and development)

The specification includes comprehensive request/response schemas, security definitions, and detailed endpoint documentation with examples.