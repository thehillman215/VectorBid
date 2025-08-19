#!/bin/bash

# VectorBid Smoke Test Script
# Tests basic functionality and health endpoints

set -e

echo "🚀 Starting VectorBid smoke tests..."

# Check if server is running
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "❌ Server not running on localhost:8000"
    echo "   Start with: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
    exit 1
fi

echo "✅ Server is running"

# Test health endpoints
echo "🔍 Testing health endpoints..."

echo "  Testing /health..."
HEALTH_RESPONSE=$(curl -s http://localhost:8000/health)
if echo "$HEALTH_RESPONSE" | grep -q '"status":"ok"' && echo "$HEALTH_RESPONSE" | grep -q '"rule_packs"'; then
    echo "  ✅ /health endpoint working (includes rule packs)"
else
    echo "  ❌ /health endpoint failed"
    echo "  Response: $HEALTH_RESPONSE"
    exit 1
fi

echo "  Testing /ping..."
PING_RESPONSE=$(curl -s http://localhost:8000/ping)
if echo "$PING_RESPONSE" | grep -q '"ping":"pong"'; then
    echo "  ✅ /ping endpoint working"
else
    echo "  ❌ /ping endpoint failed"
    echo "  Response: $PING_RESPONSE"
    exit 1
fi

echo "  Testing /api/meta/health..."
META_HEALTH_RESPONSE=$(curl -s http://localhost:8000/api/meta/health)
if echo "$META_HEALTH_RESPONSE" | grep -q '"ok":true'; then
    echo "  ✅ /api/meta/health endpoint working"
else
    echo "  ❌ /api/meta/health endpoint failed"
    echo "  Response: $META_HEALTH_RESPONSE"
    exit 1
fi

# Test basic API functionality
echo "🔍 Testing basic API functionality..."

echo "  Testing /docs endpoint..."
if curl -s http://localhost:8000/docs | grep -q "VectorBid API"; then
    echo "  ✅ API documentation accessible"
else
    echo "  ❌ API documentation not accessible"
    exit 1
fi

echo "  Testing /schemas endpoint..."
SCHEMAS_RESPONSE=$(curl -s http://localhost:8000/schemas)
if echo "$SCHEMAS_RESPONSE" | grep -q "PreferenceSchema"; then
    echo "  ✅ Schema endpoint working"
else
    echo "  ❌ Schema endpoint failed"
    echo "  Response preview: ${SCHEMAS_RESPONSE:0:100}..."
    exit 1
fi

# Test rule pack loading (if available)
echo "🔍 Testing rule pack functionality..."

if [ -f "rule_packs/UAL/2025.08.yml" ]; then
    echo "  ✅ Rule pack file exists"
    
    # Check if rule pack has required fields
    if grep -q "version:" rule_packs/UAL/2025.08.yml && grep -q "airline:" rule_packs/UAL/2025.08.yml; then
        echo "  ✅ Rule pack structure valid"
    else
        echo "  ❌ Rule pack structure invalid"
        exit 1
    fi
else
    echo "  ⚠️  No rule packs found (this is okay for basic smoke test)"
fi

echo ""
echo "🎉 All smoke tests passed!"
echo "   VectorBid is running and healthy on http://localhost:8000"
echo ""
echo "📚 Next steps:"
echo "   - Visit http://localhost:8000/docs for API documentation"
echo "   - Run 'pytest' for comprehensive testing"
echo "   - Check docs/DEVELOPER_QUICKSTART.md for development setup"
