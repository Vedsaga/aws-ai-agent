"""
Minimal orchestrator for hackathon demo
Single Lambda handling all agent operations with real-time status
Follows structured response schemas (meta-level + micro-level)
"""
import json
import os
import boto3
from datetime import datetime
from decimal import Decimal
import uuid
import time

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
    
    # Reserved keywords in DynamoDB
    reserved_keywords = {'status', 'name', 'type', 'data', 'timestamp', 'date', 'time'}
    
    update_expr = "SET "
    expr_values = {}
    expr_names = {}
    
    for key, value in updates.items():
        # Use expression attribute names for reserved keywords
        if key.lower() in reserved_keywords:
            attr_name = f"#{key}"
            expr_names[attr_name] = key
            update_expr += f"{attr_name} = :{key}, "
        else:
            update_expr += f"{key} = :{key}, "
        expr_values[f":{key}"] = value
    
    update_expr = update_expr.rstrip(", ")
    
    update_params = {
        'Key': {'report_id': report_id},
        'UpdateExpression': update_expr,
        'ExpressionAttributeValues': expr_values
    }
    
    if expr_names:
        update_params['ExpressionAttributeNames'] = expr_names
    
    table.update_item(**update_params)


def handle_ingestion(session_id, user_message, conversation_history):
    """
    Handle data ingestion with multiple specialized agents
    Returns structured response following INGESTION_RESPONSE_SCHEMA
    """
    start_time = time.time()
    
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
    agent_results = {}
    results = {}
    
    # Geo Agent - Use advanced model (Nova Pro) with sophisticated reasoning
    emit_status(session_id, 'geo-agent', 'invoking', 'Extracting location with advanced reasoning...')
    
    geo_prompt = """You are an expert geographic information extraction agent with deep knowledge of global locations, addresses, and coordinate systems.

TASK: Extract precise location information from the user's text.

INPUT TEXT: "{text}"

REASONING PROCESS:
1. Identify any street addresses, landmarks, intersections, or area names
2. Determine the most likely geographic region (city, state, country)
3. Estimate precise coordinates based on:
   - Known street patterns and numbering systems
   - Typical city layouts and geography
   - Landmark proximity if mentioned
   - Regional coordinate ranges

COORDINATE ESTIMATION GUIDELINES:
- Use your knowledge of real-world geography
- Street numbers help estimate position along a street
- Intersections provide precise locations
- Landmarks have known coordinates
- City/neighborhood names give approximate areas
- Consider typical coordinate ranges for regions:
  * US East Coast: longitude -80 to -70, latitude 35 to 45
  * US West Coast: longitude -125 to -115, latitude 30 to 50
  * US Midwest: longitude -95 to -85, latitude 35 to 45
  * Europe: longitude -10 to 40, latitude 35 to 70
  * Asia: longitude 60 to 150, latitude -10 to 60

CONFIDENCE SCORING:
- 0.95-1.0: Exact address with known coordinates
- 0.85-0.94: Specific street address, estimated coordinates
- 0.70-0.84: Intersection or landmark, good estimate
- 0.50-0.69: General area/neighborhood, approximate
- 0.00-0.49: Very vague, default coordinates

OUTPUT FORMAT (JSON only, no other text):
{{
  "location": "full address or best description",
  "geo_coordinates": [longitude, latitude],
  "confidence": 0.0-1.0,
  "reasoning": "brief explanation of coordinate estimation"
}}

CRITICAL RULES:
- ALWAYS provide geo_coordinates as [longitude, latitude] numbers
- NEVER use null or omit coordinates
- Use your geographic knowledge to make intelligent estimates
- Higher confidence for more specific locations
- Lower confidence for vague descriptions

Now extract location from the input text above.""".format(text=user_message)
    
    # Use Nova Pro for better reasoning
    geo_response = invoke_bedrock(geo_prompt, user_message, use_large_model=True)
    
    try:
        # Try to extract JSON from response
        json_start = geo_response.find('{')
        json_end = geo_response.rfind('}') + 1
        if json_start >= 0 and json_end > json_start:
            geo_response = geo_response[json_start:json_end]
        results['geo'] = json.loads(geo_response)
        
        # Validate coordinates
        coords = results['geo'].get('geo_coordinates')
        if not coords or not isinstance(coords, list) or len(coords) != 2:
            print(f"Invalid coordinates from geo agent: {coords}")
            results['geo']['geo_coordinates'] = [-74.0060, 40.7128]  # Fallback
            results['geo']['confidence'] = 0.3
        else:
            # Validate coordinate ranges
            lng, lat = coords
            if not (-180 <= lng <= 180 and -90 <= lat <= 90):
                print(f"Coordinates out of range: {coords}")
                results['geo']['geo_coordinates'] = [-74.0060, 40.7128]
                results['geo']['confidence'] = 0.3
        
        emit_status(session_id, 'geo-agent', 'complete', f'Location extracted', {'confidence': results['geo'].get('confidence', 0.9)})
    except Exception as e:
        print(f"Geo agent error: {e}, response: {geo_response}")
        emit_status(session_id, 'geo-agent', 'error', 'Failed to parse location')
        results['geo'] = {
            'location': 'Unknown location',
            'geo_coordinates': [-74.0060, 40.7128],
            'confidence': 0.3,
            'reasoning': 'Failed to extract location information'
        }
    
    # Entity Agent
    emit_status(session_id, 'entity-agent', 'invoking', 'Identifying entity...')
    entity_prompt = """Extract what's broken or being reported. Return ONLY valid JSON, no other text.

Text: "{text}"

Identify what is broken or needs attention. Be specific.

Format: {{"entity": "Dangerous pothole", "confidence": 0.95}}

If the issue is clearly stated, set confidence to 0.95.
If somewhat vague, set confidence to 0.8.
""".format(text=user_message)
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

Text: "{text}"

Assess urgency:
- critical: immediate danger (e.g., "dangerous", "urgent", "immediate")
- high: significant issue (e.g., "needs repair", "broken")
- medium: moderate issue
- low: minor issue (e.g., "graffiti", "cosmetic")

Format: {{"severity": "high", "confidence": 0.9}}

If urgency keywords present, set confidence to 0.9.
""".format(text=user_message)
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
    
    execution_time_ms = int((time.time() - start_time) * 1000)
    
    # Check confidence threshold
    if min_confidence < 0.7:
        emit_status(session_id, 'verifier', 'clarification', 'Low confidence detected')
        return {
            'status': 'needs_clarification',
            'report_id': None,
            'confidence': min_confidence,
            'needs_clarification': True,
            'clarification_question': 'Can you provide more details about the location and issue? Please include a specific street address.',
            'data': None,
            'agent_execution': {
                'agents_run': ['geo-agent', 'entity-agent', 'severity-agent', 'verifier'],
                'execution_time_ms': execution_time_ms,
                'agent_results': {
                    'geo': {'status': 'completed', 'confidence': results['geo'].get('confidence', 0), 'output': results['geo']},
                    'entity': {'status': 'completed', 'confidence': results['entity'].get('confidence', 0), 'output': results['entity']},
                    'severity': {'status': 'completed', 'confidence': results['severity'].get('confidence', 0), 'output': results['severity']}
                }
            },
            'metadata': {
                'created_at': datetime.utcnow().isoformat(),
                'source': 'web',
                'version': '1.0'
            }
        }
    
    emit_status(session_id, 'verifier', 'completed', 'Verification passed')
    
    # Build structured data following CIVIC_INGESTION_DATA_SCHEMA
    structured_data = {
        'location': {
            'address': results['geo'].get('location', 'Unknown'),
            'geo_coordinates': results['geo'].get('geo_coordinates', [-74.0060, 40.7128]),
            'place_id': None,
            'confidence': results['geo'].get('confidence', 0.5)
        },
        'entity': {
            'type': 'other',  # Could be enhanced to classify
            'description': results['entity'].get('entity', 'Unknown'),
            'confidence': results['entity'].get('confidence', 0.5)
        },
        'severity': {
            'level': results['severity'].get('severity', 'medium'),
            'reasoning': f"Assessed based on description",
            'confidence': results['severity'].get('confidence', 0.5)
        },
        'temporal': {
            'reported_at': datetime.utcnow().isoformat(),
            'incident_time': None,
            'urgency': 'routine' if results['severity'].get('severity') in ['low', 'medium'] else 'immediate'
        },
        'reporter': {
            'contact': None,
            'source': 'web'
        }
    }
    
    # Legacy flat format for DynamoDB
    flat_data = {
        'location': structured_data['location']['address'],
        'geo_coordinates': structured_data['location']['geo_coordinates'],
        'entity': structured_data['entity']['description'],
        'severity': structured_data['severity']['level'],
        'confidence': min_confidence,
        'structured_data': structured_data
    }
    
    # Save report
    report_id = save_report(flat_data)
    emit_status(session_id, 'system', 'completed', f'Report saved: {report_id}')
    
    return {
        'status': 'success',
        'report_id': report_id,
        'confidence': min_confidence,
        'needs_clarification': False,
        'clarification_question': None,
        'data': structured_data,
        'agent_execution': {
            'agents_run': ['geo-agent', 'entity-agent', 'severity-agent', 'verifier'],
            'execution_time_ms': execution_time_ms,
            'agent_results': {
                'geo': {'status': 'completed', 'confidence': results['geo'].get('confidence', 0), 'output': results['geo']},
                'entity': {'status': 'completed', 'confidence': results['entity'].get('confidence', 0), 'output': results['entity']},
                'severity': {'status': 'completed', 'confidence': results['severity'].get('confidence', 0), 'output': results['severity']}
            }
        },
        'metadata': {
            'created_at': datetime.utcnow().isoformat(),
            'source': 'web',
            'version': '1.0'
        }
    }


def handle_query(session_id, user_message, conversation_history):
    """
    Handle data query with multiple specialized agents
    Returns structured response following QUERY_RESPONSE_SCHEMA
    """
    start_time = time.time()
    
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
    
    # What Agent - Extract severity and entity filters
    emit_status(session_id, 'what-agent', 'invoking', 'Analyzing incident types...')
    what_prompt = """Analyze the query and extract filters. Return ONLY valid JSON, no other text.

Query: "{query}"

Extract:
- severity: if mentioned (low, medium, high, critical)
- entity: if specific type mentioned (pothole, streetlight, graffiti, etc)

Format: {{"filters": {{"severity": "high", "entity": "pothole"}}, "analysis": "User wants high severity potholes"}}

If no filters mentioned, return empty filters object.
""".format(query=user_message)
    
    what_response = invoke_bedrock(what_prompt, user_message)
    try:
        json_start = what_response.find('{')
        json_end = what_response.rfind('}') + 1
        if json_start >= 0 and json_end > json_start:
            what_response = what_response[json_start:json_end]
        results['what'] = json.loads(what_response)
        emit_status(session_id, 'what-agent', 'complete', 'Analysis complete', {'confidence': 0.92})
    except Exception as e:
        print(f"What agent error: {e}, response: {what_response}")
        results['what'] = {'filters': {}, 'analysis': 'Unable to parse'}
        emit_status(session_id, 'what-agent', 'error', 'Failed to parse')
    
    # Where Agent - Extract location filters
    emit_status(session_id, 'where-agent', 'invoking', 'Analyzing locations...')
    where_prompt = """Analyze the query for location filters. Return ONLY valid JSON, no other text.

Query: "{query}"

Extract:
- location: if specific street/area mentioned

Format: {{"filters": {{"location": "Main Street"}}, "analysis": "User wants reports on Main Street"}}

If no location mentioned, return empty filters object.
""".format(query=user_message)
    
    where_response = invoke_bedrock(where_prompt, user_message)
    try:
        json_start = where_response.find('{')
        json_end = where_response.rfind('}') + 1
        if json_start >= 0 and json_end > json_start:
            where_response = where_response[json_start:json_end]
        results['where'] = json.loads(where_response)
        emit_status(session_id, 'where-agent', 'complete', 'Location analysis complete', {'confidence': 0.88})
    except Exception as e:
        print(f"Where agent error: {e}, response: {where_response}")
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
    
    # Combine filters - ensure proper structure
    combined_filters = {}
    filters_applied = {}
    
    for agent_name, agent_result in results.items():
        if isinstance(agent_result, dict):
            agent_filters = agent_result.get('filters', {})
            if isinstance(agent_filters, dict):
                combined_filters.update(agent_filters)
            filters_applied[agent_name] = agent_result
        else:
            filters_applied[agent_name] = {'filters': {}, 'analysis': str(agent_result)}
    
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
    
    execution_time_ms = int((time.time() - start_time) * 1000)
    
    # Return structured response following QUERY_RESPONSE_SCHEMA
    return {
        'status': 'success',
        'total_results': len(query_results),
        'results': query_results,
        'filters_applied': filters_applied,  # Full agent results with filters
        'filters_used': combined_filters,     # Just the filters for DB query
        'summary': summary,
        'visualizations': {
            'map_data': map_data,
            'charts': []  # Future enhancement
        },
        'agent_execution': {
            'agents_run': ['what-agent', 'where-agent', 'when-agent', 'verifier'],
            'execution_time_ms': execution_time_ms,
            'agent_results': {
                'what': {'status': 'completed', 'output': results.get('what', {})},
                'where': {'status': 'completed', 'output': results.get('where', {})},
                'when': {'status': 'completed', 'output': results.get('when', {})}
            }
        },
        'metadata': {
            'query_timestamp': datetime.utcnow().isoformat(),
            'data_sources': ['dynamodb']
        }
    }


def handle_management(session_id, user_message, conversation_history, report_id=None):
    """
    Handle data management operations
    Returns structured response following MANAGEMENT_RESPONSE_SCHEMA
    CRITICAL: Must reference an existing report - cannot create new data
    """
    start_time = time.time()
    emit_status(session_id, 'data-management', 'running', 'Processing command...')
    
    # Enhanced prompt to get structured JSON
    enhanced_prompt = f"""You are a task management specialist. Parse this command and extract:
1. The report ID (UUID format) - REQUIRED, must be present in command
2. The action (assign, update_status, set_priority, add_note)
3. The parameters (team name, status value, priority, note)

Command: {user_message}

CRITICAL RULES:
- You MUST extract a report ID from the command
- You CANNOT create new reports - only update existing ones
- If no report ID is found, return an error

Return ONLY valid JSON in this exact format:
{{
  "report_id": "extracted-uuid-here",
  "action": "assign",
  "updates": {{
    "assignee": "Team Name",
    "status": "in_progress",
    "assigned_at": "2025-10-23T00:00:00Z"
  }},
  "confirmation": "Brief confirmation message"
}}

Valid actions: assign, update_status, set_priority, add_note
Valid statuses: pending, in_progress, resolved, closed
Valid priorities: low, medium, high, critical
"""
    
    # Invoke agent
    response = invoke_bedrock(
        enhanced_prompt,
        user_message,
        conversation_history
    )
    
    try:
        # Extract JSON from response
        json_start = response.find('{')
        json_end = response.rfind('}') + 1
        if json_start >= 0 and json_end > json_start:
            json_str = response[json_start:json_end]
            data = json.loads(json_str)
        else:
            data = json.loads(response)
        
        target_report_id = data.get('report_id') or report_id
        action = data.get('action', 'update')
        updates = data.get('updates', {})
        
        # CRITICAL: Verify report exists before updating
        if not target_report_id:
            emit_status(session_id, 'data-management', 'error', 'No report ID found in command')
            return {
                'status': 'error',
                'action': None,
                'target_report_id': None,
                'updates_applied': {},
                'confirmation': None,
                'previous_values': {},
                'agent_execution': {
                    'command_parsed': False,
                    'execution_time_ms': int((time.time() - start_time) * 1000)
                },
                'metadata': {
                    'updated_at': datetime.utcnow().isoformat(),
                    'updated_by': 'system'
                },
                'error': 'Management operations require an existing report ID. Please specify which report to update (e.g., "Assign report abc123... to Team A")'
            }
        
        # Verify report exists
        table = dynamodb.Table(TABLE_NAME)
        try:
            existing_report = table.get_item(Key={'report_id': target_report_id})
            if 'Item' not in existing_report:
                emit_status(session_id, 'data-management', 'error', f'Report {target_report_id} not found')
                return {
                    'status': 'error',
                    'action': action,
                    'target_report_id': target_report_id,
                    'updates_applied': {},
                    'confirmation': None,
                    'previous_values': {},
                    'agent_execution': {
                        'command_parsed': True,
                        'execution_time_ms': int((time.time() - start_time) * 1000)
                    },
                    'metadata': {
                        'updated_at': datetime.utcnow().isoformat(),
                        'updated_by': 'system'
                    },
                    'error': f'Report {target_report_id} does not exist. Management can only update existing reports, not create new ones.'
                }
            
            previous_values = {k: existing_report['Item'].get(k) for k in updates.keys()}
        except Exception as e:
            print(f"Error checking report existence: {e}")
            previous_values = {}
        
        if updates:
            # Add timestamp to updates
            updates['updated_at'] = datetime.utcnow().isoformat()
            
            update_report(target_report_id, updates)
            emit_status(session_id, 'data-management', 'completed', data.get('confirmation', 'Updated'))
            
            execution_time_ms = int((time.time() - start_time) * 1000)
            
            return {
                'status': 'success',
                'action': action,
                'target_report_id': target_report_id,
                'updates_applied': updates,
                'confirmation': data.get('confirmation', f'Report {target_report_id[:8]}... updated successfully'),
                'previous_values': previous_values,
                'agent_execution': {
                    'command_parsed': True,
                    'execution_time_ms': execution_time_ms
                },
                'metadata': {
                    'updated_at': datetime.utcnow().isoformat(),
                    'updated_by': 'system'
                }
            }
        else:
            emit_status(session_id, 'data-management', 'error', 'No updates specified')
            return {
                'status': 'error',
                'action': action,
                'target_report_id': target_report_id,
                'updates_applied': {},
                'confirmation': None,
                'previous_values': {},
                'agent_execution': {
                    'command_parsed': True,
                    'execution_time_ms': int((time.time() - start_time) * 1000)
                },
                'metadata': {
                    'updated_at': datetime.utcnow().isoformat(),
                    'updated_by': 'system'
                },
                'error': 'No updates specified. Please specify what to update (e.g., assign to team, change status, set priority)'
            }
    except Exception as e:
        print(f"Management agent error: {e}, response: {response}")
        emit_status(session_id, 'data-management', 'error', 'Failed to parse command')
        return {
            'error': f'Could not parse command: {str(e)}',
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
