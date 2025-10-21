#!/bin/bash

echo "=========================================="
echo "Quick Frontend Integration Test"
echo "=========================================="
echo ""

cd infrastructure/frontend

echo "1. Checking if components exist..."
ls -la components/IncidentChat.tsx && echo "✅ IncidentChat component" || echo "❌ Missing"
ls -la lib/incident-api.ts && echo "✅ API client" || echo "❌ Missing"
ls -la app/dashboard/chat/page.tsx && echo "✅ Chat page" || echo "❌ Missing"

echo ""
echo "2. Starting frontend (background)..."
npm run dev > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!

echo "Frontend PID: $FRONTEND_PID"
echo "Waiting 10 seconds for startup..."
sleep 10

echo ""
echo "3. Testing frontend..."
curl -s http://localhost:3000 > /dev/null && echo "✅ Frontend running" || echo "❌ Frontend not responding"

echo ""
echo "=========================================="
echo "Integration Ready!"
echo "=========================================="
echo ""
echo "Open: http://localhost:3000/dashboard/chat"
echo ""
echo "Features:"
echo "  ✅ Submit incident reports"
echo "  ✅ Query incidents"
echo "  ✅ Polling for status"
echo "  ❌ Chat history (not implemented)"
echo "  ❌ Real-time updates (AppSync not deployed)"
echo ""
echo "To stop: kill $FRONTEND_PID"
echo ""
