#!/bin/bash
curl -X POST 'https://vluqfpl2zi.execute-api.us-east-1.amazonaws.com/dev/ingest' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer eyJraWQiOiJkZW1vLWtleSIsImFsZyI6IkhTMjU2In0.eyJzdWIiOiJkZW1vLXVzZXIiLCJ0ZW5hbnRJZCI6ImRlZmF1bHQtdGVuYW50IiwidXNlcklkIjoiZGVtby11c2VyIiwiaWF0IjoxNzI5NDUwMDAwLCJleHAiOjE3NjA5ODYwMDB9.demo-signature-for-testing' \
  -d '{"domain_id":"civic_complaints","text":"There is a pothole on Main Street near the park"}'
