# Diagram 01: Authentication & Multi-Tenancy Flow

## Purpose
This diagram shows the authentication flow using AWS Cognito and how tenant isolation is enforced across all system components.

## AWS Services Used
- AWS Cognito (User Pools)
- AWS API Gateway (Lambda Authorizer)
- Amazon DynamoDB (Session Store)

## Diagram

```mermaid
flowchart TB
    subgraph Client["Client Application"]
        WebApp["Next.js Web App<br/>Login Form"]
    end
    
    subgraph CognitoService["AWS Cognito"]
        UserPool["Cognito User Pool<br/>User Directory"]
        TokenService["Token Service<br/>JWT Generation"]
    end
    
    subgraph APIGatewayAuth["API Gateway Authentication"]
        APIGW["API Gateway<br/>REST API"]
        LambdaAuth["Lambda Authorizer<br/>JWT Validation"]
    end
    
    subgraph SessionMgmt["Session Management"]
        SessionStore[("DynamoDB<br/>user_sessions Table<br/>PK user_id<br/>SK session_id")]
    end
    
    subgraph TenantIsolation["Tenant Isolation Layer"]
        TenantExtractor["Tenant ID Extractor<br/>From JWT Claims"]
        TenantValidator["Tenant Validator<br/>Verify Access"]
    end
    
    subgraph DataLayer["Data Layer - Tenant Partitioned"]
        RDS[("Amazon RDS PostgreSQL<br/>Partitioned by tenant_id")]
        DDB[("DynamoDB Tables<br/>PK includes tenant_id")]
        S3[("S3 Buckets<br/>Prefix: /{tenant_id}/")]
    end
    
    %% Authentication Flow
    WebApp -->|Step 1: POST /login<br/>username, password| UserPool
    UserPool -->|Step 2: Validate credentials| TokenService
    TokenService -->|Step 3: Generate JWT<br/>Claims: user_id, tenant_id, email| WebApp
    
    %% Session Creation
    WebApp -->|Step 4: Store session| SessionStore
    SessionStore -->|Step 5: Return session_id| WebApp
    
    %% API Request with Auth
    WebApp -->|Step 6: API Request<br/>Header: Authorization Bearer JWT| APIGW
    APIGW -->|Step 7: Invoke authorizer| LambdaAuth
    LambdaAuth -->|Step 8: Validate JWT signature<br/>Check expiration| TokenService
    TokenService -->|Step 9: Return user claims| LambdaAuth
    
    %% Tenant Isolation
    LambdaAuth -->|Step 10: Extract tenant_id| TenantExtractor
    TenantExtractor -->|Step 11: Validate tenant access| TenantValidator
    TenantValidator -->|Step 12: Allow/Deny| APIGW
    
    %% Data Access with Tenant Filter
    APIGW -->|Step 13: Forward request<br/>Context: tenant_id| RDS
    APIGW -->|Step 13: Forward request<br/>Context: tenant_id| DDB
    APIGW -->|Step 13: Forward request<br/>Context: tenant_id| S3
    
    RDS -.->|Row-level security<br/>WHERE tenant_id equals| TenantValidator
    DDB -.->|Partition key filter<br/>tenant_id equals| TenantValidator
    S3 -.->|Bucket policy<br/>Prefix by tenant_id| TenantValidator

    classDef clientBox fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    classDef cognitoBox fill:#fff3e0,stroke:#ef6c00,stroke-width:3px
    classDef apiBox fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef sessionBox fill:#fff9c4,stroke:#f57f17,stroke-width:2px
    classDef tenantBox fill:#e8f5e9,stroke:#2e7d32,stroke-width:3px
    classDef dataBox fill:#fce4ec,stroke:#c2185b,stroke-width:2px
    
    class WebApp clientBox
    class UserPool,TokenService cognitoBox
    class APIGW,LambdaAuth apiBox
    class SessionStore sessionBox
    class TenantExtractor,TenantValidator tenantBox
    class RDS,DDB,S3 dataBox
```

## Component Descriptions

### AWS Cognito User Pool
- **Purpose**: Manages user authentication and stores user credentials
- **Configuration**:
  - Password policy: Min 8 chars, uppercase, lowercase, numbers, symbols
  - MFA: Optional (SMS or TOTP)
  - Token expiration: Access token 1 hour, Refresh token 30 days
- **JWT Claims**: `sub` (user_id), `tenant_id` (custom), `email`, `cognito:groups`

### Lambda Authorizer
- **Purpose**: Validates JWT tokens on every API request
- **Runtime**: Python 3.11
- **Execution**: Synchronous, <100ms
- **Caching**: 5 minutes per token
- **Response**: IAM policy document (Allow/Deny)

### DynamoDB Session Store
- **Table**: `user_sessions`
- **Partition Key**: `user_id` (String)
- **Sort Key**: `session_id` (String)
- **TTL**: `expires_at` attribute (30 days)
- **Attributes**: `tenant_id`, `chat_id`, `connection_id`, `created_at`, `last_activity`

### Tenant Isolation Enforcement
- **PostgreSQL**: Row-level security policies on all tables
- **DynamoDB**: Partition key includes `tenant_id`
- **S3**: Bucket policies restrict access to `/{tenant_id}/` prefix
- **Lambda**: Execution role scoped to tenant resources

## Data Flow

1. User submits credentials to Cognito
2. Cognito validates and returns JWT with `tenant_id` claim
3. Client stores JWT and session_id
4. All API requests include JWT in Authorization header
5. Lambda Authorizer validates JWT and extracts `tenant_id`
6. API Gateway forwards request with `tenant_id` in context
7. All data access filtered by `tenant_id`

## Security Notes

- JWT tokens signed with RS256 (asymmetric)
- Cognito public keys rotated automatically
- Lambda Authorizer caches validation results
- Session store uses DynamoDB encryption at rest
- All data partitioned by `tenant_id` for isolation
