# RAG Engine Lambda

## Overview

The RAG (Retrieval-Augmented Generation) Engine provides contextual information retrieval for query agents. It combines three key capabilities:

1. **Vector Search**: Semantic similarity search using OpenSearch
2. **Data Retrieval**: Full incident data fetching from RDS PostgreSQL
3. **Response Generation**: Contextual answer generation using Bedrock LLM

## Architecture

```
Query Agent Request
    ↓
Vector Search (OpenSearch)
    ↓
Retrieve Full Incidents (RDS)
    ↓
Generate Response (Bedrock)
    ↓
Return Context + Answer
```

## API Interface

### Request Format

```json
{
  "question": "What are the trends in pothole complaints?",
  "tenant_id": "tenant-123",
  "domain_id": "civic-complaints",
  "agent_context": "Analyzing temporal patterns",
  "top_k": 10,
  "min_score": 0.7
}
```

### Response Format

```json
{
  "status": "success",
  "context": [
    {
      "incident_id": "incident-123",
      "domain_id": "civic-complaints",
      "created_at": "2024-01-15T10:30:00",
      "preview": "Pothole on Main Street..."
    }
  ],
  "response": "Based on the incident data, pothole complaints have increased by 30% in the last month...",
  "incident_count": 5
}
```

## Environment Variables

- `OPENSEARCH_ENDPOINT`: OpenSearch domain endpoint
- `OPENSEARCH_INDEX`: Index name (default: `incident_embeddings`)
- `DB_HOST`: PostgreSQL host
- `DB_PORT`: PostgreSQL port (default: `5432`)
- `DB_NAME`: Database name
- `DB_USER`: Database user
- `DB_PASSWORD`: Database password
- `EMBEDDING_MODEL_ID`: Bedrock embedding model (default: `amazon.titan-embed-text-v1`)
- `LLM_MODEL_ID`: Bedrock LLM model (default: `anthropic.claude-3-sonnet-20240229-v1:0`)
- `AWS_REGION`: AWS region (default: `us-east-1`)

## Usage by Query Agents

Query agents can invoke the RAG engine to get contextual information:

```python
import boto3
import json

lambda_client = boto3.client('lambda')

response = lambda_client.invoke(
    FunctionName='rag-engine',
    InvocationType='RequestResponse',
    Payload=json.dumps({
        'question': 'What are the most common complaint types?',
        'tenant_id': tenant_id,
        'domain_id': domain_id,
        'agent_context': 'Analyzing complaint categories',
        'top_k': 10
    })
)

result = json.loads(response['Payload'].read())
context = result['context']
answer = result['response']
```

## Features

### 1. Vector Search

- Creates embeddings using Amazon Titan
- Performs k-NN search in OpenSearch
- Filters by tenant_id and domain_id
- Returns top-k most similar incidents

### 2. Full Data Retrieval

- Fetches complete incident records from RDS
- Includes structured_data JSONB field
- Maintains tenant isolation
- Preserves temporal ordering

### 3. Contextual Response Generation

- Uses Claude 3 Sonnet for response generation
- Includes incident data as context
- Supports agent-specific context (interrogative perspective)
- Generates concise, fact-based answers

## Error Handling

- Returns empty context if no matches found
- Handles OpenSearch connection failures gracefully
- Logs all errors with full context
- Returns partial results on retrieval failures

## Performance Considerations

- Limits context to top 5 incidents for token efficiency
- Uses connection pooling for RDS (via RDS Proxy)
- Caches OpenSearch client
- Implements proper timeout handling

## Security

- Tenant isolation enforced at all layers
- IAM authentication for AWS services
- Database credentials from environment variables
- No sensitive data in logs

## Testing

Test the RAG engine with sample queries:

```bash
# Test vector search
aws lambda invoke \
  --function-name rag-engine \
  --payload '{"question":"pothole complaints","tenant_id":"test-tenant","domain_id":"civic"}' \
  response.json

cat response.json
```

## Integration with Query Agents

Query agents should call the RAG engine when they need contextual data:

1. **When Agent**: Get temporal context for time-based analysis
2. **Where Agent**: Get spatial context for location-based analysis
3. **Why Agent**: Get causal context for reasoning
4. **What Agent**: Get entity context for classification

Example integration in query agent:

```python
# In query agent code
rag_response = invoke_rag_engine(
    question=raw_text,
    tenant_id=tenant_id,
    domain_id=domain_id,
    agent_context=f"Analyzing from {interrogative} perspective"
)

# Use RAG context in agent analysis
context_data = rag_response['context']
llm_answer = rag_response['response']

# Combine with agent-specific analysis
agent_output = {
    'insight': llm_answer,
    'supporting_incidents': len(context_data),
    'confidence': calculate_confidence(context_data)
}
```

## Requirements

See `requirements.txt` for Python dependencies:
- boto3 (AWS SDK)
- psycopg2-binary (PostgreSQL driver)
- opensearch-py (OpenSearch client)
- requests-aws4auth (AWS authentication)
