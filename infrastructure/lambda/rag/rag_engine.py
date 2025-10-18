"""
RAG Engine Lambda

Retrieval-Augmented Generation engine for query agents.
Performs vector search, retrieves full incident data, and generates contextual responses.
"""

import json
import logging
import os
import boto3
import psycopg2
from typing import Dict, Any, List, Optional
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS clients
bedrock_runtime = boto3.client('bedrock-runtime')
session = boto3.Session()
credentials = session.get_credentials()

# OpenSearch configuration
OPENSEARCH_ENDPOINT = os.environ.get('OPENSEARCH_ENDPOINT')
OPENSEARCH_REGION = os.environ.get('AWS_REGION', 'us-east-1')
OPENSEARCH_INDEX = os.environ.get('OPENSEARCH_INDEX', 'incident_embeddings')

# Database configuration
DB_HOST = os.environ.get('DB_HOST')
DB_PORT = os.environ.get('DB_PORT', '5432')
DB_NAME = os.environ.get('DB_NAME')
DB_USER = os.environ.get('DB_USER')
DB_PASSWORD = os.environ.get('DB_PASSWORD')

# Bedrock model configuration
EMBEDDING_MODEL_ID = os.environ.get('EMBEDDING_MODEL_ID', 'amazon.titan-embed-text-v1')
LLM_MODEL_ID = os.environ.get('LLM_MODEL_ID', 'anthropic.claude-3-sonnet-20240229-v1:0')

# AWS4Auth for OpenSearch
awsauth = AWS4Auth(
    credentials.access_key,
    credentials.secret_key,
    OPENSEARCH_REGION,
    'es',
    session_token=credentials.token
)

# OpenSearch client
opensearch_client = OpenSearch(
    hosts=[{'host': OPENSEARCH_ENDPOINT, 'port': 443}],
    http_auth=awsauth,
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection
) if OPENSEARCH_ENDPOINT else None


def get_db_connection():
    """Get database connection."""
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )


def create_embedding(text: str) -> List[float]:
    """
    Create text embedding using Bedrock.
    
    Args:
        text: Input text
    
    Returns:
        Embedding vector
    """
    try:
        request_body = json.dumps({
            'inputText': text
        })
        
        response = bedrock_runtime.invoke_model(
            modelId=EMBEDDING_MODEL_ID,
            body=request_body
        )
        
        response_body = json.loads(response['body'].read())
        embedding = response_body.get('embedding', [])
        
        logger.info(f"Created embedding with {len(embedding)} dimensions")
        return embedding
    
    except Exception as e:
        logger.error(f"Error creating embedding: {str(e)}", exc_info=True)
        raise


def vector_search(
    query_text: str,
    tenant_id: str,
    domain_id: Optional[str] = None,
    top_k: int = 10,
    min_score: float = 0.7
) -> List[Dict[str, Any]]:
    """
    Perform vector similarity search in OpenSearch.
    
    Args:
        query_text: Query text
        tenant_id: Tenant identifier
        domain_id: Optional domain filter
        top_k: Number of results to return
        min_score: Minimum similarity score
    
    Returns:
        List of matching incident IDs with scores
    """
    if not opensearch_client:
        logger.warning("OpenSearch not configured, returning empty results")
        return []
    
    try:
        # Create query embedding
        query_embedding = create_embedding(query_text)
        
        # Build OpenSearch query
        query = {
            'size': top_k,
            'query': {
                'bool': {
                    'must': [
                        {
                            'knn': {
                                'text_embedding': {
                                    'vector': query_embedding,
                                    'k': top_k
                                }
                            }
                        },
                        {
                            'term': {
                                'tenant_id': tenant_id
                            }
                        }
                    ]
                }
            },
            'min_score': min_score,
            '_source': ['incident_id', 'text_content', 'created_at']
        }
        
        # Add domain filter if provided
        if domain_id:
            query['query']['bool']['must'].append({
                'term': {
                    'domain_id': domain_id
                }
            })
        
        # Execute search
        response = opensearch_client.search(
            index=OPENSEARCH_INDEX,
            body=query
        )
        
        # Extract incident IDs and scores
        results = []
        for hit in response['hits']['hits']:
            source = hit['_source']
            results.append({
                'incident_id': source.get('incident_id'),
                'score': hit['_score'],
                'text_preview': source.get('text_content', '')[:200]
            })
        
        logger.info(f"Vector search found {len(results)} results")
        return results
    
    except Exception as e:
        logger.error(f"Error performing vector search: {str(e)}", exc_info=True)
        return []


def retrieve_full_incidents(
    incident_ids: List[str],
    tenant_id: str
) -> List[Dict[str, Any]]:
    """
    Retrieve full incident data from RDS PostgreSQL.
    
    Args:
        incident_ids: List of incident IDs
        tenant_id: Tenant identifier
    
    Returns:
        List of full incident records
    """
    if not incident_ids:
        return []
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Build query with IN clause
        placeholders = ','.join(['%s'] * len(incident_ids))
        query = f"""
            SELECT 
                i.id,
                i.tenant_id,
                i.domain_id,
                i.raw_text,
                i.structured_data,
                i.created_at,
                i.updated_at
            FROM incidents i
            WHERE i.id IN ({placeholders})
            AND i.tenant_id = %s
            ORDER BY i.created_at DESC
        """
        
        params = incident_ids + [tenant_id]
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Format results
        incidents = []
        for row in rows:
            incidents.append({
                'id': str(row[0]),
                'tenant_id': str(row[1]),
                'domain_id': row[2],
                'raw_text': row[3],
                'structured_data': row[4],
                'created_at': row[5].isoformat() if row[5] else None,
                'updated_at': row[6].isoformat() if row[6] else None
            })
        
        cursor.close()
        conn.close()
        
        logger.info(f"Retrieved {len(incidents)} full incident records from RDS")
        return incidents
    
    except Exception as e:
        logger.error(f"Error retrieving incidents from RDS: {str(e)}", exc_info=True)
        return []


def generate_contextual_response(
    question: str,
    incidents: List[Dict[str, Any]],
    agent_context: Optional[str] = None
) -> str:
    """
    Generate contextual response using Bedrock LLM.
    
    Args:
        question: User's question
        incidents: Retrieved incident data
        agent_context: Optional context from agent (e.g., interrogative perspective)
    
    Returns:
        Generated contextual response
    """
    try:
        # Build context from incidents
        context_parts = []
        for idx, incident in enumerate(incidents[:5], 1):  # Limit to top 5 for token efficiency
            context_parts.append(f"Incident {idx}:")
            context_parts.append(f"Raw Text: {incident.get('raw_text', 'N/A')}")
            
            structured = incident.get('structured_data', {})
            if structured:
                context_parts.append(f"Structured Data: {json.dumps(structured, indent=2)}")
            
            context_parts.append("")  # Blank line between incidents
        
        context = "\n".join(context_parts)
        
        # Build system prompt
        system_prompt = """You are a helpful assistant analyzing incident data to answer questions.
You will be provided with relevant incident records and a user question.
Analyze the data and provide a clear, concise answer based on the evidence.
If the data doesn't contain enough information to answer the question, say so.
Focus on facts from the data, not speculation."""
        
        if agent_context:
            system_prompt += f"\n\nAdditional Context: {agent_context}"
        
        # Build user prompt
        user_prompt = f"""Question: {question}

Relevant Incident Data:
{context}

Based on the incident data above, please answer the question. Be specific and cite information from the incidents when possible."""
        
        # Prepare Bedrock request
        messages = [{'role': 'user', 'content': user_prompt}]
        
        request_body = {
            'anthropic_version': 'bedrock-2023-05-31',
            'messages': messages,
            'system': system_prompt,
            'max_tokens': 500,
            'temperature': 0.7
        }
        
        # Invoke Bedrock
        response = bedrock_runtime.invoke_model(
            modelId=LLM_MODEL_ID,
            body=json.dumps(request_body)
        )
        
        response_body = json.loads(response['body'].read())
        text = response_body.get('content', [{}])[0].get('text', '')
        
        logger.info(f"Generated contextual response ({len(text)} chars)")
        return text
    
    except Exception as e:
        logger.error(f"Error generating contextual response: {str(e)}", exc_info=True)
        return f"Error generating response: {str(e)}"


def rag_query(
    question: str,
    tenant_id: str,
    domain_id: Optional[str] = None,
    agent_context: Optional[str] = None,
    top_k: int = 10,
    min_score: float = 0.7
) -> Dict[str, Any]:
    """
    Perform RAG query: vector search + retrieval + generation.
    
    Args:
        question: User's question
        tenant_id: Tenant identifier
        domain_id: Optional domain filter
        agent_context: Optional agent context
        top_k: Number of results for vector search
        min_score: Minimum similarity score
    
    Returns:
        RAG response with context and generated answer
    """
    try:
        # Step 1: Vector search
        logger.info(f"Starting RAG query for question: {question[:100]}...")
        vector_results = vector_search(
            query_text=question,
            tenant_id=tenant_id,
            domain_id=domain_id,
            top_k=top_k,
            min_score=min_score
        )
        
        if not vector_results:
            return {
                'status': 'success',
                'context': [],
                'response': "No relevant incidents found in the database.",
                'incident_count': 0
            }
        
        # Step 2: Retrieve full incident data
        incident_ids = [r['incident_id'] for r in vector_results]
        full_incidents = retrieve_full_incidents(incident_ids, tenant_id)
        
        if not full_incidents:
            return {
                'status': 'success',
                'context': [],
                'response': "Unable to retrieve incident details.",
                'incident_count': 0
            }
        
        # Step 3: Generate contextual response
        response_text = generate_contextual_response(
            question=question,
            incidents=full_incidents,
            agent_context=agent_context
        )
        
        # Prepare context summary
        context_summary = []
        for incident in full_incidents:
            context_summary.append({
                'incident_id': incident['id'],
                'domain_id': incident['domain_id'],
                'created_at': incident['created_at'],
                'preview': incident['raw_text'][:200] if incident.get('raw_text') else None
            })
        
        return {
            'status': 'success',
            'context': context_summary,
            'response': response_text,
            'incident_count': len(full_incidents)
        }
    
    except Exception as e:
        logger.error(f"Error in RAG query: {str(e)}", exc_info=True)
        return {
            'status': 'error',
            'error': str(e),
            'response': f"Error processing query: {str(e)}"
        }


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for RAG engine.
    
    Expected input:
    {
        "question": "string",
        "tenant_id": "string",
        "domain_id": "string (optional)",
        "agent_context": "string (optional)",
        "top_k": int (optional, default: 10),
        "min_score": float (optional, default: 0.7)
    }
    """
    try:
        # Parse body
        body = event
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        elif event.get('body'):
            body = event['body']
        
        # Extract parameters
        question = body.get('question')
        tenant_id = body.get('tenant_id')
        
        if not question or not tenant_id:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'error': 'bad_request',
                    'message': 'Missing question or tenant_id'
                })
            }
        
        domain_id = body.get('domain_id')
        agent_context = body.get('agent_context')
        top_k = body.get('top_k', 10)
        min_score = body.get('min_score', 0.7)
        
        # Perform RAG query
        result = rag_query(
            question=question,
            tenant_id=tenant_id,
            domain_id=domain_id,
            agent_context=agent_context,
            top_k=top_k,
            min_score=min_score
        )
        
        if result['status'] == 'success':
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps(result)
            }
        else:
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps(result)
            }
    
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'error': 'internal_error',
                'message': str(e)
            })
        }
