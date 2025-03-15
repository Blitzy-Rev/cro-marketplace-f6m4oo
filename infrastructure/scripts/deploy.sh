#!/usr/bin/env bash
#
# Master Deployment Script for Molecular Data Management and CRO Integration Platform
#
# This script orchestrates the complete deployment process across all environments,
# coordinating infrastructure provisioning, service deployment, and post-deployment validation.
#
# Usage: ./deploy.sh [options]
#
# Options:
#   -e, --environment <env>         Environment to deploy (dev, staging, prod)
#   --backend-tag <tag>             Docker image tag for backend services
#   --frontend-tag <tag>            Docker image tag for frontend services
#   --worker-tag <tag>              Docker image tag for worker services
#   --skip-infrastructure           Skip infrastructure deployment
#   --skip-backend                  Skip backend service deployment
#   --skip-frontend                 Skip frontend service deployment
#   --skip-workers                  Skip worker service deployment
#   --skip-validation               Skip post-deployment validation
#   -v, --verbose                   Enable verbose output
#   -h, --help                      Display help message
#
# Examples:
#   ./deploy.sh -e dev --backend-tag v1.2.3 --frontend-tag v1.2.3
#   ./deploy.sh -e prod --skip-infrastructure
#
# Dependencies:
#   - aws-cli (2.x) - AWS command line interface for resource management
#   - terraform (1.5+) - Infrastructure as Code tool for AWS resource provisioning
#   - jq (1.6+) - JSON processor for parsing configuration files
#

# Exit on error
set -e

# Global variables
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
LOG_FILE="${SCRIPT_DIR}/../logs/deploy_$(date +%Y%m%d_%H%M%S).log"
ENVIRONMENT="${ENVIRONMENT:-dev}"
BACKEND_IMAGE_TAG="${BACKEND_IMAGE_TAG:-latest}"
FRONTEND_IMAGE_TAG="${FRONTEND_IMAGE_TAG:-latest}"
WORKER_IMAGE_TAG="${WORKER_IMAGE_TAG:-latest}"
DEPLOY_INFRASTRUCTURE="${DEPLOY_INFRASTRUCTURE:-true}"
DEPLOY_BACKEND="${DEPLOY_BACKEND:-true}"
DEPLOY_FRONTEND="${DEPLOY_FRONTEND:-true}"
DEPLOY_WORKERS="${DEPLOY_WORKERS:-true}"
SKIP_VALIDATION="${SKIP_VALIDATION:-false}"
AWS_REGION="${AWS_REGION:-us-east-1}"
TERRAFORM_DIR="${SCRIPT_DIR}/../terraform/environments/${ENVIRONMENT}"

# Function to set up logging for the deployment process
setup_logging() {
    # Create logs directory if it doesn't exist
    mkdir -p "$(dirname "$LOG_FILE")"
    
    # Initialize log file with timestamp and deployment parameters
    {
        echo "=== Deployment Started at $(date '+%Y-%m-%d %H:%M:%S') ==="
        echo "Environment: $ENVIRONMENT"
        echo "Backend Image Tag: $BACKEND_IMAGE_TAG"
        echo "Frontend Image Tag: $FRONTEND_IMAGE_TAG"
        echo "Worker Image Tag: $WORKER_IMAGE_TAG"
        echo "Deploy Infrastructure: $DEPLOY_INFRASTRUCTURE"
        echo "Deploy Backend: $DEPLOY_BACKEND"
        echo "Deploy Frontend: $DEPLOY_FRONTEND"
        echo "Deploy Workers: $DEPLOY_WORKERS"
        echo "Skip Validation: $SKIP_VALIDATION"
        echo "AWS Region: $AWS_REGION"
        echo "========================================================"
        echo ""
    } > "$LOG_FILE"
    
    # Set up log rotation if needed (keep last 10 logs)
    find "$(dirname "$LOG_FILE")" -name "deploy_*.log" -type f | sort -r | tail -n +11 | xargs -r rm
    
    echo "Logging to $LOG_FILE"
    return 0
}

# Function to parse command line arguments
parse_arguments() {
    local args=("$@")
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -e|--environment)
                ENVIRONMENT="$2"
                TERRAFORM_DIR="${SCRIPT_DIR}/../terraform/environments/${ENVIRONMENT}"
                shift 2
                ;;
            --backend-tag)
                BACKEND_IMAGE_TAG="$2"
                shift 2
                ;;
            --frontend-tag)
                FRONTEND_IMAGE_TAG="$2"
                shift 2
                ;;
            --worker-tag)
                WORKER_IMAGE_TAG="$2"
                shift 2
                ;;
            --skip-infrastructure)
                DEPLOY_INFRASTRUCTURE="false"
                shift
                ;;
            --skip-backend)
                DEPLOY_BACKEND="false"
                shift
                ;;
            --skip-frontend)
                DEPLOY_FRONTEND="false"
                shift
                ;;
            --skip-workers)
                DEPLOY_WORKERS="false"
                shift
                ;;
            --skip-validation)
                SKIP_VALIDATION="true"
                shift
                ;;
            --aws-region)
                AWS_REGION="$2"
                shift 2
                ;;
            -v|--verbose)
                export VERBOSE="true"
                shift
                ;;
            -h|--help)
                echo "Usage: ./deploy.sh [options]"
                echo ""
                echo "Options:"
                echo "  -e, --environment <env>         Environment to deploy (dev, staging, prod)"
                echo "  --backend-tag <tag>             Docker image tag for backend services"
                echo "  --frontend-tag <tag>            Docker image tag for frontend services"
                echo "  --worker-tag <tag>              Docker image tag for worker services"
                echo "  --skip-infrastructure           Skip infrastructure deployment"
                echo "  --skip-backend                  Skip backend service deployment"
                echo "  --skip-frontend                 Skip frontend service deployment"
                echo "  --skip-workers                  Skip worker service deployment"
                echo "  --skip-validation               Skip post-deployment validation"
                echo "  --aws-region <region>           AWS region (default: us-east-1)"
                echo "  -v, --verbose                   Enable verbose output"
                echo "  -h, --help                      Display this help message"
                echo ""
                echo "Examples:"
                echo "  ./deploy.sh -e dev --backend-tag v1.2.3 --frontend-tag v1.2.3"
                echo "  ./deploy.sh -e prod --skip-infrastructure"
                exit 0
                ;;
            *)
                echo "Unknown option: $1"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    done
    
    # Validate environment
    if [[ ! "$ENVIRONMENT" =~ ^(dev|staging|prod)$ ]]; then
        echo "ERROR: Invalid environment: $ENVIRONMENT"
        echo "Valid environments are: dev, staging, prod"
        exit 1
    fi
    
    # Export environment variables for use in child scripts
    export ENVIRONMENT
    export BACKEND_IMAGE_TAG
    export FRONTEND_IMAGE_TAG
    export WORKER_IMAGE_TAG
    export AWS_REGION
    
    return 0
}

# Function to deploy infrastructure using Terraform
deploy_infrastructure() {
    local environment="$1"
    local start_time=$(date +%s)
    
    echo "Deploying infrastructure for environment: $environment"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Deploying infrastructure" >> "$LOG_FILE"
    
    # Change to the Terraform directory
    cd "$TERRAFORM_DIR"
    
    # Initialize Terraform if needed
    if [[ ! -d ".terraform" ]]; then
        echo "Initializing Terraform..."
        terraform init >> "$LOG_FILE" 2>&1
        if [[ $? -ne 0 ]]; then
            echo "ERROR: Terraform initialization failed"
            echo "$(date '+%Y-%m-%d %H:%M:%S') - ERROR: Terraform initialization failed" >> "$LOG_FILE"
            return 1
        fi
    fi
    
    # Run terraform plan to preview changes
    echo "Planning Terraform changes..."
    terraform plan -out=tfplan -var="environment=${environment}" -var="region=${AWS_REGION}" >> "$LOG_FILE" 2>&1
    if [[ $? -ne 0 ]]; then
        echo "ERROR: Terraform plan failed"
        echo "$(date '+%Y-%m-%d %H:%M:%S') - ERROR: Terraform plan failed" >> "$LOG_FILE"
        return 1
    fi
    
    # Apply the plan
    echo "Applying Terraform changes..."
    terraform apply -auto-approve tfplan >> "$LOG_FILE" 2>&1
    if [[ $? -ne 0 ]]; then
        echo "ERROR: Terraform apply failed"
        echo "$(date '+%Y-%m-%d %H:%M:%S') - ERROR: Terraform apply failed" >> "$LOG_FILE"
        return 1
    fi
    
    # Extract and export output variables
    echo "Extracting Terraform outputs..."
    
    # Export ECS cluster name
    export ECS_CLUSTER=$(terraform output -raw ecs_cluster_name 2>/dev/null || echo "molecule-flow-${environment}")
    
    # Export ECR repository URLs
    export BACKEND_ECR_REPOSITORY=$(terraform output -raw backend_ecr_repository 2>/dev/null || echo "molecule-flow/backend")
    export FRONTEND_ECR_REPOSITORY=$(terraform output -raw frontend_ecr_repository 2>/dev/null || echo "molecule-flow/frontend")
    
    # Export load balancer info
    export API_LOAD_BALANCER=$(terraform output -raw api_load_balancer_dns 2>/dev/null || echo "")
    export FRONTEND_LOAD_BALANCER=$(terraform output -raw frontend_load_balancer_dns 2>/dev/null || echo "")
    
    # Export CloudFront distribution ID if available
    export CLOUDFRONT_DISTRIBUTION_ID=$(terraform output -raw cloudfront_distribution_id 2>/dev/null || echo "")
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    echo "Infrastructure deployment completed in $duration seconds"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Infrastructure deployment completed in $duration seconds" >> "$LOG_FILE"
    
    # Return to original directory
    cd - > /dev/null
    
    return 0
}

# Function to deploy application services to ECS
deploy_services() {
    local environment="$1"
    local deploy_success=true
    local start_time=$(date +%s)
    
    echo "Deploying services for environment: $environment"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Deploying services" >> "$LOG_FILE"
    
    # Set deployment environment variables
    export ECS_CLUSTER="${ECS_CLUSTER:-molecule-flow-${environment}}"
    
    # Deploy backend services if enabled
    if [[ "$DEPLOY_BACKEND" == "true" ]]; then
        echo "Deploying backend services with tag: $BACKEND_IMAGE_TAG"
        echo "$(date '+%Y-%m-%d %H:%M:%S') - Deploying backend services with tag: $BACKEND_IMAGE_TAG" >> "$LOG_FILE"
        
        # Source and call the backend deployment script
        source "${SCRIPT_DIR}/../../deployment/scripts/deploy_backend.sh"
        
        if deploy_backend --environment "$environment" --image-tag "$BACKEND_IMAGE_TAG" --deployment-type "rolling" >> "$LOG_FILE" 2>&1; then
            echo "Backend deployment successful"
            echo "$(date '+%Y-%m-%d %H:%M:%S') - Backend deployment successful" >> "$LOG_FILE"
        else
            echo "ERROR: Backend deployment failed"
            echo "$(date '+%Y-%m-%d %H:%M:%S') - ERROR: Backend deployment failed" >> "$LOG_FILE"
            deploy_success=false
        fi
    else
        echo "Skipping backend deployment (--skip-backend specified)"
        echo "$(date '+%Y-%m-%d %H:%M:%S') - Skipping backend deployment" >> "$LOG_FILE"
    fi
    
    # Deploy frontend services if enabled
    if [[ "$DEPLOY_FRONTEND" == "true" ]]; then
        echo "Deploying frontend services with tag: $FRONTEND_IMAGE_TAG"
        echo "$(date '+%Y-%m-%d %H:%M:%S') - Deploying frontend services with tag: $FRONTEND_IMAGE_TAG" >> "$LOG_FILE"
        
        # Source and call the frontend deployment script
        source "${SCRIPT_DIR}/../../deployment/scripts/deploy_frontend.sh"
        
        if deploy_frontend --environment "$environment" --image-tag "$FRONTEND_IMAGE_TAG" >> "$LOG_FILE" 2>&1; then
            echo "Frontend deployment successful"
            echo "$(date '+%Y-%m-%d %H:%M:%S') - Frontend deployment successful" >> "$LOG_FILE"
        else
            echo "ERROR: Frontend deployment failed"
            echo "$(date '+%Y-%m-%d %H:%M:%S') - ERROR: Frontend deployment failed" >> "$LOG_FILE"
            deploy_success=false
        fi
    else
        echo "Skipping frontend deployment (--skip-frontend specified)"
        echo "$(date '+%Y-%m-%d %H:%M:%S') - Skipping frontend deployment" >> "$LOG_FILE"
    fi
    
    # Deploy worker services if enabled
    if [[ "$DEPLOY_WORKERS" == "true" ]]; then
        echo "Deploying worker services with tag: $WORKER_IMAGE_TAG"
        echo "$(date '+%Y-%m-%d %H:%M:%S') - Deploying worker services with tag: $WORKER_IMAGE_TAG" >> "$LOG_FILE"
        
        # Source and call the workers deployment script
        source "${SCRIPT_DIR}/../../deployment/scripts/deploy_workers.sh"
        
        if deploy_workers --environment "$environment" --image-tag "$WORKER_IMAGE_TAG" >> "$LOG_FILE" 2>&1; then
            echo "Worker deployment successful"
            echo "$(date '+%Y-%m-%d %H:%M:%S') - Worker deployment successful" >> "$LOG_FILE"
        else
            echo "ERROR: Worker deployment failed"
            echo "$(date '+%Y-%m-%d %H:%M:%S') - ERROR: Worker deployment failed" >> "$LOG_FILE"
            deploy_success=false
        fi
    else
        echo "Skipping worker deployment (--skip-workers specified)"
        echo "$(date '+%Y-%m-%d %H:%M:%S') - Skipping worker deployment" >> "$LOG_FILE"
    fi
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    echo "Service deployments completed in $duration seconds"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Service deployments completed in $duration seconds" >> "$LOG_FILE"
    
    # Return overall deployment status
    if [[ "$deploy_success" == "true" ]]; then
        return 0
    else
        return 1
    fi
}

# Function to validate the deployment by checking system health
validate_deployment() {
    local environment="$1"
    local start_time=$(date +%s)
    
    if [[ "$SKIP_VALIDATION" == "true" ]]; then
        echo "Skipping deployment validation (--skip-validation specified)"
        echo "$(date '+%Y-%m-%d %H:%M:%S') - Skipping deployment validation" >> "$LOG_FILE"
        return 0
    fi
    
    echo "Validating deployment for environment: $environment"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Validating deployment" >> "$LOG_FILE"
    
    # Wait for services to stabilize
    echo "Waiting for services to stabilize (60 seconds)..."
    sleep 60
    
    # Source and use health_check.sh to verify system health
    source "${SCRIPT_DIR}/../../deployment/scripts/health_check.sh"
    
    # Check overall system health
    echo "Checking system health..."
    if check_system_health "$environment" >> "$LOG_FILE" 2>&1; then
        echo "System health check passed"
        echo "$(date '+%Y-%m-%d %H:%M:%S') - System health check passed" >> "$LOG_FILE"
    else
        echo "ERROR: System health check failed"
        echo "$(date '+%Y-%m-%d %H:%M:%S') - ERROR: System health check failed" >> "$LOG_FILE"
        return 1
    fi
    
    # Check specific services based on what was deployed
    if [[ "$DEPLOY_BACKEND" == "true" ]]; then
        echo "Checking API health..."
        if check_api_health "$environment" >> "$LOG_FILE" 2>&1; then
            echo "API health check passed"
            echo "$(date '+%Y-%m-%d %H:%M:%S') - API health check passed" >> "$LOG_FILE"
        else
            echo "ERROR: API health check failed"
            echo "$(date '+%Y-%m-%d %H:%M:%S') - ERROR: API health check failed" >> "$LOG_FILE"
            return 1
        fi
    fi
    
    if [[ "$DEPLOY_FRONTEND" == "true" ]]; then
        echo "Checking frontend health..."
        if check_frontend_health "$environment" >> "$LOG_FILE" 2>&1; then
            echo "Frontend health check passed"
            echo "$(date '+%Y-%m-%d %H:%M:%S') - Frontend health check passed" >> "$LOG_FILE"
        else
            echo "ERROR: Frontend health check failed"
            echo "$(date '+%Y-%m-%d %H:%M:%S') - ERROR: Frontend health check failed" >> "$LOG_FILE"
            return 1
        fi
    fi
    
    if [[ "$DEPLOY_WORKERS" == "true" ]]; then
        echo "Checking worker health..."
        if check_service_health "worker" "$environment" >> "$LOG_FILE" 2>&1; then
            echo "Worker health check passed"
            echo "$(date '+%Y-%m-%d %H:%M:%S') - Worker health check passed" >> "$LOG_FILE"
        else
            echo "ERROR: Worker health check failed"
            echo "$(date '+%Y-%m-%d %H:%M:%S') - ERROR: Worker health check failed" >> "$LOG_FILE"
            return 1
        fi
    fi
    
    # Verify database connectivity if backend was deployed
    if [[ "$DEPLOY_BACKEND" == "true" ]]; then
        echo "Checking database connectivity..."
        if check_service_health "database" "$environment" >> "$LOG_FILE" 2>&1; then
            echo "Database connectivity check passed"
            echo "$(date '+%Y-%m-%d %H:%M:%S') - Database connectivity check passed" >> "$LOG_FILE"
        else
            echo "WARNING: Database connectivity check failed"
            echo "$(date '+%Y-%m-%d %H:%M:%S') - WARNING: Database connectivity check failed" >> "$LOG_FILE"
            # Don't fail deployment for database check
        fi
    fi
    
    # Verify integration points if applicable
    if [[ "$DEPLOY_BACKEND" == "true" ]]; then
        echo "Checking integration points..."
        if check_integration_points "$environment" >> "$LOG_FILE" 2>&1; then
            echo "Integration points check passed"
            echo "$(date '+%Y-%m-%d %H:%M:%S') - Integration points check passed" >> "$LOG_FILE"
        else
            echo "WARNING: Integration points check failed"
            echo "$(date '+%Y-%m-%d %H:%M:%S') - WARNING: Integration points check failed" >> "$LOG_FILE"
            # Don't fail deployment for integration points check
        fi
    fi
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    echo "Deployment validation completed in $duration seconds"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Deployment validation completed in $duration seconds" >> "$LOG_FILE"
    
    return 0
}

# Function to handle deployment failure
handle_deployment_failure() {
    local component="$1"
    local error_message="$2"
    
    echo "DEPLOYMENT FAILURE: $component"
    echo "Error: $error_message"
    
    echo "$(date '+%Y-%m-%d %H:%M:%S') - DEPLOYMENT FAILURE: $component" >> "$LOG_FILE"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Error: $error_message" >> "$LOG_FILE"
    
    # Determine if rollback is possible/needed
    case "$component" in
        "infrastructure")
            echo "Infrastructure deployment failed. Manual intervention required."
            echo "$(date '+%Y-%m-%d %H:%M:%S') - Infrastructure deployment failed. Manual intervention required." >> "$LOG_FILE"
            ;;
        "backend"|"frontend"|"workers")
            echo "Service deployment failed. Consider running deployment with --skip-infrastructure to retry."
            echo "$(date '+%Y-%m-%d %H:%M:%S') - Service deployment failed. Consider running deployment with --skip-infrastructure to retry." >> "$LOG_FILE"
            ;;
        "validation")
            echo "Deployment validation failed. Services may be unstable."
            echo "$(date '+%Y-%m-%d %H:%M:%S') - Deployment validation failed. Services may be unstable." >> "$LOG_FILE"
            ;;
        *)
            echo "Unknown failure component: $component"
            echo "$(date '+%Y-%m-%d %H:%M:%S') - Unknown failure component: $component" >> "$LOG_FILE"
            ;;
    esac
    
    # Provide troubleshooting guidance
    echo ""
    echo "Troubleshooting steps:"
    echo "1. Check the deployment log at: $LOG_FILE"
    echo "2. Verify AWS credentials and permissions"
    echo "3. Check service logs in CloudWatch"
    echo "4. Verify infrastructure state using terraform state list"
    echo ""
    
    # Send notification to admins
    notify_deployment_status "$ENVIRONMENT" "false" "$component failed: $error_message"
    
    # Exit with appropriate error code
    case "$component" in
        "infrastructure") return 2 ;;
        "backend"|"frontend"|"workers") return 3 ;;
        "validation") return 4 ;;
        *) return 1 ;;
    esac
}

# Function to generate a deployment report
generate_deployment_report() {
    local environment="$1"
    local success="$2"
    local report_file="${SCRIPT_DIR}/../logs/deployment_report_${environment}_$(date +%Y%m%d_%H%M%S).json"
    
    echo "Generating deployment report..."
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Generating deployment report" >> "$LOG_FILE"
    
    # Collect deployment details
    local components_deployed=()
    [[ "$DEPLOY_INFRASTRUCTURE" == "true" ]] && components_deployed+=("infrastructure")
    [[ "$DEPLOY_BACKEND" == "true" ]] && components_deployed+=("backend")
    [[ "$DEPLOY_FRONTEND" == "true" ]] && components_deployed+=("frontend")
    [[ "$DEPLOY_WORKERS" == "true" ]] && components_deployed+=("workers")
    
    # Create JSON report
    cat > "$report_file" << EOF
{
  "deployment": {
    "environment": "$environment",
    "timestamp": "$(date '+%Y-%m-%d %H:%M:%S')",
    "success": $success,
    "components": {
      "infrastructure": {
        "deployed": ${DEPLOY_INFRASTRUCTURE},
        "version": "terraform-$(terraform --version | head -n 1 | cut -d 'v' -f 2)"
      },
      "backend": {
        "deployed": ${DEPLOY_BACKEND},
        "version": "${BACKEND_IMAGE_TAG}"
      },
      "frontend": {
        "deployed": ${DEPLOY_FRONTEND},
        "version": "${FRONTEND_IMAGE_TAG}"
      },
      "workers": {
        "deployed": ${DEPLOY_WORKERS},
        "version": "${WORKER_IMAGE_TAG}"
      }
    },
    "aws": {
      "region": "${AWS_REGION}",
      "account": "$(aws sts get-caller-identity --query Account --output text 2>/dev/null || echo "unknown")"
    },
    "urls": {
      "api": "${API_LOAD_BALANCER:-N/A}",
      "frontend": "${FRONTEND_LOAD_BALANCER:-N/A}"
    },
    "log_file": "${LOG_FILE}"
  }
}
EOF
    
    echo "Deployment report generated: $report_file"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Deployment report generated: $report_file" >> "$LOG_FILE"
    
    echo "$report_file"
    return 0
}

# Function to notify stakeholders of deployment status
notify_deployment_status() {
    local environment="$1"
    local success="$2"
    local report_path="$3"
    
    echo "Sending deployment notifications..."
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Sending deployment notifications" >> "$LOG_FILE"
    
    # Determine notification recipients based on environment
    local recipients=""
    case "$environment" in
        "dev") recipients="dev-team@example.com" ;;
        "staging") recipients="dev-team@example.com,qa-team@example.com" ;;
        "prod") recipients="dev-team@example.com,qa-team@example.com,ops-team@example.com" ;;
        *) recipients="dev-team@example.com" ;;
    esac
    
    # Prepare notification message
    local status_text="FAILED"
    [[ "$success" == "true" ]] && status_text="SUCCESSFUL"
    
    local subject="[MoleculeFlow] Deployment to $environment $status_text"
    local message="
Deployment to $environment environment $status_text at $(date '+%Y-%m-%d %H:%M:%S').

Environment: $environment
Components deployed: 
- Infrastructure: $DEPLOY_INFRASTRUCTURE
- Backend: $DEPLOY_BACKEND (tag: $BACKEND_IMAGE_TAG)
- Frontend: $DEPLOY_FRONTEND (tag: $FRONTEND_IMAGE_TAG)
- Workers: $DEPLOY_WORKERS (tag: $WORKER_IMAGE_TAG)

URLs:
- API: ${API_LOAD_BALANCER:-N/A}
- Frontend: ${FRONTEND_LOAD_BALANCER:-N/A}

See the deployment report for more details: $report_path
Log file: $LOG_FILE
"
    
    # Log the notification (in a real implementation, would send via email/Slack)
    echo "Notification would be sent to: $recipients" >> "$LOG_FILE"
    echo "Subject: $subject" >> "$LOG_FILE"
    echo "Message: $message" >> "$LOG_FILE"
    
    # If SNS is configured, send the notification
    if [[ -n "$SNS_TOPIC_ARN" ]]; then
        aws sns publish \
            --topic-arn "$SNS_TOPIC_ARN" \
            --message "$message" \
            --subject "$subject" \
            --region "$AWS_REGION" >> "$LOG_FILE" 2>&1
            
        if [[ $? -ne 0 ]]; then
            echo "Warning: Failed to send SNS notification" >> "$LOG_FILE"
            return 1
        fi
    fi
    
    # If Slack webhook is configured, send Slack notification
    if [[ -n "$SLACK_WEBHOOK_URL" ]]; then
        local color="danger"
        [[ "$success" == "true" ]] && color="good"
        
        local slack_payload="{
            \"attachments\": [
                {
                    \"color\": \"$color\",
                    \"title\": \"$subject\",
                    \"text\": \"$message\",
                    \"footer\": \"MoleculeFlow Deployment\"
                }
            ]
        }"
        
        curl -s -X POST -H "Content-type: application/json" \
            --data "$slack_payload" "$SLACK_WEBHOOK_URL" >> "$LOG_FILE" 2>&1
            
        if [[ $? -ne 0 ]]; then
            echo "Warning: Failed to send Slack notification" >> "$LOG_FILE"
            return 1
        fi
    fi
    
    echo "Notifications sent successfully"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Notifications sent successfully" >> "$LOG_FILE"
    
    return 0
}

# Main function that orchestrates the deployment process
main() {
    local args=("$@")
    local deployment_success=true
    
    # Parse command line arguments
    parse_arguments "${args[@]}"
    
    # Set up logging
    setup_logging
    
    echo "Starting deployment to environment: $ENVIRONMENT"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Starting deployment to environment: $ENVIRONMENT" >> "$LOG_FILE"
    
    # Source bootstrap script to check prerequisites
    source "${SCRIPT_DIR}/bootstrap.sh"
    
    if ! check_prerequisites; then
        echo "ERROR: Prerequisites check failed"
        echo "$(date '+%Y-%m-%d %H:%M:%S') - ERROR: Prerequisites check failed" >> "$LOG_FILE"
        handle_deployment_failure "prerequisites" "Prerequisites check failed"
        exit 1
    fi
    
    # Deploy infrastructure if enabled
    if [[ "$DEPLOY_INFRASTRUCTURE" == "true" ]]; then
        if ! deploy_infrastructure "$ENVIRONMENT"; then
            echo "ERROR: Infrastructure deployment failed"
            handle_deployment_failure "infrastructure" "Infrastructure deployment failed"
            exit 2
        fi
    else
        echo "Skipping infrastructure deployment (--skip-infrastructure specified)"
        echo "$(date '+%Y-%m-%d %H:%M:%S') - Skipping infrastructure deployment" >> "$LOG_FILE"
    fi
    
    # Deploy services
    if ! deploy_services "$ENVIRONMENT"; then
        echo "ERROR: Service deployment failed"
        handle_deployment_failure "services" "One or more services failed to deploy"
        exit 3
    fi
    
    # Validate deployment
    if [[ "$SKIP_VALIDATION" != "true" ]]; then
        if ! validate_deployment "$ENVIRONMENT"; then
            echo "ERROR: Deployment validation failed"
            handle_deployment_failure "validation" "Deployment validation failed"
            deployment_success=false
        fi
    fi
    
    # Generate deployment report
    local report_path=$(generate_deployment_report "$ENVIRONMENT" "$deployment_success")
    
    # Notify stakeholders
    notify_deployment_status "$ENVIRONMENT" "$deployment_success" "$report_path"
    
    # Final deployment status
    if [[ "$deployment_success" == "true" ]]; then
        echo "Deployment to $ENVIRONMENT completed successfully"
        echo "$(date '+%Y-%m-%d %H:%M:%S') - Deployment to $ENVIRONMENT completed successfully" >> "$LOG_FILE"
        exit 0
    else
        echo "Deployment to $ENVIRONMENT failed"
        echo "$(date '+%Y-%m-%d %H:%M:%S') - Deployment to $ENVIRONMENT failed" >> "$LOG_FILE"
        exit 1
    fi
}

# Export functions for use in CI/CD pipelines
export -f main

# Run main function if the script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi