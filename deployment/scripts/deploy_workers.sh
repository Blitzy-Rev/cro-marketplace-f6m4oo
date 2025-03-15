#!/bin/bash
#
# Worker Deployment Script for Molecular Data Management and CRO Integration Platform
#
# This script automates the deployment of Celery worker services to AWS ECS, handling task
# definition updates, service deployment, and health verification. It supports scaling worker
# instances based on queue depth and workload requirements.
#
# Dependencies:
# - aws-cli (2.x): AWS command line interface for ECS deployment operations
# - jq (1.6+): JSON processor for parsing AWS CLI outputs
# - ./health_check.sh: Script for verifying the health of the deployed worker service
# - ./rollback.sh: Script for rolling back deployments in case of failure
#
# Usage:
#   ./deploy_workers.sh [--environment <env>] [--image-tag <tag>] [--min-workers <count>] [--max-workers <count>]
#
# Options:
#   --environment <env>      Deployment environment (dev, staging, prod)
#   --image-tag <tag>        Docker image tag to deploy
#   --min-workers <count>    Minimum number of worker tasks
#   --max-workers <count>    Maximum number of worker tasks
#   --concurrency <num>      Worker concurrency (tasks per worker)
#   --queue <queue_name>     Specific queue to process (default: all queues)
#   --verbose                Enable verbose output
#
# Exit codes:
#   0 - Deployment successful
#   1 - Prerequisites not met
#   2 - Deployment failed
#   3 - Service unhealthy after deployment
#   4 - Invalid arguments
#

# Source health check script for service verification
if [[ -f "./health_check.sh" ]]; then
    source ./health_check.sh
else
    echo "ERROR: health_check.sh not found. This script requires health_check.sh for service verification."
    exit 1
fi

# Source rollback script for handling deployment failures
if [[ -f "./rollback.sh" ]]; then
    source ./rollback.sh
else
    echo "ERROR: rollback.sh not found. This script requires rollback.sh for handling deployment failures."
    exit 1
fi

# Global variables with defaults from environment variables
AWS_REGION="${AWS_REGION:-us-east-1}"
ECR_REPOSITORY="${ECR_REPOSITORY:-molecule-flow/backend}"
ECS_CLUSTER="${ECS_CLUSTER:-molecule-flow-${ENVIRONMENT}}"
ECS_SERVICE="${ECS_SERVICE:-moleculeflow-worker}"
TASK_FAMILY="${TASK_FAMILY:-moleculeflow-worker}"
ENVIRONMENT="${ENVIRONMENT:-dev}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
DEPLOYMENT_TIMEOUT="${DEPLOYMENT_TIMEOUT:-900}"
HEALTH_CHECK_RETRIES="${HEALTH_CHECK_RETRIES:-5}"
HEALTH_CHECK_INTERVAL="${HEALTH_CHECK_INTERVAL:-30}"
WORKER_CONCURRENCY="${WORKER_CONCURRENCY:-8}"
WORKER_PREFETCH_MULTIPLIER="${WORKER_PREFETCH_MULTIPLIER:-4}"
WORKER_MAX_TASKS_PER_CHILD="${WORKER_MAX_TASKS_PER_CHILD:-1000}"
MIN_WORKER_COUNT="${MIN_WORKER_COUNT:-2}"
MAX_WORKER_COUNT="${MAX_WORKER_COUNT:-50}"

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
            echo "[$timestamp] INFO: $message"
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

# Verify that all required tools and environment variables are available
check_prerequisites() {
    log_message "Checking prerequisites..." "DEBUG"
    
    # Check if AWS CLI is installed
    if ! command -v aws &> /dev/null; then
        log_message "AWS CLI is not installed. Please install aws-cli 2.x to use this script." "ERROR"
        return 1
    fi
    
    # Check if jq is installed
    if ! command -v jq &> /dev/null; then
        log_message "jq is not installed. Please install jq 1.6+ to use this script." "ERROR"
        return 1
    fi
    
    # Verify AWS credentials are configured
    if ! aws sts get-caller-identity &> /dev/null; then
        log_message "AWS credentials not configured or insufficient permissions." "ERROR"
        return 1
    fi
    
    # Verify ECR repository exists
    if ! aws ecr describe-repositories --repository-names "$ECR_REPOSITORY" --region "$AWS_REGION" &> /dev/null; then
        log_message "ECR repository $ECR_REPOSITORY does not exist or is not accessible." "ERROR"
        return 1
    fi
    
    log_message "All prerequisites are met." "DEBUG"
    return 0
}

# Retrieve the current task definition for the worker service
get_current_task_definition() {
    log_message "Getting current task definition for service $ECS_SERVICE..." "DEBUG"
    
    # Get the current task definition ARN from the service
    local task_def_arn=$(aws ecs describe-services \
        --cluster "$ECS_CLUSTER" \
        --services "$ECS_SERVICE" \
        --region "$AWS_REGION" \
        --query "services[0].taskDefinition" \
        --output text)
    
    if [[ -z "$task_def_arn" || "$task_def_arn" == "None" ]]; then
        log_message "Failed to get current task definition for service $ECS_SERVICE" "ERROR"
        return 1
    fi
    
    log_message "Current task definition ARN: $task_def_arn" "DEBUG"
    
    # Get the task definition details
    local task_def_json=$(aws ecs describe-task-definition \
        --task-definition "$task_def_arn" \
        --region "$AWS_REGION" \
        --query "taskDefinition" \
        --output json)
    
    if [[ -z "$task_def_json" ]]; then
        log_message "Failed to get task definition details" "ERROR"
        return 1
    fi
    
    # Save task definition to a temporary file
    local temp_file=$(mktemp /tmp/task-def-XXXXXX.json)
    echo "$task_def_json" > "$temp_file"
    
    log_message "Task definition saved to $temp_file" "DEBUG"
    echo "$temp_file"
    return 0
}

# Update the task definition with the new container image and worker configuration
update_task_definition() {
    local task_definition_file="$1"
    local image_uri="$2"
    
    log_message "Updating task definition with new image and worker configuration..." "DEBUG"
    
    # Load the task definition JSON
    local task_def=$(cat "$task_definition_file")
    
    # Update the container image
    local container_name=$(echo "$task_def" | jq -r '.containerDefinitions[0].name')
    task_def=$(echo "$task_def" | jq --arg IMAGE "$image_uri" --arg NAME "$container_name" \
        '.containerDefinitions[] |= if .name == $NAME then .image = $IMAGE else . end')
    
    # Update worker-specific environment variables
    log_message "Setting worker concurrency to $WORKER_CONCURRENCY" "DEBUG"
    log_message "Setting worker prefetch multiplier to $WORKER_PREFETCH_MULTIPLIER" "DEBUG"
    log_message "Setting worker max tasks per child to $WORKER_MAX_TASKS_PER_CHILD" "DEBUG"
    
    # Function to update or add environment variable
    update_env_var() {
        local task_def="$1"
        local container_name="$2"
        local var_name="$3"
        local var_value="$4"
        
        # Check if the environment variable already exists
        local env_exists=$(echo "$task_def" | jq --arg NAME "$container_name" --arg VAR "$var_name" \
            '.containerDefinitions[] | select(.name == $NAME) | .environment[] | select(.name == $VAR) | .name')
        
        if [[ -n "$env_exists" && "$env_exists" != "null" ]]; then
            # Update existing environment variable
            task_def=$(echo "$task_def" | jq --arg NAME "$container_name" --arg VAR "$var_name" --arg VAL "$var_value" \
                '.containerDefinitions[] |= if .name == $NAME then .environment |= map(if .name == $VAR then .value = $VAL else . end) else . end')
        else
            # Add new environment variable
            task_def=$(echo "$task_def" | jq --arg NAME "$container_name" --arg VAR "$var_name" --arg VAL "$var_value" \
                '.containerDefinitions[] |= if .name == $NAME then .environment += [{"name": $VAR, "value": $VAL}] else . end')
        fi
        
        echo "$task_def"
    }
    
    # Update worker configuration environment variables
    task_def=$(update_env_var "$task_def" "$container_name" "CELERY_WORKER_CONCURRENCY" "$WORKER_CONCURRENCY")
    task_def=$(update_env_var "$task_def" "$container_name" "CELERY_WORKER_PREFETCH_MULTIPLIER" "$WORKER_PREFETCH_MULTIPLIER")
    task_def=$(update_env_var "$task_def" "$container_name" "CELERY_WORKER_MAX_TASKS_PER_CHILD" "$WORKER_MAX_TASKS_PER_CHILD")
    
    # Update queue-specific concurrency if provided
    if [[ -n "$QUEUE_NAME" ]]; then
        log_message "Configuring worker for specific queue: $QUEUE_NAME" "DEBUG"
        task_def=$(update_env_var "$task_def" "$container_name" "CELERY_WORKER_QUEUE" "$QUEUE_NAME")
    fi
    
    # Save the updated task definition to a new temporary file
    local updated_task_def_file=$(mktemp /tmp/updated-task-def-XXXXXX.json)
    echo "$task_def" > "$updated_task_def_file"
    
    # Remove fields that cannot be specified in the RegisterTaskDefinition API call
    local cleaned_task_def=$(cat "$updated_task_def_file" | jq 'del(.taskDefinitionArn, .revision, .status, .requiresAttributes, .compatibilities, .registeredAt, .registeredBy)')
    echo "$cleaned_task_def" > "$updated_task_def_file"
    
    log_message "Registering new task definition..." "INFO"
    
    # Register the new task definition
    local new_task_def_arn=$(aws ecs register-task-definition \
        --cli-input-json "file://$updated_task_def_file" \
        --region "$AWS_REGION" \
        --query "taskDefinition.taskDefinitionArn" \
        --output text)
    
    if [[ -z "$new_task_def_arn" || "$new_task_def_arn" == "None" ]]; then
        log_message "Failed to register new task definition" "ERROR"
        rm -f "$updated_task_def_file"
        return 1
    fi
    
    log_message "New task definition registered: $new_task_def_arn" "INFO"
    rm -f "$updated_task_def_file"
    
    echo "$new_task_def_arn"
    return 0
}

# Deploy the updated task definition to the worker service
deploy_service() {
    local task_definition_arn="$1"
    
    log_message "Deploying new task definition to service $ECS_SERVICE..." "INFO"
    
    # Update the ECS service with the new task definition
    local deployment_result=$(aws ecs update-service \
        --cluster "$ECS_CLUSTER" \
        --service "$ECS_SERVICE" \
        --task-definition "$task_definition_arn" \
        --force-new-deployment \
        --deployment-configuration "maximumPercent=200,minimumHealthyPercent=100,deploymentCircuitBreaker={enable=true,rollback=true}" \
        --region "$AWS_REGION" \
        --query "service.deployments" \
        --output json)
    
    if [[ $? -ne 0 ]]; then
        log_message "Failed to update service with new task definition" "ERROR"
        return 1
    fi
    
    # Extract the deployment ID
    local deployment_id=$(echo "$deployment_result" | jq -r '.[0].id')
    
    if [[ -z "$deployment_id" || "$deployment_id" == "null" ]]; then
        log_message "Failed to get deployment ID" "ERROR"
        return 1
    fi
    
    log_message "Deployment initiated with ID: $deployment_id" "INFO"
    echo "$deployment_id"
    return 0
}

# Wait for the deployment to complete successfully
wait_for_deployment() {
    local deployment_id="$1"
    
    log_message "Waiting for deployment to complete (timeout: ${DEPLOYMENT_TIMEOUT}s)..." "INFO"
    
    local timeout_seconds=$DEPLOYMENT_TIMEOUT
    local start_time=$(date +%s)
    local end_time=$((start_time + timeout_seconds))
    local deployment_complete=false
    
    while [[ $(date +%s) -lt $end_time ]]; do
        local deployment_status=$(aws ecs describe-services \
            --cluster "$ECS_CLUSTER" \
            --services "$ECS_SERVICE" \
            --region "$AWS_REGION" \
            --query "services[0].deployments[?id=='$deployment_id'].status" \
            --output text)
        
        local primary_deployment_id=$(aws ecs describe-services \
            --cluster "$ECS_CLUSTER" \
            --services "$ECS_SERVICE" \
            --region "$AWS_REGION" \
            --query "services[0].deployments[0].id" \
            --output text)
        
        log_message "Current deployment status: $deployment_status" "DEBUG"
        
        if [[ "$deployment_status" == "PRIMARY" && "$primary_deployment_id" == "$deployment_id" ]]; then
            # Check if the desired count matches the running count
            local desired_count=$(aws ecs describe-services \
                --cluster "$ECS_CLUSTER" \
                --services "$ECS_SERVICE" \
                --region "$AWS_REGION" \
                --query "services[0].desiredCount" \
                --output text)
            
            local running_count=$(aws ecs describe-services \
                --cluster "$ECS_CLUSTER" \
                --services "$ECS_SERVICE" \
                --region "$AWS_REGION" \
                --query "services[0].runningCount" \
                --output text)
            
            log_message "Desired count: $desired_count, Running count: $running_count" "DEBUG"
            
            if [[ "$desired_count" == "$running_count" && "$running_count" -gt 0 ]]; then
                log_message "Deployment completed successfully" "INFO"
                deployment_complete=true
                break
            fi
        elif [[ -z "$deployment_status" || "$deployment_status" == "None" ]]; then
            # Check if the deployment was rolled back by the circuit breaker
            log_message "Deployment not found, checking if it was rolled back..." "INFO"
            
            local events=$(aws ecs describe-services \
                --cluster "$ECS_CLUSTER" \
                --services "$ECS_SERVICE" \
                --region "$AWS_REGION" \
                --query "services[0].events[?contains(message, 'circuit breaker')]" \
                --output text)
            
            if [[ -n "$events" ]]; then
                log_message "Deployment was rolled back by the circuit breaker" "ERROR"
                return 1
            fi
        fi
        
        sleep 10
    done
    
    if [[ "$deployment_complete" != "true" ]]; then
        log_message "Timeout waiting for deployment to complete" "ERROR"
        return 1
    fi
    
    return 0
}

# Verify the health of the deployed worker service
verify_worker_health() {
    log_message "Verifying worker service health..." "INFO"
    
    # Get the worker task ARNs
    local task_arns=$(aws ecs list-tasks \
        --cluster "$ECS_CLUSTER" \
        --service-name "$ECS_SERVICE" \
        --region "$AWS_REGION" \
        --query "taskArns" \
        --output text)
    
    if [[ -z "$task_arns" || "$task_arns" == "None" ]]; then
        log_message "No running worker tasks found" "ERROR"
        return 1
    fi
    
    log_message "Found running worker tasks: $task_arns" "DEBUG"
    
    # Check if there are any tasks running
    local task_count=$(echo "$task_arns" | wc -w)
    if [[ "$task_count" -lt "$MIN_WORKER_COUNT" ]]; then
        log_message "Insufficient worker tasks running. Found $task_count, expected at least $MIN_WORKER_COUNT" "ERROR"
        return 1
    fi
    
    # Use the health_check.sh script to verify worker health
    for ((i=1; i<=$HEALTH_CHECK_RETRIES; i++)); do
        log_message "Health check attempt $i of $HEALTH_CHECK_RETRIES" "DEBUG"
        
        if check_service_health "worker" "$ENVIRONMENT"; then
            log_message "Worker service is healthy" "INFO"
            return 0
        fi
        
        if [[ $i -lt $HEALTH_CHECK_RETRIES ]]; then
            log_message "Worker not yet healthy, waiting $HEALTH_CHECK_INTERVAL seconds before retry" "INFO"
            sleep $HEALTH_CHECK_INTERVAL
        fi
    done
    
    log_message "Worker service is unhealthy after $HEALTH_CHECK_RETRIES attempts" "ERROR"
    return 1
}

# Configure auto-scaling for the worker service based on queue depth
configure_autoscaling() {
    log_message "Configuring auto-scaling for worker service..." "INFO"
    
    # Register the ECS service as a scalable target
    aws application-autoscaling register-scalable-target \
        --service-namespace ecs \
        --resource-id service/${ECS_CLUSTER}/${ECS_SERVICE} \
        --scalable-dimension ecs:service:DesiredCount \
        --min-capacity "$MIN_WORKER_COUNT" \
        --max-capacity "$MAX_WORKER_COUNT" \
        --region "$AWS_REGION"
    
    if [[ $? -ne 0 ]]; then
        log_message "Failed to register scalable target" "ERROR"
        return 1
    fi
    
    # Define scaling policy based on SQS queue depth
    local policy_json='{
        "policyName": "'${ECS_SERVICE}'-scale-policy",
        "policyType": "TargetTrackingScaling",
        "resourceId": "service/'${ECS_CLUSTER}'/'${ECS_SERVICE}'",
        "scalableDimension": "ecs:service:DesiredCount",
        "serviceNamespace": "ecs",
        "targetTrackingScalingPolicyConfiguration": {
            "targetValue": 10.0,
            "scaleInCooldown": 300,
            "scaleOutCooldown": 60,
            "predefinedMetricSpecification": {
                "predefinedMetricType": "SQSQueueMessagesVisiblePerTask",
                "resourceLabel": "'${ECS_SERVICE}'-queue"
            }
        }
    }'
    
    # Save policy to a temporary file
    local policy_file=$(mktemp /tmp/scaling-policy-XXXXXX.json)
    echo "$policy_json" > "$policy_file"
    
    # Apply the scaling policy
    aws application-autoscaling put-scaling-policy \
        --cli-input-json "file://$policy_file" \
        --region "$AWS_REGION"
    
    local scaling_result=$?
    rm -f "$policy_file"
    
    if [[ $scaling_result -ne 0 ]]; then
        log_message "Failed to apply scaling policy" "ERROR"
        return 1
    fi
    
    log_message "Auto-scaling configured successfully" "INFO"
    return 0
}

# Handle deployment failure by initiating rollback
handle_deployment_failure() {
    local previous_task_definition_arn="$1"
    
    log_message "Handling deployment failure..." "ERROR"
    log_message "Rolling back to previous task definition: $previous_task_definition_arn" "INFO"
    
    # Call rollback script function
    if rollback_deployment "$ECS_SERVICE" "rolling" "$previous_task_definition_arn"; then
        log_message "Rollback completed successfully" "INFO"
        return 0
    else
        log_message "Rollback failed" "ERROR"
        return 1
    fi
}

# Clean up temporary files and resources
cleanup() {
    log_message "Cleaning up temporary resources..." "DEBUG"
    
    # Remove any temporary files
    rm -f /tmp/task-def-*.json
    rm -f /tmp/updated-task-def-*.json
    rm -f /tmp/scaling-policy-*.json
    
    log_message "Cleanup completed" "DEBUG"
}

# Main deployment function that can be called from other scripts
deploy_workers() {
    # Pass all arguments to the main function
    main "$@"
    return $?
}

# Main function that orchestrates the worker deployment process
main() {
    local VERBOSE=false
    local QUEUE_NAME=""
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --environment)
                ENVIRONMENT="$2"
                shift 2
                ;;
            --image-tag)
                IMAGE_TAG="$2"
                shift 2
                ;;
            --min-workers)
                MIN_WORKER_COUNT="$2"
                shift 2
                ;;
            --max-workers)
                MAX_WORKER_COUNT="$2"
                shift 2
                ;;
            --concurrency)
                WORKER_CONCURRENCY="$2"
                shift 2
                ;;
            --queue)
                QUEUE_NAME="$2"
                shift 2
                ;;
            --verbose)
                VERBOSE=true
                shift
                ;;
            *)
                log_message "Unknown option: $1" "ERROR"
                echo "Usage: $0 [--environment <env>] [--image-tag <tag>] [--min-workers <count>] [--max-workers <count>] [--concurrency <num>] [--queue <queue_name>] [--verbose]"
                return 4
                ;;
        esac
    done
    
    # Update derived environment variables that depend on the environment
    ECS_CLUSTER="molecule-flow-${ENVIRONMENT}"
    
    log_message "Starting worker deployment with image tag $IMAGE_TAG in $ENVIRONMENT environment" "INFO"
    log_message "Worker configuration: concurrency=$WORKER_CONCURRENCY, min=$MIN_WORKER_COUNT, max=$MAX_WORKER_COUNT" "INFO"
    
    # Check prerequisites
    if ! check_prerequisites; then
        log_message "Prerequisites check failed" "ERROR"
        return 1
    fi
    
    # Get current task definition
    local task_definition_file=$(get_current_task_definition)
    if [[ $? -ne 0 || -z "$task_definition_file" ]]; then
        log_message "Failed to get current task definition" "ERROR"
        return 2
    fi
    
    # If AWS_ACCOUNT_ID is not set, try to get it
    if [[ -z "$AWS_ACCOUNT_ID" ]]; then
        AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query "Account" --output text)
        if [[ $? -ne 0 ]]; then
            log_message "Failed to get AWS account ID" "ERROR"
            return 1
        fi
        log_message "AWS account ID: $AWS_ACCOUNT_ID" "DEBUG"
    fi
    
    # Construct ECR image URI
    local image_uri="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}:${IMAGE_TAG}"
    log_message "Using image URI: $image_uri" "INFO"
    
    # Update task definition
    local new_task_definition_arn=$(update_task_definition "$task_definition_file" "$image_uri")
    if [[ $? -ne 0 || -z "$new_task_definition_arn" ]]; then
        log_message "Failed to update task definition" "ERROR"
        cleanup
        return 2
    fi
    
    # Deploy service
    local deployment_id=$(deploy_service "$new_task_definition_arn")
    if [[ $? -ne 0 || -z "$deployment_id" ]]; then
        log_message "Failed to deploy service" "ERROR"
        handle_deployment_failure "$(aws ecs describe-services --cluster \"$ECS_CLUSTER\" --services \"$ECS_SERVICE\" --region \"$AWS_REGION\" --query \"services[0].taskDefinition\" --output text)"
        cleanup
        return 2
    fi
    
    # Wait for deployment to complete
    if ! wait_for_deployment "$deployment_id"; then
        log_message "Deployment failed or timed out" "ERROR"
        handle_deployment_failure "$(aws ecs describe-services --cluster \"$ECS_CLUSTER\" --services \"$ECS_SERVICE\" --region \"$AWS_REGION\" --query \"services[0].taskDefinition\" --output text)"
        cleanup
        return 2
    fi
    
    # Verify worker health
    if ! verify_worker_health; then
        log_message "Worker health verification failed" "ERROR"
        handle_deployment_failure "$new_task_definition_arn"
        cleanup
        return 3
    fi
    
    # Configure auto-scaling
    if ! configure_autoscaling; then
        log_message "Auto-scaling configuration failed" "WARNING"
        # Don't fail the deployment for auto-scaling configuration failure
    fi
    
    # Cleanup
    cleanup
    
    log_message "Worker deployment completed successfully" "INFO"
    return 0
}

# Run main function if script is executed directly (not sourced)
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
    exit $?
fi

# Export the deploy_workers function for use in CI/CD pipelines
export -f deploy_workers