#!/bin/bash
#
# Rollback Script for Molecular Data Management and CRO Integration Platform
#
# This script provides functionality to revert failed deployments across
# different service types (backend, frontend, workers) and deployment
# strategies (rolling, blue/green, canary). It ensures system stability by
# restoring previous working versions when deployments fail.
#
# Dependencies:
# - aws-cli (2.x): AWS command line interface for ECS and CodeDeploy operations
# - jq (1.6+): JSON processor for parsing AWS CLI outputs
# - ./health_check.sh: Script for verifying service health
#
# Usage:
#   ./rollback.sh --service <service_name> [--environment <env>] [--deployment-type <type>] [--deployment-id <id>]
#
# Options:
#   --service <service_name>       Service to roll back (e.g., api, frontend, molecule-service)
#   --environment <env>            Environment (dev, staging, prod)
#   --deployment-type <type>       Deployment type (rolling, blue-green, canary)
#   --deployment-id <id>           Specific deployment ID to roll back
#   --verbose                      Enable verbose output
#
# Exit codes:
#   0 - Rollback successful
#   1 - Prerequisites not met
#   2 - Rollback failed
#   3 - Invalid arguments
#   4 - Service health check failed after rollback
#

# Try to source health check script for service verification
if [[ -f "./health_check.sh" ]]; then
    source ./health_check.sh
else
    echo "WARNING: health_check.sh not found. Service health verification will be limited."
    # Define a minimal version of the check_service_health function
    check_service_health() {
        local service_name="$1"
        local environment="$2"
        echo "WARNING: Using minimal health check as health_check.sh was not found."
        # Always return success as we can't actually check
        return 0
    }
fi

# Global variables with defaults from environment variables
AWS_REGION="${AWS_REGION:-us-east-1}"
ECS_CLUSTER="${ECS_CLUSTER:-molecule-flow-${ENVIRONMENT}}"
ENVIRONMENT="${ENVIRONMENT:-dev}"
ROLLBACK_TIMEOUT="${ROLLBACK_TIMEOUT:-600}"
HEALTH_CHECK_RETRIES="${HEALTH_CHECK_RETRIES:-3}"
HEALTH_CHECK_INTERVAL="${HEALTH_CHECK_INTERVAL:-30}"
VERBOSE="${VERBOSE:-false}"

# Check prerequisites
check_prerequisites() {
    local missing_tools=false
    
    # Check for AWS CLI
    if ! command -v aws &> /dev/null; then
        log_message "AWS CLI is not installed. Please install aws-cli 2.x to use this script." "ERROR"
        missing_tools=true
    fi
    
    # Check for jq
    if ! command -v jq &> /dev/null; then
        log_message "jq is not installed. Please install jq 1.6+ to use this script." "ERROR"
        missing_tools=true
    fi
    
    # Check for AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        log_message "AWS credentials not configured or insufficient permissions." "ERROR"
        missing_tools=true
    fi
    
    if [[ "$missing_tools" == "true" ]]; then
        return 1
    fi
    
    log_message "All required tools are available" "DEBUG"
    return 0
}

# Logging function
log_message() {
    local message="$1"
    local level="${2:-INFO}"
    local timestamp=$(date "+%Y-%m-%d %H:%M:%S")
    
    case "$level" in
        "ERROR")
            echo "[$timestamp] ERROR: $message" >&2
            ;;
        "INFO")
            if [[ "$VERBOSE" == "true" || "$level" == "ERROR" ]]; then
                echo "[$timestamp] INFO: $message"
            fi
            ;;
        "DEBUG")
            if [[ "$VERBOSE" == "true" ]]; then
                echo "[$timestamp] DEBUG: $message"
            fi
            ;;
        *)
            echo "[$timestamp] $level: $message"
            ;;
    esac
}

# Get the previous task definition for a service
get_previous_task_definition() {
    local service_name="$1"
    
    log_message "Getting previous task definition for service $service_name" "DEBUG"
    
    # Get current task definition from the service
    local current_task_def=$(aws ecs describe-services \
        --cluster "$ECS_CLUSTER" \
        --services "$service_name" \
        --region "$AWS_REGION" \
        --query "services[0].taskDefinition" \
        --output text)
    
    if [[ -z "$current_task_def" || "$current_task_def" == "None" ]]; then
        log_message "Failed to get current task definition for service $service_name" "ERROR"
        return 1
    fi
    
    log_message "Current task definition: $current_task_def" "DEBUG"
    
    # Extract the family and current revision number
    local family=$(echo "$current_task_def" | cut -d '/' -f 2 | cut -d ':' -f 1)
    local current_revision=$(echo "$current_task_def" | cut -d ':' -f 3)
    
    log_message "Task definition family: $family, current revision: $current_revision" "DEBUG"
    
    # Get the list of task definition revisions
    local task_definitions=$(aws ecs list-task-definitions \
        --family-prefix "$family" \
        --sort DESC \
        --region "$AWS_REGION" \
        --query "taskDefinitionArns" \
        --output json)
    
    # Find the previous revision (the one before the current)
    local previous_task_def=$(echo "$task_definitions" | jq -r '.[] | select(contains(":'$(($current_revision-1))':"))' | head -1)
    
    if [[ -z "$previous_task_def" || "$previous_task_def" == "null" ]]; then
        log_message "Failed to find previous task definition for service $service_name" "ERROR"
        return 1
    fi
    
    log_message "Previous task definition: $previous_task_def" "DEBUG"
    echo "$previous_task_def"
    return 0
}

# Roll back a rolling deployment
rollback_rolling_deployment() {
    local service_name="$1"
    local previous_task_definition_arn="$2"
    
    log_message "Rolling back service $service_name to task definition $previous_task_definition_arn" "INFO"
    
    # Update the service to use the previous task definition
    local update_result=$(aws ecs update-service \
        --cluster "$ECS_CLUSTER" \
        --service "$service_name" \
        --task-definition "$previous_task_definition_arn" \
        --force-new-deployment \
        --region "$AWS_REGION" \
        --query "service.deployments" \
        --output json)
    
    if [[ $? -ne 0 ]]; then
        log_message "Failed to update service to previous task definition" "ERROR"
        return 1
    fi
    
    log_message "Service update initiated, waiting for deployment to complete..." "INFO"
    
    # Wait for the service to stabilize with the previous task definition
    if ! aws ecs wait services-stable \
        --cluster "$ECS_CLUSTER" \
        --services "$service_name" \
        --region "$AWS_REGION"; then
        log_message "Timeout waiting for service to stabilize" "ERROR"
        return 1
    fi
    
    log_message "Service has been rolled back successfully" "INFO"
    return 0
}

# Roll back a blue/green deployment
rollback_blue_green_deployment() {
    local service_name="$1"
    local deployment_id="$2"
    
    if [[ -z "$deployment_id" ]]; then
        log_message "Deployment ID is required for blue/green rollback" "ERROR"
        return 1
    fi
    
    log_message "Rolling back blue/green deployment $deployment_id for service $service_name" "INFO"
    
    # First, check if the deployment is still in progress
    local deployment_status=$(aws deploy get-deployment \
        --deployment-id "$deployment_id" \
        --region "$AWS_REGION" \
        --query "deploymentInfo.status" \
        --output text)
    
    # If deployment is still in progress, stop it first
    if [[ "$deployment_status" != "SUCCEEDED" && "$deployment_status" != "FAILED" && "$deployment_status" != "STOPPED" ]]; then
        log_message "Deployment is still in progress ($deployment_status), stopping it first" "INFO"
        
        aws deploy stop-deployment \
            --deployment-id "$deployment_id" \
            --region "$AWS_REGION" \
            --query "status" \
            --output text
            
        if [[ $? -ne 0 ]]; then
            log_message "Failed to stop in-progress deployment" "ERROR"
            return 1
        fi
    fi
    
    # Now initiate rollback through CodeDeploy
    log_message "Initiating rollback through CodeDeploy" "INFO"
    
    local rollback_result=$(aws deploy rollback-deployment \
        --deployment-id "$deployment_id" \
        --rollback-deployment-id "$deployment_id" \
        --region "$AWS_REGION" \
        --output json)
    
    if [[ $? -ne 0 ]]; then
        log_message "Failed to initiate rollback through CodeDeploy" "ERROR"
        return 1
    fi
    
    local rollback_id=$(echo "$rollback_result" | jq -r '.rollbackDeploymentId')
    log_message "Rollback deployment initiated with ID: $rollback_id" "INFO"
    
    # Wait for rollback to complete
    log_message "Waiting for rollback deployment to complete..." "INFO"
    
    local timeout_seconds=$ROLLBACK_TIMEOUT
    local start_time=$(date +%s)
    local end_time=$((start_time + timeout_seconds))
    local rollback_complete=false
    
    while [[ $(date +%s) -lt $end_time ]]; do
        local current_status=$(aws deploy get-deployment \
            --deployment-id "$rollback_id" \
            --region "$AWS_REGION" \
            --query "deploymentInfo.status" \
            --output text)
        
        log_message "Rollback deployment status: $current_status" "DEBUG"
        
        if [[ "$current_status" == "SUCCEEDED" ]]; then
            rollback_complete=true
            break
        elif [[ "$current_status" == "FAILED" || "$current_status" == "STOPPED" ]]; then
            log_message "Rollback deployment failed or was stopped: $current_status" "ERROR"
            return 1
        fi
        
        sleep 10
    done
    
    if [[ "$rollback_complete" != "true" ]]; then
        log_message "Timeout waiting for rollback deployment to complete" "ERROR"
        return 1
    fi
    
    log_message "Blue/green rollback completed successfully" "INFO"
    return 0
}

# Roll back a canary deployment
rollback_canary_deployment() {
    local service_name="$1"
    local deployment_id="$2"
    
    if [[ -z "$deployment_id" ]]; then
        log_message "Deployment ID is required for canary rollback" "ERROR"
        return 1
    fi
    
    log_message "Rolling back canary deployment $deployment_id for service $service_name" "INFO"
    
    # First, check if the deployment is still in progress
    local deployment_status=$(aws deploy get-deployment \
        --deployment-id "$deployment_id" \
        --region "$AWS_REGION" \
        --query "deploymentInfo.status" \
        --output text)
    
    # If deployment is still in progress, stop it first
    if [[ "$deployment_status" != "SUCCEEDED" && "$deployment_status" != "FAILED" && "$deployment_status" != "STOPPED" ]]; then
        log_message "Deployment is still in progress ($deployment_status), stopping it first" "INFO"
        
        aws deploy stop-deployment \
            --deployment-id "$deployment_id" \
            --region "$AWS_REGION" \
            --query "status" \
            --output text
            
        if [[ $? -ne 0 ]]; then
            log_message "Failed to stop in-progress deployment" "ERROR"
            return 1
        fi
    fi
    
    # For canary deployments, we need to get the previous task definition
    local previous_task_definition_arn=$(get_previous_task_definition "$service_name")
    if [[ -z "$previous_task_definition_arn" ]]; then
        log_message "Failed to find previous task definition for canary rollback" "ERROR"
        return 1
    fi
    
    # Get the deployment info to find the app specification
    local deployment_info=$(aws deploy get-deployment \
        --deployment-id "$deployment_id" \
        --region "$AWS_REGION" \
        --query "deploymentInfo" \
        --output json)
    
    local application_name=$(echo "$deployment_info" | jq -r '.applicationName')
    local deployment_group=$(echo "$deployment_info" | jq -r '.deploymentGroupName')
    
    # Initiate an immediate rollback
    local rollback_result=$(aws deploy create-deployment \
        --application-name "$application_name" \
        --deployment-group-name "$deployment_group" \
        --revision "{\"revisionType\": \"String\", \"string\": {\"content\": \"{\\\"version\\\": 1, \\\"Resources\\\": [{\\\"TargetService\\\": {\\\"Type\\\": \\\"AWS::ECS::Service\\\", \\\"Properties\\\": {\\\"TaskDefinition\\\": \\\"${previous_task_definition_arn}\\\", \\\"LoadBalancerInfo\\\": {\\\"ContainerName\\\": \\\"${service_name}\\\", \\\"ContainerPort\\\": 8000}}}]}}\"}}" \
        --description "Immediate rollback of canary deployment" \
        --region "$AWS_REGION" \
        --output json)
    
    if [[ $? -ne 0 ]]; then
        log_message "Failed to initiate immediate rollback" "ERROR"
        return 1
    fi
    
    local rollback_id=$(echo "$rollback_result" | jq -r '.deploymentId')
    log_message "Rollback deployment initiated with ID: $rollback_id" "INFO"
    
    # Wait for rollback to complete
    log_message "Waiting for rollback deployment to complete..." "INFO"
    
    local timeout_seconds=$ROLLBACK_TIMEOUT
    local start_time=$(date +%s)
    local end_time=$((start_time + timeout_seconds))
    local rollback_complete=false
    
    while [[ $(date +%s) -lt $end_time ]]; do
        local current_status=$(aws deploy get-deployment \
            --deployment-id "$rollback_id" \
            --region "$AWS_REGION" \
            --query "deploymentInfo.status" \
            --output text)
        
        log_message "Rollback deployment status: $current_status" "DEBUG"
        
        if [[ "$current_status" == "SUCCEEDED" ]]; then
            rollback_complete=true
            break
        elif [[ "$current_status" == "FAILED" || "$current_status" == "STOPPED" ]]; then
            log_message "Rollback deployment failed or was stopped: $current_status" "ERROR"
            return 1
        fi
        
        sleep 10
    done
    
    if [[ "$rollback_complete" != "true" ]]; then
        log_message "Timeout waiting for rollback deployment to complete" "ERROR"
        return 1
    fi
    
    log_message "Canary rollback completed successfully" "INFO"
    return 0
}

# Determine the deployment type for a service
get_deployment_type() {
    local service_name="$1"
    local environment="${2:-$ENVIRONMENT}"
    
    log_message "Determining deployment type for service $service_name in environment $environment" "DEBUG"
    
    # Check if the service is using CodeDeploy (blue/green or canary)
    local deployment_controller=$(aws ecs describe-services \
        --cluster "$ECS_CLUSTER" \
        --services "$service_name" \
        --region "$AWS_REGION" \
        --query "services[0].deploymentController.type" \
        --output text)
    
    if [[ "$deployment_controller" == "CODE_DEPLOY" ]]; then
        # It's either blue/green or canary - need to check the deployment configuration
        
        # First, get the associated CodeDeploy application and deployment group
        local task_set_info=$(aws ecs describe-task-sets \
            --cluster "$ECS_CLUSTER" \
            --service "$service_name" \
            --region "$AWS_REGION" \
            --query "taskSets[?status=='ACTIVE']" \
            --output json)
        
        if [[ -z "$task_set_info" || "$task_set_info" == "[]" ]]; then
            log_message "No active task sets found for service $service_name" "ERROR"
            echo "rolling"  # Default to rolling if we can't determine
            return
        fi
        
        local deployment_info=$(echo "$task_set_info" | jq -r '.[0].externalId' 2>/dev/null)
        
        if [[ -n "$deployment_info" && "$deployment_info" != "null" ]]; then
            # Get the deployment configuration
            local deployment_config=$(aws deploy get-deployment \
                --deployment-id "$deployment_info" \
                --region "$AWS_REGION" \
                --query "deploymentInfo.deploymentStyle" \
                --output json 2>/dev/null)
            
            if [[ -n "$deployment_config" && "$deployment_config" != "null" ]]; then
                local deployment_option=$(echo "$deployment_config" | jq -r '.deploymentOption')
                
                if [[ "$deployment_option" == "WITH_TRAFFIC_CONTROL" ]]; then
                    # Check if it uses alarms or time-based traffic shifting
                    local deployment_config_name=$(aws deploy get-deployment \
                        --deployment-id "$deployment_info" \
                        --region "$AWS_REGION" \
                        --query "deploymentInfo.deploymentConfigName" \
                        --output text 2>/dev/null)
                    
                    if [[ "$deployment_config_name" == *"Canary"* ]]; then
                        echo "canary"
                        return
                    else
                        echo "blue-green"
                        return
                    fi
                fi
            fi
        fi
    fi
    
    # Default to rolling deployment if we can't determine a specific type
    echo "rolling"
}

# Get the active deployment ID for a service
get_active_deployment_id() {
    local service_name="$1"
    local deployment_type="$2"
    
    log_message "Getting active deployment ID for service $service_name (type: $deployment_type)" "DEBUG"
    
    case "$deployment_type" in
        "rolling")
            # For rolling deployments, get the ECS deployment ID
            local deployment_id=$(aws ecs describe-services \
                --cluster "$ECS_CLUSTER" \
                --services "$service_name" \
                --region "$AWS_REGION" \
                --query "services[0].deployments[0].id" \
                --output text)
            
            if [[ -z "$deployment_id" || "$deployment_id" == "None" ]]; then
                log_message "No active ECS deployment found for service $service_name" "ERROR"
                echo ""
                return 1
            fi
            
            echo "$deployment_id"
            ;;
            
        "blue-green"|"canary")
            # For blue/green or canary, get the CodeDeploy deployment ID
            local task_set_info=$(aws ecs describe-task-sets \
                --cluster "$ECS_CLUSTER" \
                --service "$service_name" \
                --region "$AWS_REGION" \
                --query "taskSets[?status=='ACTIVE']" \
                --output json)
            
            if [[ -z "$task_set_info" || "$task_set_info" == "[]" ]]; then
                log_message "No active task sets found for service $service_name" "ERROR"
                echo ""
                return 1
            fi
            
            local deployment_id=$(echo "$task_set_info" | jq -r '.[0].externalId' 2>/dev/null)
            
            if [[ -z "$deployment_id" || "$deployment_id" == "null" ]]; then
                log_message "No CodeDeploy deployment ID found for service $service_name" "ERROR"
                echo ""
                return 1
            fi
            
            echo "$deployment_id"
            ;;
            
        *)
            log_message "Unknown deployment type: $deployment_type" "ERROR"
            echo ""
            return 1
            ;;
    esac
}

# Verify rollback was successful by checking service health
verify_rollback() {
    local service_name="$1"
    
    log_message "Verifying health of service $service_name after rollback" "INFO"
    
    # Use the check_service_health function from health_check.sh
    for ((i=1; i<=$HEALTH_CHECK_RETRIES; i++)); do
        log_message "Health check attempt $i of $HEALTH_CHECK_RETRIES" "DEBUG"
        
        if check_service_health "$service_name" "$ENVIRONMENT"; then
            log_message "Service $service_name is healthy after rollback" "INFO"
            return 0
        fi
        
        if [[ $i -lt $HEALTH_CHECK_RETRIES ]]; then
            log_message "Service not yet healthy, waiting $HEALTH_CHECK_INTERVAL seconds before retry" "INFO"
            sleep $HEALTH_CHECK_INTERVAL
        fi
    done
    
    log_message "Service $service_name is still unhealthy after rollback" "ERROR"
    return 1
}

# Notify administrators of rollback status
notify_rollback_status() {
    local service_name="$1"
    local success="$2"
    local details="$3"
    
    local status_msg="FAILED"
    if [[ "$success" == "true" ]]; then
        status_msg="SUCCESSFUL"
    fi
    
    local message="Rollback of $service_name in $ENVIRONMENT environment: $status_msg. $details"
    log_message "$message" "INFO"
    
    # If SNS topic is configured, send notification
    if [[ -n "$SNS_TOPIC_ARN" ]]; then
        aws sns publish \
            --topic-arn "$SNS_TOPIC_ARN" \
            --message "$message" \
            --subject "Deployment Rollback $status_msg: $service_name ($ENVIRONMENT)" \
            --region "$AWS_REGION"
    fi
    
    if [[ "$success" != "true" ]]; then
        return 1
    fi
    
    return 0
}

# Main rollback function
rollback_deployment() {
    local service_name="$1"
    local deployment_type="$2"
    local deployment_id="$3"
    
    log_message "Starting rollback process for service $service_name" "INFO"
    
    # If deployment type not provided, try to determine it
    if [[ -z "$deployment_type" ]]; then
        deployment_type=$(get_deployment_type "$service_name" "$ENVIRONMENT")
        log_message "Determined deployment type: $deployment_type" "INFO"
    fi
    
    # If deployment ID not provided, try to get the active one
    if [[ -z "$deployment_id" && "$deployment_type" != "rolling" ]]; then
        deployment_id=$(get_active_deployment_id "$service_name" "$deployment_type")
        log_message "Found active deployment ID: $deployment_id" "INFO"
    fi
    
    local rollback_success=false
    local details=""
    
    case "$deployment_type" in
        "rolling")
            log_message "Performing rolling deployment rollback" "INFO"
            
            # Get the previous task definition
            local previous_task_def=$(get_previous_task_definition "$service_name")
            
            if [[ -z "$previous_task_def" ]]; then
                details="Failed to find previous task definition."
                notify_rollback_status "$service_name" "false" "$details"
                return 1
            fi
            
            # Perform the rollback
            if rollback_rolling_deployment "$service_name" "$previous_task_def"; then
                rollback_success=true
                details="Successfully rolled back to task definition $previous_task_def."
            else
                details="Failed to roll back to previous task definition."
            fi
            ;;
            
        "blue-green")
            log_message "Performing blue/green deployment rollback" "INFO"
            
            if [[ -z "$deployment_id" ]]; then
                details="No deployment ID provided or found for blue/green rollback."
                notify_rollback_status "$service_name" "false" "$details"
                return 1
            fi
            
            # Perform the rollback
            if rollback_blue_green_deployment "$service_name" "$deployment_id"; then
                rollback_success=true
                details="Successfully rolled back blue/green deployment $deployment_id."
            else
                details="Failed to roll back blue/green deployment."
            fi
            ;;
            
        "canary")
            log_message "Performing canary deployment rollback" "INFO"
            
            if [[ -z "$deployment_id" ]]; then
                details="No deployment ID provided or found for canary rollback."
                notify_rollback_status "$service_name" "false" "$details"
                return 1
            fi
            
            # Perform the rollback
            if rollback_canary_deployment "$service_name" "$deployment_id"; then
                rollback_success=true
                details="Successfully rolled back canary deployment $deployment_id."
            else
                details="Failed to roll back canary deployment."
            fi
            ;;
            
        *)
            details="Unknown deployment type: $deployment_type"
            notify_rollback_status "$service_name" "false" "$details"
            return 1
            ;;
    esac
    
    # If rollback was successful, verify the service health
    if [[ "$rollback_success" == "true" ]]; then
        log_message "Rollback completed, verifying service health" "INFO"
        
        if verify_rollback "$service_name"; then
            details+=" Service health verified after rollback."
        else
            rollback_success=false
            details+=" Service is unhealthy after rollback!"
        fi
    fi
    
    # Notify rollback status
    notify_rollback_status "$service_name" "$rollback_success" "$details"
    
    if [[ "$rollback_success" == "true" ]]; then
        return 0
    else
        return 1
    fi
}

# Main function to parse arguments and execute rollback
main() {
    local SERVICE=""
    local DEPLOYMENT_TYPE=""
    local DEPLOYMENT_ID=""
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --service)
                SERVICE="$2"
                shift 2
                ;;
            --environment)
                ENVIRONMENT="$2"
                shift 2
                ;;
            --deployment-type)
                DEPLOYMENT_TYPE="$2"
                shift 2
                ;;
            --deployment-id)
                DEPLOYMENT_ID="$2"
                shift 2
                ;;
            --verbose)
                VERBOSE=true
                shift
                ;;
            *)
                log_message "Unknown option: $1" "ERROR"
                echo "Usage: $0 --service <service_name> [--environment <env>] [--deployment-type <type>] [--deployment-id <id>] [--verbose]"
                return 3
                ;;
        esac
    done
    
    # Validate required arguments
    if [[ -z "$SERVICE" ]]; then
        log_message "Service name is required" "ERROR"
        echo "Usage: $0 --service <service_name> [--environment <env>] [--deployment-type <type>] [--deployment-id <id>] [--verbose]"
        return 3
    fi
    
    # Check prerequisites
    if ! check_prerequisites; then
        return 1
    fi
    
    # Execute rollback
    if rollback_deployment "$SERVICE" "$DEPLOYMENT_TYPE" "$DEPLOYMENT_ID"; then
        log_message "Rollback of $SERVICE completed successfully" "INFO"
        return 0
    else
        log_message "Rollback of $SERVICE failed" "ERROR"
        return 2
    fi
}

# Run main function if script is executed directly (not sourced)
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
    exit $?
fi

# Export functions for use in other scripts
export -f rollback_deployment