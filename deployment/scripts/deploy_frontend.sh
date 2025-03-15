#!/bin/bash
#
# Frontend Deployment Script for Molecular Data Management and CRO Integration Platform
#
# This script automates the deployment of the React frontend service to AWS ECS,
# handling task definition updates, service deployment, and health verification.
#
# Dependencies:
# - aws-cli (2.x): AWS command line interface for ECS deployment operations
# - jq (1.6+): JSON processor for parsing AWS CLI outputs
# - aws-sdk-codedeploy (2.x): AWS SDK for CodeDeploy integration for Blue/Green deployments
# - ./health_check.sh: Script for verifying service health
# - ./rollback.sh: Script for rolling back failed deployments
#
# Usage:
#   ./deploy_frontend.sh [--environment <env>] [--image-tag <tag>] [--deployment-type <type>]
#
# Options:
#   --environment <env>        Deployment environment (dev, staging, prod)
#   --image-tag <tag>          Docker image tag to deploy
#   --deployment-type <type>   Override deployment type (rolling, blue-green, canary)
#
# Exit codes:
#   0 - Deployment successful
#   1 - Prerequisites not met
#   2 - Deployment failed
#   3 - Invalid arguments
#   4 - Service health check failed after deployment
#

# Global variables with defaults from environment variables
AWS_REGION="${AWS_REGION:-us-east-1}"
ECR_REPOSITORY="${ECR_REPOSITORY:-molecule-flow/frontend}"
ECS_CLUSTER="${ECS_CLUSTER:-molecule-flow-${ENVIRONMENT}}"
ECS_SERVICE="${ECS_SERVICE:-moleculeflow-frontend}"
TASK_FAMILY="${TASK_FAMILY:-moleculeflow-frontend}"
ENVIRONMENT="${ENVIRONMENT:-dev}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
DEPLOYMENT_TIMEOUT="${DEPLOYMENT_TIMEOUT:-900}"
HEALTH_CHECK_RETRIES="${HEALTH_CHECK_RETRIES:-5}"
HEALTH_CHECK_INTERVAL="${HEALTH_CHECK_INTERVAL:-30}"
DEPLOYMENT_TYPE="${DEPLOYMENT_TYPE:-rolling}"
CLOUDFRONT_DISTRIBUTION_ID="${CLOUDFRONT_DISTRIBUTION_ID}"

# Source helper scripts
if [[ -f "./health_check.sh" ]]; then
    source ./health_check.sh
else
    echo "ERROR: health_check.sh not found. This script is required for deployment verification."
    exit 1
fi

if [[ -f "./rollback.sh" ]]; then
    source ./rollback.sh
else
    echo "ERROR: rollback.sh not found. This script is required for deployment rollback."
    exit 1
fi

# Verify that all required tools and environment variables are available
check_prerequisites() {
    local missing_prereqs=false

    # Check if AWS CLI is installed
    if ! command -v aws &> /dev/null; then
        echo "ERROR: AWS CLI is not installed. Please install aws-cli 2.x."
        missing_prereqs=true
    fi

    # Check if jq is installed
    if ! command -v jq &> /dev/null; then
        echo "ERROR: jq is not installed. Please install jq 1.6+."
        missing_prereqs=true
    fi

    # Verify required environment variables
    if [[ -z "$ECS_CLUSTER" ]]; then
        echo "ERROR: ECS_CLUSTER environment variable is not set."
        missing_prereqs=true
    fi

    if [[ -z "$ECS_SERVICE" ]]; then
        echo "ERROR: ECS_SERVICE environment variable is not set."
        missing_prereqs=true
    fi

    # Ensure AWS credentials are configured
    if ! aws sts get-caller-identity &> /dev/null; then
        echo "ERROR: AWS credentials are not configured or do not have sufficient permissions."
        missing_prereqs=true
    fi

    # Validate ECR repository exists
    if ! aws ecr describe-repositories --repository-names "$ECR_REPOSITORY" --region "$AWS_REGION" &> /dev/null; then
        echo "ERROR: ECR repository $ECR_REPOSITORY does not exist or is not accessible."
        missing_prereqs=true
    fi

    if [[ "$missing_prereqs" == "true" ]]; then
        return 1
    fi

    echo "All prerequisites met."
    return 0
}

# Retrieves the current task definition for the frontend service
get_current_task_definition() {
    echo "Retrieving current task definition for $ECS_SERVICE..."
    
    # Get the current task definition ARN
    local task_def_arn=$(aws ecs describe-services \
        --cluster "$ECS_CLUSTER" \
        --services "$ECS_SERVICE" \
        --region "$AWS_REGION" \
        --query "services[0].taskDefinition" \
        --output text)
    
    if [[ -z "$task_def_arn" || "$task_def_arn" == "None" ]]; then
        echo "ERROR: Failed to retrieve current task definition ARN for service $ECS_SERVICE."
        return 1
    fi
    
    echo "Current task definition ARN: $task_def_arn"
    
    # Retrieve the task definition
    local task_def=$(aws ecs describe-task-definition \
        --task-definition "$task_def_arn" \
        --region "$AWS_REGION" \
        --query "taskDefinition" \
        --output json)
    
    if [[ -z "$task_def" ]]; then
        echo "ERROR: Failed to retrieve task definition for $task_def_arn."
        return 1
    fi
    
    # Save to a temporary file
    local temp_file="/tmp/task-definition-$$.json"
    echo "$task_def" > "$temp_file"
    
    echo "Task definition saved to $temp_file"
    echo "$temp_file"
}

# Updates the task definition with the new container image
update_task_definition() {
    local task_definition_file="$1"
    local image_uri="$2"
    
    echo "Updating task definition with new image: $image_uri"
    
    # Read the task definition from the file
    local task_def=$(cat "$task_definition_file")
    
    # Update the container image
    local container_name=$(echo "$task_def" | jq -r '.containerDefinitions[0].name')
    local updated_task_def=$(echo "$task_def" | jq --arg IMAGE "$image_uri" --arg NAME "$container_name" \
        '.containerDefinitions |= map(if .name == $NAME then .image = $IMAGE else . end)')
    
    # Remove fields that can't be included in the register-task-definition call
    updated_task_def=$(echo "$updated_task_def" | jq 'del(.taskDefinitionArn, .revision, .status, .registeredAt, .registeredBy, .compatibilities)')
    
    # Write the updated task definition to a new file
    local updated_task_def_file="/tmp/updated-task-definition-$$.json"
    echo "$updated_task_def" > "$updated_task_def_file"
    
    # Register the new task definition
    echo "Registering new task definition..."
    local new_task_def_arn=$(aws ecs register-task-definition \
        --cli-input-json "file://$updated_task_def_file" \
        --region "$AWS_REGION" \
        --query "taskDefinition.taskDefinitionArn" \
        --output text)
    
    if [[ -z "$new_task_def_arn" || "$new_task_def_arn" == "None" ]]; then
        echo "ERROR: Failed to register new task definition."
        return 1
    fi
    
    echo "New task definition registered: $new_task_def_arn"
    
    # Clean up temporary files
    rm -f "$updated_task_def_file"
    
    # Return the new task definition ARN
    echo "$new_task_def_arn"
}

# Deploys the updated task definition using a rolling update strategy
deploy_rolling_update() {
    local task_definition_arn="$1"
    
    echo "Deploying task definition $task_definition_arn with rolling update strategy..."
    
    # Update the service to use the new task definition
    local deployment_id=$(aws ecs update-service \
        --cluster "$ECS_CLUSTER" \
        --service "$ECS_SERVICE" \
        --task-definition "$task_definition_arn" \
        --force-new-deployment \
        --deployment-configuration "maximumPercent=200,minimumHealthyPercent=100,deploymentCircuitBreaker={enable=true,rollback=true}" \
        --region "$AWS_REGION" \
        --query "service.deployments[0].id" \
        --output text)
    
    if [[ -z "$deployment_id" || "$deployment_id" == "None" ]]; then
        echo "ERROR: Failed to initiate rolling update deployment."
        return 1
    fi
    
    echo "Rolling update deployment initiated with ID: $deployment_id"
    
    # Return the deployment ID for tracking
    echo "$deployment_id"
}

# Deploys the updated task definition using a blue/green deployment strategy with AWS CodeDeploy
deploy_blue_green() {
    local task_definition_arn="$1"
    
    echo "Deploying task definition $task_definition_arn with blue/green deployment strategy..."
    
    # First, get the CodeDeploy application and deployment group names
    local codedeploy_app=$(aws ecs describe-services \
        --cluster "$ECS_CLUSTER" \
        --services "$ECS_SERVICE" \
        --region "$AWS_REGION" \
        --query "services[0].deploymentController.codeDeployConfig.applicationName" \
        --output text)
    
    local codedeploy_group=$(aws ecs describe-services \
        --cluster "$ECS_CLUSTER" \
        --services "$ECS_SERVICE" \
        --region "$AWS_REGION" \
        --query "services[0].deploymentController.codeDeployConfig.deploymentGroupName" \
        --output text)
    
    if [[ -z "$codedeploy_app" || "$codedeploy_app" == "None" || 
          -z "$codedeploy_group" || "$codedeploy_group" == "None" ]]; then
        echo "ERROR: Service $ECS_SERVICE is not configured for CodeDeploy blue/green deployments."
        return 1
    fi
    
    # Get container name and port from the task definition
    local container_name=$(aws ecs describe-task-definition \
        --task-definition "$task_definition_arn" \
        --region "$AWS_REGION" \
        --query "taskDefinition.containerDefinitions[0].name" \
        --output text)
    
    local container_port=$(aws ecs describe-task-definition \
        --task-definition "$task_definition_arn" \
        --region "$AWS_REGION" \
        --query "taskDefinition.containerDefinitions[0].portMappings[0].containerPort" \
        --output text)
    
    # Create AppSpec content for blue/green deployment
    local appspec="{
        \"version\": 1,
        \"Resources\": [
            {
                \"TargetService\": {
                    \"Type\": \"AWS::ECS::Service\",
                    \"Properties\": {
                        \"TaskDefinition\": \"$task_definition_arn\",
                        \"LoadBalancerInfo\": {
                            \"ContainerName\": \"$container_name\",
                            \"ContainerPort\": $container_port
                        }
                    }
                }
            }
        ]
    }"
    
    # Create the deployment
    local deployment_id=$(aws deploy create-deployment \
        --application-name "$codedeploy_app" \
        --deployment-group-name "$codedeploy_group" \
        --revision "{\"revisionType\": \"String\", \"string\": {\"content\": \"$appspec\"}}" \
        --deployment-config-name "CodeDeployDefault.ECSAllAtOnce" \
        --description "Blue/Green deployment of task definition $task_definition_arn" \
        --region "$AWS_REGION" \
        --query "deploymentId" \
        --output text)
    
    if [[ -z "$deployment_id" || "$deployment_id" == "None" ]]; then
        echo "ERROR: Failed to initiate blue/green deployment."
        return 1
    fi
    
    echo "Blue/Green deployment initiated with ID: $deployment_id"
    
    # Return the deployment ID for tracking
    echo "$deployment_id"
}

# Deploys the updated task definition using a canary deployment strategy for production
deploy_canary() {
    local task_definition_arn="$1"
    
    echo "Deploying task definition $task_definition_arn with canary deployment strategy..."
    
    # First, get the CodeDeploy application and deployment group names
    local codedeploy_app=$(aws ecs describe-services \
        --cluster "$ECS_CLUSTER" \
        --services "$ECS_SERVICE" \
        --region "$AWS_REGION" \
        --query "services[0].deploymentController.codeDeployConfig.applicationName" \
        --output text)
    
    local codedeploy_group=$(aws ecs describe-services \
        --cluster "$ECS_CLUSTER" \
        --services "$ECS_SERVICE" \
        --region "$AWS_REGION" \
        --query "services[0].deploymentController.codeDeployConfig.deploymentGroupName" \
        --output text)
    
    if [[ -z "$codedeploy_app" || "$codedeploy_app" == "None" || 
          -z "$codedeploy_group" || "$codedeploy_group" == "None" ]]; then
        echo "ERROR: Service $ECS_SERVICE is not configured for CodeDeploy canary deployments."
        return 1
    fi
    
    # Get container name and port from the task definition
    local container_name=$(aws ecs describe-task-definition \
        --task-definition "$task_definition_arn" \
        --region "$AWS_REGION" \
        --query "taskDefinition.containerDefinitions[0].name" \
        --output text)
    
    local container_port=$(aws ecs describe-task-definition \
        --task-definition "$task_definition_arn" \
        --region "$AWS_REGION" \
        --query "taskDefinition.containerDefinitions[0].portMappings[0].containerPort" \
        --output text)
    
    # Create AppSpec content for canary deployment
    local appspec="{
        \"version\": 1,
        \"Resources\": [
            {
                \"TargetService\": {
                    \"Type\": \"AWS::ECS::Service\",
                    \"Properties\": {
                        \"TaskDefinition\": \"$task_definition_arn\",
                        \"LoadBalancerInfo\": {
                            \"ContainerName\": \"$container_name\",
                            \"ContainerPort\": $container_port
                        }
                    }
                }
            }
        ]
    }"
    
    # Create the deployment with canary configuration
    local deployment_id=$(aws deploy create-deployment \
        --application-name "$codedeploy_app" \
        --deployment-group-name "$codedeploy_group" \
        --revision "{\"revisionType\": \"String\", \"string\": {\"content\": \"$appspec\"}}" \
        --deployment-config-name "CodeDeployDefault.ECSCanary10Percent5Minutes" \
        --description "Canary deployment of task definition $task_definition_arn" \
        --region "$AWS_REGION" \
        --query "deploymentId" \
        --output text)
    
    if [[ -z "$deployment_id" || "$deployment_id" == "None" ]]; then
        echo "ERROR: Failed to initiate canary deployment."
        return 1
    fi
    
    echo "Canary deployment initiated with ID: $deployment_id"
    
    # Return the deployment ID for tracking
    echo "$deployment_id"
}

# Waits for the deployment to complete successfully
wait_for_deployment() {
    local deployment_id="$1"
    local deployment_type="$2"
    
    echo "Waiting for deployment $deployment_id to complete (timeout: $DEPLOYMENT_TIMEOUT seconds)..."
    
    local start_time=$(date +%s)
    local end_time=$((start_time + DEPLOYMENT_TIMEOUT))
    local deployment_completed=false
    
    while [[ $(date +%s) -lt $end_time ]]; do
        if [[ "$deployment_type" == "rolling" ]]; then
            # For rolling updates, check ECS deployment status
            local deployment_status=$(aws ecs describe-services \
                --cluster "$ECS_CLUSTER" \
                --services "$ECS_SERVICE" \
                --region "$AWS_REGION" \
                --query "services[0].deployments[?id=='$deployment_id'].status" \
                --output text)
            
            # If the deployment ID is no longer found, it might have completed
            if [[ -z "$deployment_status" || "$deployment_status" == "None" ]]; then
                # Check if the service is stable
                local running_count=$(aws ecs describe-services \
                    --cluster "$ECS_CLUSTER" \
                    --services "$ECS_SERVICE" \
                    --region "$AWS_REGION" \
                    --query "services[0].runningCount" \
                    --output text)
                
                local desired_count=$(aws ecs describe-services \
                    --cluster "$ECS_CLUSTER" \
                    --services "$ECS_SERVICE" \
                    --region "$AWS_REGION" \
                    --query "services[0].desiredCount" \
                    --output text)
                
                if [[ "$running_count" == "$desired_count" && "$running_count" -gt 0 ]]; then
                    deployment_completed=true
                    break
                fi
            elif [[ "$deployment_status" == "PRIMARY" ]]; then
                deployment_completed=true
                break
            fi
        else
            # For blue/green or canary deployments, check CodeDeploy status
            local deployment_status=$(aws deploy get-deployment \
                --deployment-id "$deployment_id" \
                --region "$AWS_REGION" \
                --query "deploymentInfo.status" \
                --output text)
            
            echo "Current deployment status: $deployment_status"
            
            if [[ "$deployment_status" == "SUCCEEDED" ]]; then
                deployment_completed=true
                break
            elif [[ "$deployment_status" == "FAILED" || "$deployment_status" == "STOPPED" ]]; then
                echo "ERROR: Deployment $deployment_id failed or was stopped: $deployment_status"
                return 1
            fi
        fi
        
        echo "Deployment still in progress, waiting 10 seconds..."
        sleep 10
    done
    
    if [[ "$deployment_completed" != "true" ]]; then
        echo "ERROR: Timeout waiting for deployment to complete."
        return 1
    fi
    
    echo "Deployment completed successfully."
    return 0
}

# Verifies the deployment by checking frontend service health
verify_deployment() {
    echo "Verifying deployment by checking frontend service health..."
    
    # Wait a short time for services to stabilize
    sleep 10
    
    # Try health checks multiple times with delay between attempts
    for ((i=1; i<=$HEALTH_CHECK_RETRIES; i++)); do
        echo "Health check attempt $i of $HEALTH_CHECK_RETRIES..."
        
        if check_frontend_health "$ENVIRONMENT"; then
            echo "Frontend service is healthy after deployment."
            return 0
        fi
        
        if [[ $i -lt $HEALTH_CHECK_RETRIES ]]; then
            echo "Health check failed, retrying in $HEALTH_CHECK_INTERVAL seconds..."
            sleep $HEALTH_CHECK_INTERVAL
        fi
    done
    
    echo "ERROR: Frontend service is not healthy after deployment."
    return 1
}

# Invalidates the CloudFront cache to ensure users get the latest frontend version
invalidate_cloudfront_cache() {
    if [[ -z "$CLOUDFRONT_DISTRIBUTION_ID" ]]; then
        echo "No CloudFront distribution ID provided, skipping cache invalidation."
        return 0
    fi
    
    echo "Invalidating CloudFront cache for distribution $CLOUDFRONT_DISTRIBUTION_ID..."
    
    # Create the invalidation
    local invalidation_id=$(aws cloudfront create-invalidation \
        --distribution-id "$CLOUDFRONT_DISTRIBUTION_ID" \
        --paths "/*" \
        --region "$AWS_REGION" \
        --query "Invalidation.Id" \
        --output text)
    
    if [[ -z "$invalidation_id" || "$invalidation_id" == "None" ]]; then
        echo "WARNING: Failed to invalidate CloudFront cache."
        return 1
    fi
    
    echo "CloudFront invalidation initiated with ID: $invalidation_id"
    
    # Wait for invalidation to complete
    echo "Waiting for CloudFront invalidation to complete..."
    aws cloudfront wait invalidation-completed \
        --distribution-id "$CLOUDFRONT_DISTRIBUTION_ID" \
        --id "$invalidation_id" \
        --region "$AWS_REGION"
    
    echo "CloudFront cache invalidation completed."
    
    # Return the invalidation ID
    echo "$invalidation_id"
}

# Handles deployment failure by initiating rollback
handle_deployment_failure() {
    local previous_task_definition_arn="$1"
    local deployment_type="$2"
    
    echo "ERROR: Deployment failed! Initiating rollback to $previous_task_definition_arn..."
    
    # Extract the previous task definition information
    local task_def_family=$(echo "$previous_task_definition_arn" | cut -d '/' -f 2 | cut -d ':' -f 1)
    
    # Initiate rollback using the rollback.sh script
    if rollback_deployment "$ECS_SERVICE" "$deployment_type" ""; then
        echo "Rollback successful, service should be stable now."
        return 0
    else
        echo "ERROR: Rollback failed. Manual intervention required."
        return 1
    fi
}

# Cleans up temporary files and resources
cleanup() {
    echo "Cleaning up temporary files..."
    
    # Clean up any temporary files created during deployment
    rm -f /tmp/task-definition-$$.json /tmp/updated-task-definition-$$.json
    
    echo "Cleanup completed."
}

# Main function that orchestrates the frontend deployment process
main() {
    echo "Starting frontend deployment process..."
    
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
            --deployment-type)
                DEPLOYMENT_TYPE="$2"
                shift 2
                ;;
            *)
                echo "ERROR: Unknown option: $1"
                echo "Usage: $0 [--environment <env>] [--image-tag <tag>] [--deployment-type <type>]"
                return 3
                ;;
        esac
    done
    
    echo "Deployment environment: $ENVIRONMENT"
    echo "Image tag: $IMAGE_TAG"
    echo "Deployment type: $DEPLOYMENT_TYPE"
    
    # Update ECS cluster name based on environment
    ECS_CLUSTER="molecule-flow-${ENVIRONMENT}"
    
    # Check prerequisites
    if ! check_prerequisites; then
        echo "ERROR: Prerequisites check failed. Cannot proceed with deployment."
        return 1
    fi
    
    # Get current task definition
    local task_definition_file=$(get_current_task_definition)
    if [[ -z "$task_definition_file" || ! -f "$task_definition_file" ]]; then
        echo "ERROR: Failed to get current task definition."
        return 1
    fi
    
    local current_task_definition_arn=$(cat "$task_definition_file" | jq -r '.taskDefinitionArn')
    
    # Construct the new image URI
    local aws_account_id=$(aws sts get-caller-identity --query Account --output text)
    local image_uri="${aws_account_id}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}:${IMAGE_TAG}"
    
    echo "Using image URI: $image_uri"
    
    # Update task definition with new image
    local new_task_definition_arn=$(update_task_definition "$task_definition_file" "$image_uri")
    if [[ -z "$new_task_definition_arn" ]]; then
        echo "ERROR: Failed to update task definition."
        cleanup
        return 1
    fi
    
    # Deploy based on environment and deployment type
    local deployment_id=""
    local deployment_successful=false
    
    if [[ "$DEPLOYMENT_TYPE" == "auto" ]]; then
        # Determine deployment type based on environment
        case "$ENVIRONMENT" in
            "dev"|"development")
                DEPLOYMENT_TYPE="rolling"
                ;;
            "staging")
                DEPLOYMENT_TYPE="blue-green"
                ;;
            "prod"|"production")
                DEPLOYMENT_TYPE="canary"
                ;;
            *)
                DEPLOYMENT_TYPE="rolling"
                ;;
        esac
    fi
    
    # Deploy using the appropriate strategy
    case "$DEPLOYMENT_TYPE" in
        "rolling")
            deployment_id=$(deploy_rolling_update "$new_task_definition_arn")
            ;;
        "blue-green")
            deployment_id=$(deploy_blue_green "$new_task_definition_arn")
            ;;
        "canary")
            deployment_id=$(deploy_canary "$new_task_definition_arn")
            ;;
        *)
            echo "ERROR: Unknown deployment type: $DEPLOYMENT_TYPE"
            cleanup
            return 3
            ;;
    esac
    
    if [[ -z "$deployment_id" ]]; then
        echo "ERROR: Failed to initiate deployment."
        handle_deployment_failure "$current_task_definition_arn" "$DEPLOYMENT_TYPE"
        cleanup
        return 2
    fi
    
    # Wait for deployment to complete
    if wait_for_deployment "$deployment_id" "$DEPLOYMENT_TYPE"; then
        # Verify deployment
        if verify_deployment; then
            deployment_successful=true
            
            # Invalidate CloudFront cache if configured
            if [[ -n "$CLOUDFRONT_DISTRIBUTION_ID" ]]; then
                invalidate_cloudfront_cache
            fi
        else
            echo "ERROR: Deployment verification failed."
            handle_deployment_failure "$current_task_definition_arn" "$DEPLOYMENT_TYPE"
        fi
    else
        echo "ERROR: Deployment did not complete successfully."
        handle_deployment_failure "$current_task_definition_arn" "$DEPLOYMENT_TYPE"
    fi
    
    # Cleanup
    cleanup
    
    if [[ "$deployment_successful" == "true" ]]; then
        echo "Frontend deployment completed successfully."
        return 0
    else
        echo "Frontend deployment failed."
        return 2
    fi
}

# Run main function if script is executed directly (not sourced)
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
    exit $?
fi

# Export the main function for use in other scripts
export -f deploy_frontend