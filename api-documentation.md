# VectorBid API Documentation

This document describes the REST API endpoints for VectorBid, an AI-powered pilot schedule bidding assistant.

## Overview

VectorBid provides both web interface endpoints for pilot users and administrative API endpoints for managing bid packets. The application processes schedule files (PDF, CSV, TXT) and uses OpenAI's GPT-4o to rank trips based on user preferences.

## Base URLs

- **Production**: `https://your-repl.replit.app`
- **Development**: `http://localhost:5000`

## Authentication

### Admin Endpoints

Administrative endpoints require Bearer token authentication:

```http
Authorization: Bearer YOUR_ADMIN_TOKEN
```

The admin token is configured via the `ADMIN_BEARER_TOKEN` environment variable.

### User Authentication

User authentication is handled via Replit Auth OAuth flow. Users access protected features through web interface login.

## API Endpoints

### Web Interface Endpoints

#### GET /
Main landing page for the VectorBid application.

**Response**: HTML home page

#### POST /process
Process uploaded schedule file with user preferences.

**Request Body** (multipart/form-data):
- `schedule_file` (file): Schedule file in PDF, CSV, or TXT format
- `preferences` (string): Natural language trip preferences

**Response**: HTML results page with AI-ranked trips

**Example preferences**:
- "I prefer shorter trips with no weekend flying"
- "Routes through Denver with good layovers"
- "Maximum 3-day trips, avoid red-eyes"

#### GET /download_csv
Download previously processed ranked trips as CSV.

**Response**: CSV file with ranked trip data

**CSV Columns**:
- `rank`: AI-assigned ranking (1 is best)
- `trip_id`: Trip identifier
- `days`: Trip duration
- `credit_hours`: Flight hours earned
- `routing`: Route information
- `includes_weekend`: Boolean weekend indicator
- `comment`: AI explanation for ranking

### Authentication Endpoints

#### GET /replit_auth/logout
Log out current user and redirect to Replit logout.

#### GET /replit_auth/error
Display authentication error page.

### Administrative Endpoints

#### POST /admin/upload-bid
Upload monthly bid packet PDF.

**Authentication**: Bearer token required

**Request Body** (multipart/form-data):
- `month_tag` (string): Month in YYYYMM format (e.g., "202508")
- `file` (file): PDF bid packet file

**Response**:
```json
{
  "status": "ok",
  "stored": "202508"
}
```

**Month Tag Validation**:
- Must be exactly 6 digits
- Year: 2000-2099
- Month: 01-12

**Error Responses**:
- `400`: Invalid month_tag format or missing parameters
- `401`: Missing or invalid Bearer token
- `405`: Wrong HTTP method (only POST allowed)

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

## File Format Support

### PDF Files
- Airline bid packets (United, Delta, American, etc.)
- Multi-column layouts supported
- Date ranges: 12NOV-15NOV
- Routing codes: IAH-SFO-IAH
- Time formats: 18:30

### CSV Files
Expected columns:
- Trip ID
- Days/Duration
- Credit Hours
- Routing
- Dates
- Weekend indicator (optional)

### TXT Files
- Plain text schedule data
- Line-based trip entries
- Flexible parsing with pattern matching

## Error Handling

### HTTP Status Codes
- `200`: Success
- `302`: Redirect (typically to home page with flash message)
- `400`: Bad Request (invalid parameters)
- `401`: Unauthorized (missing/invalid authentication)
- `403`: Forbidden (authentication error page)
- `405`: Method Not Allowed

### Error Response Format
Web endpoints typically redirect with flash messages rather than returning JSON errors.

Admin endpoints return standard HTTP error responses.

## Rate Limiting

No explicit rate limiting is currently implemented. Administrative endpoints are protected by authentication.

## Examples

### Upload Schedule for Processing

```bash
curl -X POST http://localhost:5000/process \
  -F "schedule_file=@my_schedule.pdf" \
  -F "preferences=I prefer short trips with no weekend work"
```

### Upload Admin Bid Packet

```bash
curl -X POST http://localhost:5000/admin/upload-bid \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -F "month_tag=202508" \
  -F "file=@august_bid_packet.pdf"
```

### Download Ranked Trips CSV

```bash
curl -X GET http://localhost:5000/download_csv \
  -H "Cookie: session=your_session_cookie" \
  -o ranked_trips.csv
```

## Security Considerations

1. **Admin Authentication**: All admin endpoints require Bearer token authentication
2. **Session Management**: User sessions are managed via Flask sessions
3. **File Upload**: Only specific file types accepted (PDF, CSV, TXT)
4. **Input Validation**: Month tags and file formats are validated
5. **CSRF Protection**: Web forms include CSRF protection
6. **Secure Comparison**: Admin tokens use timing-safe comparison

## OpenAPI Specification

The complete OpenAPI 3.1 specification is available in:
- YAML format: `openapi.yaml`
- JSON format: `openapi.json`

These files can be used with API documentation tools like Swagger UI or imported into API testing tools like Postman.