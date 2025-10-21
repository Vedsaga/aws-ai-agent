#!/bin/bash

################################################################################
# CLEANUP OLD FILES
# Removes outdated deployment scripts and documentation
# Keeps only: DEPLOY.sh, DEPLOYMENT.md, and essential test files
################################################################################

echo "=========================================="
echo "Cleaning up outdated files..."
echo "=========================================="
echo ""

# Files to delete (outdated deployment scripts)
OLD_SCRIPTS=(
    "deploy-apis.sh"
    "deploy_all_fixes.sh"
    "deploy_and_test_apis.sh"
    "deploy_authorizer.py"
    "deploy_authorizer.sh"
    "deploy_config_handler.py"
    "deploy_orchestrator.py"
    "deploy_orchestrator.sh"
    "deploy_orchestrator_with_realtime.sh"
    "deploy_realtime_stack.sh"
    "deploy_status_publisher.sh"
    "deploy_status_updates_quick.sh"
    "quick_fix_deploy.sh"
    "redeploy_with_status.sh"
)

# Outdated test scripts (keep comprehensive_api_test.py)
OLD_TESTS=(
    "test-all-apis.sh"
    "test_all_apis.py"
    "test_all_endpoints.py"
    "test_api.py"
    "test_api_simple.sh"
    "test_appsync_realtime.py"
    "test_current_state.sh"
    "test_demo_api.sh"
    "test_e2e_workflow.py"
    "test_end_to_end.sh"
    "test_ingest_api_realtime.sh"
    "test_ingest_simple.sh"
    "test_proof.sh"
    "test_with_outputs.py"
    "quick_api_test.py"
    "quick_test.py"
    "run_tests.sh"
)

# Outdated proof/demo scripts
OLD_PROOF=(
    "proof_agents.sh"
    "prove_agents_simple.py"
    "prove_multiagent_working.py"
)

# Outdated documentation (keep essential ones)
OLD_DOCS=(
    "ACTION_NOW.md"
    "API_AUTHORIZATION_FIX.md"
    "API_CHECKLIST.md"
    "API_FIX_SUMMARY.md"
    "API_REFERENCE.md"
    "API_SUMMARY.md"
    "API_TESTING_CHECKLIST.md"
    "APPSYNC_STATUS.md"
    "AWS_OUTAGE_RECOVERY.md"
    "CRITICAL_ACTION_PLAN.md"
    "CRITICAL_FIXES.md"
    "DEMO_SCRIPT.md"
    "DEPLOYMENT_GUIDE.md"
    "DEPLOYMENT_SUCCESS.md"
    "DOMAIN_AND_AGENT_DETAILS.md"
    "E2E_WORKFLOW_SUMMARY.md"
    "EXECUTION_GUIDE.md"
    "FRONTEND_API_GUIDE.md"
    "FRONTEND_INTEGRATION_PLAN.md"
    "FRONTEND_RUNNING.md"
    "GAP_ANALYSIS.md"
    "GEOMETRY_TYPE_IMPLEMENTATION.md"
    "HONEST_AGENT_PROOF.md"
    "HONEST_STATUS.md"
    "IMPLEMENTATION_COMPLETE.md"
    "INTEGRATION_READY.md"
    "MANUAL_TESTING_CHECKLIST.md"
    "MULTI_AGENT_PROOF_EXECUTIVE_SUMMARY.md"
    "MULTI_AGENT_PROOF_REPORT.md"
    "ORCHESTRATOR_REALTIME_DEPLOYMENT_SUMMARY.md"
    "QUICK_API_REFERENCE.md"
    "QUICK_API_TEST.md"
    "QUICK_FRONTEND_TEST.sh"
    "QUICK_TEST_CHECKLIST.md"
    "README_ACTIONS.md"
    "SETUP_COMPLETE.md"
    "START_HERE.md"
    "TASK_5_COMPLETION_REPORT.md"
    "TASK_5_SUMMARY.md"
    "TESTING_SUMMARY.md"
    "TESTING_TASK_SUMMARY.md"
    "TEST_REPORT.md"
    "TEST_SUITE_README.md"
    "TEST_SUITE_SUMMARY.md"
    "URGENT_API_FIX_PLAN.md"
    "VERIFICATION_SUMMARY.md"
)

# Outdated output/log files
OLD_OUTPUTS=(
    "ACTUAL_DATABASE_PROOF.txt"
    "AGENT_OUTPUT_PROOF.txt"
    "ANSWERS.txt"
    "CRITICAL_FIXES_DONE.txt"
    "END_TO_END_TEST_RESULTS.txt"
    "EVIDENCE_SUMMARY.txt"
    "FINAL_INTEGRATION_STATUS.txt"
    "FINAL_STATUS.txt"
    "FINAL_TEST_SUMMARY.txt"
    "PROOF_COMPLETE.txt"
    "URGENT_FIXES.txt"
    "e2e_workflow_results.txt"
    "orchestrator_deploy.log"
    "orchestrator_deploy2.log"
    "proof_output.txt"
    "test_output.txt"
    "test_output_comprehensive.txt"
    "test_results_raw.txt"
    "TEST_FRONTEND_COMPILATION.txt"
)

# Outdated config/data files
OLD_CONFIGS=(
    "appsync_client_example.js"
    "appsync_client_example.py"
    "APPSYNC_IMPLEMENTATION.py"
    "APPSYNC_QUICKSTART.sh"
    "client_polling_example.js"
    "demo_api.py"
    "diagnose_api.py"
    "fix_lambda_handlers.py"
    "frontend-api-client.js"
    "get_jwt_token.sh"
    "grant_permissions.json"
    "lambda_invoke_permissions.json"
    "lambda_response.json"
    "monitor_aws.sh"
    "orchestrator_permissions.json"
    "package_lambda.py"
    "setup_test_user.sh"
    "test_orchestrator_realtime.json"
    "test_payload.json"
    "test_results_20251020_174151.json"
    "update_lambdas.py"
)

# Function to delete files
delete_files() {
    local category=$1
    shift
    local files=("$@")
    
    echo "Deleting $category..."
    for file in "${files[@]}"; do
        if [ -f "$file" ]; then
            rm "$file"
            echo "  ✓ Deleted: $file"
        fi
    done
    echo ""
}

# Delete all outdated files
delete_files "deployment scripts" "${OLD_SCRIPTS[@]}"
delete_files "test scripts" "${OLD_TESTS[@]}"
delete_files "proof scripts" "${OLD_PROOF[@]}"
delete_files "documentation" "${OLD_DOCS[@]}"
delete_files "output files" "${OLD_OUTPUTS[@]}"
delete_files "config files" "${OLD_CONFIGS[@]}"

echo "=========================================="
echo "Cleanup complete!"
echo "=========================================="
echo ""
echo "Kept essential files:"
echo "  ✓ DEPLOY.sh - Main deployment script"
echo "  ✓ DEPLOYMENT.md - Complete deployment guide"
echo "  ✓ comprehensive_api_test.py - API test suite"
echo "  ✓ API_STATUS_VERIFIED.md - Latest test results"
echo "  ✓ HACKATHON_READY_SUMMARY.md - Demo guide"
echo "  ✓ FRONTEND_INTEGRATION_COMPLETE.md - Frontend docs"
echo "  ✓ API_COMPLETE_GUIDE.md - API reference"
echo "  ✓ README.md - Project overview"
echo ""
echo "To deploy the system, run:"
echo "  ./DEPLOY.sh"
echo ""
