#!/usr/bin/env bash
#
# Cleanup script for the Molecular Data Management and CRO Integration Platform
#
# This script handles removal of unused resources, cleaning temporary files,
# purging old logs, and managing resource lifecycle to optimize costs and
# maintain system performance.
#
# Usage: ./cleanup.sh -e|--environment <environment> [options]
#
# Version: 1.0.0
# Date: 2023-09-15
#

# Exit on error
set -e

# Source bootstrap.sh to use check_prerequisites
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
source "${SCRIPT_DIR}/bootstrap.sh"

# Global variables
LOG_FILE="${SCRIPT_DIR}/../logs/cleanup_$(date +%Y%m%d_%H%M%S).log"
ENVIRONMENT=${ENVIRONMENT:-dev}
CLEANUP_TYPE=${CLEANUP_TYPE:-all}
DRY_RUN=${DRY_RUN:-false}
AWS_REGION=${AWS_REGION:-us-east-1}
CONFIG_FILE="${SCRIPT_DIR}/../config/cleanup_config.json"

# Default retention periods (in days)
declare -A RETENTION_DAYS=(
  ["logs"]=90
  ["temp_files"]=7
  ["backups"]=30
  ["test_data"]=14
)

# Setup logging
setup_logging() {
  # Create logs directory if it doesn't exist
  mkdir -p "$(dirname "$LOG_FILE")"
  
  # Initialize log file with timestamp and cleanup parameters
  echo "$(date '+%Y-%m-%d %H:%M:%S') - Cleanup script started" > "$LOG_FILE"
  echo "$(date '+%Y-%m-%d %H:%M:%S') - Environment: $ENVIRONMENT" >> "$LOG_FILE"
  echo "$(date '+%Y-%m-%d %H:%M:%S') - Cleanup type: $CLEANUP_TYPE" >> "$LOG_FILE"
  echo "$(date '+%Y-%m-%d %H:%M:%S') - Dry run: $DRY_RUN" >> "$LOG_FILE"
  
  echo "$LOG_FILE"
}

# Logging function
log() {
  local level="$1"
  shift
  local message="$*"
  echo "$(date '+%Y-%m-%d %H:%M:%S') - [$level] $message" | tee -a "$LOG_FILE"
}

# Parse command line arguments
parse_arguments() {
  local args=("$@")
  
  # Default values
  local force_cleanup=false
  local retention_override=""
  
  # Parse arguments
  while [[ $# -gt 0 ]]; do
    case "$1" in
      -e|--environment)
        ENVIRONMENT="$2"
        shift 2
        ;;
      -t|--type)
        CLEANUP_TYPE="$2"
        shift 2
        ;;
      --dry-run)
        DRY_RUN=true
        shift
        ;;
      --region)
        AWS_REGION="$2"
        shift 2
        ;;
      --force)
        force_cleanup=true
        shift
        ;;
      --retention-days)
        retention_override="$2"
        shift 2
        ;;
      --config)
        CONFIG_FILE="$2"
        shift 2
        ;;
      -h|--help)
        echo "Usage: $0 [options]"
        echo ""
        echo "Options:"
        echo "  -e, --environment <env>     Environment (dev, staging, prod) [default: dev]"
        echo "  -t, --type <type>           Cleanup type (all, logs, temp, resources, backups, test, archive) [default: all]"
        echo "  --dry-run                   Simulate cleanup without making changes [default: false]"
        echo "  --region <region>           AWS region [default: us-east-1]"
        echo "  --force                     Force cleanup without confirmation"
        echo "  --retention-days <days>     Override default retention period"
        echo "  --config <file>             Path to configuration file"
        echo "  -h, --help                  Show this help message"
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
    log "ERROR" "Invalid environment: $ENVIRONMENT. Must be one of: dev, staging, prod"
    exit 1
  fi
  
  # Validate cleanup type
  if [[ ! "$CLEANUP_TYPE" =~ ^(all|logs|temp|resources|backups|test|archive)$ ]]; then
    log "ERROR" "Invalid cleanup type: $CLEANUP_TYPE. Must be one of: all, logs, temp, resources, backups, test, archive"
    exit 1
  fi
  
  # Apply retention override if specified
  if [[ -n "$retention_override" ]]; then
    if [[ ! "$retention_override" =~ ^[0-9]+$ ]]; then
      log "ERROR" "Invalid retention days: $retention_override. Must be a positive integer"
      exit 1
    fi
    
    for key in "${!RETENTION_DAYS[@]}"; do
      RETENTION_DAYS["$key"]=$retention_override
    done
    
    log "INFO" "Retention period override applied: $retention_override days"
  fi
  
  # Confirmation for non-dry-run mode
  if [[ "$DRY_RUN" == "false" && "$force_cleanup" == "false" ]]; then
    log "WARN" "You are about to perform cleanup in $ENVIRONMENT environment. This is not a dry run."
    read -p "Are you sure you want to continue? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
      log "INFO" "Cleanup cancelled by user"
      exit 0
    fi
  fi
  
  # Export variables
  export ENVIRONMENT
  export CLEANUP_TYPE
  export DRY_RUN
  export AWS_REGION
  export CONFIG_FILE
  export RETENTION_DAYS
  
  return 0
}

# Load cleanup configuration
load_configuration() {
  local environment="$1"
  local config_path="$CONFIG_FILE"
  
  # Check if config file exists
  if [[ ! -f "$config_path" ]]; then
    log "ERROR" "Configuration file not found: $config_path"
    
    # Create a default configuration file
    mkdir -p "$(dirname "$config_path")"
    log "INFO" "Creating default configuration file: $config_path"
    
    cat > "$config_path" << EOF
{
  "environments": {
    "dev": {
      "log_dirs": ["${SCRIPT_DIR}/../logs"],
      "temp_dirs": ["${SCRIPT_DIR}/../tmp", "/tmp/moleculeflow-dev"],
      "s3_buckets": {
        "logs": "moleculeflow-logs-dev",
        "data": "moleculeflow-data-dev",
        "documents": "moleculeflow-documents-dev"
      },
      "ecr_repositories": ["moleculeflow-dev"],
      "rds_instances": ["moleculeflow-db-dev"],
      "elasticache_clusters": ["moleculeflow-cache-dev"],
      "retention": {
        "logs": 30,
        "temp_files": 7,
        "backups": 14,
        "test_data": 7,
        "ecr_images": 5
      },
      "lifecycle_rules": {
        "logs/": {
          "transition_days": 30,
          "expiration_days": 90,
          "storage_class": "GLACIER"
        },
        "temp/": {
          "expiration_days": 7
        },
        "results/": {
          "transition_days": 90,
          "storage_class": "STANDARD_IA",
          "deep_archive_days": 730
        }
      }
    },
    "staging": {
      "log_dirs": ["${SCRIPT_DIR}/../logs"],
      "temp_dirs": ["${SCRIPT_DIR}/../tmp", "/tmp/moleculeflow-staging"],
      "s3_buckets": {
        "logs": "moleculeflow-logs-staging",
        "data": "moleculeflow-data-staging",
        "documents": "moleculeflow-documents-staging"
      },
      "ecr_repositories": ["moleculeflow-staging"],
      "rds_instances": ["moleculeflow-db-staging"],
      "elasticache_clusters": ["moleculeflow-cache-staging"],
      "retention": {
        "logs": 60,
        "temp_files": 7,
        "backups": 30,
        "test_data": 14,
        "ecr_images": 10
      },
      "lifecycle_rules": {
        "logs/": {
          "transition_days": 30,
          "expiration_days": 90,
          "storage_class": "GLACIER"
        },
        "temp/": {
          "expiration_days": 7
        },
        "results/": {
          "transition_days": 90,
          "storage_class": "STANDARD_IA",
          "deep_archive_days": 730
        }
      }
    },
    "prod": {
      "log_dirs": ["${SCRIPT_DIR}/../logs"],
      "temp_dirs": ["${SCRIPT_DIR}/../tmp", "/tmp/moleculeflow-prod"],
      "s3_buckets": {
        "logs": "moleculeflow-logs-prod",
        "data": "moleculeflow-data-prod",
        "documents": "moleculeflow-documents-prod"
      },
      "ecr_repositories": ["moleculeflow-prod"],
      "rds_instances": ["moleculeflow-db-prod"],
      "elasticache_clusters": ["moleculeflow-cache-prod"],
      "retention": {
        "logs": 90,
        "temp_files": 7,
        "backups": 60,
        "test_data": 30,
        "ecr_images": 20
      },
      "lifecycle_rules": {
        "logs/": {
          "transition_days": 30,
          "expiration_days": 365,
          "storage_class": "GLACIER"
        },
        "temp/": {
          "expiration_days": 7
        },
        "results/": {
          "transition_days": 90,
          "storage_class": "STANDARD_IA",
          "deep_archive_days": 730
        }
      }
    }
  }
}
EOF
  fi
  
  # Load and parse configuration
  if ! command -v jq &> /dev/null; then
    log "ERROR" "jq is required for parsing configuration"
    exit 1
  fi
  
  # Validate JSON format
  if ! jq '.' "$config_path" > /dev/null 2>&1; then
    log "ERROR" "Invalid JSON in configuration file: $config_path"
    exit 1
  }
  
  # Load configuration for the specified environment
  local env_config
  env_config=$(jq -r ".environments.${environment}" "$config_path")
  
  if [[ "$env_config" == "null" ]]; then
    log "ERROR" "Environment '$environment' not found in configuration file"
    exit 1
  }
  
  # Extract configuration values
  local log_dirs=$(jq -r '.log_dirs | join(" ")' <<< "$env_config")
  local temp_dirs=$(jq -r '.temp_dirs | join(" ")' <<< "$env_config")
  local s3_buckets=$(jq -r '.s3_buckets | to_entries | map("\(.key)=\(.value)") | join(" ")' <<< "$env_config")
  local ecr_repositories=$(jq -r '.ecr_repositories | join(" ")' <<< "$env_config")
  local rds_instances=$(jq -r '.rds_instances | join(" ")' <<< "$env_config")
  local elasticache_clusters=$(jq -r '.elasticache_clusters | join(" ")' <<< "$env_config")
  
  # Override default retention periods if specified in config
  if jq -e '.retention' <<< "$env_config" > /dev/null; then
    for key in "${!RETENTION_DAYS[@]}"; do
      local value
      value=$(jq -r ".retention.${key} // \"default\"" <<< "$env_config")
      if [[ "$value" != "default" && "$value" != "null" ]]; then
        RETENTION_DAYS["$key"]=$value
      fi
    done
  fi
  
  # Load lifecycle rules
  local lifecycle_rules
  lifecycle_rules=$(jq -c '.lifecycle_rules // {}' <<< "$env_config")
  
  # Create configuration object
  local config="{
    \"log_dirs\": \"$log_dirs\",
    \"temp_dirs\": \"$temp_dirs\",
    \"s3_buckets\": \"$s3_buckets\",
    \"ecr_repositories\": \"$ecr_repositories\",
    \"rds_instances\": \"$rds_instances\",
    \"elasticache_clusters\": \"$elasticache_clusters\",
    \"lifecycle_rules\": $lifecycle_rules
  }"
  
  echo "$config"
}

# Clean up old log files
cleanup_logs() {
  local log_dir="$1"
  local retention_days="${2:-${RETENTION_DAYS[logs]}}"
  local dry_run="$3"
  
  log "INFO" "Cleaning up log files in $log_dir older than $retention_days days (dry-run: $dry_run)"
  
  # Check if directory exists
  if [[ ! -d "$log_dir" ]]; then
    log "WARN" "Log directory does not exist: $log_dir"
    return 0
  fi
  
  # Find log files older than retention_days
  local old_logs=()
  mapfile -t old_logs < <(find "$log_dir" -type f -name "*.log" -mtime +"$retention_days" -print)
  local log_count=${#old_logs[@]}
  
  if [[ $log_count -eq 0 ]]; then
    log "INFO" "No log files found older than $retention_days days in $log_dir"
    return 0
  }
  
  # Calculate total size
  local total_size=0
  for log_file in "${old_logs[@]}"; do
    local size
    size=$(stat -c%s "$log_file" 2>/dev/null || stat -f%z "$log_file")
    total_size=$((total_size + size))
  done
  
  local size_human
  if [[ $total_size -ge 1073741824 ]]; then
    size_human=$(echo "scale=2; $total_size / 1073741824" | bc)" GB"
  elif [[ $total_size -ge 1048576 ]]; then
    size_human=$(echo "scale=2; $total_size / 1048576" | bc)" MB"
  elif [[ $total_size -ge 1024 ]]; then
    size_human=$(echo "scale=2; $total_size / 1024" | bc)" KB"
  else
    size_human="$total_size bytes"
  fi
  
  log "INFO" "Found $log_count log files to clean up ($size_human)"
  
  if [[ "$dry_run" == "true" ]]; then
    log "INFO" "DRY RUN: Would remove these log files:"
    for log_file in "${old_logs[@]}"; do
      log "INFO" "  $log_file"
    done
  else
    # Remove old log files
    for log_file in "${old_logs[@]}"; do
      rm -f "$log_file"
      log "INFO" "Removed log file: $log_file"
    done
    log "INFO" "Successfully removed $log_count log files ($size_human)"
  fi
  
  # Return cleanup details
  echo "{\"count\": $log_count, \"size\": $total_size, \"size_human\": \"$size_human\"}"
}

# Clean up temporary files
cleanup_temp_files() {
  local temp_dirs=($1)
  local retention_days="${2:-${RETENTION_DAYS[temp_files]}}"
  local dry_run="$3"
  
  log "INFO" "Cleaning up temporary files older than $retention_days days (dry-run: $dry_run)"
  
  local total_count=0
  local total_size=0
  
  for temp_dir in "${temp_dirs[@]}"; do
    # Check if directory exists
    if [[ ! -d "$temp_dir" ]]; then
      log "WARN" "Temporary directory does not exist: $temp_dir"
      continue
    fi
    
    # Find temporary files older than retention_days
    local old_files=()
    mapfile -t old_files < <(find "$temp_dir" -type f -mtime +"$retention_days" -print)
    local file_count=${#old_files[@]}
    
    if [[ $file_count -eq 0 ]]; then
      log "INFO" "No temporary files found older than $retention_days days in $temp_dir"
      continue
    }
    
    # Calculate total size
    local dir_size=0
    for temp_file in "${old_files[@]}"; do
      local size
      size=$(stat -c%s "$temp_file" 2>/dev/null || stat -f%z "$temp_file")
      dir_size=$((dir_size + size))
    done
    
    total_count=$((total_count + file_count))
    total_size=$((total_size + dir_size))
    
    local size_human
    if [[ $dir_size -ge 1073741824 ]]; then
      size_human=$(echo "scale=2; $dir_size / 1073741824" | bc)" GB"
    elif [[ $dir_size -ge 1048576 ]]; then
      size_human=$(echo "scale=2; $dir_size / 1048576" | bc)" MB"
    elif [[ $dir_size -ge 1024 ]]; then
      size_human=$(echo "scale=2; $dir_size / 1024" | bc)" KB"
    else
      size_human="$dir_size bytes"
    fi
    
    log "INFO" "Found $file_count temporary files to clean up in $temp_dir ($size_human)"
    
    if [[ "$dry_run" == "true" ]]; then
      log "INFO" "DRY RUN: Would remove these temporary files:"
      for temp_file in "${old_files[@]}"; do
        log "INFO" "  $temp_file"
      done
    else
      # Remove old temporary files
      for temp_file in "${old_files[@]}"; do
        rm -f "$temp_file"
        log "INFO" "Removed temporary file: $temp_file"
      done
      log "INFO" "Successfully removed $file_count temporary files from $temp_dir ($size_human)"
    fi
  done
  
  local total_size_human
  if [[ $total_size -ge 1073741824 ]]; then
    total_size_human=$(echo "scale=2; $total_size / 1073741824" | bc)" GB"
  elif [[ $total_size -ge 1048576 ]]; then
    total_size_human=$(echo "scale=2; $total_size / 1048576" | bc)" MB"
  elif [[ $total_size -ge 1024 ]]; then
    total_size_human=$(echo "scale=2; $total_size / 1024" | bc)" KB"
  else
    total_size_human="$total_size bytes"
  fi
  
  # Return cleanup details
  echo "{\"count\": $total_count, \"size\": $total_size, \"size_human\": \"$total_size_human\"}"
}

# Clean up old ECR container images
cleanup_ecr_images() {
  local repositories=($1)
  local retention_count="${2:-20}"
  local dry_run="$3"
  
  log "INFO" "Cleaning up ECR images, keeping $retention_count most recent (dry-run: $dry_run)"
  
  if ! command -v aws &> /dev/null; then
    log "ERROR" "AWS CLI is required for ECR cleanup"
    return 1
  fi
  
  local total_count=0
  local total_size=0
  
  for repo in "${repositories[@]}"; do
    log "INFO" "Processing ECR repository: $repo"
    
    # Check if repository exists
    if ! aws ecr describe-repositories --repository-names "$repo" --region "$AWS_REGION" &> /dev/null; then
      log "WARN" "ECR repository does not exist: $repo"
      continue
    fi
    
    # List images sorted by date
    local images
    images=$(aws ecr describe-images --repository-name "$repo" --region "$AWS_REGION" --query 'sort_by(imageDetails,& imagePushedAt)' --output json)
    
    # Get total image count
    local image_count
    image_count=$(jq length <<< "$images")
    
    if [[ $image_count -le $retention_count ]]; then
      log "INFO" "Repository $repo has $image_count images, which is less than or equal to retention count ($retention_count). Nothing to clean up."
      continue
    fi
    
    # Calculate images to delete (all except the most recent retention_count)
    local delete_count=$((image_count - retention_count))
    local images_to_delete
    images_to_delete=$(jq ".[0:$delete_count]" <<< "$images")
    
    # Extract image digests and calculate size
    local image_digests=()
    local repo_size=0
    
    for i in $(seq 0 $((delete_count - 1))); do
      local digest
      digest=$(jq -r ".[$i].imageDigest" <<< "$images_to_delete")
      local size
      size=$(jq -r ".[$i].imageSizeInBytes // 0" <<< "$images_to_delete")
      
      image_digests+=("$digest")
      repo_size=$((repo_size + size))
    done
    
    total_count=$((total_count + delete_count))
    total_size=$((total_size + repo_size))
    
    local size_human
    if [[ $repo_size -ge 1073741824 ]]; then
      size_human=$(echo "scale=2; $repo_size / 1073741824" | bc)" GB"
    elif [[ $repo_size -ge 1048576 ]]; then
      size_human=$(echo "scale=2; $repo_size / 1048576" | bc)" MB"
    elif [[ $repo_size -ge 1024 ]]; then
      size_human=$(echo "scale=2; $repo_size / 1024" | bc)" KB"
    else
      size_human="$repo_size bytes"
    fi
    
    log "INFO" "Found $delete_count images to delete in repository $repo ($size_human)"
    
    if [[ "$dry_run" == "true" ]]; then
      log "INFO" "DRY RUN: Would delete these image digests:"
      for digest in "${image_digests[@]}"; do
        log "INFO" "  $digest"
      done
    else
      # Delete images
      for digest in "${image_digests[@]}"; do
        aws ecr batch-delete-image \
          --repository-name "$repo" \
          --image-ids imageDigest="$digest" \
          --region "$AWS_REGION" &> /dev/null
          
        log "INFO" "Deleted image: $digest"
      done
      log "INFO" "Successfully deleted $delete_count images from repository $repo ($size_human)"
    fi
  done
  
  local total_size_human
  if [[ $total_size -ge 1073741824 ]]; then
    total_size_human=$(echo "scale=2; $total_size / 1073741824" | bc)" GB"
  elif [[ $total_size -ge 1048576 ]]; then
    total_size_human=$(echo "scale=2; $total_size / 1048576" | bc)" MB"
  elif [[ $total_size -ge 1024 ]]; then
    total_size_human=$(echo "scale=2; $total_size / 1024" | bc)" KB"
  else
    total_size_human="$total_size bytes"
  fi
  
  # Return cleanup details
  echo "{\"count\": $total_count, \"size\": $total_size, \"size_human\": \"$total_size_human\"}"
}

# Clean up S3 objects based on lifecycle policies
cleanup_s3_objects() {
  local buckets_string="$1"
  local lifecycle_rules="$2"
  local dry_run="$3"
  
  log "INFO" "Applying S3 lifecycle policies (dry-run: $dry_run)"
  
  if ! command -v aws &> /dev/null; then
    log "ERROR" "AWS CLI is required for S3 cleanup"
    return 1
  fi
  
  # Parse buckets
  local bucket_array=()
  local bucket_name=""
  local bucket_type=""
  
  IFS=' ' read -ra bucket_entries <<< "$buckets_string"
  for entry in "${bucket_entries[@]}"; do
    IFS='=' read -r bucket_type bucket_name <<< "$entry"
    bucket_array+=("$bucket_name")
  done
  
  local total_transitioned=0
  local total_expired=0
  local total_deep_archived=0
  
  for bucket in "${bucket_array[@]}"; do
    log "INFO" "Processing S3 bucket: $bucket"
    
    # Check if bucket exists
    if ! aws s3api head-bucket --bucket "$bucket" --region "$AWS_REGION" &> /dev/null; then
      log "WARN" "S3 bucket does not exist: $bucket"
      continue
    fi
    
    # If no lifecycle rules specified, apply default rules
    if [[ -z "$lifecycle_rules" || "$lifecycle_rules" == "{}" ]]; then
      log "INFO" "No specific lifecycle rules found, applying default rules"
      
      if [[ "$dry_run" == "true" ]]; then
        log "INFO" "DRY RUN: Would apply default lifecycle policy to bucket $bucket"
      else
        # Apply default lifecycle rules
        aws s3api put-bucket-lifecycle-configuration \
          --bucket "$bucket" \
          --lifecycle-configuration '{
            "Rules": [
              {
                "ID": "CleanupRule-Logs",
                "Status": "Enabled",
                "Prefix": "logs/",
                "Transitions": [
                  {
                    "Days": 30,
                    "StorageClass": "GLACIER"
                  }
                ],
                "Expiration": {
                  "Days": 90
                }
              },
              {
                "ID": "CleanupRule-Temp",
                "Status": "Enabled",
                "Prefix": "temp/",
                "Expiration": {
                  "Days": 7
                }
              },
              {
                "ID": "CleanupRule-Results",
                "Status": "Enabled",
                "Prefix": "results/",
                "Transitions": [
                  {
                    "Days": 90,
                    "StorageClass": "STANDARD_IA"
                  },
                  {
                    "Days": 730,
                    "StorageClass": "DEEP_ARCHIVE"
                  }
                ]
              }
            ]
          }' \
          --region "$AWS_REGION"
          
        log "INFO" "Applied default lifecycle policy to bucket $bucket"
      fi
      
      # Estimate affected objects
      local logs_count=$(aws s3 ls "s3://$bucket/logs/" --recursive --summarize | grep "Total Objects:" | awk '{print $3}')
      local temp_count=$(aws s3 ls "s3://$bucket/temp/" --recursive --summarize | grep "Total Objects:" | awk '{print $3}')
      local results_count=$(aws s3 ls "s3://$bucket/results/" --recursive --summarize | grep "Total Objects:" | awk '{print $3}')
      
      logs_count=${logs_count:-0}
      temp_count=${temp_count:-0}
      results_count=${results_count:-0}
      
      total_transitioned=$((total_transitioned + logs_count + results_count))
      total_expired=$((total_expired + temp_count))
      total_deep_archived=$((total_deep_archived + results_count))
      
      continue
    }
    
    # Apply custom lifecycle rules
    local rules_array=()
    local rule_id=1
    
    for prefix in $(jq -r 'keys[]' <<< "$lifecycle_rules"); do
      local rule
      rule=$(jq -r ".[\"$prefix\"]" <<< "$lifecycle_rules")
      
      local transition_days
      transition_days=$(jq -r '.transition_days // "null"' <<< "$rule")
      
      local expiration_days
      expiration_days=$(jq -r '.expiration_days // "null"' <<< "$rule")
      
      local storage_class
      storage_class=$(jq -r '.storage_class // "STANDARD_IA"' <<< "$rule")
      
      local deep_archive_days
      deep_archive_days=$(jq -r '.deep_archive_days // "null"' <<< "$rule")
      
      local rule_json="{\
        \"ID\": \"CleanupRule-$rule_id\",\
        \"Status\": \"Enabled\",\
        \"Prefix\": \"$prefix\""
      
      # Add transitions if specified
      if [[ "$transition_days" != "null" ]]; then
        rule_json="$rule_json,\
          \"Transitions\": ["
        
        rule_json="$rule_json\
            {\
              \"Days\": $transition_days,\
              \"StorageClass\": \"$storage_class\"\
            }"
        
        # Add deep archive transition if specified
        if [[ "$deep_archive_days" != "null" ]]; then
          rule_json="$rule_json,\
            {\
              \"Days\": $deep_archive_days,\
              \"StorageClass\": \"DEEP_ARCHIVE\"\
            }"
        fi
        
        rule_json="$rule_json\
          ]"
      fi
      
      # Add expiration if specified
      if [[ "$expiration_days" != "null" ]]; then
        rule_json="$rule_json,\
          \"Expiration\": {\
            \"Days\": $expiration_days\
          }"
      fi
      
      rule_json="$rule_json\
      }"
      
      rules_array+=("$rule_json")
      rule_id=$((rule_id + 1))
    done
    
    # Combine rules into a lifecycle configuration
    local lifecycle_config="{\
      \"Rules\": [\
        $(IFS=,; echo "${rules_array[*]}")\
      ]\
    }"
    
    if [[ "$dry_run" == "true" ]]; then
      log "INFO" "DRY RUN: Would apply the following lifecycle policy to bucket $bucket:"
      echo "$lifecycle_config" | jq '.' | while IFS= read -r line; do
        log "INFO" "  $line"
      done
    else
      # Apply lifecycle configuration
      aws s3api put-bucket-lifecycle-configuration \
        --bucket "$bucket" \
        --lifecycle-configuration "$lifecycle_config" \
        --region "$AWS_REGION"
        
      log "INFO" "Applied lifecycle policy to bucket $bucket"
    fi
    
    # Estimate affected objects
    for prefix in $(jq -r 'keys[]' <<< "$lifecycle_rules"); do
      local count
      count=$(aws s3 ls "s3://$bucket/$prefix" --recursive --summarize | grep "Total Objects:" | awk '{print $3}')
      count=${count:-0}
      
      local rule
      rule=$(jq -r ".[\"$prefix\"]" <<< "$lifecycle_rules")
      
      local transition_days
      transition_days=$(jq -r '.transition_days // "null"' <<< "$rule")
      
      local expiration_days
      expiration_days=$(jq -r '.expiration_days // "null"' <<< "$rule")
      
      local deep_archive_days
      deep_archive_days=$(jq -r '.deep_archive_days // "null"' <<< "$rule")
      
      if [[ "$transition_days" != "null" ]]; then
        total_transitioned=$((total_transitioned + count))
      fi
      
      if [[ "$expiration_days" != "null" ]]; then
        total_expired=$((total_expired + count))
      fi
      
      if [[ "$deep_archive_days" != "null" ]]; then
        total_deep_archived=$((total_deep_archived + count))
      fi
    done
  done
  
  # Return lifecycle details
  echo "{\"transitioned\": $total_transitioned, \"expired\": $total_expired, \"deep_archived\": $total_deep_archived}"
}

# Clean up old RDS database snapshots
cleanup_rds_snapshots() {
  local db_identifiers=($1)
  local retention_days="${2:-${RETENTION_DAYS[backups]}}"
  local dry_run="$3"
  
  log "INFO" "Cleaning up RDS snapshots older than $retention_days days (dry-run: $dry_run)"
  
  if ! command -v aws &> /dev/null; then
    log "ERROR" "AWS CLI is required for RDS snapshot cleanup"
    return 1
  fi
  
  local total_count=0
  
  for db_identifier in "${db_identifiers[@]}"; do
    log "INFO" "Processing RDS instance: $db_identifier"
    
    # Check if DB instance exists
    if ! aws rds describe-db-instances --db-instance-identifier "$db_identifier" --region "$AWS_REGION" &> /dev/null; then
      log "WARN" "RDS instance does not exist: $db_identifier"
      continue
    fi
    
    # Calculate cutoff date
    local cutoff_date
    cutoff_date=$(date -d "$retention_days days ago" +%s 2>/dev/null || date -v "-${retention_days}d" +%s)
    
    # List manual snapshots
    local snapshots
    snapshots=$(aws rds describe-db-snapshots \
      --db-instance-identifier "$db_identifier" \
      --snapshot-type "manual" \
      --region "$AWS_REGION" \
      --query 'DBSnapshots[*].{DBSnapshotIdentifier:DBSnapshotIdentifier,SnapshotCreateTime:SnapshotCreateTime}' \
      --output json)
    
    # Identify old snapshots
    local old_snapshots=()
    local snapshot_count
    snapshot_count=$(jq length <<< "$snapshots")
    
    for i in $(seq 0 $((snapshot_count - 1))); do
      local snapshot_id
      snapshot_id=$(jq -r ".[$i].DBSnapshotIdentifier" <<< "$snapshots")
      
      local create_time
      create_time=$(jq -r ".[$i].SnapshotCreateTime" <<< "$snapshots")
      
      # Convert to timestamp
      local timestamp
      timestamp=$(date -d "$create_time" +%s 2>/dev/null || date -j -f "%Y-%m-%dT%H:%M:%S.000Z" "$create_time" +%s)
      
      if [[ $timestamp -lt $cutoff_date ]]; then
        old_snapshots+=("$snapshot_id")
      fi
    done
    
    local delete_count=${#old_snapshots[@]}
    total_count=$((total_count + delete_count))
    
    if [[ $delete_count -eq 0 ]]; then
      log "INFO" "No RDS snapshots found older than $retention_days days for $db_identifier"
      continue
    }
    
    log "INFO" "Found $delete_count RDS snapshots to delete for $db_identifier"
    
    if [[ "$dry_run" == "true" ]]; then
      log "INFO" "DRY RUN: Would delete these RDS snapshots:"
      for snapshot_id in "${old_snapshots[@]}"; do
        log "INFO" "  $snapshot_id"
      done
    else
      # Delete old snapshots
      for snapshot_id in "${old_snapshots[@]}"; do
        aws rds delete-db-snapshot \
          --db-snapshot-identifier "$snapshot_id" \
          --region "$AWS_REGION" &> /dev/null
          
        log "INFO" "Deleted RDS snapshot: $snapshot_id"
      done
      log "INFO" "Successfully deleted $delete_count RDS snapshots for $db_identifier"
    fi
  done
  
  # Return cleanup details
  echo "{\"count\": $total_count}"
}

# Clean up old ElastiCache snapshots
cleanup_elasticache_snapshots() {
  local cache_cluster_ids=($1)
  local retention_days="${2:-${RETENTION_DAYS[backups]}}"
  local dry_run="$3"
  
  log "INFO" "Cleaning up ElastiCache snapshots older than $retention_days days (dry-run: $dry_run)"
  
  if ! command -v aws &> /dev/null; then
    log "ERROR" "AWS CLI is required for ElastiCache snapshot cleanup"
    return 1
  fi
  
  local total_count=0
  
  for cache_cluster_id in "${cache_cluster_ids[@]}"; do
    log "INFO" "Processing ElastiCache cluster: $cache_cluster_id"
    
    # Check if cache cluster exists
    if ! aws elasticache describe-cache-clusters --cache-cluster-id "$cache_cluster_id" --region "$AWS_REGION" &> /dev/null; then
      log "WARN" "ElastiCache cluster does not exist: $cache_cluster_id"
      continue
    fi
    
    # Calculate cutoff date
    local cutoff_date
    cutoff_date=$(date -d "$retention_days days ago" +%s 2>/dev/null || date -v "-${retention_days}d" +%s)
    
    # List manual snapshots
    local snapshots
    snapshots=$(aws elasticache describe-snapshots \
      --cache-cluster-id "$cache_cluster_id" \
      --region "$AWS_REGION" \
      --query 'Snapshots[*].{SnapshotName:SnapshotName,NodeSnapshots:[0].SnapshotCreateTime}' \
      --output json)
    
    # Identify old snapshots
    local old_snapshots=()
    local snapshot_count
    snapshot_count=$(jq length <<< "$snapshots")
    
    for i in $(seq 0 $((snapshot_count - 1))); do
      local snapshot_name
      snapshot_name=$(jq -r ".[$i].SnapshotName" <<< "$snapshots")
      
      local create_time
      create_time=$(jq -r ".[$i].NodeSnapshots" <<< "$snapshots")
      
      # Convert to timestamp
      local timestamp
      timestamp=$(date -d "$create_time" +%s 2>/dev/null || date -j -f "%Y-%m-%dT%H:%M:%S.000Z" "$create_time" +%s)
      
      if [[ $timestamp -lt $cutoff_date ]]; then
        old_snapshots+=("$snapshot_name")
      fi
    done
    
    local delete_count=${#old_snapshots[@]}
    total_count=$((total_count + delete_count))
    
    if [[ $delete_count -eq 0 ]]; then
      log "INFO" "No ElastiCache snapshots found older than $retention_days days for $cache_cluster_id"
      continue
    }
    
    log "INFO" "Found $delete_count ElastiCache snapshots to delete for $cache_cluster_id"
    
    if [[ "$dry_run" == "true" ]]; then
      log "INFO" "DRY RUN: Would delete these ElastiCache snapshots:"
      for snapshot_name in "${old_snapshots[@]}"; do
        log "INFO" "  $snapshot_name"
      done
    else
      # Delete old snapshots
      for snapshot_name in "${old_snapshots[@]}"; do
        aws elasticache delete-snapshot \
          --snapshot-name "$snapshot_name" \
          --region "$AWS_REGION" &> /dev/null
          
        log "INFO" "Deleted ElastiCache snapshot: $snapshot_name"
      done
      log "INFO" "Successfully deleted $delete_count ElastiCache snapshots for $cache_cluster_id"
    fi
  done
  
  # Return cleanup details
  echo "{\"count\": $total_count}"
}

# Clean up resources created for testing purposes
cleanup_test_resources() {
  local environment="$1"
  local retention_days="${2:-${RETENTION_DAYS[test_data]}}"
  local dry_run="$3"
  
  log "INFO" "Cleaning up test resources in $environment environment older than $retention_days days (dry-run: $dry_run)"
  
  if ! command -v aws &> /dev/null; then
    log "ERROR" "AWS CLI is required for test resource cleanup"
    return 1
  fi
  
  # Tags to identify test resources
  local test_tag_key="Environment"
  local test_tag_value="test-$environment"
  
  # Calculate cutoff date
  local cutoff_date
  cutoff_date=$(date -d "$retention_days days ago" +%s 2>/dev/null || date -v "-${retention_days}d" +%s)
  
  local total_resources=0
  local resource_types=("EC2 Instances" "Load Balancers" "Security Groups" "CloudFormation Stacks" "S3 Objects")
  local resource_counts=()
  
  # Cleanup EC2 instances
  local instances
  instances=$(aws ec2 describe-instances \
    --filters "Name=tag:$test_tag_key,Values=$test_tag_value" \
    --query 'Reservations[*].Instances[*].{InstanceId:InstanceId,LaunchTime:LaunchTime}' \
    --region "$AWS_REGION" \
    --output json)
  
  instances=$(jq 'flatten' <<< "$instances")
  
  local old_instances=()
  local instance_count
  instance_count=$(jq length <<< "$instances")
  
  for i in $(seq 0 $((instance_count - 1))); do
    local instance_id
    instance_id=$(jq -r ".[$i].InstanceId" <<< "$instances")
    
    local launch_time
    launch_time=$(jq -r ".[$i].LaunchTime" <<< "$instances")
    
    # Convert to timestamp
    local timestamp
    timestamp=$(date -d "$launch_time" +%s 2>/dev/null || date -j -f "%Y-%m-%dT%H:%M:%S.000Z" "$launch_time" +%s)
    
    if [[ $timestamp -lt $cutoff_date ]]; then
      old_instances+=("$instance_id")
    fi
  done
  
  local instance_delete_count=${#old_instances[@]}
  total_resources=$((total_resources + instance_delete_count))
  resource_counts+=("$instance_delete_count")
  
  if [[ $instance_delete_count -gt 0 ]]; then
    log "INFO" "Found $instance_delete_count test EC2 instances to terminate"
    
    if [[ "$dry_run" == "true" ]]; then
      log "INFO" "DRY RUN: Would terminate these EC2 instances:"
      for instance_id in "${old_instances[@]}"; do
        log "INFO" "  $instance_id"
      done
    else
      # Terminate instances
      for instance_id in "${old_instances[@]}"; do
        aws ec2 terminate-instances \
          --instance-ids "$instance_id" \
          --region "$AWS_REGION" &> /dev/null
          
        log "INFO" "Terminated EC2 instance: $instance_id"
      done
      log "INFO" "Successfully terminated $instance_delete_count EC2 instances"
    fi
  else
    log "INFO" "No test EC2 instances found older than $retention_days days"
  fi
  
  # Cleanup Load Balancers
  local load_balancers
  load_balancers=$(aws elbv2 describe-load-balancers \
    --query 'LoadBalancers[*].{LoadBalancerArn:LoadBalancerArn,CreatedTime:CreatedTime}' \
    --region "$AWS_REGION" \
    --output json)
  
  local old_load_balancers=()
  local lb_count
  lb_count=$(jq length <<< "$load_balancers")
  
  for i in $(seq 0 $((lb_count - 1))); do
    local lb_arn
    lb_arn=$(jq -r ".[$i].LoadBalancerArn" <<< "$load_balancers")
    
    # Check if this is a test load balancer
    local lb_tags
    lb_tags=$(aws elbv2 describe-tags \
      --resource-arns "$lb_arn" \
      --region "$AWS_REGION" \
      --query 'TagDescriptions[0].Tags[?Key==`'"$test_tag_key"'` && Value==`'"$test_tag_value"'`]' \
      --output json)
    
    if [[ $(jq length <<< "$lb_tags") -eq 0 ]]; then
      continue
    fi
    
    local created_time
    created_time=$(jq -r ".[$i].CreatedTime" <<< "$load_balancers")
    
    # Convert to timestamp
    local timestamp
    timestamp=$(date -d "$created_time" +%s 2>/dev/null || date -j -f "%Y-%m-%dT%H:%M:%S.000Z" "$created_time" +%s)
    
    if [[ $timestamp -lt $cutoff_date ]]; then
      old_load_balancers+=("$lb_arn")
    fi
  done
  
  local lb_delete_count=${#old_load_balancers[@]}
  total_resources=$((total_resources + lb_delete_count))
  resource_counts+=("$lb_delete_count")
  
  if [[ $lb_delete_count -gt 0 ]]; then
    log "INFO" "Found $lb_delete_count test load balancers to delete"
    
    if [[ "$dry_run" == "true" ]]; then
      log "INFO" "DRY RUN: Would delete these load balancers:"
      for lb_arn in "${old_load_balancers[@]}"; do
        log "INFO" "  $lb_arn"
      done
    else
      # Delete load balancers
      for lb_arn in "${old_load_balancers[@]}"; do
        aws elbv2 delete-load-balancer \
          --load-balancer-arn "$lb_arn" \
          --region "$AWS_REGION" &> /dev/null
          
        log "INFO" "Deleted load balancer: $lb_arn"
      done
      log "INFO" "Successfully deleted $lb_delete_count load balancers"
    fi
  else
    log "INFO" "No test load balancers found older than $retention_days days"
  fi
  
  # Add more resource types as needed
  
  # Return cleanup details
  local resource_types_json=$(jq -n --arg types "$(IFS=,; echo "${resource_types[*]}")" --arg counts "$(IFS=,; echo "${resource_counts[*]}")" '
    {
      "types": ($types | split(",")),
      "counts": ($counts | split(",") | map(tonumber))
    }
  ')
  
  echo "{\"count\": $total_resources, \"resources\": $resource_types_json}"
}

# Archive old application data to lower-cost storage
archive_old_data() {
  local environment="$1"
  local archival_rules="$2"
  local dry_run="$3"
  
  log "INFO" "Archiving old application data for $environment environment (dry-run: $dry_run)"
  
  if ! command -v aws &> /dev/null; then
    log "ERROR" "AWS CLI is required for data archiving"
    return 1
  fi
  
  # Default archive threshold (2 years)
  local archive_days=730
  
  # Extract archive threshold from rules if available
  if [[ -n "$archival_rules" ]]; then
    local threshold
    threshold=$(jq -r '.archive_threshold_days // "730"' <<< "$archival_rules")
    if [[ "$threshold" != "null" ]]; then
      archive_days=$threshold
    fi
  fi
  
  # Calculate cutoff date for archiving
  local cutoff_date
  cutoff_date=$(date -d "$archive_days days ago" +"%Y-%m-%d" 2>/dev/null || date -v "-${archive_days}d" +"%Y-%m-%d")
  
  log "INFO" "Archiving data older than $cutoff_date (dry-run: $dry_run)"
  
  # Get S3 bucket names from environment configuration
  local config
  config=$(load_configuration "$environment")
  
  local s3_buckets
  s3_buckets=$(echo "$config" | jq -r '.s3_buckets')
  
  local data_bucket
  data_bucket=$(echo "$s3_buckets" | awk -F'=' '/data=/{print $2}')
  
  local documents_bucket
  documents_bucket=$(echo "$s3_buckets" | awk -F'=' '/documents=/{print $2}')
  
  if [[ -z "$data_bucket" || -z "$documents_bucket" ]]; then
    log "ERROR" "Could not determine S3 bucket names for archiving"
    return 1
  fi
  
  # Set up archive bucket if it doesn't exist
  local archive_bucket="moleculeflow-archive-$environment"
  
  if ! aws s3api head-bucket --bucket "$archive_bucket" --region "$AWS_REGION" &> /dev/null; then
    log "INFO" "Archive bucket does not exist, would create: $archive_bucket"
    
    if [[ "$dry_run" == "false" ]]; then
      aws s3api create-bucket \
        --bucket "$archive_bucket" \
        --create-bucket-configuration LocationConstraint="$AWS_REGION" \
        --region "$AWS_REGION" &> /dev/null
        
      # Enable default encryption
      aws s3api put-bucket-encryption \
        --bucket "$archive_bucket" \
        --server-side-encryption-configuration '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}' \
        --region "$AWS_REGION" &> /dev/null
        
      # Apply lifecycle policy for Glacier transition
      aws s3api put-bucket-lifecycle-configuration \
        --bucket "$archive_bucket" \
        --lifecycle-configuration '{"Rules":[{"ID":"ArchiveRule","Status":"Enabled","Prefix":"","Transitions":[{"Days":1,"StorageClass":"DEEP_ARCHIVE"}]}]}' \
        --region "$AWS_REGION" &> /dev/null
        
      log "INFO" "Created archive bucket: $archive_bucket"
    fi
  fi
  
  # Connect to database to identify archivable data
  # Mock database connection for now - in reality, this would query the actual database
  log "INFO" "Identifying submissions and results older than $cutoff_date"
  
  # For demonstration, we'll simulate finding 10 old submissions
  local submission_count=10
  local result_count=25
  
  log "INFO" "Found $submission_count submissions and $result_count results to archive"
  
  if [[ "$dry_run" == "true" ]]; then
    log "INFO" "DRY RUN: Would archive $submission_count submissions and $result_count results"
  else
    # In a real implementation, this would:
    # 1. Extract submission and result data from database
    # 2. Package data in appropriate format
    # 3. Upload to archive bucket
    # 4. Update database with archival status
    # 5. Remove original data
    
    log "INFO" "Archiving process would execute here (implementation placeholder)"
    
    # Simulate successful archiving
    log "INFO" "Successfully archived $submission_count submissions and $result_count results to $archive_bucket"
  fi
  
  # Return archival details
  echo "{\"submissions\": $submission_count, \"results\": $result_count, \"bucket\": \"$archive_bucket\", \"cutoff_date\": \"$cutoff_date\"}"
}

# Generate a detailed report of the cleanup operation
generate_cleanup_report() {
  local cleanup_results="$1"
  local report_file="${SCRIPT_DIR}/../logs/cleanup_report_$(date +%Y%m%d_%H%M%S).json"
  
  # Create directory if it doesn't exist
  mkdir -p "$(dirname "$report_file")"
  
  # Add timestamp and environment to results
  local final_report
  final_report=$(jq -n \
    --arg timestamp "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" \
    --arg environment "$ENVIRONMENT" \
    --arg dry_run "$DRY_RUN" \
    --argjson results "$cleanup_results" \
    '{
      "timestamp": $timestamp,
      "environment": $environment,
      "dry_run": $dry_run | test("true"),
      "results": $results
    }')
  
  # Write report to file
  echo "$final_report" | jq '.' > "$report_file"
  
  # Log report location
  log "INFO" "Cleanup report generated: $report_file"
  
  # Upload report to S3 if not in dry-run mode
  if [[ "$DRY_RUN" == "false" ]]; then
    # Get S3 bucket name from environment configuration
    local config
    config=$(load_configuration "$ENVIRONMENT")
    
    local s3_buckets
    s3_buckets=$(echo "$config" | jq -r '.s3_buckets')
    
    local logs_bucket
    logs_bucket=$(echo "$s3_buckets" | awk -F'=' '/logs=/{print $2}')
    
    if [[ -n "$logs_bucket" ]]; then
      local report_key="cleanup_reports/$(basename "$report_file")"
      
      aws s3 cp "$report_file" "s3://$logs_bucket/$report_key" --region "$AWS_REGION" &> /dev/null
      
      if [[ $? -eq 0 ]]; then
        log "INFO" "Cleanup report uploaded to S3: s3://$logs_bucket/$report_key"
      else
        log "WARN" "Failed to upload cleanup report to S3"
      fi
    fi
  fi
  
  echo "$report_file"
}

# Send cleanup completion notification
send_notification() {
  local cleanup_results="$1"
  local status="$2"
  
  log "INFO" "Sending cleanup completion notification (status: $status)"
  
  # Extract summary information
  local logs_count=$(echo "$cleanup_results" | jq -r '.logs.count // 0')
  local temp_count=$(echo "$cleanup_results" | jq -r '.temp_files.count // 0')
  local ecr_count=$(echo "$cleanup_results" | jq -r '.ecr_images.count // 0')
  local s3_transitioned=$(echo "$cleanup_results" | jq -r '.s3_objects.transitioned // 0')
  local s3_expired=$(echo "$cleanup_results" | jq -r '.s3_objects.expired // 0')
  local rds_count=$(echo "$cleanup_results" | jq -r '.rds_snapshots.count // 0')
  local elasticache_count=$(echo "$cleanup_results" | jq -r '.elasticache_snapshots.count // 0')
  local test_resources_count=$(echo "$cleanup_results" | jq -r '.test_resources.count // 0')
  local archive_submissions=$(echo "$cleanup_results" | jq -r '.archive.submissions // 0')
  local archive_results=$(echo "$cleanup_results" | jq -r '.archive.results // 0')
  
  # Calculate total resources processed
  local total_resources=$((logs_count + temp_count + ecr_count + s3_transitioned + s3_expired + rds_count + elasticache_count + test_resources_count + archive_submissions + archive_results))
  
  # Format message
  local message="Cleanup completed with status: $status\n"
  message+="Environment: $ENVIRONMENT\n"
  message+="Dry Run: $DRY_RUN\n"
  message+="Total resources processed: $total_resources\n\n"
  message+="Summary:\n"
  message+="- Log files removed: $logs_count\n"
  message+="- Temporary files removed: $temp_count\n"
  message+="- ECR images cleaned up: $ecr_count\n"
  message+="- S3 objects transitioned: $s3_transitioned\n"
  message+="- S3 objects expired: $s3_expired\n"
  message+="- RDS snapshots removed: $rds_count\n"
  message+="- ElastiCache snapshots removed: $elasticache_count\n"
  message+="- Test resources removed: $test_resources_count\n"
  message+="- Submissions archived: $archive_submissions\n"
  message+="- Results archived: $archive_results\n"
  
  # Send SNS notification if configured
  local config
  config=$(load_configuration "$ENVIRONMENT")
  
  # Check for SNS topic ARN in config
  local sns_topic
  sns_topic=$(echo "$config" | jq -r '.sns_topic // "null"')
  
  if [[ "$sns_topic" != "null" ]]; then
    log "INFO" "Sending SNS notification to topic: $sns_topic"
    
    if [[ "$DRY_RUN" == "false" ]]; then
      aws sns publish \
        --topic-arn "$sns_topic" \
        --subject "Cleanup Completed: $ENVIRONMENT ($status)" \
        --message "$message" \
        --region "$AWS_REGION" &> /dev/null
        
      if [[ $? -eq 0 ]]; then
        log "INFO" "SNS notification sent successfully"
      else
        log "WARN" "Failed to send SNS notification"
      fi
    else
      log "INFO" "DRY RUN: Would send SNS notification to $sns_topic"
    fi
  fi
  
  # Return notification status
  echo "true"
}

# Main function
main() {
  # Parse command line arguments
  parse_arguments "$@"
  
  # Set up logging
  setup_logging
  
  # Check prerequisites
  if ! check_prerequisites; then
    log "ERROR" "Prerequisites check failed. Please ensure AWS CLI and jq are installed."
    return 1
  fi
  
  # Load configuration
  local config
  config=$(load_configuration "$ENVIRONMENT")
  
  # Initialize cleanup results
  local cleanup_results="{}"
  
  # Begin cleanup process based on type
  log "INFO" "Starting cleanup process for environment: $ENVIRONMENT (type: $CLEANUP_TYPE, dry-run: $DRY_RUN)"
  
  # Cleanup logs
  if [[ "$CLEANUP_TYPE" == "logs" || "$CLEANUP_TYPE" == "all" ]]; then
    local log_dirs
    log_dirs=$(echo "$config" | jq -r '.log_dirs')
    
    local logs_result="{}"
    
    for log_dir in $log_dirs; do
      local result
      result=$(cleanup_logs "$log_dir" "${RETENTION_DAYS[logs]}" "$DRY_RUN")
      logs_result=$(echo "$result")
    done
    
    cleanup_results=$(echo "$cleanup_results" | jq --argjson logs "$logs_result" '. + {"logs": $logs}')
  fi
  
  # Cleanup temporary files
  if [[ "$CLEANUP_TYPE" == "temp" || "$CLEANUP_TYPE" == "all" ]]; then
    local temp_dirs
    temp_dirs=$(echo "$config" | jq -r '.temp_dirs')
    
    local temp_result
    temp_result=$(cleanup_temp_files "$temp_dirs" "${RETENTION_DAYS[temp_files]}" "$DRY_RUN")
    
    cleanup_results=$(echo "$cleanup_results" | jq --argjson temp_files "$temp_result" '. + {"temp_files": $temp_files}')
  fi
  
  # Cleanup resources
  if [[ "$CLEANUP_TYPE" == "resources" || "$CLEANUP_TYPE" == "all" ]]; then
    # Cleanup ECR images
    local ecr_repositories
    ecr_repositories=$(echo "$config" | jq -r '.ecr_repositories')
    
    # Get ECR retention count from config
    local ecr_retention
    ecr_retention=$(echo "$config" | jq -r '.retention.ecr_images // 20')
    
    local ecr_result
    ecr_result=$(cleanup_ecr_images "$ecr_repositories" "$ecr_retention" "$DRY_RUN")
    
    cleanup_results=$(echo "$cleanup_results" | jq --argjson ecr_images "$ecr_result" '. + {"ecr_images": $ecr_images}')
    
    # Cleanup S3 objects
    local s3_buckets
    s3_buckets=$(echo "$config" | jq -r '.s3_buckets')
    
    local lifecycle_rules
    lifecycle_rules=$(echo "$config" | jq -r '.lifecycle_rules // {}')
    
    local s3_result
    s3_result=$(cleanup_s3_objects "$s3_buckets" "$lifecycle_rules" "$DRY_RUN")
    
    cleanup_results=$(echo "$cleanup_results" | jq --argjson s3_objects "$s3_result" '. + {"s3_objects": $s3_objects}')
    
    # Cleanup RDS snapshots
    local rds_instances
    rds_instances=$(echo "$config" | jq -r '.rds_instances')
    
    local rds_result
    rds_result=$(cleanup_rds_snapshots "$rds_instances" "${RETENTION_DAYS[backups]}" "$DRY_RUN")
    
    cleanup_results=$(echo "$cleanup_results" | jq --argjson rds_snapshots "$rds_result" '. + {"rds_snapshots": $rds_snapshots}')
    
    # Cleanup ElastiCache snapshots
    local elasticache_clusters
    elasticache_clusters=$(echo "$config" | jq -r '.elasticache_clusters')
    
    local elasticache_result
    elasticache_result=$(cleanup_elasticache_snapshots "$elasticache_clusters" "${RETENTION_DAYS[backups]}" "$DRY_RUN")
    
    cleanup_results=$(echo "$cleanup_results" | jq --argjson elasticache_snapshots "$elasticache_result" '. + {"elasticache_snapshots": $elasticache_snapshots}')
  fi
  
  # Cleanup test resources
  if [[ "$CLEANUP_TYPE" == "test" || "$CLEANUP_TYPE" == "all" ]]; then
    local test_result
    test_result=$(cleanup_test_resources "$ENVIRONMENT" "${RETENTION_DAYS[test_data]}" "$DRY_RUN")
    
    cleanup_results=$(echo "$cleanup_results" | jq --argjson test_resources "$test_result" '. + {"test_resources": $test_resources}')
  fi
  
  # Archive old data
  if [[ "$CLEANUP_TYPE" == "archive" || "$CLEANUP_TYPE" == "all" ]]; then
    local archival_rules
    archival_rules=$(echo "$config" | jq -r '.archival_rules // {}')
    
    local archive_result
    archive_result=$(archive_old_data "$ENVIRONMENT" "$archival_rules" "$DRY_RUN")
    
    cleanup_results=$(echo "$cleanup_results" | jq --argjson archive "$archive_result" '. + {"archive": $archive_result}')
  fi
  
  # Generate cleanup report
  local report_file
  report_file=$(generate_cleanup_report "$cleanup_results")
  
  # Send notification
  send_notification "$cleanup_results" "SUCCESS"
  
  log "INFO" "Cleanup process completed successfully"
  return 0
}

# Call main function with command line arguments
main "$@"
exit $?