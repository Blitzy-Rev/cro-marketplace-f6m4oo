#!/bin/bash
#
# Backend Deployment Script for Molecular Data Management and CRO Integration Platform
#
# This script automates the deployment of the FastAPI backend service to AWS ECS,
# handling task definition updates, service deployment, and health verification.
# It supports both rolling updates and blue/green deployments through AWS CodeDeploy.
#
# Dependencies:
# - aws-cli (2.x): AWS command line interface for ECS deployment operations
# - jq (1.6+): JSON processor for parsing AWS CLI outputs
# - aws-sdk-codedeploy (2.x): AWS SDK for CodeDeploy integration
#
# Usage:
#   ./deploy_backend.sh [options]
#
# Options:
#   --environment <env>      Deployment environment (dev, staging, prod) (default: ${ENVIRONMENT})
#   --image-tag <tag>        Container image tag to deploy (default: ${IMAGE_TAG})
#   --deployment-type <type> Deployment strategy (rolling, blue-green) (default: ${DEPLOYMENT_TYPE})
#   --timeout <seconds>      Deployment timeout in seconds (default: ${DEPLOYMENT_TIMEOUT})
#   --verbose                Enable verbose output
#   --help                   Display this help message
#
# Examples:
#   ./deploy_backend.sh --environment staging --image-tag v1.2.3
#   ./deploy_backend.sh --deployment-type rolling
#

# Source required scripts
if [[ -f "./health_check.sh" ]]; then
    source ./health_check.sh
else
    echo "ERROR: health_check.sh not found. Make sure it's in the same directory."
    exit 1
fi

if [[ -f "./rollback.sh" ]]; then
    source ./rollback.sh
else
    echo "ERROR: rollback.sh not found. Make sure it's in the same directory."
    exit 1
fi

# Global variables with defaults from environment variables
AWS_REGION="${AWS_REGION:-us-east-1}"
ECR_REPOSITORY="${ECR_REPOSITORY:-molecule-flow/backend}"
ECS_CLUSTER="${ECS_CLUSTER:-molecule-flow-${ENVIRONMENT}}"
ECS_SERVICE="${ECS_SERVICE:-moleculeflow-backend}"
TASK_FAMILY="${TASK_FAMILY:-moleculeflow-backend}"
ENVIRONMENT="${ENVIRONMENT:-dev}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
DEPLOYMENT_TIMEOUT="${DEPLOYMENT_TIMEOUT:-900}"
HEALTH_CHECK_RETRIES="${HEALTH_CHECK_RETRIES:-5}"
HEALTH_CHECK_INTERVAL="${HEALTH_CHECK_INTERVAL:-30}"
DEPLOYMENT_TYPE="${DEPLOYMENT_TYPE:-blue-green}"
VERBOSE="${VERBOSE:-false}"

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

# Check if all prerequisites are met
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
    
    # Check for required environment variables
    if [[ -z "$AWS_REGION" ]]; then
        log_message "AWS_REGION environment variable is not set." "ERROR"
        missing_tools=true
    fi
    
    if [[ -z "$ECR_REPOSITORY" ]]; then
        log_message "ECR_REPOSITORY environment variable is not set." "ERROR"
        missing_tools=true
    fi
    
    if [[ -z "$ECS_CLUSTER" ]]; then
        log_message "ECS_CLUSTER environment variable is not set." "ERROR"
        missing_tools=true
    fi
    
    if [[ -z "$ECS_SERVICE" ]]; then
        log_message "ECS_SERVICE environment variable is not set." "ERROR"
        missing_tools=true
    fi
    
    if [[ -z "$TASK_FAMILY" ]]; then
        log_message "TASK_FAMILY environment variable is not set." "ERROR"
        missing_tools=true
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        log_message "AWS credentials not configured or insufficient permissions." "ERROR"
        missing_tools=true
    fi
    
    # Verify ECR repository exists
    if ! aws ecr describe-repositories --repository-names "$ECR_REPOSITORY" --region "$AWS_REGION" &> /dev/null; then
        log_message "ECR repository $ECR_REPOSITORY does not exist in region $AWS_REGION." "ERROR"
        missing_tools=true
    fi
    
    if [[ "$missing_tools" == "true" ]]; then
        return 1
    fi
    
    log_message "All prerequisites are met." "DEBUG"
    return 0
}

# Get the current task definition for the service
get_current_task_definition() {
    log_message "Getting current task definition for service $ECS_SERVICE" "DEBUG"
    
    # Get the current task definition ARN from the service
    local task_def_arn=$(aws ecs describe-services \
        --cluster "$ECS_CLUSTER" \
        --services "$ECS_SERVICE" \
        --region "$AWS_REGION" \
        --query "services[0].taskDefinition" \
        --output text)
    
    if [[ -z "$task_def_arn" || "$task_def_arn" == "None" ]]; then
        log_message "Failed to get current task definition ARN for service $ECS_SERVICE" "ERROR"
        return 1
    fi
    
    log_message "Current task definition ARN: $task_def_arn" "DEBUG"
    
    # Retrieve the task definition
    local task_def_file=$(mktemp)
    aws ecs describe-task-definition \
        --task-definition "$task_def_arn" \
        --region "$AWS_REGION" \
        --query "taskDefinition" > "$task_def_file"
    
    if [[ $? -ne 0 ]]; then
        log_message "Failed to retrieve task definition details" "ERROR"
        rm -f "$task_def_file"
        return 1
    fi
    
    log_message "Task definition saved to $task_def_file" "DEBUG"
    echo "$task_def_file"
    return 0
}

# Update the task definition with the new container image
update_task_definition() {
    local task_definition_file="$1"
    local image_uri="$2"
    
    log_message "Updating task definition with image: $image_uri" "DEBUG"
    
    # Create a new task definition file with the updated image
    local new_task_def_file=$(mktemp)
    
    # Extract container definitions from the task definition
    local container_definitions=$(jq '.containerDefinitions' "$task_definition_file")
    
    # Update the image in the container definitions
    local updated_container_definitions=$(echo "$container_definitions" | jq --arg IMAGE "$image_uri" '
        map(if .name == env.ECS_SERVICE then .image = $IMAGE else . end)
    ')
    
    # Update environment variables if provided
    if [[ -n "$CONTAINER_ENV_VARS" ]]; then
        log_message "Updating container environment variables" "DEBUG"
        # Parse environment variables JSON
        local env_vars=$(echo "$CONTAINER_ENV_VARS" | jq '.')
        updated_container_definitions=$(echo "$updated_container_definitions" | jq --argjson ENV "$env_vars" '
            map(if .name == env.ECS_SERVICE then .environment = $ENV else . end)
        ')
    fi
    
    # Create a new task definition
    jq --argjson CD "$updated_container_definitions" '
        .containerDefinitions = $CD |
        del(.status) |
        del(.taskDefinitionArn) |
        del(.revision) |
        del(.compatibilities) |
        del(.requiresAttributes) |
        del(.registeredAt) |
        del(.registeredBy)
    ' "$task_definition_file" > "$new_task_def_file"
    
    # Register the new task definition
    local new_task_def_arn=$(aws ecs register-task-definition \
        --cli-input-json "file://$new_task_def_file" \
        --region "$AWS_REGION" \
        --query "taskDefinition.taskDefinitionArn" \
        --output text)
    
    if [[ -z "$new_task_def_arn" || "$new_task_def_arn" == "None" ]]; then
        log_message "Failed to register new task definition" "ERROR"
        rm -f "$new_task_def_file"
        return 1
    fi
    
    log_message "New task definition registered: $new_task_def_arn" "INFO"
    
    # Clean up temporary files
    rm -f "$new_task_def_file"
    
    echo "$new_task_def_arn"
    return 0
}

# Deploy using a rolling update strategy
deploy_rolling_update() {
    local task_definition_arn="$1"
    
    log_message "Deploying task definition $task_definition_arn using rolling update strategy" "INFO"
    
    # Update the service with the new task definition
    local deployment_info=$(aws ecs update-service \
        --cluster "$ECS_CLUSTER" \
        --service "$ECS_SERVICE" \
        --task-definition "$task_definition_arn" \
        --deployment-configuration "minimumHealthyPercent=100,maximumPercent=200,deploymentCircuitBreaker={enable=true,rollback=true}" \
        --force-new-deployment \
        --region "$AWS_REGION" \
        --query "service.deployments" \
        --output json)
    
    if [[ $? -ne 0 || -z "$deployment_info" ]]; then
        log_message "Failed to update service with new task definition" "ERROR"
        return 1
    fi
    
    # Extract the deployment ID
    local deployment_id=$(echo "$deployment_info" | jq -r '.[0].id')
    
    log_message "Deployment initiated with ID: $deployment_id" "INFO"
    
    echo "$deployment_id"
    return 0
}

# Deploy using a blue/green deployment strategy with AWS CodeDeploy
deploy_blue_green() {
    local task_definition_arn="$1"
    
    log_message "Deploying task definition $task_definition_arn using blue/green deployment strategy" "INFO"
    
    # First, check if the service is configured for blue/green deployments
    local deployment_controller=$(aws ecs describe-services \
        --cluster "$ECS_CLUSTER" \
        --services "$ECS_SERVICE" \
        --region "$AWS_REGION" \
        --query "services[0].deploymentController.type" \
        --output text)
    
    if [[ "$deployment_controller" != "CODE_DEPLOY" ]]; then
        log_message "Service $ECS_SERVICE is not configured for blue/green deployments (current type: $deployment_controller)" "ERROR"
        log_message "Falling back to rolling update deployment" "INFO"
        return $(deploy_rolling_update "$task_definition_arn")
    fi
    
    # Get the CodeDeploy app and deployment group
    local app_name="${ECS_CLUSTER}-${ECS_SERVICE}"
    local deployment_group="${ECS_CLUSTER}-${ECS_SERVICE}"
    
    # Check if the CodeDeploy app exists
    if ! aws deploy get-application --application-name "$app_name" --region "$AWS_REGION" &> /dev/null; then
        log_message "CodeDeploy application $app_name not found" "ERROR"
        return 1
    fi
    
    # Check if the deployment group exists
    if ! aws deploy get-deployment-group \
        --application-name "$app_name" \
        --deployment-group-name "$deployment_group" \
        --region "$AWS_REGION" &> /dev/null; then
        log_message "CodeDeploy deployment group $deployment_group not found" "ERROR"
        return 1
    fi
    
    # Create the AppSpec file for the deployment
    local appspec_file=$(mktemp)
    local container_name="$ECS_SERVICE"
    local container_port=8000  # Default port for the backend service
    
    # Create the AppSpec content
    cat > "$appspec_file" << EOF
{
  "version": 0.0,
  "Resources": [
    {
      "TargetService": {
        "Type": "AWS::ECS::Service",
        "Properties": {
          "TaskDefinition": "$task_definition_arn",
          "LoadBalancerInfo": {
            "ContainerName": "$container_name",
            "ContainerPort": $container_port
          }
        }
      }
    }
  ]
}
EOF
    
    # Create the deployment
    local deployment_id=$(aws deploy create-deployment \
        --application-name "$app_name" \
        --deployment-group-name "$deployment_group" \
        --revision "{\"revisionType\": \"String\", \"string\": {\"content\": $(cat "$appspec_file" | jq -R -s .)}}" \
        --description "Automated deployment of $ECS_SERVICE with task definition $task_definition_arn" \
        --region "$AWS_REGION" \
        --query "deploymentId" \
        --output text)
    
    if [[ -z "$deployment_id" || "$deployment_id" == "None" ]]; then
        log_message "Failed to create CodeDeploy deployment" "ERROR"
        rm -f "$appspec_file"
        return 1
    fi
    
    log_message "CodeDeploy deployment initiated with ID: $deployment_id" "INFO"
    
    # Clean up temporary files
    rm -f "$appspec_file"
    
    echo "$deployment_id"
    return 0
}

# Wait for the deployment to complete
wait_for_deployment() {
    local deployment_id="$1"
    local deployment_type="$2"
    
    log_message "Waiting for deployment $deployment_id to complete (type: $deployment_type)" "INFO"
    
    local timeout_seconds=$DEPLOYMENT_TIMEOUT
    local start_time=$(date +%s)
    local end_time=$((start_time + timeout_seconds))
    local deployment_complete=false
    
    while [[ $(date +%s) -lt $end_time ]]; do
        local status=""
        
        case "$deployment_type" in
            "rolling")
                # For rolling deployments, check the ECS service status
                local deployment_status=$(aws ecs describe-services \
                    --cluster "$ECS_CLUSTER" \
                    --services "$ECS_SERVICE" \
                    --region "$AWS_REGION" \
                    --query "services[0].deployments" \
                    --output json)
                
                # Check if the deployment exists in the list
                local deployment=$(echo "$deployment_status" | jq --arg ID "$deployment_id" '.[] | select(.id == $ID)')
                
                if [[ -z "$deployment" ]]; then
                    # Deployment no longer exists in list, check if primary deployment is healthy
                    local primary_deployment=$(echo "$deployment_status" | jq '.[0]')
                    local primary_status=$(echo "$primary_deployment" | jq -r '.status')
                    
                    if [[ "$primary_status" == "PRIMARY" ]]; then
                        local running_count=$(echo "$primary_deployment" | jq -r '.runningCount')
                        local desired_count=$(echo "$primary_deployment" | jq -r '.desiredCount')
                        
                        if [[ "$running_count" -eq "$desired_count" ]]; then
                            log_message "Deployment completed: $running_count/$desired_count tasks running" "INFO"
                            deployment_complete=true
                            break
                        fi
                    fi
                else
                    local status=$(echo "$deployment" | jq -r '.status')
                    local running_count=$(echo "$deployment" | jq -r '.runningCount')
                    local desired_count=$(echo "$deployment" | jq -r '.desiredCount')
                    
                    log_message "Deployment status: $status, $running_count/$desired_count tasks running" "DEBUG"
                    
                    if [[ "$status" == "PRIMARY" && "$running_count" -eq "$desired_count" ]]; then
                        log_message "Deployment completed: $running_count/$desired_count tasks running" "INFO"
                        deployment_complete=true
                        break
                    fi
                fi
                ;;
                
            "blue-green")
                # For blue/green deployments, check the CodeDeploy deployment status
                local deployment_status=$(aws deploy get-deployment \
                    --deployment-id "$deployment_id" \
                    --region "$AWS_REGION" \
                    --query "deploymentInfo.status" \
                    --output text)
                
                log_message "CodeDeploy deployment status: $deployment_status" "DEBUG"
                
                if [[ "$deployment_status" == "SUCCEEDED" ]]; then
                    log_message "Deployment completed successfully" "INFO"
                    deployment_complete=true
                    break
                elif [[ "$deployment_status" == "FAILED" || "$deployment_status" == "STOPPED" ]]; then
                    log_message "Deployment failed or was stopped: $deployment_status" "ERROR"
                    return 1
                fi
                ;;
                
            *)
                log_message "Unknown deployment type: $deployment_type" "ERROR"
                return 1
                ;;
        esac
        
        # Sleep before checking again
        sleep 10
    done
    
    if [[ "$deployment_complete" != "true" ]]; then
        log_message "Deployment timed out after $timeout_seconds seconds" "ERROR"
        return 1
    fi
    
    return 0
}

# Verify the deployment by checking service health
verify_deployment() {
    log_message "Verifying deployment of service $ECS_SERVICE" "INFO"
    
    # Get service endpoint for health check
    local service_endpoint=""
    
    # For ECS services, we need to get the load balancer target
    local load_balancer_info=$(aws ecs describe-services \
        --cluster "$ECS_CLUSTER" \
        --services "$ECS_SERVICE" \
        --region "$AWS_REGION" \
        --query "services[0].loadBalancers" \
        --output json)
    
    if [[ -n "$load_balancer_info" && "$load_balancer_info" != "[]" ]]; then
        local target_group_arn=$(echo "$load_balancer_info" | jq -r '.[0].targetGroupArn // ""')
        
        if [[ -n "$target_group_arn" && "$target_group_arn" != "null" ]]; then
            # Get the load balancer from the target group
            local load_balancer_arn=$(aws elbv2 describe-target-groups \
                --target-group-arns "$target_group_arn" \
                --region "$AWS_REGION" \
                --query "TargetGroups[0].LoadBalancerArns[0]" \
                --output text)
            
            if [[ -n "$load_balancer_arn" && "$load_balancer_arn" != "None" ]]; then
                local load_balancer_dns=$(aws elbv2 describe-load-balancers \
                    --load-balancer-arns "$load_balancer_arn" \
                    --region "$AWS_REGION" \
                    --query "LoadBalancers[0].DNSName" \
                    --output text)
                
                if [[ -n "$load_balancer_dns" && "$load_balancer_dns" != "None" ]]; then
                    service_endpoint="http://$load_balancer_dns"
                fi
            fi
        fi
    fi
    
    if [[ -z "$service_endpoint" ]]; then
        log_message "Could not determine service endpoint for health check" "ERROR"
        return 1
    fi
    
    log_message "Using service endpoint: $service_endpoint" "DEBUG"
    
    # Try to call health_check.sh to verify backend API health
    log_message "Verifying API health..." "INFO"
    
    # Use check_api_health from health_check.sh
    local retry_count=0
    local max_retries=$HEALTH_CHECK_RETRIES
    local is_healthy=false
    
    while [[ $retry_count -lt $max_retries ]]; do
        if check_api_health "$ENVIRONMENT"; then
            is_healthy=true
            break
        fi
        
        retry_count=$((retry_count + 1))
        
        if [[ $retry_count -lt $max_retries ]]; then
            log_message "Health check failed, retrying in $HEALTH_CHECK_INTERVAL seconds (attempt $retry_count of $max_retries)" "INFO"
            sleep $HEALTH_CHECK_INTERVAL
        fi
    done
    
    if [[ "$is_healthy" == "true" ]]; then
        log_message "Service $ECS_SERVICE is healthy" "INFO"
        return 0
    else
        log_message "Service $ECS_SERVICE is unhealthy after $max_retries attempts" "ERROR"
        return 1
    fi
}

# Handle deployment failure by initiating rollback
handle_deployment_failure() {
    local previous_task_definition_arn="$1"
    local deployment_type="$2"
    
    log_message "Handling deployment failure for service $ECS_SERVICE" "ERROR"
    log_message "Rolling back to previous task definition: $previous_task_definition_arn" "INFO"
    
    # Call rollback.sh to revert to previous task definition
    if rollback_deployment "$ECS_SERVICE" "$deployment_type" ""; then
        log_message "Rollback completed successfully" "INFO"
        # Even if the rollback was successful, we should still indicate a deployment failure
        return 1
    else
        log_message "Rollback failed" "ERROR"
        return 2
    fi
}

# Clean up temporary files and resources
cleanup() {
    log_message "Cleaning up temporary resources" "DEBUG"
    
    # Remove any temporary files created
    if [[ -n "$1" && -f "$1" ]]; then
        rm -f "$1"
        log_message "Removed temporary file: $1" "DEBUG"
    fi
    
    # Add any other cleanup tasks as needed
    
    log_message "Cleanup completed" "DEBUG"
}

# Update service discovery entries if applicable
update_service_discovery() {
    log_message "Checking for service discovery configuration" "DEBUG"
    
    # Check if service discovery is enabled for the service
    local service_discovery_info=$(aws ecs describe-services \
        --cluster "$ECS_CLUSTER" \
        --services "$ECS_SERVICE" \
        --region "$AWS_REGION" \
        --query "services[0].serviceRegistries" \
        --output json)
    
    if [[ -z "$service_discovery_info" || "$service_discovery_info" == "[]" ]]; then
        log_message "Service discovery is not enabled for this service" "DEBUG"
        return 0
    fi
    
    log_message "Service discovery is enabled, checking status" "INFO"
    
    # Extract the service registry ARN
    local registry_arn=$(echo "$service_discovery_info" | jq -r '.[0].registryArn // ""')
    
    if [[ -z "$registry_arn" || "$registry_arn" == "null" ]]; then
        log_message "Could not find service registry ARN" "ERROR"
        return 1
    fi
    
    # Extract the service registry ID
    local registry_id=$(echo "$registry_arn" | rev | cut -d'/' -f1 | rev)
    
    # Check the health status of the service discovery instance
    local instance_health=$(aws servicediscovery get-instance-health \
        --service-id "$registry_id" \
        --region "$AWS_REGION" \
        --query "Status" \
        --output text)
    
    log_message "Service discovery instance health: $instance_health" "INFO"
    
    if [[ "$instance_health" != "HEALTHY" ]]; then
        log_message "Service discovery instance is not healthy" "ERROR"
        return 1
    fi
    
    log_message "Service discovery is healthy" "INFO"
    return 0
}

# Main function to orchestrate the deployment process
main() {
    local task_def_file=""
    local previous_task_def_arn=""
    local new_task_def_arn=""
    local deployment_id=""
    local exit_code=0
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --environment)
                ENVIRONMENT="$2"
                ECS_CLUSTER="molecule-flow-${ENVIRONMENT}"
                shift 2
                ;;
            --image-tag)
                IMAGE_TAG="$2"
                shift 2
                ;;
            --deployment-type)
                DEPLOYMENT_TYPE="$2"
                shift 2
                ;;
            --timeout)
                DEPLOYMENT_TIMEOUT="$2"
                shift 2
                ;;
            --verbose)
                VERBOSE=true
                shift
                ;;
            --help)
                echo "Usage: $0 [options]"
                echo
                echo "Options:"
                echo "  --environment <env>      Deployment environment (dev, staging, prod) (default: ${ENVIRONMENT})"
                echo "  --image-tag <tag>        Container image tag to deploy (default: ${IMAGE_TAG})"
                echo "  --deployment-type <type> Deployment strategy (rolling, blue-green) (default: ${DEPLOYMENT_TYPE})"
                echo "  --timeout <seconds>      Deployment timeout in seconds (default: ${DEPLOYMENT_TIMEOUT})"
                echo "  --verbose                Enable verbose output"
                echo "  --help                   Display this help message"
                echo
                echo "Examples:"
                echo "  $0 --environment staging --image-tag v1.2.3"
                echo "  $0 --deployment-type rolling"
                exit 0
                ;;
            *)
                log_message "Unknown option: $1" "ERROR"
                echo "Use --help for usage information."
                exit 1
                ;;
        esac
    done
    
    log_message "Starting deployment of backend service for environment: $ENVIRONMENT" "INFO"
    log_message "Using deployment type: $DEPLOYMENT_TYPE" "INFO"
    
    # Check prerequisites
    if ! check_prerequisites; then
        log_message "Prerequisites check failed" "ERROR"
        exit 1
    fi
    
    # Construct ECR image URI
    local ecr_domain=$(aws ecr describe-repositories \
        --repository-names "$ECR_REPOSITORY" \
        --region "$AWS_REGION" \
        --query "repositories[0].repositoryUri" \
        --output text | sed "s/$ECR_REPOSITORY//")
    
    local image_uri="${ecr_domain}${ECR_REPOSITORY}:${IMAGE_TAG}"
    log_message "Using image URI: $image_uri" "INFO"
    
    # Get current task definition
    task_def_file=$(get_current_task_definition)
    if [[ $? -ne 0 || -z "$task_def_file" ]]; then
        log_message "Failed to get current task definition" "ERROR"
        exit 1
    fi
    
    # Store the current task definition ARN for rollback if needed
    previous_task_def_arn=$(jq -r '.taskDefinitionArn' "$task_def_file")
    log_message "Current task definition: $previous_task_def_arn" "INFO"
    
    # Update task definition with new image
    new_task_def_arn=$(update_task_definition "$task_def_file" "$image_uri")
    if [[ $? -ne 0 || -z "$new_task_def_arn" ]]; then
        log_message "Failed to update task definition" "ERROR"
        cleanup "$task_def_file"
        exit 1
    fi
    
    # Deploy based on deployment type
    if [[ "$DEPLOYMENT_TYPE" == "rolling" ]]; then
        deployment_id=$(deploy_rolling_update "$new_task_def_arn")
    elif [[ "$DEPLOYMENT_TYPE" == "blue-green" ]]; then
        deployment_id=$(deploy_blue_green "$new_task_def_arn")
    else
        log_message "Unknown deployment type: $DEPLOYMENT_TYPE" "ERROR"
        cleanup "$task_def_file"
        exit 1
    fi
    
    if [[ $? -ne 0 || -z "$deployment_id" ]]; then
        log_message "Failed to initiate deployment" "ERROR"
        cleanup "$task_def_file"
        exit 1
    fi
    
    # Wait for deployment to complete
    if ! wait_for_deployment "$deployment_id" "$DEPLOYMENT_TYPE"; then
        log_message "Deployment failed or timed out" "ERROR"
        handle_deployment_failure "$previous_task_def_arn" "$DEPLOYMENT_TYPE"
        cleanup "$task_def_file"
        exit 1
    fi
    
    # Verify deployment
    if ! verify_deployment; then
        log_message "Deployment verification failed" "ERROR"
        handle_deployment_failure "$previous_task_def_arn" "$DEPLOYMENT_TYPE"
        cleanup "$task_def_file"
        exit 1
    fi
    
    # Update service discovery if applicable
    if ! update_service_discovery; then
        log_message "Service discovery update check failed" "ERROR"
        # This is not critical enough to trigger a rollback, but worth noting
    fi
    
    log_message "Deployment of backend service completed successfully" "INFO"
    
    # Clean up
    cleanup "$task_def_file"
    
    exit 0
}

# Function exported for use in CI/CD pipelines
deploy_backend() {
    # Call main with all arguments passed through
    main "$@"
    return $?
}

# Run main function if script is executed directly (not sourced)
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
    exit $?
fi

# Export the deploy_backend function for use in other scripts
export -f deploy_backend