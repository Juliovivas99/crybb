#!/usr/bin/env bash
# Test script to verify CryBB bot health endpoints

echo "🧪 Testing CryBB Bot Health Endpoints"
echo "======================================"

# Test health endpoint
echo "Testing /health endpoint..."
curl -s http://localhost:8000/health | jq . || echo "Health endpoint not responding"

echo ""
echo "Testing /metrics endpoint..."
curl -s http://localhost:8000/metrics | jq . || echo "Metrics endpoint not responding"

echo ""
echo "✅ Health endpoint test complete!"
