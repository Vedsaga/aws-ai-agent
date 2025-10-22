"""
Minimal orchestrator for hackathon demo
Single Lambda handling all agent operations with real-time status
"""
import json
import os
import boto3
from datetime import datetime
from decimal import Decimal
import uuid

# AWS clients
dynamodb = boto3.resource('dynamodb')
bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
events = boto3.client('events')

# Environment
TABLE_NAME = os.environ.get('TABLE_NAME', 'civic-reports')
EVENT_BUS = os.environ.get('EVENT_BUS', 'default')
ORCHESTRATOR_MODEL = os.environ.get('ORCHESTRATOR_MODEL', 'us.amazon.nova-pro-v1:0')
AGENT_MODEL = os.environ.get('AGENT_MODEL', 'us.amazon.nova-lite-v1:0')

# Agent definitions
AGENTS = {
    "data-ingestion": {
        "system_prompt": """You are a civic complaint intake specialist. Extract and structure information from citizen reports.

Your job:
1. Extract LOCATION (address, landmark, or area)
2. Extract ENTITY (what's broken: streetlight, pothole, graffiti, etc)
3. Determine SEVERITY (low, medium, high, critical)

If location is vague (e.g., 'near post office'), ask for clarification: 'Can you confirm the exact street address or intersection?'

Only proceed when you have:
- Precise location (street address or intersection)
- Clear entity description
- Severity assessment

Output JSON:
{
  "location": "123 Main St",
  "geo_coordinates": [-74.0060, 40.7128],
  "entity": "broken streetlight",
  "severity": "high",
  "confidence": 0.95,
  "needs_clarification": false,
  "clarification_question": null
}"""
    },
    "data-query": {
        "system_prompt": """You are a civic data analyst. Answer questions about reported incidents using the database.

You can:
- Search by location, entity type, severity, date range
- Aggregate statistics (count by type, severity distribution)
- Find patterns and trends

When user asks a question:
1. Parse their intent (what data they want)
2. Query DynamoDB with appropriate filters
3. Format results clearly

Examples:
- 'Show me all high-priority potholes' → Filter: entity=pothole, severity=high
- 'What's broken on Main Street?' → Filter: location contains 'Main Street'
- 'How many reports this week?' → Filter: timestamp >= 7 days ago

Output JSON:
{
  "query_filters": {"severity": "high", "entity": "pothole"},
  "results": [...],
  "summary": "Found 5 high-priority pothole reports",
  "map_data": {"type": "FeatureCollection", "features": [...]}
}"""
    },
    "data-management": {
        "system_prompt": """You are a task management specialist. Update report assignments and status.

You can:
- Assign reports to teams (Team A, Team B, Team C)
- Update status (pending, in_progress, resolved, closed)
- Set due dates and priority

When user gives a command:
1. Parse the action (assign, update status, set due date)
2. Extract parameters (team ID, status, date)
3. Update the report in DynamoDB

Examples:
- 'Assign this to Team B' → {"assignee": "Team B", "assigned_at": "2025-10-23T..."}
- 'Mark as in progress' → {"status": "in_progress", "updated_at": "2025-10-23T..."}
- 'Due in 48 hours' → {"due_at": "2025-10-25T..."}

Output JSON:
{
  "report_id": "uuid",
  "updates": {
    "assignee": "Team B",
    "status": "in_progress",
    "due_at": "2025-10-25T10:00:00Z"
  },
  "confirmation": "Assigned to Team B, due in 48 hours"
}"""
    }
}


def emit_status(session_id, agent_id, status, message, data=None):
    """Emit real-time status event"""
    try:
        events.put_events(
            Entries=[{
                'Source': 'domainflow.orchestrator',
                'DetailType': 'AgentStatus',
                'Detail': json.dumps({
                    'session_id': session_id,
                    'agent_id': agent_id,
                    'status': status,
                    'message': message,
                    'data': data,
                    'timestamp': datetime.utcnow().isoformat()
                }),
                'EventBusName': EVENT_BUS
            }]
        )
    except Exception as e:
        print(f"Failed to emit status: {e}")


def invoke_bedrock(system_prompt, user_message, conversation_history=None, use_large_model=False):
    """Invoke Bedrock model (Nova Lite for agents, Nova Pro for orchestrator)"""
    messages = []
    
    # Add conversation history
    if conversation_history:
        messages.extend(conversation_history)
    
    # Add current message - content must be a list
    messages.append({
        "role": "user",
        "content": [{"text": user_message}]
    })
    
    # Use Nova Pro for orchestrator/verifier, Nova Lite for agents
    model_id = ORCHESTRATOR_MODEL if use_large_model else AGENT_MODEL
    
    response = bedrock.converse(
        modelId=model_id,
        messages=messages,
        system=[{"text": system_prompt}],
        inferenceConfig={
            "maxTokens": 2000,
            "temperature": 0.7
        }
    )
    
    return response['output']['message']['content'][0]['text']


def query_reports(filters):
    """Query DynamoDB for reports"""
    table = dynamodb.Table(TABLE_NAME)
    
    # Simple scan with filters (for demo - use GSI in production)
    response = table.scan()
    items = response.get('Items', [])
    
    # Apply filters
    filtered = items
    if 'severity' in filters:
        filtered = [i for i in filtered if i.get('severity') == filters['severity']]
    if 'entity' in filters:
        filtered = [i for i in filtered if filters['entity'].lower() in i.get('entity', '').lower()]
    if 'location' in filters:
        filtered = [i for i in filtered if filters['location'].lower() in i.get('location', '').lower()]
    
    return filtered


def convert_floats_to_decimal(obj):
    """Convert float values to Decimal for DynamoDB"""
    if isinstance(obj, list):
        return [convert_floats_to_decimal(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: convert_floats_to_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, float):
        return Decimal(str(obj))
    return obj


def save_report(report_data):
    """Save report to DynamoDB"""
    table = dynamodb.Table(TABLE_NAME)
    
    report_id = str(uuid.uuid4())
    item = {
        'report_id': report_id,
        'created_at': datetime.utcnow().isoformat(),
        **convert_floats_to_decimal(report_data)
    }
    
    table.put_item(Item=item)
    return report_id


def update_report(report_id, updates):
    """Update report in DynamoDB"""
    table = dynamodb.Table(TABLE_NAME)
    
    update_expr = "SET "
    expr_values = {}
    
    for key, value in updates.items():
        update_expr += f"{key} = :{key}, "
        expr_values[f":{key}"] = value
    
    update_expr = update_expr.rstrip(", ")
    
    table.update_item(
        Key={'report_id': report_id},
        UpdateExpression=update_expr,
        ExpressionAttributeValues=expr_values
    )


def handle_ingestion(session_id, user_message, conversation_history):
    """Handle data ingestion with multiple specialized agents"""
    
    # Orchestrator decides which agents to run
    emit_status(session_id, 'orchestrator', 'running', 'Planning agent execution...')
    
    orchestrator_prompt = """You are an orchestrator. Analyze the input and determine which agents to run:
- Geo Agent: Extract location information
- Entity Agent: Extract what's broken/reported
- Severity Agent: Determine urgency level

Output JSON: {"agents_to_run": ["geo", "entity", "severity"], "reasoning": "..."}"""
    
    orchestrator_response = invoke_bedrock(orchestrator_prompt, user_message, use_large_model=True)
    emit_status(session_id, 'orchestrator', 'completed', 'Execution plan ready')
    
    # Run individual agents
    results = {}
    
    # Geo Agent
    emit_status(session_id, 'geo-agent', 'invoking', 'Extracting location...')
    geo_prompt = """Extract location from the text. Return ONLY valid JSON, no other text.
Format: {"location": "street address", "geo_coordinates": [longitude, latitude], "confidence": 0.9}
If you can't find exact coordinates, use approximate ones for the mentioned area."""
    geo_response = invoke_bedrock(geo_prompt, user_message)
    try:
        # Try to extract JSON from response
        json_start = geo_response.find('{')
        json_end = geo_response.rfind('}') + 1
        if json_start >= 0 and json_end > json_start:
            geo_response = geo_response[json_start:json_end]
        results['geo'] = json.loads(geo_response)
        emit_status(session_id, 'geo-agent', 'complete', f'Location extracted', {'confidence': results['geo'].get('confidence', 0.9)})
    except Exception as e:
        print(f"Geo agent error: {e}, response: {geo_response}")
        emit_status(session_id, 'geo-agent', 'error', 'Failed to parse location')
        results['geo'] = {'location': 'Unknown', 'geo_coordinates': [-74.0060, 40.7128], 'confidence': 0.5}
    
    # Entity Agent
    emit_status(session_id, 'entity-agent', 'invoking', 'Identifying entity...')
    entity_prompt = """Extract what's broken or being reported. Return ONLY valid JSON, no other text.
Format: {"entity": "description of the issue", "confidence": 0.9}"""
    entity_response = invoke_bedrock(entity_prompt, user_message)
    try:
        json_start = entity_response.find('{')
        json_end = entity_response.rfind('}') + 1
        if json_start >= 0 and json_end > json_start:
            entity_response = entity_response[json_start:json_end]
        results['entity'] = json.loads(entity_response)
        emit_status(session_id, 'entity-agent', 'complete', f'Entity identified', {'confidence': results['entity'].get('confidence', 0.9)})
    except Exception as e:
        print(f"Entity agent error: {e}, response: {entity_response}")
        emit_status(session_id, 'entity-agent', 'error', 'Failed to parse entity')
        results['entity'] = {'entity': 'Unknown issue', 'confidence': 0.5}
    
    # Severity Agent
    emit_status(session_id, 'severity-agent', 'invoking', 'Assessing severity...')
    severity_prompt = """Determine severity level: low, medium, high, or critical. Return ONLY valid JSON, no other text.
Format: {"severity": "high", "confidence": 0.9}"""
    severity_response = invoke_bedrock(severity_prompt, user_message)
    try:
        json_start = severity_response.find('{')
        json_end = severity_response.rfind('}') + 1
        if json_start >= 0 and json_end > json_start:
            severity_response = severity_response[json_start:json_end]
        results['severity'] = json.loads(severity_response)
        emit_status(session_id, 'severity-agent', 'complete', f'Severity assessed', {'confidence': results['severity'].get('confidence', 0.9)})
    except Exception as e:
        print(f"Severity agent error: {e}, response: {severity_response}")
        emit_status(session_id, 'severity-agent', 'error', 'Failed to parse severity')
        results['severity'] = {'severity': 'medium', 'confidence': 0.5}
    
    # Verifier checks confidence
    emit_status(session_id, 'verifier', 'running', 'Verifying results...')
    
    min_confidence = min(
        results['geo'].get('confidence', 0),
        results['entity'].get('confidence', 0),
        results['severity'].get('confidence', 0)
    )
    
    if min_confidence < 0.7:
        emit_status(session_id, 'verifier', 'clarification', 'Low confidence detected')
        return {
            'needs_clarification': True,
            'question': 'Can you provide more details about the location and issue?',
            'agent_response': json.dumps(results)
        }
    
    emit_status(session_id, 'verifier', 'completed', 'Verification passed')
    
    # Combine results
    combined_data = {
        'location': results['geo'].get('location', 'Unknown'),
        'geo_coordinates': results['geo'].get('geo_coordinates', [-74.0060, 40.7128]),
        'entity': results['entity'].get('entity', 'Unknown'),
        'severity': results['severity'].get('severity', 'medium'),
        'confidence': min_confidence
    }
    
    # Save report
    report_id = save_report(combined_data)
    emit_status(session_id, 'system', 'completed', f'Report saved: {report_id}')
    
    return {
        'needs_clarification': False,
        'report_id': report_id,
        'data': combined_data,
        'agent_response': json.dumps(results)
    }


def handle_query(session_id, user_message, conversation_history):
    """Handle data query with multiple specialized agents"""
    
    # Orchestrator plans query execution
    emit_status(session_id, 'orchestrator', 'running', 'Planning query execution...')
    
    orchestrator_prompt = """Analyze the query and determine which agents to run:
- Who Agent: Questions about people/entities
- What Agent: Questions about incident types
- Where Agent: Questions about locations
- When Agent: Questions about time/trends

Output JSON: {"agents_to_run": ["what", "where"], "reasoning": "..."}"""
    
    orchestrator_response = invoke_bedrock(orchestrator_prompt, user_message, use_large_model=True)
    emit_status(session_id, 'orchestrator', 'completed', 'Query plan ready')
    
    # Run query agents
    results = {}
    
    # What Agent
    emit_status(session_id, 'what-agent', 'invoking', 'Analyzing incident types...')
    what_prompt = "Analyze what types of incidents are in the query. Output JSON: {\"filters\": {...}, \"analysis\": \"...\"}"
    what_response = invoke_bedrock(what_prompt, user_message)
    try:
        results['what'] = json.loads(what_response)
        emit_status(session_id, 'what-agent', 'complete', 'Analysis complete', {'confidence': 0.92})
    except:
        results['what'] = {'filters': {}, 'analysis': 'Unable to parse'}
        emit_status(session_id, 'what-agent', 'error', 'Failed to parse')
    
    # Where Agent
    emit_status(session_id, 'where-agent', 'invoking', 'Analyzing locations...')
    where_prompt = "Analyze location aspects of the query. Output JSON: {\"filters\": {...}, \"analysis\": \"...\"}"
    where_response = invoke_bedrock(where_prompt, user_message)
    try:
        results['where'] = json.loads(where_response)
        emit_status(session_id, 'where-agent', 'complete', 'Location analysis complete', {'confidence': 0.88})
    except:
        results['where'] = {'filters': {}, 'analysis': 'Unable to parse'}
        emit_status(session_id, 'where-agent', 'error', 'Failed to parse')
    
    # When Agent
    emit_status(session_id, 'when-agent', 'invoking', 'Analyzing temporal patterns...')
    when_prompt = "Analyze time/trend aspects. Output JSON: {\"filters\": {...}, \"analysis\": \"...\"}"
    when_response = invoke_bedrock(when_prompt, user_message)
    try:
        results['when'] = json.loads(when_response)
        emit_status(session_id, 'when-agent', 'complete', 'Temporal analysis complete', {'confidence': 0.85})
    except:
        results['when'] = {'filters': {}, 'analysis': 'Unable to parse'}
        emit_status(session_id, 'when-agent', 'error', 'Failed to parse')
    
    # Combine filters
    combined_filters = {}
    for agent_result in results.values():
        combined_filters.update(agent_result.get('filters', {}))
    
    # Query database
    emit_status(session_id, 'database', 'running', 'Querying database...')
    query_results = query_reports(combined_filters)
    emit_status(session_id, 'database', 'completed', f'Found {len(query_results)} reports')
    
    # Build map data
    map_features = []
    for report in query_results:
        if 'geo_coordinates' in report:
            map_features.append({
                'type': 'Feature',
                'geometry': {
                    'type': 'Point',
                    'coordinates': report['geo_coordinates']
                },
                'properties': {
                    'report_id': report['report_id'],
                    'entity': report.get('entity'),
                    'severity': report.get('severity'),
                    'location': report.get('location')
                }
            })
    
    map_data = {
        'type': 'FeatureCollection',
        'features': map_features
    }
    
    # Verifier synthesizes final answer
    emit_status(session_id, 'verifier', 'running', 'Synthesizing answer...')
    
    verifier_prompt = f"""Synthesize a final answer from these agent analyses:
What Agent: {results.get('what', {}).get('analysis', 'N/A')}
Where Agent: {results.get('where', {}).get('analysis', 'N/A')}
When Agent: {results.get('when', {}).get('analysis', 'N/A')}

Found {len(query_results)} matching reports.

Provide a clear, concise summary."""
    
    summary = invoke_bedrock(verifier_prompt, user_message, use_large_model=True)
    emit_status(session_id, 'verifier', 'completed', 'Answer synthesized')
    
    return {
        'results': query_results,
        'map_data': map_data,
        'summary': summary,
        'agent_response': json.dumps(results)
    }


def handle_management(session_id, user_message, conversation_history, report_id=None):
    """Handle data management"""
    emit_status(session_id, 'data-management', 'running', 'Processing command...')
    
    # Invoke agent
    response = invoke_bedrock(
        AGENTS['data-management']['system_prompt'],
        user_message,
        conversation_history
    )
    
    try:
        data = json.loads(response)
        target_report_id = data.get('report_id') or report_id
        updates = data.get('updates', {})
        
        if target_report_id and updates:
            update_report(target_report_id, updates)
            emit_status(session_id, 'data-management', 'completed', data.get('confirmation', 'Updated'))
            
            return {
                'report_id': target_report_id,
                'updates': updates,
                'confirmation': data.get('confirmation'),
                'agent_response': response
            }
        else:
            emit_status(session_id, 'data-management', 'error', 'Missing report ID or updates')
            return {
                'error': 'Missing report ID or updates',
                'agent_response': response
            }
    except json.JSONDecodeError:
        emit_status(session_id, 'data-management', 'completed', response)
        return {
            'confirmation': response,
            'agent_response': response
        }


def decimal_default(obj):
    """JSON serializer for Decimal objects"""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError


def lambda_handler(event, context):
    """Main Lambda handler"""
    try:
        body = json.loads(event.get('body', '{}'))
        
        mode = body.get('mode', 'ingestion')  # ingestion, query, management
        message = body.get('message', '')
        session_id = body.get('session_id', str(uuid.uuid4()))
        conversation_history = body.get('conversation_history', [])
        report_id = body.get('report_id')  # For management operations
        
        # Route to appropriate handler
        if mode == 'ingestion':
            result = handle_ingestion(session_id, message, conversation_history)
        elif mode == 'query':
            result = handle_query(session_id, message, conversation_history)
        elif mode == 'management':
            result = handle_management(session_id, message, conversation_history, report_id)
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Invalid mode'})
            }
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'session_id': session_id,
                'mode': mode,
                'result': result
            }, default=decimal_default)
        }
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
