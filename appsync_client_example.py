"""
AppSync Client Example for Real-time Status Updates (Python)

This example shows how to subscribe to job status updates using AWS AppSync
with Python. The client receives real-time notifications as agents execute
and the job progresses.
"""

import os
import json
import asyncio
import base64
import uuid
from typing import Callable, Dict, Any, Optional
import websockets
import requests
from datetime import datetime


# Configuration
APPSYNC_API_URL = os.environ.get(
    "APPSYNC_API_URL",
    "https://your-api-id.appsync-api.us-east-1.amazonaws.com/graphql",
)
APPSYNC_API_KEY = os.environ.get("APPSYNC_API_KEY", "your-api-key-here")
USER_ID = os.environ.get("USER_ID", "demo-user")
API_BASE_URL = os.environ.get(
    "API_BASE_URL",
    "https://your-api-gateway-url.execute-api.us-east-1.amazonaws.com/dev",
)

# GraphQL subscription query
SUBSCRIPTION_QUERY = """
subscription OnStatusUpdate($userId: ID!) {
  onStatusUpdate(userId: $userId) {
    jobId
    userId
    agentName
    status
    message
    timestamp
    metadata
  }
}
"""


class AppSyncStatusSubscriber:
    """
    Subscribe to real-time status updates from AWS AppSync
    """

    def __init__(self, api_url: str, api_key: str, user_id: str):
        self.api_url = api_url
        self.api_key = api_key
        self.user_id = user_id
        self.ws = None
        self.subscription_id = None
        self.status_callbacks = []
        self.running = False

    def on_status(self, callback: Callable[[Dict[str, Any]], None]):
        """Register a callback for status updates"""
        self.status_callbacks.append(callback)

    async def subscribe(self):
        """Start the subscription"""
        print(f"Subscribing to status updates for user: {self.user_id}")

        # Build subscription payload
        subscription_payload = {
            "query": SUBSCRIPTION_QUERY,
            "variables": {"userId": self.user_id},
        }

        # Encode subscription payload
        encoded_payload = base64.b64encode(
            json.dumps(subscription_payload).encode()
        ).decode()

        # Build WebSocket URL
        ws_url = self.api_url.replace("https://", "wss://").replace(
            "/graphql", "/realtime"
        )

        header = base64.b64encode(
            json.dumps(
                {
                    "host": self.api_url.split("//")[1].split("/")[0],
                    "x-api-key": self.api_key,
                }
            ).encode()
        ).decode()

        url = f"{ws_url}?header={header}&payload={encoded_payload}"

        # Connect WebSocket
        self.running = True
        async with websockets.connect(url, subprotocols=["graphql-ws"]) as ws:
            self.ws = ws
            print("WebSocket connected")

            # Send connection init
            await ws.send(json.dumps({"type": "connection_init"}))

            # Message loop
            try:
                async for message in ws:
                    if not self.running:
                        break

                    data = json.loads(message)
                    await self.handle_message(data)
            except websockets.exceptions.ConnectionClosed:
                print("WebSocket connection closed")
            except Exception as e:
                print(f"WebSocket error: {e}")
            finally:
                self.ws = None
                self.subscription_id = None

    async def handle_message(self, message: Dict[str, Any]):
        """Handle WebSocket messages"""
        message_type = message.get("type")

        if message_type == "connection_ack":
            print("Connection acknowledged")
            await self.start_subscription()

        elif message_type == "start_ack":
            print("Subscription started")
            self.subscription_id = message.get("id")

        elif message_type == "data":
            status_update = (
                message.get("payload", {}).get("data", {}).get("onStatusUpdate")
            )
            if status_update:
                self.handle_status_update(status_update)

        elif message_type == "error":
            print(f"Subscription error: {message.get('payload')}")

        elif message_type == "complete":
            print("Subscription completed")

        elif message_type == "ka":
            # Keep-alive
            pass

        else:
            print(f"Unknown message type: {message_type}")

    async def start_subscription(self):
        """Start the GraphQL subscription"""
        start_message = {
            "id": str(uuid.uuid4()),
            "type": "start",
            "payload": {
                "data": json.dumps(
                    {"query": SUBSCRIPTION_QUERY, "variables": {"userId": self.user_id}}
                ),
                "extensions": {"authorization": {"x-api-key": self.api_key}},
            },
        }

        await self.ws.send(json.dumps(start_message))

    def handle_status_update(self, update: Dict[str, Any]):
        """Handle status update"""
        print("\n--- Status Update ---")
        print(f"Job ID: {update.get('jobId')}")
        print(f"Status: {update.get('status')}")
        print(f"Message: {update.get('message')}")

        if update.get("agentName"):
            print(f"Agent: {update.get('agentName')}")

        if update.get("metadata"):
            try:
                metadata = json.loads(update.get("metadata"))
                print(f"Metadata: {json.dumps(metadata, indent=2)}")
            except:
                print(f"Metadata: {update.get('metadata')}")

        print(f"Timestamp: {update.get('timestamp')}")
        print("-------------------\n")

        # Call registered callbacks
        for callback in self.status_callbacks:
            try:
                callback(update)
            except Exception as e:
                print(f"Error in status callback: {e}")

    async def unsubscribe(self):
        """Stop the subscription"""
        self.running = False
        if self.ws and self.subscription_id:
            await self.ws.send(json.dumps({"type": "stop", "id": self.subscription_id}))


def submit_report(
    report_data: Dict[str, Any], tenant_id: str = "default-tenant"
) -> Dict[str, Any]:
    """Submit a report via REST API"""
    url = f"{API_BASE_URL}/api/v1/ingest"
    headers = {
        "Content-Type": "application/json",
        "X-Tenant-ID": tenant_id,
    }

    response = requests.post(url, json=report_data, headers=headers)
    response.raise_for_status()
    return response.json()


def submit_query(
    query_data: Dict[str, Any], tenant_id: str = "default-tenant"
) -> Dict[str, Any]:
    """Submit a query via REST API"""
    url = f"{API_BASE_URL}/api/v1/query"
    headers = {
        "Content-Type": "application/json",
        "X-Tenant-ID": tenant_id,
    }

    response = requests.post(url, json=query_data, headers=headers)
    response.raise_for_status()
    return response.json()


async def submit_report_and_monitor():
    """
    Example: Submit a report and monitor status in real-time
    """
    print("=== Submit Report and Monitor Status ===\n")

    # Create subscriber
    subscriber = AppSyncStatusSubscriber(APPSYNC_API_URL, APPSYNC_API_KEY, USER_ID)

    # Track job completion
    job_completed = asyncio.Event()
    job_result = {"status": None, "data": None}

    def on_status_update(update):
        status = update.get("status")
        if status in ["complete", "error"]:
            job_result["status"] = status
            job_result["data"] = update
            job_completed.set()

    subscriber.on_status(on_status_update)

    # Start subscription in background
    subscription_task = asyncio.create_task(subscriber.subscribe())

    # Wait for connection
    await asyncio.sleep(2)

    # Submit report
    print("Submitting report...")
    report_payload = {
        "domain_id": "civic_complaints",
        "text": "There is a large pothole at the intersection of Main Street and 5th Avenue causing traffic issues",
        "source": "web",
        "priority": "normal",
    }

    try:
        ingest_result = submit_report(report_payload)
        print(f"Report submitted: {ingest_result}")
        print(f"Job ID: {ingest_result.get('job_id')}\n")

        # Wait for job completion
        print("Monitoring job progress...\n")
        await job_completed.wait()

        print("\nJob completed!")
        print(f"Final status: {job_result['status']}")
        print(f"Result: {json.dumps(job_result['data'], indent=2)}")

    except Exception as e:
        print(f"Error: {e}")

    finally:
        # Clean up
        await subscriber.unsubscribe()
        subscription_task.cancel()
        try:
            await subscription_task
        except asyncio.CancelledError:
            pass


async def submit_query_and_monitor():
    """
    Example: Submit a query and monitor status in real-time
    """
    print("=== Submit Query and Monitor Status ===\n")

    # Create subscriber
    subscriber = AppSyncStatusSubscriber(APPSYNC_API_URL, APPSYNC_API_KEY, USER_ID)

    # Track job completion
    job_completed = asyncio.Event()
    job_result = {"status": None, "data": None}

    def on_status_update(update):
        status = update.get("status")
        if status in ["complete", "error"]:
            job_result["status"] = status
            job_result["data"] = update
            job_completed.set()

    subscriber.on_status(on_status_update)

    # Start subscription in background
    subscription_task = asyncio.create_task(subscriber.subscribe())

    # Wait for connection
    await asyncio.sleep(2)

    # Submit query
    print("Submitting query...")
    query_payload = {
        "domain_id": "civic_complaints",
        "question": "Show me all pothole complaints in downtown from last week",
    }

    try:
        query_result = submit_query(query_payload)
        print(f"Query submitted: {query_result}")
        print(f"Job ID: {query_result.get('job_id')}\n")

        # Wait for job completion
        print("Monitoring query progress...\n")
        await job_completed.wait()

        print("\nQuery completed!")
        print(f"Final status: {job_result['status']}")
        print(f"Result: {json.dumps(job_result['data'], indent=2)}")

    except Exception as e:
        print(f"Error: {e}")

    finally:
        # Clean up
        await subscriber.unsubscribe()
        subscription_task.cancel()
        try:
            await subscription_task
        except asyncio.CancelledError:
            pass


async def monitor_multiple_jobs(job_ids):
    """
    Example: Monitor multiple jobs simultaneously
    """
    print(f"=== Monitoring {len(job_ids)} Jobs ===\n")

    subscriber = AppSyncStatusSubscriber(APPSYNC_API_URL, APPSYNC_API_KEY, USER_ID)

    job_status = {
        job_id: {"started": False, "completed": False, "updates": []}
        for job_id in job_ids
    }

    all_completed = asyncio.Event()

    def on_status_update(update):
        job_id = update.get("jobId")

        if job_id in job_status:
            job_status[job_id]["started"] = True
            job_status[job_id]["updates"].append(update)

            if update.get("status") in ["complete", "error"]:
                job_status[job_id]["completed"] = True

            # Check if all jobs completed
            if all(job["completed"] for job in job_status.values()):
                print("\nAll jobs completed!")
                all_completed.set()

    subscriber.on_status(on_status_update)

    # Start subscription
    subscription_task = asyncio.create_task(subscriber.subscribe())

    print(f"Monitoring {len(job_ids)} jobs...")

    # Wait for all jobs to complete
    await all_completed.wait()

    print("\nSummary:")
    for job_id, status in job_status.items():
        print(f"  {job_id}: {len(status['updates'])} updates")

    # Clean up
    await subscriber.unsubscribe()
    subscription_task.cancel()
    try:
        await subscription_task
    except asyncio.CancelledError:
        pass


async def continuous_monitor():
    """
    Example: Continuous monitoring (useful for admin dashboards)
    """
    print("=== Continuous Status Monitor ===")
    print("Press Ctrl+C to stop\n")

    subscriber = AppSyncStatusSubscriber(APPSYNC_API_URL, APPSYNC_API_KEY, USER_ID)

    # Track active jobs
    active_jobs = {}

    def on_status_update(update):
        job_id = update.get("jobId")
        status = update.get("status")

        if job_id not in active_jobs:
            active_jobs[job_id] = {
                "started_at": datetime.now(),
                "updates": [],
                "completed": False,
            }
            print(f"\n🆕 New job detected: {job_id}")

        active_jobs[job_id]["updates"].append(update)

        if status in ["complete", "error"]:
            active_jobs[job_id]["completed"] = True
            duration = (
                datetime.now() - active_jobs[job_id]["started_at"]
            ).total_seconds()
            print(f"\n✅ Job {job_id} completed in {duration:.1f}s")

    subscriber.on_status(on_status_update)

    try:
        await subscriber.subscribe()
    except KeyboardInterrupt:
        print("\nStopping monitor...")
        await subscriber.unsubscribe()


# Example usage
if __name__ == "__main__":
    import sys

    print("AppSync Real-time Status Monitor")
    print("================================\n")

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "ingest":
            asyncio.run(submit_report_and_monitor())
        elif command == "query":
            asyncio.run(submit_query_and_monitor())
        elif command == "monitor":
            asyncio.run(continuous_monitor())
        else:
            print(f"Unknown command: {command}")
            print("Usage: python appsync_client_example.py [ingest|query|monitor]")
    else:
        # Default: submit report and monitor
        asyncio.run(submit_report_and_monitor())
