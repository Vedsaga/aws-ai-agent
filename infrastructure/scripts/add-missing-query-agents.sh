#!/bin/bash
# Add missing query agents to DynamoDB

TABLE_NAME="MultiAgentOrchestration-dev-Data-Configurations"
TIMESTAMP=$(date +%s)

echo "Adding missing query agents to table: $TABLE_NAME"

# Why Agent
echo "✓ Adding Why Agent..."
aws dynamodb put-item --table-name "$TABLE_NAME" --item '{
  "tenant_id": {"S": "system"},
  "config_key": {"S": "agent#query_why_agent"},
  "config_type": {"S": "agent"},
  "agent_id": {"S": "query_why_agent"},
  "agent_name": {"S": "Why Agent"},
  "agent_type": {"S": "query"},
  "interrogative": {"S": "why"},
  "system_prompt": {"S": "Analyze causal relationships and reasons behind incidents. Answer questions about why incidents occurred, root causes, contributing factors, and correlations. Use the Analytics API for pattern detection."},
  "tools": {"L": [{"S": "bedrock"}, {"S": "analytics_api"}, {"S": "retrieval_api"}]},
  "output_schema": {"M": {
    "causes": {"S": "array"},
    "factors": {"S": "array"},
    "analysis": {"S": "string"},
    "confidence": {"S": "number"}
  }},
  "is_builtin": {"BOOL": true},
  "created_at": {"N": "'"$TIMESTAMP"'"},
  "updated_at": {"N": "'"$TIMESTAMP"'"},
  "created_by": {"S": "system"},
  "version": {"N": "1"}
}' --region us-east-1

# How Agent
echo "✓ Adding How Agent..."
aws dynamodb put-item --table-name "$TABLE_NAME" --item '{
  "tenant_id": {"S": "system"},
  "config_key": {"S": "agent#query_how_agent"},
  "config_type": {"S": "agent"},
  "agent_id": {"S": "query_how_agent"},
  "agent_name": {"S": "How Agent"},
  "agent_type": {"S": "query"},
  "interrogative": {"S": "how"},
  "system_prompt": {"S": "Analyze methods, processes, and mechanisms. Answer questions about how incidents occurred, how they were resolved, and how patterns emerged. Use the Retrieval API for incident details."},
  "tools": {"L": [{"S": "bedrock"}, {"S": "retrieval_api"}]},
  "output_schema": {"M": {
    "methods": {"S": "array"},
    "process": {"S": "string"},
    "insights": {"S": "string"},
    "confidence": {"S": "number"}
  }},
  "is_builtin": {"BOOL": true},
  "created_at": {"N": "'"$TIMESTAMP"'"},
  "updated_at": {"N": "'"$TIMESTAMP"'"},
  "created_by": {"S": "system"},
  "version": {"N": "1"}
}' --region us-east-1

# Who Agent
echo "✓ Adding Who Agent..."
aws dynamodb put-item --table-name "$TABLE_NAME" --item '{
  "tenant_id": {"S": "system"},
  "config_key": {"S": "agent#query_who_agent"},
  "config_type": {"S": "agent"},
  "agent_id": {"S": "query_who_agent"},
  "agent_name": {"S": "Who Agent"},
  "agent_type": {"S": "query"},
  "interrogative": {"S": "who"},
  "system_prompt": {"S": "Analyze entities and actors involved in incidents. Answer questions about who reported incidents, who was affected, and entity patterns. Use the Retrieval API to get entity information."},
  "tools": {"L": [{"S": "bedrock"}, {"S": "retrieval_api"}, {"S": "aggregation_api"}]},
  "output_schema": {"M": {
    "entities": {"S": "array"},
    "reporters": {"S": "string"},
    "affected": {"S": "string"},
    "confidence": {"S": "number"}
  }},
  "is_builtin": {"BOOL": true},
  "created_at": {"N": "'"$TIMESTAMP"'"},
  "updated_at": {"N": "'"$TIMESTAMP"'"},
  "created_by": {"S": "system"},
  "version": {"N": "1"}
}' --region us-east-1

# Which Agent
echo "✓ Adding Which Agent..."
aws dynamodb put-item --table-name "$TABLE_NAME" --item '{
  "tenant_id": {"S": "system"},
  "config_key": {"S": "agent#query_which_agent"},
  "config_type": {"S": "agent"},
  "agent_id": {"S": "query_which_agent"},
  "agent_name": {"S": "Which Agent"},
  "agent_type": {"S": "query"},
  "interrogative": {"S": "which"},
  "system_prompt": {"S": "Analyze and identify specific items, options, or choices from a set. Answer questions about which incidents match criteria, which categories are most relevant, and which patterns are significant. Use the Retrieval API to filter and compare data."},
  "tools": {"L": [{"S": "bedrock"}, {"S": "retrieval_api"}, {"S": "aggregation_api"}]},
  "output_schema": {"M": {
    "selected_items": {"S": "array"},
    "criteria": {"S": "string"},
    "reasoning": {"S": "string"},
    "confidence": {"S": "number"}
  }},
  "is_builtin": {"BOOL": true},
  "created_at": {"N": "'"$TIMESTAMP"'"},
  "updated_at": {"N": "'"$TIMESTAMP"'"},
  "created_by": {"S": "system"},
  "version": {"N": "1"}
}' --region us-east-1

# How Many Agent
echo "✓ Adding How Many Agent..."
aws dynamodb put-item --table-name "$TABLE_NAME" --item '{
  "tenant_id": {"S": "system"},
  "config_key": {"S": "agent#query_how_many_agent"},
  "config_type": {"S": "agent"},
  "agent_id": {"S": "query_how_many_agent"},
  "agent_name": {"S": "How Many Agent"},
  "agent_type": {"S": "query"},
  "interrogative": {"S": "how_many"},
  "system_prompt": {"S": "Analyze quantitative aspects of the data. Answer questions about counts, frequencies, and numerical distributions. Use the Aggregation API to compute statistics and counts across different dimensions."},
  "tools": {"L": [{"S": "bedrock"}, {"S": "aggregation_api"}, {"S": "retrieval_api"}]},
  "output_schema": {"M": {
    "count": {"S": "number"},
    "breakdown": {"S": "object"},
    "total": {"S": "number"},
    "confidence": {"S": "number"}
  }},
  "is_builtin": {"BOOL": true},
  "created_at": {"N": "'"$TIMESTAMP"'"},
  "updated_at": {"N": "'"$TIMESTAMP"'"},
  "created_by": {"S": "system"},
  "version": {"N": "1"}
}' --region us-east-1

# How Much Agent
echo "✓ Adding How Much Agent..."
aws dynamodb put-item --table-name "$TABLE_NAME" --item '{
  "tenant_id": {"S": "system"},
  "config_key": {"S": "agent#query_how_much_agent"},
  "config_type": {"S": "agent"},
  "agent_id": {"S": "query_how_much_agent"},
  "agent_name": {"S": "How Much Agent"},
  "agent_type": {"S": "query"},
  "interrogative": {"S": "how_much"},
  "system_prompt": {"S": "Analyze quantitative measurements and magnitudes. Answer questions about amounts, degrees, extents, and intensity levels. Use the Analytics API to compute aggregated measurements and trends."},
  "tools": {"L": [{"S": "bedrock"}, {"S": "analytics_api"}, {"S": "aggregation_api"}]},
  "output_schema": {"M": {
    "amount": {"S": "string"},
    "measurement": {"S": "string"},
    "scale": {"S": "string"},
    "confidence": {"S": "number"}
  }},
  "is_builtin": {"BOOL": true},
  "created_at": {"N": "'"$TIMESTAMP"'"},
  "updated_at": {"N": "'"$TIMESTAMP"'"},
  "created_by": {"S": "system"},
  "version": {"N": "1"}
}' --region us-east-1

# From Where Agent
echo "✓ Adding From Where Agent..."
aws dynamodb put-item --table-name "$TABLE_NAME" --item '{
  "tenant_id": {"S": "system"},
  "config_key": {"S": "agent#query_from_where_agent"},
  "config_type": {"S": "agent"},
  "agent_id": {"S": "query_from_where_agent"},
  "agent_name": {"S": "From Where Agent"},
  "agent_type": {"S": "query"},
  "interrogative": {"S": "from_where"},
  "system_prompt": {"S": "Analyze origin and source locations. Answer questions about where incidents originated from, source regions, and directional patterns. Use the Spatial Query API for origin-based geospatial analysis."},
  "tools": {"L": [{"S": "bedrock"}, {"S": "spatial_api"}, {"S": "retrieval_api"}]},
  "output_schema": {"M": {
    "origin_locations": {"S": "array"},
    "source_regions": {"S": "array"},
    "direction": {"S": "string"},
    "confidence": {"S": "number"}
  }},
  "is_builtin": {"BOOL": true},
  "created_at": {"N": "'"$TIMESTAMP"'"},
  "updated_at": {"N": "'"$TIMESTAMP"'"},
  "created_by": {"S": "system"},
  "version": {"N": "1"}
}' --region us-east-1

# What Kind Agent
echo "✓ Adding What Kind Agent..."
aws dynamodb put-item --table-name "$TABLE_NAME" --item '{
  "tenant_id": {"S": "system"},
  "config_key": {"S": "agent#query_what_kind_agent"},
  "config_type": {"S": "agent"},
  "agent_id": {"S": "query_what_kind_agent"},
  "agent_name": {"S": "What Kind Agent"},
  "agent_type": {"S": "query"},
  "interrogative": {"S": "what_kind"},
  "system_prompt": {"S": "Analyze types, categories, and classifications. Answer questions about what kind of incidents occurred, types of issues, and categorical patterns. Use the Retrieval API to identify and classify incident types."},
  "tools": {"L": [{"S": "bedrock"}, {"S": "retrieval_api"}, {"S": "aggregation_api"}]},
  "output_schema": {"M": {
    "types": {"S": "array"},
    "categories": {"S": "array"},
    "classification": {"S": "string"},
    "confidence": {"S": "number"}
  }},
  "is_builtin": {"BOOL": true},
  "created_at": {"N": "'"$TIMESTAMP"'"},
  "updated_at": {"N": "'"$TIMESTAMP"'"},
  "created_by": {"S": "system"},
  "version": {"N": "1"}
}' --region us-east-1

echo ""
echo "✅ Successfully added all missing query agents!"
echo "Total query agents should now be 11"
