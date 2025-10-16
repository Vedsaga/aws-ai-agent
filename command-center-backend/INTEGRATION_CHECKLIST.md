# Backend-Dashboard Integration Checklist

Use this checklist to ensure complete and correct integration between the Command Center Backend and Dashboard.

---

## Pre-Integration Checklist

### Backend Deployment

- [ ] Backend deployed successfully to AWS
- [ ] All Lambda functions created and running
- [ ] DynamoDB table created with correct schema
- [ ] Bedrock Agent configured and tested
- [ ] API Gateway endpoints accessible
- [ ] API key generated and retrieved
- [ ] Database populated with simulation data
- [ ] CloudWatch logs showing no errors
- [ ] Cost monitoring alarms configured

### Backend Verification

- [ ] Run integration tests: `npm run test:integration`
- [ ] Test updates endpoint with curl
- [ ] Test query endpoint with curl
- [ ] Test action endpoint with curl
- [ ] Verify Bedrock Agent in AWS Console
- [ ] Check DynamoDB has data: `aws dynamodb scan --table-name MasterEventTimeline --select COUNT`
- [ ] Review CloudWatch logs for errors

### Documentation

- [ ] API endpoint URL documented
- [ ] API key securely stored
- [ ] API documentation reviewed (`API_DOCUMENTATION.md`)
- [ ] Deployment guide reviewed (`DEPLOYMENT_GUIDE.md`)
- [ ] Integration guide reviewed (`INTEGRATION_GUIDE.md`)

---

## Dashboard Configuration

### Environment Setup

- [ ] Create/update `.env.local` in dashboard directory
- [ ] Set `NEXT_PUBLIC_API_BASE_URL` to backend endpoint
- [ ] Set `NEXT_PUBLIC_API_KEY` to API key value
- [ ] Set `NEXT_PUBLIC_USE_MOCK_API=false` (if using conditional API)
- [ ] Verify `.env.local` is in `.gitignore`
- [ ] Document environment variables for team

### Code Updates

- [ ] Copy `apiService.ts` to dashboard services directory
- [ ] Update imports from `mockApiService` to `apiService`
- [ ] Add error handling for API calls
- [ ] Implement loading states for API requests
- [ ] Add health check on dashboard startup
- [ ] Update TypeScript types to match backend contracts
- [ ] Remove or comment out mock data imports (if not needed)

### Files to Update

- [ ] `app/page.tsx` - Main page component
- [ ] `components/ChatPanel.tsx` - Chat interface
- [ ] `components/InteractionPanel.tsx` - Action buttons
- [ ] `components/MapComponent.tsx` - Map updates (if needed)
- [ ] `store/useStore.ts` - State management (if needed)
- [ ] Any other components using API service

---

## Integration Testing

### Manual Testing - Basic Functionality

- [ ] Dashboard loads without errors
- [ ] Initial data loads from backend
- [ ] Map displays incidents from backend
- [ ] Chat panel is functional
- [ ] Can send a simple query: "What are the most urgent needs?"
- [ ] AI responds with real data
- [ ] Map updates based on query response
- [ ] Critical alerts appear in alerts panel

### Manual Testing - Query Types

- [ ] Simple query: "Show me the current situation"
- [ ] Domain query: "Show me all medical incidents"
- [ ] Location query: "What's happening in Nurdağı?"
- [ ] Time query: "Show me incidents from the last 6 hours"
- [ ] Severity query: "Show me critical incidents"
- [ ] Resource query: "Where are the medical resources?"
- [ ] Supply query: "Where are the food and water supply gaps?"

### Manual Testing - Actions

- [ ] Click "Generate Area Briefing" action
- [ ] Click "Show Critical Incidents" action
- [ ] Click any suggested action from AI response
- [ ] Verify actions execute and return results
- [ ] Verify map updates correctly for actions

### Manual Testing - Map Functionality

- [ ] Map layers render correctly
- [ ] Point markers appear with correct icons
- [ ] Polygon layers render with correct styling
- [ ] Map zooms/pans to relevant areas (viewState)
- [ ] Click on markers shows correct information
- [ ] Map action REPLACE clears previous layers
- [ ] Map action APPEND adds to existing layers

### Manual Testing - Updates Polling

- [ ] Let dashboard run for 1 minute
- [ ] Verify polling requests in network tab
- [ ] Check that new events appear (if any)
- [ ] Verify `latestTimestamp` updates correctly
- [ ] Test domain filter with updates
- [ ] Verify critical alerts update

### Manual Testing - Session Continuity

- [ ] Ask initial query: "Show me medical incidents"
- [ ] Ask follow-up: "How many are critical?"
- [ ] Ask another follow-up: "Show them on the map"
- [ ] Verify AI maintains context across queries

### Manual Testing - Error Handling

- [ ] Test with invalid API key (should show error)
- [ ] Test with network disconnected (should handle gracefully)
- [ ] Test with malformed query (should handle gracefully)
- [ ] Test with very long query (should handle gracefully)
- [ ] Verify error messages are user-friendly

### Browser Console Checks

- [ ] No JavaScript errors
- [ ] No CORS errors
- [ ] API requests show 200 status codes
- [ ] Response data structures are correct
- [ ] No authentication errors
- [ ] No network errors

### Network Tab Checks

- [ ] API requests include `x-api-key` header
- [ ] Requests go to correct endpoint
- [ ] Response times are acceptable (< 3s for queries)
- [ ] No failed requests
- [ ] Polling interval is correct

---

## Data Contract Verification

### Updates Endpoint Response

- [ ] `latestTimestamp` is present and valid ISO 8601
- [ ] `mapUpdates.mapAction` is "APPEND" or "REPLACE"
- [ ] `mapUpdates.mapLayers` is an array
- [ ] Each layer has `layerId`, `layerName`, `geometryType`, `style`, `data`
- [ ] `data` is valid GeoJSON FeatureCollection
- [ ] `criticalAlerts` is an array (if present)
- [ ] Each alert has required fields

### Query/Action Endpoint Response

- [ ] `simulationTime` is present
- [ ] `timestamp` is valid ISO 8601
- [ ] `chatResponse` contains text
- [ ] `mapAction` is "REPLACE" or "APPEND"
- [ ] `mapLayers` is an array
- [ ] `viewState` has valid bounds or center/zoom (if present)
- [ ] `uiContext.suggestedActions` is an array (if present)
- [ ] Each suggested action has `label`, `actionId`

### GeoJSON Validation

- [ ] All features have valid geometry
- [ ] Coordinates are [longitude, latitude] (not reversed)
- [ ] Point geometries render correctly
- [ ] Polygon geometries render correctly
- [ ] Feature properties are accessible

---

## Performance Testing

### Response Times

- [ ] Initial load: < 3 seconds
- [ ] Simple query: < 3 seconds
- [ ] Complex query: < 5 seconds
- [ ] Updates polling: < 500ms
- [ ] Action execution: < 3 seconds

### Load Testing

- [ ] Test with 10 concurrent users
- [ ] Test rapid-fire queries (5 in 10 seconds)
- [ ] Test long-running session (30 minutes)
- [ ] Monitor backend CloudWatch metrics
- [ ] Check for Lambda throttling
- [ ] Check for DynamoDB throttling

### Optimization

- [ ] Implement request debouncing for queries
- [ ] Add caching for repeated queries (optional)
- [ ] Optimize polling frequency
- [ ] Add loading indicators for all API calls
- [ ] Implement request cancellation for abandoned queries

---

## Production Readiness

### Security

- [ ] API key not committed to version control
- [ ] Environment variables properly configured
- [ ] CORS configured for production dashboard URL
- [ ] API rate limiting tested
- [ ] No sensitive data in logs
- [ ] HTTPS enforced for all requests

### Monitoring

- [ ] CloudWatch dashboard configured
- [ ] Error alerts set up
- [ ] Cost alerts configured
- [ ] API usage tracking implemented
- [ ] User analytics configured (optional)

### Documentation

- [ ] API endpoint documented for team
- [ ] API key access documented
- [ ] Common queries documented
- [ ] Troubleshooting guide available
- [ ] User guide created (optional)

### Deployment

- [ ] Production environment variables set
- [ ] Dashboard deployed to production
- [ ] Backend CORS updated for production URL
- [ ] DNS configured (if applicable)
- [ ] SSL certificate configured (if applicable)

---

## Post-Integration Tasks

### User Acceptance Testing

- [ ] Conduct UAT with stakeholders
- [ ] Gather feedback on AI responses
- [ ] Test with real user scenarios
- [ ] Document common use cases
- [ ] Identify areas for improvement

### Optimization

- [ ] Review Bedrock Agent instruction prompt
- [ ] Refine based on user feedback
- [ ] Add more pre-defined actions
- [ ] Optimize query patterns
- [ ] Improve error messages

### Training

- [ ] Create user training materials
- [ ] Document best practices for queries
- [ ] Provide example queries
- [ ] Train support team
- [ ] Create FAQ document

### Maintenance

- [ ] Set up regular health checks
- [ ] Schedule periodic data refreshes
- [ ] Plan for schema updates
- [ ] Document update procedures
- [ ] Establish support process

---

## Automated Testing Script

Run the automated integration test:

```bash
cd command-center-backend
API_ENDPOINT=https://your-api.com \
API_KEY=your-key \
./scripts/test-integration.sh
```

Expected output: All tests pass

---

## Sign-Off

### Backend Team

- [ ] Backend deployed and verified
- [ ] API documentation provided
- [ ] Integration support provided
- [ ] Monitoring configured

**Signed**: _________________ Date: _________

### Frontend Team

- [ ] Dashboard integrated with backend
- [ ] All tests passing
- [ ] User acceptance complete
- [ ] Production ready

**Signed**: _________________ Date: _________

### Project Manager

- [ ] Integration complete
- [ ] Requirements met
- [ ] Ready for production

**Signed**: _________________ Date: _________

---

## Troubleshooting Reference

If you encounter issues, refer to:

1. **INTEGRATION_GUIDE.md** - Detailed integration instructions
2. **API_DOCUMENTATION.md** - API reference and examples
3. **DEPLOYMENT_GUIDE.md** - Backend deployment and configuration
4. **Backend CloudWatch Logs** - Detailed error information
5. **Browser Console** - Frontend error information

---

**Last Updated**: [Current Date]
**Version**: 1.0.0
