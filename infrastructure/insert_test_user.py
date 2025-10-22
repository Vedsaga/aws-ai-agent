#!/usr/bin/env python3
"""
Quick script to insert test user into database for hackathon
"""
import psycopg2
import os
import json
from datetime import datetime
import boto3

# Get DB credentials from Secrets Manager
secrets = boto3.client('secretsmanager', region_name='us-east-1')
secret = secrets.get_secret_value(SecretId='MultiAgentOrchestration-dev-Data-DatabaseCredentials')
db_creds = json.loads(secret['SecretString'])

# Connect to database
conn = psycopg2.connect(
    host=db_creds['host'],
    port=db_creds['port'],
    database=db_creds['dbname'],
    user=db_creds['username'],
    password=db_creds['password']
)

cursor = conn.cursor()

# Insert test user
user_id = 'd4188428-4071-704d-015a-189f11510585'
username = 'testuser'
email = 'test@example.com'

cursor.execute('''
    INSERT INTO users (user_id, username, email, created_at, updated_at)
    VALUES (%s, %s, %s, NOW(), NOW())
    ON CONFLICT (user_id) DO NOTHING
''', (user_id, username, email))

conn.commit()
print(f'✓ Test user {username} ({user_id}) inserted/verified in database')

cursor.close()
conn.close()
