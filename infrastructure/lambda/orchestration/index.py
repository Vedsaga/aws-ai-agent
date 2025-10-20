import json
import uuid

def handler(event, context):
    try:
        body = json.loads(event.get("body", "{}"))
        if not body.get("domain_id") or not body.get("text"):
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
                "body": json.dumps({"error": "Missing required fields"})
            }
        
        return {
            "statusCode": 202,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": json.dumps({"job_id": "job_" + uuid.uuid4().hex, "status": "accepted"})
        }
    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
