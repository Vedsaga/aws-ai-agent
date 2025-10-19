#!/bin/bash
# Seed DynamoDB with configuration data using AWS CLI

TABLE_NAME="MultiAgentOrchestration-dev-Data-Configurations"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

echo "Seeding data into table: $TABLE_NAME"

# Seed Civic Complaints Domain
echo "✓ Seeding Civic Complaints domain..."
aws dynamodb put-item --table-name "$TABLE_NAME" --item '{
  "tenant_id": {"S": "system"},
  "config_key": {"S": "DOMAIN#civic_complaints"},
  "config_type": {"S": "domain_template"},
  "domain_id": {"S": "civic_complaints"},
  "template_name": {"S": "Civic Complaints"},
  "description": {"S": "Template for civic complaint reporting and analysis"},
  "is_builtin": {"BOOL": true},
  "created_at": {"N": "'"$(date +%s)"'"}
}' --region us-east-1

# Seed Geo Agent
echo "  ✓ Seeding Geo Agent..."
aws dynamodb put-item --table-name "$TABLE_NAME" --item '{
  "tenant_id": {"S": "system"},
  "config_key": {"S": "AGENT#civic_complaints#geo_agent"},
  "config_type": {"S": "agent_config"},
  "domain_id": {"S": "civic_complaints"},
  "agent_id": {"S": "geo_agent"},
  "agent_name": {"S": "Geo Agent"},
  "agent_type": {"S": "ingestion"},
  "system_prompt": {"S": "Extract location information from the complaint text."},
  "tools": {"L": [{"S": "bedrock"}, {"S": "location_service"}]},
  "is_builtin": {"BOOL": true},
  "created_at": {"N": "'"$(date +%s)"'"}
}' --region us-east-1

# Seed Temporal Agent
echo "  ✓ Seeding Temporal Agent..."
aws dynamodb put-item --table-name "$TABLE_NAME" --item '{
  "tenant_id": {"S": "system"},
  "config_key": {"S": "AGENT#civic_complaints#temporal_agent"},
  "config_type": {"S": "agent_config"},
  "domain_id": {"S": "civic_complaints"},
  "agent_id": {"S": "temporal_agent"},
  "agent_name": {"S": "Temporal Agent"},
  "agent_type": {"S": "ingestion"},
  "system_prompt": {"S": "Extract time and date information from the complaint text."},
  "tools": {"L": [{"S": "bedrock"}]},
  "is_builtin": {"BOOL": true},
  "created_at": {"N": "'"$(date +%s)"'"}
}' --region us-east-1

# Seed Entity Agent
echo "  ✓ Seeding Entity Agent..."
aws dynamodb put-item --table-name "$TABLE_NAME" --item '{
  "tenant_id": {"S": "system"},
  "config_key": {"S": "AGENT#civic_complaints#entity_agent"},
  "config_type": {"S": "agent_config"},
  "domain_id": {"S": "civic_complaints"},
  "agent_id": {"S": "entity_agent"},
  "agent_name": {"S": "Entity Agent"},
  "agent_type": {"S": "ingestion"},
  "system_prompt": {"S": "Extract entities, sentiment, and key phrases from the complaint."},
  "tools": {"L": [{"S": "bedrock"}, {"S": "comprehend"}]},
  "is_builtin": {"BOOL": true},
  "created_at": {"N": "'"$(date +%s)"'"}
}' --region us-east-1

# Seed Ingestion Playbook
echo "  ✓ Seeding Ingestion Playbook..."
aws dynamodb put-item --table-name "$TABLE_NAME" --item '{
  "tenant_id": {"S": "system"},
  "config_key": {"S": "PLAYBOOK#civic_complaints#ingestion"},
  "config_type": {"S": "playbook_config"},
  "domain_id": {"S": "civic_complaints"},
  "playbook_id": {"S": "civic_complaints_ingestion"},
  "playbook_type": {"S": "ingestion"},
  "agent_ids": {"L": [{"S": "geo_agent"}, {"S": "temporal_agent"}, {"S": "entity_agent"}]},
  "description": {"S": "Ingestion pipeline for civic complaints"},
  "created_at": {"N": "'"$(date +%s)"'"}
}' --region us-east-1

# Seed Query Agents
echo "✓ Seeding Query Agents..."

# When Agent
aws dynamodb put-item --table-name "$TABLE_NAME" --item '{
  "tenant_id": {"S": "system"},
  "config_key": {"S": "QUERY_AGENT#when"},
  "config_type": {"S": "query_agent"},
  "agent_id": {"S": "query_when_agent"},
  "agent_name": {"S": "When Agent"},
  "agent_type": {"S": "query"},
  "interrogative": {"S": "when"},
  "system_prompt": {"S": "Analyze temporal patterns in the data."},
  "tools": {"L": [{"S": "bedrock"}, {"S": "retrieval_api"}]},
  "is_builtin": {"BOOL": true},
  "created_at": {"N": "'"$(date +%s)"'"}
}' --region us-east-1

# Where Agent
aws dynamodb put-item --table-name "$TABLE_NAME" --item '{
  "tenant_id": {"S": "system"},
  "config_key": {"S": "QUERY_AGENT#where"},
  "config_type": {"S": "query_agent"},
  "agent_id": {"S": "query_where_agent"},
  "agent_name": {"S": "Where Agent"},
  "agent_type": {"S": "query"},
  "interrogative": {"S": "where"},
  "system_prompt": {"S": "Analyze spatial patterns in the data."},
  "tools": {"L": [{"S": "bedrock"}, {"S": "spatial_api"}]},
  "is_builtin": {"BOOL": true},
  "created_at": {"N": "'"$(date +%s)"'"}
}' --region us-east-1

# What Agent
aws dynamodb put-item --table-name "$TABLE_NAME" --item '{
  "tenant_id": {"S": "system"},
  "config_key": {"S": "QUERY_AGENT#what"},
  "config_type": {"S": "query_agent"},
  "agent_id": {"S": "query_what_agent"},
  "agent_name": {"S": "What Agent"},
  "agent_type": {"S": "query"},
  "interrogative": {"S": "what"},
  "system_prompt": {"S": "Analyze what types of incidents occurred."},
  "tools": {"L": [{"S": "bedrock"}, {"S": "retrieval_api"}]},
  "is_builtin": {"BOOL": true},
  "created_at": {"N": "'"$(date +%s)"'"}
}' --region us-east-1

echo ""
echo "✅ Successfully seeded configuration data!"
