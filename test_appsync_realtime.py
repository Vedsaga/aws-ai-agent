#!/usr/bin/env python3
"""
Test AppSync Real-time Status Updates

This script tests the end-to-end AppSync integration by:
1. Subscribing to real-time status updates
2. Submitting a report/query
3. Verifying that status updates are received
4. Checking that all expected status transitions occur
"""

import os
import sys
import json
import asyncio
import argparse
from datetime import datetime
from typing import List, Dict, Any
import requests

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from appsync_client_example import AppSyncStatusSubscriber
except ImportError:
    print("Error: Could not import AppSyncStatusSubscriber")
    print("Make sure appsync_client_example.py is in the same directory")
    sys.exit(1)


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
TENANT_ID = os.environ.get("TENANT_ID", "default-tenant")


# Expected status transitions
EXPECTED_INGEST_STATUSES = [
    "accepted",
    "processing",
    "loading_agents",
    "agents_loaded",
    "agent_invoking",
    "agent_complete",
    "verifying",
    "synthesizing",
    "saving",
    "complete",
]

EXPECTED_QUERY_STATUSES = [
    "accepted",
    "processing",
    "loading_agents",
    "agents_loaded",
    "agent_invoking",
    "agent_complete",
    "verifying",
    "synthesizing",
    "saving",
    "complete",
]


class TestResult:
    """Test result container"""

    def __init__(self, test_name: str):
        self.test_name = test_name
        self.passed = False
        self.message = ""
        self.details = {}
        self.start_time = datetime.now()
        self.end_time = None

    def pass_test(self, message: str = "", details: Dict[str, Any] = None):
        self.passed = True
        self.message = message
        self.details = details or {}
        self.end_time = datetime.now()

    def fail_test(self, message: str = "", details: Dict[str, Any] = None):
        self.passed = False
        self.message = message
        self.details = details or {}
        self.end_time = datetime.now()

    @property
    def duration(self):
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

    def __str__(self):
        status = "✅ PASS" if self.passed else "❌ FAIL"
        duration = f" ({self.duration:.2f}s)" if self.duration else ""
        return f"{status} {self.test_name}{duration}: {self.message}"


class AppSyncTester:
    """Test harness for AppSync real-time updates"""

    def __init__(self):
        self.results: List[TestResult] = []
        self.subscriber = None

    def add_result(self, result: TestResult):
        self.results.append(result)
        print(result)

    async def test_subscription_connection(self) -> TestResult:
        """Test 1: Verify we can connect to AppSync and establish subscription"""
        result = TestResult("AppSync Subscription Connection")

        try:
            self.subscriber = AppSyncStatusSubscriber(
                APPSYNC_API_URL, APPSYNC_API_KEY, USER_ID
            )

            # Track connection
            connected = asyncio.Event()

            # Override handle_message to detect connection
            original_handle_message = self.subscriber.handle_message

            async def track_connection(message):
                if message.get("type") == "start_ack":
                    connected.set()
                await original_handle_message(message)

            self.subscriber.handle_message = track_connection

            # Start subscription
            subscription_task = asyncio.create_task(self.subscriber.subscribe())

            # Wait for connection
            try:
                await asyncio.wait_for(connected.wait(), timeout=10)
                result.pass_test(
                    "Successfully connected to AppSync", {"url": APPSYNC_API_URL}
                )
            except asyncio.TimeoutError:
                result.fail_test("Connection timeout", {"timeout": 10})
                subscription_task.cancel()
                return result

        except Exception as e:
            result.fail_test(f"Connection error: {str(e)}")

        return result

    async def test_ingest_status_updates(self) -> TestResult:
        """Test 2: Submit report and verify status updates"""
        result = TestResult("Ingest Status Updates")

        try:
            # Track updates
            updates_received = []
            job_completed = asyncio.Event()
            job_id = None

            def on_status(update):
                updates_received.append(update)
                if update.get("status") in ["complete", "error"]:
                    job_completed.set()

            self.subscriber.on_status(on_status)

            # Submit report
            report_payload = {
                "domain_id": "civic_complaints",
                "text": "Large pothole at Main Street and 5th Avenue intersection",
                "source": "test",
                "priority": "normal",
            }

            response = requests.post(
                f"{API_BASE_URL}/api/v1/ingest",
                json=report_payload,
                headers={"Content-Type": "application/json", "X-Tenant-ID": TENANT_ID},
                timeout=10,
            )

            if response.status_code not in [200, 202]:
                result.fail_test(
                    f"Failed to submit report: {response.status_code}",
                    {"response": response.text},
                )
                return result

            response_data = response.json()
            job_id = response_data.get("job_id")

            if not job_id:
                result.fail_test("No job_id in response", {"response": response_data})
                return result

            # Wait for completion
            try:
                await asyncio.wait_for(job_completed.wait(), timeout=60)
            except asyncio.TimeoutError:
                result.fail_test(
                    "Job did not complete within timeout",
                    {
                        "job_id": job_id,
                        "updates_received": len(updates_received),
                        "statuses": [u.get("status") for u in updates_received],
                    },
                )
                return result

            # Verify updates
            statuses = [u.get("status") for u in updates_received]
            unique_statuses = list(dict.fromkeys(statuses))  # Preserve order

            if len(updates_received) == 0:
                result.fail_test("No status updates received", {"job_id": job_id})
            elif "complete" in statuses or "error" not in statuses:
                result.pass_test(
                    f"Received {len(updates_received)} status updates",
                    {
                        "job_id": job_id,
                        "total_updates": len(updates_received),
                        "unique_statuses": unique_statuses,
                        "final_status": statuses[-1] if statuses else None,
                    },
                )
            else:
                result.fail_test(
                    "Job completed with error",
                    {
                        "job_id": job_id,
                        "statuses": unique_statuses,
                        "error": updates_received[-1].get("message"),
                    },
                )

        except Exception as e:
            result.fail_test(f"Test error: {str(e)}")

        return result

    async def test_query_status_updates(self) -> TestResult:
        """Test 3: Submit query and verify status updates"""
        result = TestResult("Query Status Updates")

        try:
            # Track updates
            updates_received = []
            job_completed = asyncio.Event()
            job_id = None

            def on_status(update):
                updates_received.append(update)
                if update.get("status") in ["complete", "error"]:
                    job_completed.set()

            self.subscriber.on_status(on_status)

            # Submit query
            query_payload = {
                "domain_id": "civic_complaints",
                "question": "Show me all pothole complaints from last week",
            }

            response = requests.post(
                f"{API_BASE_URL}/api/v1/query",
                json=query_payload,
                headers={"Content-Type": "application/json", "X-Tenant-ID": TENANT_ID},
                timeout=10,
            )

            if response.status_code not in [200, 202]:
                result.fail_test(
                    f"Failed to submit query: {response.status_code}",
                    {"response": response.text},
                )
                return result

            response_data = response.json()
            job_id = response_data.get("job_id")

            if not job_id:
                result.fail_test("No job_id in response", {"response": response_data})
                return result

            # Wait for completion
            try:
                await asyncio.wait_for(job_completed.wait(), timeout=60)
            except asyncio.TimeoutError:
                result.fail_test(
                    "Query did not complete within timeout",
                    {
                        "job_id": job_id,
                        "updates_received": len(updates_received),
                        "statuses": [u.get("status") for u in updates_received],
                    },
                )
                return result

            # Verify updates
            statuses = [u.get("status") for u in updates_received]
            unique_statuses = list(dict.fromkeys(statuses))

            if len(updates_received) == 0:
                result.fail_test("No status updates received", {"job_id": job_id})
            elif "complete" in statuses or "error" not in statuses:
                result.pass_test(
                    f"Received {len(updates_received)} status updates",
                    {
                        "job_id": job_id,
                        "total_updates": len(updates_received),
                        "unique_statuses": unique_statuses,
                        "final_status": statuses[-1] if statuses else None,
                    },
                )
            else:
                result.fail_test(
                    "Query completed with error",
                    {
                        "job_id": job_id,
                        "statuses": unique_statuses,
                        "error": updates_received[-1].get("message"),
                    },
                )

        except Exception as e:
            result.fail_test(f"Test error: {str(e)}")

        return result

    async def test_agent_level_updates(self) -> TestResult:
        """Test 4: Verify agent-level status updates"""
        result = TestResult("Agent-Level Status Updates")

        try:
            # Track updates
            updates_received = []
            agent_updates = []
            job_completed = asyncio.Event()

            def on_status(update):
                updates_received.append(update)
                if update.get("agentName"):
                    agent_updates.append(update)
                if update.get("status") in ["complete", "error"]:
                    job_completed.set()

            self.subscriber.on_status(on_status)

            # Submit report
            report_payload = {
                "domain_id": "civic_complaints",
                "text": "Traffic light malfunction at Broadway and 42nd Street",
                "source": "test",
            }

            response = requests.post(
                f"{API_BASE_URL}/api/v1/ingest",
                json=report_payload,
                headers={"Content-Type": "application/json", "X-Tenant-ID": TENANT_ID},
                timeout=10,
            )

            if response.status_code not in [200, 202]:
                result.fail_test(f"Failed to submit report: {response.status_code}")
                return result

            job_id = response.json().get("job_id")

            # Wait for completion
            try:
                await asyncio.wait_for(job_completed.wait(), timeout=60)
            except asyncio.TimeoutError:
                result.fail_test("Job timeout")
                return result

            # Verify agent updates
            agent_names = list(
                set([u.get("agentName") for u in agent_updates if u.get("agentName")])
            )

            if len(agent_updates) == 0:
                result.fail_test(
                    "No agent-level updates received",
                    {"total_updates": len(updates_received)},
                )
            else:
                result.pass_test(
                    f"Received {len(agent_updates)} agent updates from {len(agent_names)} agents",
                    {
                        "job_id": job_id,
                        "agent_updates": len(agent_updates),
                        "agents": agent_names,
                    },
                )

        except Exception as e:
            result.fail_test(f"Test error: {str(e)}")

        return result

    async def run_all_tests(self):
        """Run all tests"""
        print("=" * 60)
        print("AppSync Real-time Status Updates Test Suite")
        print("=" * 60)
        print(f"AppSync URL: {APPSYNC_API_URL}")
        print(f"API Base URL: {API_BASE_URL}")
        print(f"User ID: {USER_ID}")
        print(f"Tenant ID: {TENANT_ID}")
        print("=" * 60)
        print()

        # Test 1: Connection
        print("Running Test 1: Subscription Connection...")
        result = await self.test_subscription_connection()
        self.add_result(result)

        if not result.passed:
            print("\n❌ Connection test failed. Aborting remaining tests.\n")
            return

        # Wait a bit for subscription to be fully ready
        await asyncio.sleep(2)

        # Test 2: Ingest status updates
        print("\nRunning Test 2: Ingest Status Updates...")
        result = await self.test_ingest_status_updates()
        self.add_result(result)

        await asyncio.sleep(2)

        # Test 3: Query status updates
        print("\nRunning Test 3: Query Status Updates...")
        result = await self.test_query_status_updates()
        self.add_result(result)

        await asyncio.sleep(2)

        # Test 4: Agent-level updates
        print("\nRunning Test 4: Agent-Level Updates...")
        result = await self.test_agent_level_updates()
        self.add_result(result)

        # Cleanup
        if self.subscriber:
            await self.subscriber.unsubscribe()

        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("Test Summary")
        print("=" * 60)

        passed = sum(1 for r in self.results if r.passed)
        total = len(self.results)

        for result in self.results:
            print(result)

        print("=" * 60)
        print(f"Total: {passed}/{total} tests passed")

        if passed == total:
            print("✅ All tests passed!")
        else:
            print(f"❌ {total - passed} test(s) failed")

        print("=" * 60)

        # Print detailed failures
        failures = [r for r in self.results if not r.passed]
        if failures:
            print("\nFailed Tests Details:")
            print("-" * 60)
            for result in failures:
                print(f"\n{result.test_name}:")
                print(f"  Message: {result.message}")
                if result.details:
                    print(f"  Details: {json.dumps(result.details, indent=4)}")
            print("-" * 60)


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Test AppSync real-time status updates"
    )
    parser.add_argument(
        "--api-url", help="API Base URL", default=API_BASE_URL, dest="api_url"
    )
    parser.add_argument(
        "--appsync-url",
        help="AppSync GraphQL URL",
        default=APPSYNC_API_URL,
        dest="appsync_url",
    )
    parser.add_argument(
        "--api-key", help="AppSync API Key", default=APPSYNC_API_KEY, dest="api_key"
    )
    parser.add_argument(
        "--user-id", help="User ID for testing", default=USER_ID, dest="user_id"
    )
    parser.add_argument(
        "--tenant-id",
        help="Tenant ID for testing",
        default=TENANT_ID,
        dest="tenant_id",
    )

    args = parser.parse_args()

    # Update globals
    global API_BASE_URL, APPSYNC_API_URL, APPSYNC_API_KEY, USER_ID, TENANT_ID
    API_BASE_URL = args.api_url
    APPSYNC_API_URL = args.appsync_url
    APPSYNC_API_KEY = args.api_key
    USER_ID = args.user_id
    TENANT_ID = args.tenant_id

    # Check configuration
    if "your-api" in APPSYNC_API_URL or "your-api" in API_BASE_URL:
        print("❌ Error: Please configure APPSYNC_API_URL and API_BASE_URL")
        print("\nSet environment variables:")
        print(
            "  export APPSYNC_API_URL='https://xxx.appsync-api.region.amazonaws.com/graphql'"
        )
        print("  export APPSYNC_API_KEY='your-api-key'")
        print(
            "  export API_BASE_URL='https://xxx.execute-api.region.amazonaws.com/dev'"
        )
        sys.exit(1)

    # Run tests
    tester = AppSyncTester()
    try:
        await tester.run_all_tests()

        # Exit with appropriate code
        passed = sum(1 for r in tester.results if r.passed)
        sys.exit(0 if passed == len(tester.results) else 1)

    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        if tester.subscriber:
            await tester.subscriber.unsubscribe()
        sys.exit(130)


if __name__ == "__main__":
    asyncio.run(main())
