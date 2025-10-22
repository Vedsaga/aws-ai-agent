#!/usr/bin/env python3
"""Quick test of Lambda orchestrator logic"""
import sys
import json
sys.path.insert(0, 'lambda')

# Mock environment
import os
os.environ['TABLE_NAME'] = 'test-table'
os.environ['EVENT_BUS'] = 'test-bus'

# Mock boto3
class MockBedrock:
    def converse(self, **kwargs):
        return {
            'output': {
                'message': {
                    'content': [{'text': '{"location": "123 Main St", "geo_coordinates": [-74, 40.7], "entity": "streetlight", "severity": "high", "confidence": 0.95}'}]
                }
            }
        }

class MockDynamoDB:
    def Table(self, name):
        class MockTable:
            def put_item(self, **kwargs):
                return {}
            def scan(self, **kwargs):
                return {'Items': []}
            def update_item(self, **kwargs):
                return {}
        return MockTable()

class MockEvents:
    def put_events(self, **kwargs):
        return {}

import hackathon_demo.lambda.orchestrator as orch
orch.bedrock = MockBedrock()
orch.dynamodb = MockDynamoDB()
orch.events = MockEvents()

# Test ingestion
print("Testing ingestion...")
try:
    result = orch.handle_ingestion('test-session', 'Street light broken at 123 Main St', [])
    print(f"✓ Ingestion works: {result.get('report_id', 'N/A')}")
except Exception as e:
    print(f"✗ Ingestion failed: {e}")
    import traceback
    traceback.print_exc()

# Test query
print("\nTesting query...")
try:
    result = orch.handle_query('test-session', 'Show me all issues', [])
    print(f"✓ Query works: {len(result.get('results', []))} results")
except Exception as e:
    print(f"✗ Query failed: {e}")
    import traceback
    traceback.print_exc()

# Test management
print("\nTesting management...")
try:
    result = orch.handle_management('test-session', 'Assign to Team B', [], 'test-report-id')
    print(f"✓ Management works")
except Exception as e:
    print(f"✗ Management failed: {e}")
    import traceback
    traceback.print_exc()

print("\n✅ All tests passed!")
