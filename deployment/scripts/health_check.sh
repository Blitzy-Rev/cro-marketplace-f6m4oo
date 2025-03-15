#!/bin/bash
#
# Health Check Script for Molecular Data Management and CRO Integration Platform
#
# This script provides functions to verify the health and availability of 
# deployed services by checking API endpoints, connectivity to dependencies,
# and overall system status. It is used during deployment, monitoring, and 
# rollback processes to ensure system reliability.
#
# Dependencies:
# - curl (7.0+): Make HTTP requests to health check endpoints
# - jq (1.6+): Parse JSON responses from health check endpoints
# - aws-cli (2.x): Retrieve service information from AWS resources
#
# Usage:
#   ./health_check.sh [--service <service_name>] [--environment <env>] [--wait] [--timeout <seconds>]
#
# Options:
#   --service <service_name>    Check health of a specific service (api, frontend, etc.)
#   --environment <env>         Environment to check (dev, staging, prod, local)
#   --wait                      Wait for service to become healthy (uses --timeout)
#   --timeout <seconds>         Timeout in seconds when waiting for service health
#   --verbose                   Enable verbose output
#
# Exit codes:
#   0 - All specified services are healthy
#   1 - Prerequisites not met
#   2 - One or more services are unhealthy
#   3 - Timeout waiting for service to become healthy
#

# Global variables with defaults from environment variables
AWS_REGION="${AWS_REGION:-us-east-1}"
ENVIRONMENT="${ENVIRONMENT:-dev}"
HEALTH_CHECK_TIMEOUT="${HEALTH_CHECK_TIMEOUT:-5}"
HEALTH_CHECK_RETRIES="${HEALTH_CHECK_RETRIES:-3}"
HEALTH_CHECK_INTERVAL="${HEALTH_CHECK_INTERVAL:-10}"
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

# Check if required tools are installed
check_prerequisites() {
    local missing_tools=false
    
    # Check for curl
    if ! command -v curl &> /dev/null; then
        log_message "curl is not installed. Please install curl 7.0+ to use this script." "ERROR"
        missing_tools=true
    fi
    
    # Check for jq
    if ! command -v jq &> /dev/null; then
        log_message "jq is not installed. Please install jq 1.6+ to use this script." "ERROR"
        missing_tools=true
    fi
    
    # Check for AWS CLI if we're using AWS resources
    if [[ "$ENVIRONMENT" != "local" ]]; then
        if ! command -v aws &> /dev/null; then
            log_message "AWS CLI is not installed. Please install aws-cli 2.x for non-local environments." "ERROR"
            missing_tools=true
        fi
    fi
    
    if [[ "$missing_tools" == "true" ]]; then
        return 1
    fi
    
    log_message "All required tools are available" "DEBUG"
    return 0
}

# Get service URL based on environment
get_service_url() {
    local service_name="$1"
    local environment="${2:-$ENVIRONMENT}"
    local service_url=""
    
    log_message "Getting URL for service $service_name in environment $environment" "DEBUG"
    
    case "$environment" in
        "local")
            # Local development environment
            case "$service_name" in
                "api")
                    service_url="http://localhost:8000"
                    ;;
                "frontend")
                    service_url="http://localhost:3000"
                    ;;
                "molecule-service")
                    service_url="http://localhost:8001"
                    ;;
                "cro-service")
                    service_url="http://localhost:8002"
                    ;;
                "document-service")
                    service_url="http://localhost:8003"
                    ;;
                *)
                    log_message "Unknown service: $service_name" "ERROR"
                    service_url=""
                    ;;
            esac
            ;;
            
        "dev"|"staging"|"prod")
            # AWS deployment environments
            local lb_name=""
            
            case "$service_name" in
                "api")
                    lb_name="api-lb"
                    ;;
                "frontend")
                    lb_name="frontend-lb"
                    ;;
                "molecule-service")
                    lb_name="molecule-service-lb"
                    ;;
                "cro-service")
                    lb_name="cro-service-lb"
                    ;;
                "document-service")
                    lb_name="document-service-lb"
                    ;;
                *)
                    log_message "Unknown service: $service_name" "ERROR"
                    lb_name=""
                    ;;
            esac
            
            if [[ -n "$lb_name" ]]; then
                # Get load balancer DNS name from AWS
                local lb_url=$(aws elbv2 describe-load-balancers \
                    --region "$AWS_REGION" \
                    --query "LoadBalancers[?contains(LoadBalancerName, '${environment}-${lb_name}')].DNSName" \
                    --output text)
                
                if [[ -n "$lb_url" && "$lb_url" != "None" ]]; then
                    # Determine protocol based on environment (dev might use HTTP, prod uses HTTPS)
                    local protocol="https"
                    if [[ "$environment" == "dev" ]]; then
                        protocol="http"
                    fi
                    
                    service_url="${protocol}://${lb_url}"
                    log_message "Found load balancer URL for $service_name: $service_url" "DEBUG"
                else
                    log_message "Could not find load balancer for $service_name in $environment" "ERROR"
                    service_url=""
                fi
            fi
            ;;
            
        "kubernetes")
            # For Kubernetes deployments
            if command -v kubectl &> /dev/null; then
                local service_endpoint=$(kubectl get service "${service_name}" \
                    -n "${environment}" \
                    -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
                
                if [[ -n "$service_endpoint" ]]; then
                    service_url="https://${service_endpoint}"
                else
                    log_message "Could not find Kubernetes service endpoint for $service_name" "ERROR"
                    service_url=""
                fi
            else
                log_message "kubectl not found, cannot get Kubernetes service endpoints" "ERROR"
                service_url=""
            fi
            ;;
            
        *)
            log_message "Unknown environment: $environment" "ERROR"
            service_url=""
            ;;
    esac
    
    echo "$service_url"
}

# Check HTTP health endpoint
check_http_health() {
    local url="$1"
    local endpoint="${2:-/health}"
    local timeout="${3:-$HEALTH_CHECK_TIMEOUT}"
    local health_url="${url}${endpoint}"
    local result=""
    local status_code=0
    local is_healthy=false
    local details="{}"
    
    log_message "Checking health at $health_url (timeout: ${timeout}s)" "DEBUG"
    
    # Make HTTP request with curl
    result=$(curl -s -o - -w "%{http_code}" --connect-timeout "$timeout" "$health_url" 2>/dev/null)
    
    if [[ $? -ne 0 ]]; then
        log_message "Failed to connect to $health_url" "ERROR"
        echo '{"status": "unhealthy", "reason": "connection_failed", "details": {}}'
        return
    fi
    
    # Extract status code (last line) and response body
    status_code=${result: -3}
    local response_body=${result:0:${#result}-3}
    
    log_message "Received status code $status_code from $health_url" "DEBUG"
    
    if [[ "$status_code" == "200" ]]; then
        is_healthy=true
        
        # Try to parse JSON response if available
        if [[ -n "$response_body" ]]; then
            if echo "$response_body" | jq -e . >/dev/null 2>&1; then
                details="$response_body"
                
                # Check if response contains status that might indicate unhealthy components
                local service_status=$(echo "$details" | jq -r '.status // "unknown"')
                if [[ "$service_status" != "healthy" && "$service_status" != "ok" && "$service_status" != "UP" ]]; then
                    is_healthy=false
                    log_message "Service reported unhealthy status: $service_status" "ERROR"
                fi
            else
                log_message "Health endpoint returned non-JSON response" "DEBUG"
                details="{\"raw_response\": \"${response_body}\"}"
            fi
        fi
    else
        is_healthy=false
        log_message "Unhealthy status code: $status_code" "ERROR"
        details="{\"status_code\": $status_code}"
    fi
    
    if [[ "$is_healthy" == "true" ]]; then
        echo "{\"status\": \"healthy\", \"details\": $details}"
    else
        echo "{\"status\": \"unhealthy\", \"details\": $details}"
    fi
}

# Check API service health
check_api_health() {
    local environment="${1:-$ENVIRONMENT}"
    local api_url=$(get_service_url "api" "$environment")
    local is_healthy=false
    
    if [[ -z "$api_url" ]]; then
        log_message "Could not determine API URL for environment $environment" "ERROR"
        return 1
    fi
    
    log_message "Checking API health at $api_url" "INFO"
    
    # Check API health endpoint
    local health_result=$(check_http_health "$api_url" "/api/v1/health")
    local health_status=$(echo "$health_result" | jq -r '.status')
    
    if [[ "$health_status" == "healthy" ]]; then
        # Further verify critical dependencies in the health response
        local details=$(echo "$health_result" | jq -r '.details')
        
        # Check database status if available in response
        local db_status=$(echo "$details" | jq -r '.database.status // "unknown"')
        if [[ "$db_status" != "healthy" && "$db_status" != "ok" && "$db_status" != "UP" ]]; then
            log_message "Database reported unhealthy status: $db_status" "ERROR"
            is_healthy=false
        else
            # Check cache status if available
            local cache_status=$(echo "$details" | jq -r '.cache.status // "unknown"')
            if [[ "$cache_status" != "healthy" && "$cache_status" != "ok" && "$cache_status" != "UP" && "$cache_status" != "unknown" ]]; then
                log_message "Cache reported unhealthy status: $cache_status" "ERROR"
                is_healthy=false
            else
                # Check any other critical dependencies
                is_healthy=true
                log_message "API health check passed" "INFO"
            fi
        fi
    else
        local error_details=$(echo "$health_result" | jq -r '.details')
        log_message "API health check failed: $error_details" "ERROR"
        is_healthy=false
    fi
    
    if [[ "$is_healthy" == "true" ]]; then
        return 0
    else
        return 1
    fi
}

# Check frontend health
check_frontend_health() {
    local environment="${1:-$ENVIRONMENT}"
    local frontend_url=$(get_service_url "frontend" "$environment")
    local is_healthy=false
    
    if [[ -z "$frontend_url" ]]; then
        log_message "Could not determine frontend URL for environment $environment" "ERROR"
        return 1
    fi
    
    log_message "Checking frontend health at $frontend_url" "INFO"
    
    # For frontend, we just check if the main page loads
    local response=$(curl -s -o - -w "%{http_code}" --connect-timeout "$HEALTH_CHECK_TIMEOUT" "$frontend_url" 2>/dev/null)
    
    if [[ $? -ne 0 ]]; then
        log_message "Failed to connect to frontend at $frontend_url" "ERROR"
        return 1
    fi
    
    # Extract status code (last line) and response body
    local status_code=${response: -3}
    local response_body=${response:0:${#response}-3}
    
    if [[ "$status_code" == "200" ]]; then
        # Check if response contains expected HTML content
        if [[ "$response_body" == *"MoleculeFlow"* || "$response_body" == *"<html"* ]]; then
            log_message "Frontend health check passed" "INFO"
            is_healthy=true
        else
            log_message "Frontend returned 200 but content doesn't appear to be HTML" "ERROR"
            is_healthy=false
        fi
    else
        log_message "Frontend returned unhealthy status code: $status_code" "ERROR"
        is_healthy=false
    fi
    
    if [[ "$is_healthy" == "true" ]]; then
        return 0
    else
        return 1
    fi
}

# Check specific service health
check_service_health() {
    local service_name="$1"
    local environment="${2:-$ENVIRONMENT}"
    local retry_count=0
    local max_retries="$HEALTH_CHECK_RETRIES"
    local is_healthy=false
    
    log_message "Checking health of service: $service_name in $environment" "INFO"
    
    while [[ $retry_count -lt $max_retries ]]; do
        case "$service_name" in
            "api")
                if check_api_health "$environment"; then
                    is_healthy=true
                    break
                fi
                ;;
            "frontend")
                if check_frontend_health "$environment"; then
                    is_healthy=true
                    break
                fi
                ;;
            "molecule-service")
                local url=$(get_service_url "molecule-service" "$environment")
                if [[ -n "$url" ]]; then
                    local health_result=$(check_http_health "$url" "/health")
                    local health_status=$(echo "$health_result" | jq -r '.status')
                    if [[ "$health_status" == "healthy" ]]; then
                        is_healthy=true
                        break
                    fi
                fi
                ;;
            "cro-service")
                local url=$(get_service_url "cro-service" "$environment")
                if [[ -n "$url" ]]; then
                    local health_result=$(check_http_health "$url" "/health")
                    local health_status=$(echo "$health_result" | jq -r '.status')
                    if [[ "$health_status" == "healthy" ]]; then
                        is_healthy=true
                        break
                    fi
                fi
                ;;
            "document-service")
                local url=$(get_service_url "document-service" "$environment")
                if [[ -n "$url" ]]; then
                    local health_result=$(check_http_health "$url" "/health")
                    local health_status=$(echo "$health_result" | jq -r '.status')
                    if [[ "$health_status" == "healthy" ]]; then
                        is_healthy=true
                        break
                    fi
                fi
                ;;
            "worker")
                # For worker services, we might need to check different metrics
                # This could involve checking CloudWatch metrics or SQS queue status
                log_message "Worker health check not implemented yet" "ERROR"
                is_healthy=false
                break
                ;;
            *)
                log_message "Unknown service: $service_name" "ERROR"
                is_healthy=false
                break
                ;;
        esac
        
        retry_count=$((retry_count + 1))
        
        if [[ $retry_count -lt $max_retries ]]; then
            log_message "Health check failed for $service_name, retrying in $HEALTH_CHECK_INTERVAL seconds (attempt $retry_count of $max_retries)" "INFO"
            sleep "$HEALTH_CHECK_INTERVAL"
        fi
    done
    
    if [[ "$is_healthy" == "true" ]]; then
        log_message "Service $service_name is healthy" "INFO"
        return 0
    else
        log_message "Service $service_name is unhealthy after $max_retries attempts" "ERROR"
        return 1
    fi
}

# Check health of all services
check_all_services() {
    local environment="${1:-$ENVIRONMENT}"
    local all_healthy=true
    local results="{}"
    
    log_message "Checking health of all services in $environment environment" "INFO"
    
    # Check API health
    if check_api_health "$environment"; then
        results=$(echo "$results" | jq '. + {"api": "healthy"}')
    else
        results=$(echo "$results" | jq '. + {"api": "unhealthy"}')
        all_healthy=false
    fi
    
    # Check frontend health
    if check_frontend_health "$environment"; then
        results=$(echo "$results" | jq '. + {"frontend": "healthy"}')
    else
        results=$(echo "$results" | jq '. + {"frontend": "unhealthy"}')
        all_healthy=false
    fi
    
    # Check other services as needed
    # Molecule Service
    if check_service_health "molecule-service" "$environment"; then
        results=$(echo "$results" | jq '. + {"molecule-service": "healthy"}')
    else
        results=$(echo "$results" | jq '. + {"molecule-service": "unhealthy"}')
        all_healthy=false
    fi
    
    # CRO Service
    if check_service_health "cro-service" "$environment"; then
        results=$(echo "$results" | jq '. + {"cro-service": "healthy"}')
    else
        results=$(echo "$results" | jq '. + {"cro-service": "unhealthy"}')
        all_healthy=false
    fi
    
    # Document Service
    if check_service_health "document-service" "$environment"; then
        results=$(echo "$results" | jq '. + {"document-service": "healthy"}')
    else
        results=$(echo "$results" | jq '. + {"document-service": "unhealthy"}')
        all_healthy=false
    fi
    
    # Add overall status
    if [[ "$all_healthy" == "true" ]]; then
        results=$(echo "$results" | jq '. + {"overall": "healthy"}')
        log_message "All services are healthy" "INFO"
    else
        results=$(echo "$results" | jq '. + {"overall": "unhealthy"}')
        log_message "One or more services are unhealthy" "ERROR"
    fi
    
    echo "$results"
}

# Wait for a service to become healthy with timeout
wait_for_healthy() {
    local service_name="$1"
    local environment="${2:-$ENVIRONMENT}"
    local timeout_seconds="${3:-300}"  # Default 5 minutes
    local start_time=$(date +%s)
    local end_time=$((start_time + timeout_seconds))
    local is_healthy=false
    
    log_message "Waiting up to $timeout_seconds seconds for $service_name to become healthy" "INFO"
    
    while [[ $(date +%s) -lt $end_time ]]; do
        if check_service_health "$service_name" "$environment"; then
            is_healthy=true
            break
        fi
        
        local elapsed=$(($(date +%s) - start_time))
        local remaining=$((timeout_seconds - elapsed))
        
        log_message "Service $service_name still unhealthy, waiting $HEALTH_CHECK_INTERVAL seconds (${elapsed}s elapsed, ${remaining}s remaining)" "INFO"
        sleep "$HEALTH_CHECK_INTERVAL"
    done
    
    if [[ "$is_healthy" == "true" ]]; then
        log_message "Service $service_name is now healthy" "INFO"
        return 0
    else
        log_message "Timeout waiting for $service_name to become healthy (${timeout_seconds}s)" "ERROR"
        return 1
    fi
}

# Main function
main() {
    local SERVICE=""
    local WAIT=false
    local TIMEOUT=300
    
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
            --wait)
                WAIT=true
                shift
                ;;
            --timeout)
                TIMEOUT="$2"
                shift 2
                ;;
            --verbose)
                VERBOSE=true
                shift
                ;;
            *)
                log_message "Unknown option: $1" "ERROR"
                echo "Usage: $0 [--service <service_name>] [--environment <env>] [--wait] [--timeout <seconds>] [--verbose]"
                return 1
                ;;
        esac
    done
    
    # Check prerequisites
    if ! check_prerequisites; then
        return 1
    fi
    
    log_message "Health check started for environment: $ENVIRONMENT" "INFO"
    
    # If a specific service is specified
    if [[ -n "$SERVICE" ]]; then
        if [[ "$WAIT" == "true" ]]; then
            if wait_for_healthy "$SERVICE" "$ENVIRONMENT" "$TIMEOUT"; then
                log_message "Service $SERVICE is healthy" "INFO"
                return 0
            else
                log_message "Timeout waiting for $SERVICE to become healthy" "ERROR"
                return 3
            fi
        else
            if check_service_health "$SERVICE" "$ENVIRONMENT"; then
                log_message "Service $SERVICE is healthy" "INFO"
                return 0
            else
                log_message "Service $SERVICE is unhealthy" "ERROR"
                return 2
            fi
        fi
    else
        # Check all services
        local results=$(check_all_services "$ENVIRONMENT")
        local overall_status=$(echo "$results" | jq -r '.overall')
        
        echo "$results" | jq .
        
        if [[ "$overall_status" == "healthy" ]]; then
            log_message "All services are healthy" "INFO"
            return 0
        else
            log_message "One or more services are unhealthy" "ERROR"
            return 2
        fi
    fi
}

# Run main function if script is executed directly (not sourced)
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
    exit $?
fi

# Export functions for use in other scripts
export -f check_service_health
export -f check_api_health
export -f wait_for_healthy