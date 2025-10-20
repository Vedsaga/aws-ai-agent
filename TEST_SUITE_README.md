# API Test Suite - Quick Start Guide

## Overview

This comprehensive test suite validates all API endpoints of the Multi-Agent Orchestration System, including:

- ✅ Config API (Agent, Domain, Playbook, Dependency Graph CRUD)
- ✅ Data API (Retrieval, Spatial, Analytics, Aggregation, Vector Search)
- ✅ Ingest API (Report submission)
- ✅ Query API (Question answering)
- ✅ Tool Registry API (Tool management)
- ✅ Authentication and Authorization
- ✅ Error Handling
- ✅ Edge Cases
- ✅ Performance Testing

## Prerequisites

1. Python 3.7 or higher
2. `requests` library: `pip install requests`
3. API URL and JWT token

## Quick Start

### 1. Set Environment Variables

```bash
export API_URL="https://your-api-gateway-url.amazonaws.com/"
export JWT_TOKEN="your-jwt-token-here"
```

### 2. Run the Test Suite

```bash
python test_api.py
```

### 3. View Results

The test suite will:
- Display real-time test results in the console
- Generate a detailed `TEST_REPORT.md` file
- Exit with code 0 (success) or 1 (failure)

## Getting a JWT Token

If you need to obtain a JWT token for testing:

```bash
# Using AWS CLI to authenticate with Cognito
aws cognito-idp initiate-auth \
  --auth-flow USER_PASSWORD_AUTH \
  --client-id YOUR_CLIENT_ID \
  --auth-parameters USERNAME=testuser,PASSWORD=YourPassword123! \
  --region us-east-1 \
  --query 'AuthenticationResult.IdToken' \
  --output text
```

## Test Categories

### 1. Authentication Tests (5 tests)
- No authorization header
- Invalid JWT token
- Expired JWT token
- Valid JWT token
- Tenant ID scoping

### 2. Config API - Agent CRUD (6 tests)
- Create agent
- List agents
- Get specific agent
- Update agent
- Delete agent
- Verify deletion

### 3. Config API - Domain CRUD (6 tests)
- Create domain
- List domains
- Get specific domain
- Update domain
- Delete domain
- Verify deletion

### 4. Config API - Dependency Graph (2 tests)
- List dependency graphs
- Verify dependency relationships

### 5. Data API (9 tests)
- Retrieve incidents
- Filter by date range
- Filter by location (bbox)
- Filter by category
- Pagination
- Spatial queries
- Analytics queries
- Aggregation queries
- Vector search

### 6. Ingest API (6 tests)
- Submit text-only report
- Submit report with images
- Invalid domain ID
- Missing required fields
- Extremely long text
- Special characters and Unicode

### 7. Query API (5 tests)
- Ask simple question
- Ask complex question
- Invalid domain ID
- Missing required fields
- Extremely long question

### 8. Tool Registry API (4 tests)
- List all tools
- Verify built-in tools present
- Verify tool schema
- Get tool details

### 9. Error Handling (5 tests)
- 400 errors include validation details
- 401 errors include authentication guidance
- 404 errors include resource identification
- Error response format consistency
- User-friendly error messages

### 10. Edge Cases (8 tests)
- Missing required fields
- Invalid data types
- Out-of-range values
- Empty strings and arrays
- Null values
- Special characters and Unicode
- Malformed JSON
- Concurrent requests

### 11. Performance (6 tests)
- Config API response time (< 500ms)
- Data API response time (< 1000ms)
- Ingest API response time (< 2000ms)
- Query API response time (< 2000ms)
- 10 concurrent requests
- Pagination performance

## Expected Results

**Total Tests:** ~62 tests  
**Expected Duration:** 2-5 minutes  
**Target Pass Rate:** > 90%

## Troubleshooting

### Issue: "API_URL environment variable is required"
**Solution:** Set the API_URL environment variable:
```bash
export API_URL="https://your-api-url.com/"
```

### Issue: "WARNING: JWT_TOKEN not provided"
**Solution:** Set the JWT_TOKEN environment variable or authentication tests will be skipped:
```bash
export JWT_TOKEN="your-jwt-token"
```

### Issue: Many 401 errors
**Solution:** Your JWT token may be expired. Generate a new token using the Cognito authentication command above.

### Issue: Connection errors
**Solution:** Verify:
1. API URL is correct and accessible
2. Network connectivity
3. API Gateway is deployed and running

### Issue: 404 errors for domain "civic_complaints"
**Solution:** The test suite expects a domain called "civic_complaints" to exist. Either:
1. Create this domain in your system
2. Modify the test fixtures in `test_api.py` to use an existing domain

## Test Report

After running the tests, check `TEST_REPORT.md` for:
- Summary statistics
- Detailed results by category
- Failed test details with request/response data
- Performance metrics

## Continuous Integration

To use this test suite in CI/CD:

```bash
#!/bin/bash
# ci-test.sh

# Set environment variables
export API_URL="${CI_API_URL}"
export JWT_TOKEN="${CI_JWT_TOKEN}"

# Run tests
python test_api.py

# Check exit code
if [ $? -eq 0 ]; then
  echo "✅ All tests passed"
  exit 0
else
  echo "❌ Tests failed"
  cat TEST_REPORT.md
  exit 1
fi
```

## Customization

### Modify Test Fixtures

Edit the test fixtures at the top of `test_api.py`:

```python
TEST_AGENT = {
    "agent_name": "Your Custom Agent",
    # ... customize as needed
}

TEST_DOMAIN = {
    "domain_id": "your_domain",
    # ... customize as needed
}
```

### Skip Specific Tests

To skip specific test categories, comment out the test suite in the `run_all_tests()` method:

```python
test_suites = [
    # ("Authentication Tests", self.run_authentication_tests),  # Skip auth tests
    ("Config API - Agent CRUD Tests", self.run_config_agent_tests),
    # ... other tests
]
```

## Support

For issues or questions:
1. Check the TEST_REPORT.md for detailed error information
2. Review the API_REFERENCE.md for endpoint documentation
3. Check CloudWatch logs for backend errors
4. Verify your deployment is complete and healthy

## License

This test suite is part of the Multi-Agent Orchestration System project.
