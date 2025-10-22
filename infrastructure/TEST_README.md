# DomainFlow API Test Suite

Comprehensive test suite for the DomainFlow Agentic Orchestration Platform API. Tests all endpoints in chronological order from least to most dependent components.

## Features

- **Two Test Modes**:
  - **Mock Mode**: Tests API structure without deployment (no AWS resources needed)
  - **Deployed Mode**: Tests against actual deployed API endpoints

- **Comprehensive Coverage**:
  - Agent Management API (CRUD)
  - Domain Management API (CRUD)
  - Report Submission API
  - Session Management API
  - Query Submission API
  - Execution Log Verification

- **Chronological Testing**: Tests are ordered from least to most dependent components
- **Automatic Cleanup**: Created resources are automatically deleted after tests
- **Colored Output**: Easy-to-read test results with color coding
- **Demo Readiness Check**: Validates critical endpoints for demo preparation

## Prerequisites

### For Mock Mode
- Python 3.11+
- Required packages: `requests`, `boto3`

### For Deployed Mode
- All mock mode requirements
- Deployed DomainFlow API
- AWS Cognito credentials
- Environment variables configured

## Installation

```bash
# Install dependencies
pip install requests boto3

# Make the test script executable
chmod +x infrastructure/TEST.py
```

## Configuration

### Environment Variables

Create a `.env` file in the `infrastructure` directory:

```bash
# API Configuration
API_BASE_URL=https://your-api-gateway-url.execute-api.us-east-1.amazonaws.com/prod

# Cognito Configuration
COGNITO_CLIENT_ID=your-cognito-client-id
AWS_REGION=us-east-1

# Test User Credentials
TEST_USERNAME=your-test-username
TEST_PASSWORD=your-test-password
```

Load environment variables:
```bash
source infrastructure/.env
export $(cat infrastructure/.env | xargs)
```

## Usage

### Mock Mode (No Deployment Required)

Test the API structure without deploying to AWS:

```bash
python3 infrastructure/TEST.py --mode mock
```

This mode:
- Returns mock responses for all endpoints
- Validates request/response structure
- Tests the test suite logic itself
- Useful for development and CI/CD

### Deployed Mode (Test Real API)

Test against your deployed API:

```bash
python3 infrastructure/TEST.py --mode deployed
```

This mode:
- Makes actual HTTP requests to your API
- Validates authentication with Cognito
- Tests real agent execution and orchestration
- Automatically cleans up created resources

### Skip Cleanup

To keep created resources for inspection:

```bash
python3 infrastructure/TEST.py --mode deployed --no-cleanup
```

## Test Coverage

### Test Execution Order

Tests are executed in chronological order based on component dependencies:

1. **Authentication** (Test 1)
   - Validates JWT token requirement
   - Tests unauthorized access rejection

2. **Agent Management** (Tests 2-7)
   - List all agents
   - List agents filtered by class
   - Create agent
   - Get agent by ID (with dependency graph)
   - Update agent
   - Delete agent

3. **Domain Management** (Tests 8-12)
   - List all domains
   - Create domain (with 3 playbooks)
   - Get domain by ID
   - Update domain
   - Delete domain

4. **Report Submission** (Tests 13-16)
   - Submit report
   - Get report with ingestion_data
   - List reports filtered by domain
   - Update report management_data

5. **Session Management** (Tests 17-20)
   - Create session
   - List sessions
   - Get session with messages
   - Update session

6. **Query Submission** (Tests 21-24)
   - Submit query (read mode)
   - Submit query (management mode)
   - Get query result with execution_log
   - List queries by session

7. **Execution Log Verification** (Test 25)
   - Verify execution log structure
   - Validate reasoning and output fields

### Critical Tests for Demo

The following tests must pass for demo readiness:
- Agent - Create
- Agent - List All
- Domain - Create
- Domain - List All
- Report - Submit
- Report - Get with Schema
- Session - Create
- Query - Submit (Read)
- Query - Get with Execution Log

## Output Format

### Test Results

```
TEST: Create new agent
ℹ INFO - Status: 201
ℹ INFO - Response: {"agent_id": "agent-123", ...}
✓ PASS - Expected status 201
ℹ INFO - Created agent: agent-123
```

### Summary

```
================================================================================
                                  TEST SUMMARY                                  
================================================================================

Total Tests: 25
Passed: 24
Failed: 0
Skipped: 1
Success Rate: 96.0%

Detailed Results:
  ⊘ Authentication
  ✓ Agent - List All
  ✓ Agent - Create
  ...

================================================================================
                              DEMO READINESS CHECK                              
================================================================================

✓ READY FOR DEMO
All critical endpoints are working!
```

## Exit Codes

- `0`: All tests passed
- `1`: One or more tests failed

## Troubleshooting

### Mock Mode Issues

**Problem**: Tests fail in mock mode
- **Solution**: Check that the test logic is correct. Mock mode should always pass unless there's a bug in the test suite itself.

### Deployed Mode Issues

**Problem**: Authentication fails
- **Solution**: Verify `COGNITO_CLIENT_ID`, `TEST_USERNAME`, and `TEST_PASSWORD` are correct
- Check that the Cognito user pool allows `USER_PASSWORD_AUTH` flow

**Problem**: 404 errors on endpoints
- **Solution**: Verify `API_BASE_URL` is correct and includes the stage (e.g., `/prod`)
- Check that the API Gateway has been deployed

**Problem**: Tests timeout
- **Solution**: Increase timeout values in the code (default: 30 seconds)
- Check Lambda function logs for errors

**Problem**: Cleanup fails
- **Solution**: Manually delete resources using AWS Console or CLI
- Use `--no-cleanup` flag to skip automatic cleanup

## Development

### Adding New Tests

1. Add test method to `APITester` class
2. Add mock response handler if needed
3. Call test method in `run_all_tests()`
4. Update critical tests list if needed

Example:

```python
def test_new_feature(self):
    """Test X: New Feature"""
    print_section("TEST X: New Feature")
    
    print_test("Test new endpoint")
    success, response = self.make_request("GET", "/api/v1/new", expected_status=200)
    self.results.add_result("New Feature - Test", success)
```

### Mock Response Format

Mock responses should match the actual API response structure:

```python
def _mock_new_response(self, method, endpoint, data, expected_status):
    if method == "POST" and endpoint == "/api/v1/new":
        response = {
            "id": "new-123",
            "created_at": datetime.utcnow().isoformat()
        }
        mock_response = type('Response', (), {
            'json': lambda self: response,
            'status_code': 201
        })()
        return True, mock_response
    return True, None
```

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: API Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install requests boto3
      - name: Run mock tests
        run: python3 infrastructure/TEST.py --mode mock
      - name: Run deployed tests
        if: github.ref == 'refs/heads/main'
        env:
          API_BASE_URL: ${{ secrets.API_BASE_URL }}
          COGNITO_CLIENT_ID: ${{ secrets.COGNITO_CLIENT_ID }}
          TEST_USERNAME: ${{ secrets.TEST_USERNAME }}
          TEST_PASSWORD: ${{ secrets.TEST_PASSWORD }}
        run: python3 infrastructure/TEST.py --mode deployed
```

## License

Part of the DomainFlow Agentic Orchestration Platform.
