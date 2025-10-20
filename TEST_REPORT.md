# API Test Report

**Generated:** 2025-10-20 12:40:13
**Duration:** 593.69 seconds

## Summary

- **Total Tests:** 48
- **Passed:** 2 (4.2%)
- **Failed:** 38
- **Skipped:** 8

❌ **38 test(s) failed**

## Detailed Results

### Authentication

**Tests:** 5 | **Passed:** 1 | **Failed:** 3 | **Skipped:** 1

| Status | Test Name | Endpoint | Response Time | HTTP Code |
|--------|-----------|----------|---------------|-----------|
| ✅ | No Authorization Header | `GET /api/v1/config?type=agent` | 1248ms | 401 |
| ❌ | Invalid JWT Token | `GET /api/v1/config?type=agent` | 541225ms | - |
| ❌ | Expired JWT Token | `GET /api/v1/config?type=agent` | 1545ms | 500 |
| ❌ | Valid JWT Token | `GET /api/v1/config?type=agent` | 1229ms | 500 |
| ⊘ | Tenant ID Scoping | `Various` | - | - |

### Config API - Agent CRUD

**Tests:** 1 | **Passed:** 0 | **Failed:** 1 | **Skipped:** 0

| Status | Test Name | Endpoint | Response Time | HTTP Code |
|--------|-----------|----------|---------------|-----------|
| ❌ | Create Agent | `POST /api/v1/config` | 1025ms | 500 |

### Config API - Dependency Graph

**Tests:** 1 | **Passed:** 0 | **Failed:** 1 | **Skipped:** 0

| Status | Test Name | Endpoint | Response Time | HTTP Code |
|--------|-----------|----------|---------------|-----------|
| ❌ | List Dependency Graphs | `GET /api/v1/config?type=dependency_graph` | 1024ms | 500 |

### Config API - Domain CRUD

**Tests:** 1 | **Passed:** 0 | **Failed:** 1 | **Skipped:** 0

| Status | Test Name | Endpoint | Response Time | HTTP Code |
|--------|-----------|----------|---------------|-----------|
| ❌ | Create Domain | `POST /api/v1/config` | 1022ms | 500 |

### Data API

**Tests:** 9 | **Passed:** 0 | **Failed:** 9 | **Skipped:** 0

| Status | Test Name | Endpoint | Response Time | HTTP Code |
|--------|-----------|----------|---------------|-----------|
| ❌ | Retrieve Incidents | `GET /api/v1/data?type=retrieval` | 615ms | 500 |
| ❌ | Filter by Date Range | `GET /api/v1/data?type=retrieval&filters=...` | 933ms | 500 |
| ❌ | Filter by Location (bbox) | `GET /api/v1/data?type=retrieval&filters=...` | 1112ms | 500 |
| ❌ | Filter by Category | `GET /api/v1/data?type=retrieval&filters=...` | 1025ms | 500 |
| ❌ | Pagination | `GET /api/v1/data?type=retrieval&page=1&page_size=1...` | 1023ms | 500 |
| ❌ | Spatial Queries | `GET /api/v1/data?type=spatial` | 1024ms | 500 |
| ❌ | Analytics Queries | `GET /api/v1/data?type=analytics` | 1024ms | 500 |
| ❌ | Aggregation Queries | `GET /api/v1/data?type=aggregation` | 1025ms | 500 |
| ❌ | Vector Search | `GET /api/v1/data?type=vector_search` | 1023ms | 500 |

### Edge Cases

**Tests:** 8 | **Passed:** 0 | **Failed:** 8 | **Skipped:** 0

| Status | Test Name | Endpoint | Response Time | HTTP Code |
|--------|-----------|----------|---------------|-----------|
| ❌ | Missing Required Fields | `POST /api/v1/config` | 1022ms | 500 |
| ❌ | Invalid Data Types | `POST /api/v1/config` | 1024ms | 500 |
| ❌ | Out-of-Range Values | `POST /api/v1/config` | 1022ms | 500 |
| ❌ | Empty Strings and Arrays | `POST /api/v1/config` | 481ms | 500 |
| ❌ | Null Values | `POST /api/v1/config` | 954ms | 500 |
| ❌ | Special Characters and Unicode | `POST /api/v1/config` | 614ms | 500 |
| ❌ | Malformed JSON | `POST /api/v1/config` | 818ms | 500 |
| ❌ | Concurrent Requests | `POST /api/v1/config` | 1186ms | - |

### Error Handling

**Tests:** 5 | **Passed:** 1 | **Failed:** 2 | **Skipped:** 2

| Status | Test Name | Endpoint | Response Time | HTTP Code |
|--------|-----------|----------|---------------|-----------|
| ❌ | 400 Error Includes Validation Details | `POST /api/v1/config` | 965ms | 500 |
| ✅ | 401 Error Includes Authentication Guidance | `GET /api/v1/config?type=agent` | 818ms | 401 |
| ❌ | 404 Error Includes Resource Identification | `GET /api/v1/config/agent/nonexistent_agent_12345` | 614ms | 500 |
| ⊘ | Error Response Format is Consistent | `Various` | - | - |
| ⊘ | Error Messages are User-Friendly | `Various` | - | - |

### Ingest API

**Tests:** 6 | **Passed:** 0 | **Failed:** 6 | **Skipped:** 0

| Status | Test Name | Endpoint | Response Time | HTTP Code |
|--------|-----------|----------|---------------|-----------|
| ❌ | Submit Text-Only Report | `POST /api/v1/ingest` | 1024ms | 500 |
| ❌ | Submit Report with Images | `POST /api/v1/ingest` | 1026ms | 500 |
| ❌ | Invalid Domain ID | `POST /api/v1/ingest` | 1020ms | 500 |
| ❌ | Missing Required Fields | `POST /api/v1/ingest` | 1024ms | 500 |
| ❌ | Extremely Long Text | `POST /api/v1/ingest` | 513ms | 500 |
| ❌ | Special Characters and Unicode | `POST /api/v1/ingest` | 921ms | 500 |

### Performance

**Tests:** 6 | **Passed:** 0 | **Failed:** 1 | **Skipped:** 5

| Status | Test Name | Endpoint | Response Time | HTTP Code |
|--------|-----------|----------|---------------|-----------|
| ⊘ | Config API Response Time | `GET /api/v1/config?type=agent` | - | - |
| ⊘ | Data API Response Time | `GET /api/v1/data?type=retrieval` | - | - |
| ⊘ | Ingest API Response Time | `POST /api/v1/ingest` | - | - |
| ⊘ | Query API Response Time | `POST /api/v1/query` | - | - |
| ❌ | 10 Concurrent Requests | `GET /api/v1/config?type=agent` | 1268ms | - |
| ⊘ | Pagination Performance | `GET /api/v1/data?type=retrieval&page=X&page_size=1...` | - | - |

### Query API

**Tests:** 5 | **Passed:** 0 | **Failed:** 5 | **Skipped:** 0

| Status | Test Name | Endpoint | Response Time | HTTP Code |
|--------|-----------|----------|---------------|-----------|
| ❌ | Ask Simple Question | `POST /api/v1/query` | 1005ms | 500 |
| ❌ | Ask Complex Question | `POST /api/v1/query` | 1041ms | 500 |
| ❌ | Invalid Domain ID | `POST /api/v1/query` | 615ms | 500 |
| ❌ | Missing Required Fields | `POST /api/v1/query` | 916ms | 500 |
| ❌ | Extremely Long Question | `POST /api/v1/query` | 925ms | 500 |

### Tool Registry API

**Tests:** 1 | **Passed:** 0 | **Failed:** 1 | **Skipped:** 0

| Status | Test Name | Endpoint | Response Time | HTTP Code |
|--------|-----------|----------|---------------|-----------|
| ❌ | List All Tools | `GET /api/v1/tools` | 468ms | 500 |

## Failed Tests Details

### 1. Invalid JWT Token

- **Category:** Authentication
- **Endpoint:** `GET /api/v1/config?type=agent`
- **HTTP Code:** 0
- **Response Time:** 541225ms
- **Error:** Expected 401, got 0

### 2. Expired JWT Token

- **Category:** Authentication
- **Endpoint:** `GET /api/v1/config?type=agent`
- **HTTP Code:** 500
- **Response Time:** 1545ms
- **Error:** Expected 401, got 500

### 3. Valid JWT Token

- **Category:** Authentication
- **Endpoint:** `GET /api/v1/config?type=agent`
- **HTTP Code:** 500
- **Response Time:** 1229ms
- **Error:** Expected 200/201/202, got 500

### 4. Create Agent

- **Category:** Config API - Agent CRUD
- **Endpoint:** `POST /api/v1/config`
- **HTTP Code:** 500
- **Response Time:** 1025ms
- **Error:** Expected 201, got 500

### 5. Create Domain

- **Category:** Config API - Domain CRUD
- **Endpoint:** `POST /api/v1/config`
- **HTTP Code:** 500
- **Response Time:** 1022ms
- **Error:** Expected 201, got 500

### 6. List Dependency Graphs

- **Category:** Config API - Dependency Graph
- **Endpoint:** `GET /api/v1/config?type=dependency_graph`
- **HTTP Code:** 500
- **Response Time:** 1024ms
- **Error:** Expected 200, got 500

### 7. Retrieve Incidents

- **Category:** Data API
- **Endpoint:** `GET /api/v1/data?type=retrieval`
- **HTTP Code:** 500
- **Response Time:** 615ms
- **Error:** Expected 200, got 500

### 8. Filter by Date Range

- **Category:** Data API
- **Endpoint:** `GET /api/v1/data?type=retrieval&filters=...`
- **HTTP Code:** 500
- **Response Time:** 933ms
- **Error:** Expected 200, got 500

### 9. Filter by Location (bbox)

- **Category:** Data API
- **Endpoint:** `GET /api/v1/data?type=retrieval&filters=...`
- **HTTP Code:** 500
- **Response Time:** 1112ms
- **Error:** Expected 200, got 500

### 10. Filter by Category

- **Category:** Data API
- **Endpoint:** `GET /api/v1/data?type=retrieval&filters=...`
- **HTTP Code:** 500
- **Response Time:** 1025ms
- **Error:** Expected 200, got 500

### 11. Pagination

- **Category:** Data API
- **Endpoint:** `GET /api/v1/data?type=retrieval&page=1&page_size=10`
- **HTTP Code:** 500
- **Response Time:** 1023ms
- **Error:** Expected 200, got 500

### 12. Spatial Queries

- **Category:** Data API
- **Endpoint:** `GET /api/v1/data?type=spatial`
- **HTTP Code:** 500
- **Response Time:** 1024ms
- **Error:** Expected 200, got 500

### 13. Analytics Queries

- **Category:** Data API
- **Endpoint:** `GET /api/v1/data?type=analytics`
- **HTTP Code:** 500
- **Response Time:** 1024ms
- **Error:** Expected 200, got 500

### 14. Aggregation Queries

- **Category:** Data API
- **Endpoint:** `GET /api/v1/data?type=aggregation`
- **HTTP Code:** 500
- **Response Time:** 1025ms
- **Error:** Expected 200, got 500

### 15. Vector Search

- **Category:** Data API
- **Endpoint:** `GET /api/v1/data?type=vector_search`
- **HTTP Code:** 500
- **Response Time:** 1023ms
- **Error:** Expected 200, got 500

### 16. Submit Text-Only Report

- **Category:** Ingest API
- **Endpoint:** `POST /api/v1/ingest`
- **HTTP Code:** 500
- **Response Time:** 1024ms
- **Error:** Expected 202, got 500

### 17. Submit Report with Images

- **Category:** Ingest API
- **Endpoint:** `POST /api/v1/ingest`
- **HTTP Code:** 500
- **Response Time:** 1026ms
- **Error:** Expected 202, got 500

### 18. Invalid Domain ID

- **Category:** Ingest API
- **Endpoint:** `POST /api/v1/ingest`
- **HTTP Code:** 500
- **Response Time:** 1020ms
- **Error:** Expected 404, got 500

### 19. Missing Required Fields

- **Category:** Ingest API
- **Endpoint:** `POST /api/v1/ingest`
- **HTTP Code:** 500
- **Response Time:** 1024ms
- **Error:** Expected 400, got 500

### 20. Extremely Long Text

- **Category:** Ingest API
- **Endpoint:** `POST /api/v1/ingest`
- **HTTP Code:** 500
- **Response Time:** 513ms
- **Error:** Expected 202 or 400, got 500

### 21. Special Characters and Unicode

- **Category:** Ingest API
- **Endpoint:** `POST /api/v1/ingest`
- **HTTP Code:** 500
- **Response Time:** 921ms
- **Error:** Expected 202, got 500

### 22. Ask Simple Question

- **Category:** Query API
- **Endpoint:** `POST /api/v1/query`
- **HTTP Code:** 500
- **Response Time:** 1005ms
- **Error:** Expected 202, got 500

### 23. Ask Complex Question

- **Category:** Query API
- **Endpoint:** `POST /api/v1/query`
- **HTTP Code:** 500
- **Response Time:** 1041ms
- **Error:** Expected 202, got 500

### 24. Invalid Domain ID

- **Category:** Query API
- **Endpoint:** `POST /api/v1/query`
- **HTTP Code:** 500
- **Response Time:** 615ms
- **Error:** Expected 404, got 500

### 25. Missing Required Fields

- **Category:** Query API
- **Endpoint:** `POST /api/v1/query`
- **HTTP Code:** 500
- **Response Time:** 916ms
- **Error:** Expected 400, got 500

### 26. Extremely Long Question

- **Category:** Query API
- **Endpoint:** `POST /api/v1/query`
- **HTTP Code:** 500
- **Response Time:** 925ms
- **Error:** Expected 202 or 400, got 500

### 27. List All Tools

- **Category:** Tool Registry API
- **Endpoint:** `GET /api/v1/tools`
- **HTTP Code:** 500
- **Response Time:** 468ms
- **Error:** Expected 200, got 500

### 28. 400 Error Includes Validation Details

- **Category:** Error Handling
- **Endpoint:** `POST /api/v1/config`
- **HTTP Code:** 500
- **Response Time:** 965ms
- **Error:** Expected 400, got 500

### 29. 404 Error Includes Resource Identification

- **Category:** Error Handling
- **Endpoint:** `GET /api/v1/config/agent/nonexistent_agent_12345`
- **HTTP Code:** 500
- **Response Time:** 614ms
- **Error:** Expected 404, got 500

### 30. Missing Required Fields

- **Category:** Edge Cases
- **Endpoint:** `POST /api/v1/config`
- **HTTP Code:** 500
- **Response Time:** 1022ms
- **Error:** Expected 400, got 500

### 31. Invalid Data Types

- **Category:** Edge Cases
- **Endpoint:** `POST /api/v1/config`
- **HTTP Code:** 500
- **Response Time:** 1024ms
- **Error:** Expected 400, got 500

### 32. Out-of-Range Values

- **Category:** Edge Cases
- **Endpoint:** `POST /api/v1/config`
- **HTTP Code:** 500
- **Response Time:** 1022ms
- **Error:** Expected 400, got 500

### 33. Empty Strings and Arrays

- **Category:** Edge Cases
- **Endpoint:** `POST /api/v1/config`
- **HTTP Code:** 500
- **Response Time:** 481ms
- **Error:** Expected 400, got 500

### 34. Null Values

- **Category:** Edge Cases
- **Endpoint:** `POST /api/v1/config`
- **HTTP Code:** 500
- **Response Time:** 954ms
- **Error:** Expected 400, got 500

### 35. Special Characters and Unicode

- **Category:** Edge Cases
- **Endpoint:** `POST /api/v1/config`
- **HTTP Code:** 500
- **Response Time:** 614ms
- **Error:** Expected 201 or 400, got 500

### 36. Malformed JSON

- **Category:** Edge Cases
- **Endpoint:** `POST /api/v1/config`
- **HTTP Code:** 500
- **Response Time:** 818ms
- **Error:** Expected 400, got 500

### 37. Concurrent Requests

- **Category:** Edge Cases
- **Endpoint:** `POST /api/v1/config`
- **HTTP Code:** 0
- **Response Time:** 1186ms
- **Error:** Only 0/5 concurrent requests succeeded

### 38. 10 Concurrent Requests

- **Category:** Performance
- **Endpoint:** `GET /api/v1/config?type=agent`
- **HTTP Code:** 0
- **Response Time:** 1268ms
- **Error:** Only 0/10 concurrent requests succeeded

## Performance Summary

| Test | Avg Response Time | Target | Status |
|------|-------------------|--------|--------|
| Config API Response Time | 0ms |  | ❌ |
| Data API Response Time | 0ms |  | ❌ |
| Ingest API Response Time | 0ms |  | ❌ |
| Query API Response Time | 0ms |  | ❌ |
| 10 Concurrent Requests | 1268ms |  | ❌ |
| Pagination Performance | 0ms |  | ❌ |
