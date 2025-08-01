#!/bin/bash
# VectorBid United Airlines Rapid Development Workflow

set -e

echo "🚀 VectorBid United Airlines Development"
echo "======================================"

# Quick tests
quick() {
    echo "🧪 Quick United Tests..."
    python3 test_harness.py
}

# Test parser only
parser() {
    echo "🔍 Testing United Parser..."
    python3 test_harness.py parser
}

# Test ranking only  
ranking() {
    echo "🤖 Testing AI Ranking..."
    python3 test_harness.py ranking
}

# Performance test
perf() {
    echo "⚡ Performance Test..."
    python3 test_harness.py perf
}

# Watch mode
watch() {
    echo "👀 Watch Mode - Testing every 5 seconds..."
    echo "Press Ctrl+C to stop"
    while true; do
        clear
        echo "$(date): Running United tests..."
        python3 test_harness.py parser
        sleep 5
    done
}

# Test with real United data
united() {
    echo "✈️ Testing with United Sample Data..."

    # Create United sample file
    cat > /tmp/united_sample.txt << 'EOF'
UNITED AIRLINES BID PACKAGE - MARCH 2025
Base: DEN  Equipment: 737  Position: FO

UA123 3DAY 15MAR-17MAR DEN-LAX-DEN 18:30
UA456 4DAY 20MAR-23MAR DEN-LHR-FRA-DEN 25:12 SAT
789 2DAY 25MAR-26MAR DEN-PHX-DEN 12:00
UA101 737 5DAY DEN-NRT-ICN-DEN Credit: 32:15
UA202 1DAY DEN-ORD-DEN 06:45
EOF

    echo "  ✅ Created United sample: /tmp/united_sample.txt"

    # Test parsing if enhanced parser exists
    if [ -f "schedule_parser/united_patterns.py" ]; then
        python3 -c "
import sys
sys.path.append('.')
from schedule_parser.united_patterns import parse_united_content

with open('/tmp/united_sample.txt', 'r') as f:
    content = f.read()

trips = parse_united_content(content, 'united_sample.txt')
print(f'✅ Parsed {len(trips)} United trips:')
for i, trip in enumerate(trips[:3]):
    print(f'  {i+1}. {trip[\"trip_id\"]}: {trip[\"days\"]}d, {trip[\"credit_hours\"]}h')
"
    else
        echo "  ⚠️ Enhanced United parser not installed yet"
        echo "  Run: ./rapid_dev.sh install"
    fi
}

# Install enhanced parser
install() {
    echo "📦 Installing Enhanced United Parser..."

    if [ ! -d "schedule_parser" ]; then
        echo "  ❌ schedule_parser/ directory not found"
        echo "  Make sure you're in the VectorBid root directory"
        exit 1
    fi

    echo "  ✅ Ready to install United patterns"
    echo "  Copy the united_patterns.py file from Claude's artifact"
    echo "  Then run: ./rapid_dev.sh united"
}

# Main command handling
case "${1:-quick}" in
    "quick") quick ;;
    "parser") parser ;;
    "ranking") ranking ;;
    "perf") perf ;;
    "watch") watch ;;
    "united") united ;;
    "install") install ;;
    *)
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  quick    - Quick United tests (default)"
        echo "  parser   - Test United parser only"
        echo "  ranking  - Test AI ranking only"
        echo "  perf     - Performance benchmark"
        echo "  watch    - Continuous testing"
        echo "  united   - Test with United sample data"
        echo "  install  - Install enhanced parser"
        echo ""
        echo "Examples:"
        echo "  $0 quick    # Fast United feedback"
        echo "  $0 parser   # Test parsing only"
        echo "  $0 watch    # Continuous testing"
        ;;
esac