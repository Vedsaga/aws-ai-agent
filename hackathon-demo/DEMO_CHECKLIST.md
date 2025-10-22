# Demo Day Checklist

## Pre-Demo Setup (30 minutes before)

### AWS Infrastructure
- [ ] Stack deployed: `aws cloudformation describe-stacks --stack-name DomainFlowDemo`
- [ ] Lambda function exists: `aws lambda get-function --function-name domainflow-orchestrator`
- [ ] DynamoDB table exists: `aws dynamodb describe-table --table-name civic-reports`
- [ ] API Gateway endpoint accessible: `curl <API_URL>/reports`

### Test Data
- [ ] Run `./test-api.sh` to seed sample reports
- [ ] Verify reports in DynamoDB: `aws dynamodb scan --table-name civic-reports --max-items 5`
- [ ] Check map shows markers in frontend

### Frontend
- [ ] Mapbox token configured in `frontend/index.html`
- [ ] API endpoint configured in `frontend/index.html`
- [ ] Frontend loads without errors (check browser console)
- [ ] Map displays correctly
- [ ] All 3 mode buttons work

### Browser Setup
- [ ] Open frontend in browser
- [ ] Zoom to comfortable level
- [ ] Clear chat history (refresh page)
- [ ] Test one message to verify connection
- [ ] Close any error popups

### Presentation
- [ ] Demo script printed/accessible: `DEMO_SCRIPT.md`
- [ ] Talking points ready: `ARCHITECTURE.md`
- [ ] Backup slides ready (in case of technical issues)
- [ ] Screen recording software ready (optional)

## During Demo (5 minutes)

### Opening (30 seconds)
- [ ] Introduce DomainFlow concept
- [ ] Mention 3 agent classes
- [ ] Show frontend interface

### Scene 1: Ingestion (2 minutes)
- [ ] Type: "Street light broken near the post office"
- [ ] Wait for agent clarification question
- [ ] Point out status indicator
- [ ] Type: "Yes, it's at 123 Main Street"
- [ ] Wait for confirmation
- [ ] Show marker on map
- [ ] Click marker to show popup

### Scene 2: Query (1.5 minutes)
- [ ] Switch to Query mode
- [ ] Type: "Show me all high-priority streetlight issues"
- [ ] Wait for results
- [ ] Point to filtered map markers
- [ ] Mention count in response

### Scene 3: Management (1.5 minutes)
- [ ] Switch to Management mode
- [ ] Type: "Assign this report to Team B and make it due in 48 hours"
- [ ] Wait for confirmation
- [ ] Click marker to show updated assignment
- [ ] Emphasize real-time update

### Closing (30 seconds)
- [ ] Summarize what was shown
- [ ] Mention extensibility (new domains = new prompts)
- [ ] Thank audience

## Backup Plans

### If API is slow
- [ ] Have pre-recorded video ready
- [ ] Show screenshots of expected flow
- [ ] Walk through code instead

### If frontend breaks
- [ ] Use `curl` commands from terminal
- [ ] Show JSON responses
- [ ] Explain what UI would show

### If Bedrock throttles
- [ ] Have sample responses ready to paste
- [ ] Explain what agent would return
- [ ] Show DynamoDB data directly

### If map doesn't load
- [ ] Show GeoJSON in response
- [ ] Explain coordinates
- [ ] Use backup map screenshot

## Post-Demo

### Questions to Anticipate
- [ ] "How does this scale?" → See ARCHITECTURE.md
- [ ] "What about security?" → See COMPARISON.md
- [ ] "Can I try it?" → Share GitHub repo
- [ ] "How much does it cost?" → ~$6/month for demo
- [ ] "What's next?" → See migration path in COMPARISON.md

### Follow-Up Materials
- [ ] GitHub repo link ready
- [ ] Architecture diagram ready
- [ ] Contact info ready
- [ ] Demo video link (if recorded)

## Technical Troubleshooting

### Lambda timeout
```bash
# Increase timeout
aws lambda update-function-configuration \
  --function-name domainflow-orchestrator \
  --timeout 120
```

### DynamoDB empty
```bash
# Seed data
python3 test-client.py
```

### API Gateway CORS error
```bash
# Check CORS config
aws apigateway get-rest-api --rest-api-id <API_ID>
```

### Bedrock access denied
```bash
# Check IAM role
aws iam get-role-policy \
  --role-name DomainFlowDemo-OrchestratorRole \
  --policy-name BedrockAccess
```

### Frontend not connecting
```bash
# Test API directly
curl -X POST <API_URL>/orchestrate \
  -H "Content-Type: application/json" \
  -d '{"mode":"ingestion","message":"test"}'
```

## Emergency Contacts

- AWS Support: (if infrastructure issues)
- Mapbox Support: (if map issues)
- Team backup: (if presenter unavailable)

## Post-Demo Cleanup

### Keep Running (for follow-up demos)
- [ ] Leave stack deployed
- [ ] Keep test data
- [ ] Monitor costs

### Tear Down (if done)
```bash
cd cdk
cdk destroy
```

- [ ] Confirm stack deleted
- [ ] Verify no orphaned resources
- [ ] Check final AWS bill

## Success Metrics

- [ ] Demo completed without major issues
- [ ] Audience understood core concept
- [ ] Questions answered satisfactorily
- [ ] Interest generated (GitHub stars, contacts)
- [ ] Feedback collected

## Notes Section

Use this space for last-minute notes, changes, or observations:

```
[Your notes here]
```
