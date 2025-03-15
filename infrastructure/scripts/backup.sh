#!/usr/bin/env bash
#
# Backup script for the Molecular Data Management and CRO Integration Platform
#
# This script creates and manages backups of databases, S3 buckets, and configurations
# with appropriate retention policies and cross-region replication for disaster recovery.
#
# Usage: ./backup.sh -e|--environment <environment> -t|--type <backup_type> [options]
#
# Version: 1.0.0
# Date: 2023-09-15
#

# Exit on error
set -e

# Source bootstrap.sh to get check_prerequisites function
source "$(dirname "${BASH_SOURCE[0]}")/bootstrap.sh"

# Global variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="${SCRIPT_DIR}/../logs/backup_$(date +%Y%m%d_%H%M%S).log"
ENVIRONMENT="${ENVIRONMENT:-dev}"
BACKUP_TYPE="${BACKUP_TYPE:-full}"
BACKUP_RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"
AWS_REGION="${AWS_REGION:-us-east-1}"
BACKUP_BUCKET="${BACKUP_BUCKET:-}"
CONFIG_FILE="${SCRIPT_DIR}/../config/backup_config.json"

# Setup logging
setup_logging() {
  # Create logs directory if it doesn't exist
  mkdir -p "$(dirname "$LOG_FILE")"
  
  # Initialize log file with header
  echo "$(date '+%Y-%m-%d %H:%M:%S') - Backup script started" > "$LOG_FILE"
  echo "$(date '+%Y-%m-%d %H:%M:%S') - Environment: $ENVIRONMENT" >> "$LOG_FILE"
  echo "$(date '+%Y-%m-%d %H:%M:%S') - Backup type: $BACKUP_TYPE" >> "$LOG_FILE"
  echo "$(date '+%Y-%m-%d %H:%M:%S') - Retention days: $BACKUP_RETENTION_DAYS" >> "$LOG_FILE"
  
  # Return log file path
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
  ENVIRONMENT="dev"
  BACKUP_TYPE="full"
  BACKUP_RETENTION_DAYS=30
  CROSS_REGION_REPLICATION=false
  SECONDARY_REGION=""
  NOTIFICATION_ENABLED=true
  NOTIFICATION_SNS_TOPIC=""
  NOTIFICATION_EMAIL=""
  
  # Parse arguments
  while [[ ${#args[@]} -gt 0 ]]; do
    case "${args[0]}" in
      -e|--environment)
        ENVIRONMENT="${args[1]}"
        args=("${args[@]:2}")
        ;;
      -t|--type)
        BACKUP_TYPE="${args[1]}"
        args=("${args[@]:2}")
        ;;
      -r|--retention)
        BACKUP_RETENTION_DAYS="${args[1]}"
        args=("${args[@]:2}")
        ;;
      --cross-region)
        CROSS_REGION_REPLICATION=true
        args=("${args[@]:1}")
        ;;
      --secondary-region)
        SECONDARY_REGION="${args[1]}"
        args=("${args[@]:2}")
        ;;
      --no-notification)
        NOTIFICATION_ENABLED=false
        args=("${args[@]:1}")
        ;;
      --sns-topic)
        NOTIFICATION_SNS_TOPIC="${args[1]}"
        args=("${args[@]:2}")
        ;;
      --email)
        NOTIFICATION_EMAIL="${args[1]}"
        args=("${args[@]:2}")
        ;;
      --config)
        CONFIG_FILE="${args[1]}"
        args=("${args[@]:2}")
        ;;
      -h|--help)
        echo "Usage: $0 -e|--environment <environment> -t|--type <backup_type> [options]"
        echo ""
        echo "Options:"
        echo "  -e, --environment <env>     Environment (dev, staging, prod)"
        echo "  -t, --type <type>           Backup type (full, incremental, snapshot, logical)"
        echo "  -r, --retention <days>      Backup retention in days (default: 30)"
        echo "  --cross-region              Enable cross-region replication"
        echo "  --secondary-region <region> Secondary region for replication"
        echo "  --no-notification           Disable backup completion notifications"
        echo "  --sns-topic <arn>           SNS topic ARN for notifications"
        echo "  --email <address>           Email address for notifications"
        echo "  --config <file>             Configuration file path"
        echo "  -h, --help                  Show this help message"
        exit 0
        ;;
      *)
        echo "Unknown option: ${args[0]}"
        echo "Use --help for usage information"
        exit 1
        ;;
    esac
  done
  
  # Validate arguments
  if [[ ! "$ENVIRONMENT" =~ ^(dev|staging|prod)$ ]]; then
    echo "Error: Invalid environment: $ENVIRONMENT"
    echo "Valid environments are: dev, staging, prod"
    exit 1
  fi
  
  if [[ ! "$BACKUP_TYPE" =~ ^(full|incremental|snapshot|logical)$ ]]; then
    echo "Error: Invalid backup type: $BACKUP_TYPE"
    echo "Valid backup types are: full, incremental, snapshot, logical"
    exit 1
  fi
  
  if ! [[ "$BACKUP_RETENTION_DAYS" =~ ^[0-9]+$ ]]; then
    echo "Error: Backup retention must be a positive integer"
    exit 1
  fi
  
  if [ "$CROSS_REGION_REPLICATION" = true ] && [ -z "$SECONDARY_REGION" ]; then
    echo "Error: Secondary region must be specified when cross-region replication is enabled"
    exit 1
  fi
  
  # If notification enabled, ensure either SNS topic or email is provided
  if [ "$NOTIFICATION_ENABLED" = true ] && [ -z "$NOTIFICATION_SNS_TOPIC" ] && [ -z "$NOTIFICATION_EMAIL" ]; then
    echo "Warning: Notification is enabled but neither SNS topic nor email address is provided"
    NOTIFICATION_ENABLED=false
  fi
  
  # Set backup bucket name if not explicitly provided
  if [ -z "$BACKUP_BUCKET" ]; then
    BACKUP_BUCKET="moleculeflow-backups-${ENVIRONMENT}"
    export BACKUP_BUCKET
  fi
  
  return 0
}

# Load configuration from config file
load_configuration() {
  local environment="$1"
  
  log "INFO" "Loading configuration for environment: $environment"
  
  # Check if config file exists
  if [ ! -f "$CONFIG_FILE" ]; then
    log "ERROR" "Configuration file not found: $CONFIG_FILE"
    return 1
  fi
  
  # Load configuration using jq
  if ! command -v jq &> /dev/null; then
    log "ERROR" "jq is required for parsing configuration"
    return 1
  fi
  
  # Load configuration for specified environment
  local config
  config=$(jq -r --arg env "$environment" '.[$env]' "$CONFIG_FILE")
  
  if [ "$config" = "null" ]; then
    log "ERROR" "Configuration not found for environment: $environment"
    return 1
  fi
  
  # Extract database configuration
  DB_IDENTIFIER=$(echo "$config" | jq -r '.database.identifier // empty')
  DB_SNAPSHOT_PREFIX=$(echo "$config" | jq -r '.database.snapshot_prefix // "moleculeflow"')
  DB_EXPORT_BUCKET=$(echo "$config" | jq -r '.database.export_bucket // empty')
  
  # Extract S3 bucket configuration
  S3_BUCKETS=$(echo "$config" | jq -r '.s3_buckets | join(" ") // empty')
  S3_BACKUP_PREFIX=$(echo "$config" | jq -r '.s3_backup_prefix // "backup"')
  
  # Extract ElastiCache configuration
  ELASTICACHE_IDENTIFIER=$(echo "$config" | jq -r '.elasticache.identifier // empty')
  ELASTICACHE_SNAPSHOT_PREFIX=$(echo "$config" | jq -r '.elasticache.snapshot_prefix // "moleculeflow"')
  
  # Extract configuration backup settings
  CONFIG_BACKUP_ENABLED=$(echo "$config" | jq -r '.config_backup.enabled // "true"')
  CONFIG_BACKUP_PATHS=$(echo "$config" | jq -r '.config_backup.paths | join(" ") // empty')
  
  # Extract cross-region replication settings
  if [ "$CROSS_REGION_REPLICATION" = true ] && [ -z "$SECONDARY_REGION" ]; then
    SECONDARY_REGION=$(echo "$config" | jq -r '.cross_region.region // empty')
  fi
  CROSS_REGION_BUCKET=$(echo "$config" | jq -r '.cross_region.bucket // empty')
  
  # Extract notification settings
  if [ "$NOTIFICATION_ENABLED" = true ]; then
    if [ -z "$NOTIFICATION_SNS_TOPIC" ]; then
      NOTIFICATION_SNS_TOPIC=$(echo "$config" | jq -r '.notifications.sns_topic // empty')
    fi
    
    if [ -z "$NOTIFICATION_EMAIL" ]; then
      NOTIFICATION_EMAIL=$(echo "$config" | jq -r '.notifications.email // empty')
    fi
    
    NOTIFICATION_SLACK_WEBHOOK=$(echo "$config" | jq -r '.notifications.slack_webhook // empty')
  fi
  
  # Validate required configuration
  if [ "$BACKUP_TYPE" = "full" ] || [ "$BACKUP_TYPE" = "snapshot" ] || [ "$BACKUP_TYPE" = "logical" ]; then
    if [ -z "$DB_IDENTIFIER" ]; then
      log "ERROR" "Database identifier is required for backup type: $BACKUP_TYPE"
      return 1
    fi
  fi
  
  if [ "$BACKUP_TYPE" = "full" ] && [ -z "$DB_EXPORT_BUCKET" ]; then
    log "ERROR" "Database export bucket is required for full backup"
    return 1
  fi
  
  log "INFO" "Configuration loaded successfully"
  return 0
}

# Backup database
backup_database() {
  local db_identifier="$1"
  local backup_type="$2"
  local snapshot_identifier="$3"
  
  log "INFO" "Starting database backup for $db_identifier (type: $backup_type)"
  
  local result
  local start_time
  local end_time
  local duration
  
  start_time=$(date +%s)
  
  case "$backup_type" in
    snapshot)
      log "INFO" "Creating RDS snapshot: $snapshot_identifier"
      
      # Create RDS snapshot
      aws rds create-db-snapshot \
        --db-instance-identifier "$db_identifier" \
        --db-snapshot-identifier "$snapshot_identifier" \
        --region "$AWS_REGION" \
        --tags Key=Environment,Value="$ENVIRONMENT" Key=BackupType,Value="snapshot" Key=CreatedBy,Value="backup-script"
      
      # Wait for snapshot to complete
      log "INFO" "Waiting for snapshot to complete..."
      aws rds wait db-snapshot-completed \
        --db-snapshot-identifier "$snapshot_identifier" \
        --region "$AWS_REGION"
      
      # Get snapshot details
      local snapshot_details
      snapshot_details=$(aws rds describe-db-snapshots \
        --db-snapshot-identifier "$snapshot_identifier" \
        --region "$AWS_REGION" \
        --query 'DBSnapshots[0]')
      
      local snapshot_status
      snapshot_status=$(echo "$snapshot_details" | jq -r '.Status')
      
      if [ "$snapshot_status" = "available" ]; then
        log "INFO" "RDS snapshot created successfully: $snapshot_identifier"
        result="success"
      else
        log "ERROR" "RDS snapshot creation failed or timed out: $snapshot_identifier"
        result="failed"
      fi
      ;;
      
    full)
      log "INFO" "Creating RDS snapshot for full backup: $snapshot_identifier"
      
      # Create RDS snapshot
      aws rds create-db-snapshot \
        --db-instance-identifier "$db_identifier" \
        --db-snapshot-identifier "$snapshot_identifier" \
        --region "$AWS_REGION" \
        --tags Key=Environment,Value="$ENVIRONMENT" Key=BackupType,Value="full" Key=CreatedBy,Value="backup-script"
      
      # Wait for snapshot to complete
      log "INFO" "Waiting for snapshot to complete..."
      aws rds wait db-snapshot-completed \
        --db-snapshot-identifier "$snapshot_identifier" \
        --region "$AWS_REGION"
      
      # Export snapshot to S3
      log "INFO" "Exporting snapshot to S3: $DB_EXPORT_BUCKET"
      
      local export_task_id
      export_task_id="export-$snapshot_identifier-$(date +%Y%m%d%H%M%S)"
      
      aws rds start-export-task \
        --export-task-identifier "$export_task_id" \
        --source-arn "arn:aws:rds:$AWS_REGION:$(aws sts get-caller-identity --query 'Account' --output text):snapshot:$snapshot_identifier" \
        --s3-bucket-name "$DB_EXPORT_BUCKET" \
        --s3-prefix "database-exports/$ENVIRONMENT" \
        --iam-role-arn "arn:aws:iam::$(aws sts get-caller-identity --query 'Account' --output text):role/rds-s3-export-role" \
        --kms-key-id "alias/aws/rds" \
        --region "$AWS_REGION"
      
      # Check export task status
      log "INFO" "Checking export task status: $export_task_id"
      
      local export_status
      local retry_count=0
      local max_retries=30
      
      while [ $retry_count -lt $max_retries ]; do
        export_status=$(aws rds describe-export-tasks \
          --export-task-identifier "$export_task_id" \
          --region "$AWS_REGION" \
          --query 'ExportTasks[0].Status' \
          --output text)
        
        if [ "$export_status" = "COMPLETE" ]; then
          log "INFO" "Export task completed successfully: $export_task_id"
          result="success"
          break
        elif [ "$export_status" = "FAILED" ]; then
          local failure_reason
          failure_reason=$(aws rds describe-export-tasks \
            --export-task-identifier "$export_task_id" \
            --region "$AWS_REGION" \
            --query 'ExportTasks[0].FailureCause' \
            --output text)
          
          log "ERROR" "Export task failed: $export_task_id, Reason: $failure_reason"
          result="failed"
          break
        elif [ "$export_status" = "CANCELED" ]; then
          log "ERROR" "Export task was canceled: $export_task_id"
          result="failed"
          break
        fi
        
        log "INFO" "Export task in progress: $export_status, waiting..."
        sleep 60
        ((retry_count++))
      done
      
      if [ $retry_count -eq $max_retries ]; then
        log "ERROR" "Export task timed out after $max_retries retries: $export_task_id"
        result="timeout"
      fi
      ;;
      
    logical)
      log "INFO" "Creating logical backup (pg_dump) for $db_identifier"
      
      # Get database connection information
      local db_info
      db_info=$(aws rds describe-db-instances \
        --db-instance-identifier "$db_identifier" \
        --region "$AWS_REGION" \
        --query 'DBInstances[0]')
      
      local db_name
      local db_endpoint
      local db_port
      local db_username
      
      db_name=$(echo "$db_info" | jq -r '.DBName // "postgres"')
      db_endpoint=$(echo "$db_info" | jq -r '.Endpoint.Address')
      db_port=$(echo "$db_info" | jq -r '.Endpoint.Port')
      db_username=$(echo "$db_info" | jq -r '.MasterUsername')
      
      # Generate temporary password file
      local password_file
      password_file=$(mktemp)
      
      # Get database password from AWS Secrets Manager
      local secret_id="moleculeflow-$ENVIRONMENT-db-credentials"
      local db_password
      
      db_password=$(aws secretsmanager get-secret-value \
        --secret-id "$secret_id" \
        --region "$AWS_REGION" \
        --query 'SecretString' \
        --output text | jq -r '.password')
      
      echo "$db_password" > "$password_file"
      
      # Set PGPASSFILE environment variable
      export PGPASSFILE="$password_file"
      
      # Create logical backup using pg_dump
      local dump_file="/tmp/pg_dump_$db_identifier.sql.gz"
      
      log "INFO" "Running pg_dump to $dump_file"
      
      if PGPASSWORD="$db_password" pg_dump \
        -h "$db_endpoint" \
        -p "$db_port" \
        -U "$db_username" \
        -d "$db_name" \
        -F c -b -v -Z 9 > "$dump_file"; then
        
        # Upload dump file to S3
        log "INFO" "Uploading logical backup to S3"
        
        local s3_key="database-logical-backups/$ENVIRONMENT/$db_identifier/$(date +%Y%m%d)_$db_name.sql.gz"
        
        if aws s3 cp "$dump_file" "s3://$BACKUP_BUCKET/$s3_key" \
          --region "$AWS_REGION" \
          --metadata "BackupType=logical,Environment=$ENVIRONMENT,Timestamp=$(date +%Y%m%d%H%M%S)"; then
          
          log "INFO" "Logical backup uploaded successfully to s3://$BACKUP_BUCKET/$s3_key"
          result="success"
        else
          log "ERROR" "Failed to upload logical backup to S3"
          result="failed"
        fi
      else
        log "ERROR" "pg_dump failed for database $db_identifier"
        result="failed"
      fi
      
      # Remove temporary files
      rm -f "$password_file" "$dump_file"
      unset PGPASSFILE
      ;;
      
    incremental)
      log "INFO" "Verifying point-in-time recovery capability for $db_identifier"
      
      # Check if point-in-time recovery is enabled
      local db_info
      db_info=$(aws rds describe-db-instances \
        --db-instance-identifier "$db_identifier" \
        --region "$AWS_REGION" \
        --query 'DBInstances[0]')
      
      local backup_retention_period
      backup_retention_period=$(echo "$db_info" | jq -r '.BackupRetentionPeriod')
      
      if [ "$backup_retention_period" -gt 0 ]; then
        log "INFO" "Point-in-time recovery is enabled with retention period of $backup_retention_period days"
        
        # Get latest automated backup
        log "INFO" "Getting latest automated backup information"
        
        local latest_backup
        latest_backup=$(aws rds describe-db-instance-automated-backups \
          --db-instance-identifier "$db_identifier" \
          --region "$AWS_REGION" \
          --query 'DBInstanceAutomatedBackups[0]')
        
        if [ -n "$latest_backup" ]; then
          local backup_arn
          local backup_time
          
          backup_arn=$(echo "$latest_backup" | jq -r '.DBInstanceAutomatedBackupsArn')
          backup_time=$(echo "$latest_backup" | jq -r '.InstanceCreateTime')
          
          log "INFO" "Latest automated backup: $backup_arn, Created: $backup_time"
          log "INFO" "Incremental backup status verified successfully"
          
          result="success"
        else
          log "WARN" "No automated backups found for $db_identifier"
          result="warning"
        fi
      else
        log "ERROR" "Point-in-time recovery is not enabled for $db_identifier"
        result="failed"
      fi
      ;;
      
    *)
      log "ERROR" "Unsupported backup type: $backup_type"
      result="failed"
      ;;
  esac
  
  end_time=$(date +%s)
  duration=$((end_time - start_time))
  
  log "INFO" "Database backup completed in $duration seconds with status: $result"
  
  # Return result
  echo "{\"type\":\"database\",\"db_identifier\":\"$db_identifier\",\"backup_type\":\"$backup_type\",\"snapshot_identifier\":\"$snapshot_identifier\",\"result\":\"$result\",\"duration\":$duration}"
}

# Backup S3 buckets
backup_s3_buckets() {
  local bucket_names=("$@")
  local destination_bucket="$BACKUP_BUCKET"
  local prefix="$S3_BACKUP_PREFIX/$(date +%Y%m%d)"
  
  log "INFO" "Starting S3 bucket backup to $destination_bucket/$prefix"
  
  # Ensure backup bucket exists
  if ! aws s3api head-bucket --bucket "$destination_bucket" 2>/dev/null; then
    log "INFO" "Creating backup bucket: $destination_bucket"
    
    # Create bucket with versioning enabled
    if ! aws s3api create-bucket \
      --bucket "$destination_bucket" \
      --create-bucket-configuration LocationConstraint="$AWS_REGION" \
      --region "$AWS_REGION"; then
      
      log "ERROR" "Failed to create backup bucket: $destination_bucket"
      return "{\"type\":\"s3\",\"result\":\"failed\",\"message\":\"Failed to create backup bucket\"}"
    fi
    
    # Enable versioning
    aws s3api put-bucket-versioning \
      --bucket "$destination_bucket" \
      --versioning-configuration Status=Enabled
    
    # Enable server-side encryption
    aws s3api put-bucket-encryption \
      --bucket "$destination_bucket" \
      --server-side-encryption-configuration '{
        "Rules": [
          {
            "ApplyServerSideEncryptionByDefault": {
              "SSEAlgorithm": "AES256"
            }
          }
        ]
      }'
    
    # Add lifecycle rules for backup rotation
    aws s3api put-bucket-lifecycle-configuration \
      --bucket "$destination_bucket" \
      --lifecycle-configuration '{
        "Rules": [
          {
            "ID": "Backup Rotation",
            "Status": "Enabled",
            "Prefix": "'"$S3_BACKUP_PREFIX"'/",
            "Expiration": {
              "Days": '"$BACKUP_RETENTION_DAYS"'
            }
          }
        ]
      }'
    
    log "INFO" "Backup bucket created and configured: $destination_bucket"
  fi
  
  local result="success"
  local start_time
  local end_time
  local duration
  local total_size=0
  local total_objects=0
  local bucket_results=()
  
  start_time=$(date +%s)
  
  # Process each bucket
  for bucket in "${bucket_names[@]}"; do
    log "INFO" "Backing up bucket: $bucket"
    
    local bucket_prefix="$prefix/$bucket"
    local sync_result
    
    # Use aws s3 sync to copy objects
    if sync_result=$(aws s3 sync "s3://$bucket" "s3://$destination_bucket/$bucket_prefix" \
      --region "$AWS_REGION" \
      --metadata "BackupTimestamp=$(date +%Y%m%d%H%M%S),Environment=$ENVIRONMENT,Source=$bucket" \
      --metadata-directive REPLACE 2>&1); then
      
      # Get bucket size and object count
      local bucket_size
      local object_count
      
      bucket_size=$(aws s3 ls --summarize --recursive "s3://$destination_bucket/$bucket_prefix" | grep "Total Size" | awk '{print $3}')
      object_count=$(aws s3 ls --summarize --recursive "s3://$destination_bucket/$bucket_prefix" | grep "Total Objects" | awk '{print $3}')
      
      bucket_size=${bucket_size:-0}
      object_count=${object_count:-0}
      
      total_size=$((total_size + bucket_size))
      total_objects=$((total_objects + object_count))
      
      log "INFO" "Bucket backup completed: $bucket, Size: $bucket_size bytes, Objects: $object_count"
      
      bucket_results+=("{\"bucket\":\"$bucket\",\"size\":$bucket_size,\"objects\":$object_count,\"result\":\"success\"}")
    else
      log "ERROR" "Failed to backup bucket: $bucket"
      log "ERROR" "Error details: $sync_result"
      
      result="partial"
      bucket_results+=("{\"bucket\":\"$bucket\",\"result\":\"failed\",\"error\":\"Sync failed\"}")
    fi
  done
  
  end_time=$(date +%s)
  duration=$((end_time - start_time))
  
  log "INFO" "S3 bucket backup completed in $duration seconds with status: $result"
  log "INFO" "Total size: $total_size bytes, Total objects: $total_objects"
  
  # Format bucket results JSON
  local bucket_results_json
  bucket_results_json=$(printf "%s," "${bucket_results[@]}" | sed 's/,$//')
  
  # Return result
  echo "{\"type\":\"s3\",\"result\":\"$result\",\"duration\":$duration,\"total_size\":$total_size,\"total_objects\":$total_objects,\"buckets\":[$bucket_results_json]}"
}

# Backup ElastiCache
backup_elasticache() {
  local replication_group_id="$1"
  local snapshot_name="$2"
  
  log "INFO" "Starting ElastiCache backup for $replication_group_id"
  
  local result
  local start_time
  local end_time
  local duration
  
  start_time=$(date +%s)
  
  # Create ElastiCache snapshot
  log "INFO" "Creating ElastiCache snapshot: $snapshot_name"
  
  if aws elasticache create-snapshot \
    --replication-group-id "$replication_group_id" \
    --snapshot-name "$snapshot_name" \
    --region "$AWS_REGION" > /dev/null 2>&1; then
    
    # Wait for snapshot to complete
    log "INFO" "Waiting for ElastiCache snapshot to complete..."
    
    local snapshot_status
    local retry_count=0
    local max_retries=30
    
    while [ $retry_count -lt $max_retries ]; do
      snapshot_status=$(aws elasticache describe-snapshots \
        --snapshot-name "$snapshot_name" \
        --region "$AWS_REGION" \
        --query 'Snapshots[0].SnapshotStatus' \
        --output text)
      
      if [ "$snapshot_status" = "available" ]; then
        log "INFO" "ElastiCache snapshot created successfully: $snapshot_name"
        result="success"
        break
      elif [ "$snapshot_status" = "failed" ]; then
        log "ERROR" "ElastiCache snapshot creation failed: $snapshot_name"
        result="failed"
        break
      fi
      
      log "INFO" "ElastiCache snapshot in progress: $snapshot_status, waiting..."
      sleep 30
      ((retry_count++))
    done
    
    if [ $retry_count -eq $max_retries ]; then
      log "ERROR" "ElastiCache snapshot creation timed out after $max_retries retries: $snapshot_name"
      result="timeout"
    fi
  else
    log "ERROR" "Failed to create ElastiCache snapshot: $snapshot_name"
    result="failed"
  fi
  
  end_time=$(date +%s)
  duration=$((end_time - start_time))
  
  log "INFO" "ElastiCache backup completed in $duration seconds with status: $result"
  
  # Return result
  echo "{\"type\":\"elasticache\",\"replication_group_id\":\"$replication_group_id\",\"snapshot_name\":\"$snapshot_name\",\"result\":\"$result\",\"duration\":$duration}"
}

# Backup configuration
backup_configuration() {
  local environment="$1"
  local destination_bucket="$BACKUP_BUCKET"
  local prefix="config-backups/$environment/$(date +%Y%m%d%H%M%S)"
  
  log "INFO" "Starting configuration backup to $destination_bucket/$prefix"
  
  local result="success"
  local start_time
  local end_time
  local duration
  local total_size=0
  local total_files=0
  
  start_time=$(date +%s)
  
  # Create temporary directory for configuration files
  local temp_dir
  temp_dir=$(mktemp -d)
  
  # Backup Terraform state files
  log "INFO" "Backing up Terraform state files"
  
  local tf_state_bucket="moleculeflow-terraform-state-$environment"
  local tf_state_key="terraform.tfstate"
  
  if aws s3 cp "s3://$tf_state_bucket/$tf_state_key" "$temp_dir/terraform.tfstate" \
    --region "$AWS_REGION" > /dev/null 2>&1; then
    log "INFO" "Terraform state backed up successfully"
  else
    log "WARN" "Failed to backup Terraform state from s3://$tf_state_bucket/$tf_state_key"
    result="partial"
  fi
  
  # Backup environment configuration files
  log "INFO" "Backing up environment configuration files"
  
  local config_paths=($CONFIG_BACKUP_PATHS)
  
  for path in "${config_paths[@]}"; do
    if [ -d "$path" ]; then
      # Directory path
      mkdir -p "$temp_dir/$(basename "$path")"
      cp -r "$path"/* "$temp_dir/$(basename "$path")/" 2>/dev/null
    elif [ -f "$path" ]; then
      # File path
      cp "$path" "$temp_dir/" 2>/dev/null
    else
      log "WARN" "Config path not found: $path"
      continue
    fi
  done
  
  # Backup AWS resource configurations
  log "INFO" "Backing up AWS resource configurations"
  
  # Get list of AWS Config recorders
  local config_recorders
  config_recorders=$(aws configservice describe-configuration-recorders \
    --region "$AWS_REGION" \
    --query 'ConfigurationRecorders[*].name' \
    --output text)
  
  if [ -n "$config_recorders" ]; then
    mkdir -p "$temp_dir/aws-config"
    
    # Export AWS Config snapshots
    for recorder in $config_recorders; do
      log "INFO" "Exporting AWS Config snapshot for recorder: $recorder"
      
      aws configservice deliver-config-snapshot \
        --delivery-channel-name "$recorder" \
        --region "$AWS_REGION" \
        > "$temp_dir/aws-config/$recorder-snapshot.json" 2>/dev/null
    done
  else
    log "WARN" "No AWS Config recorders found"
  fi
  
  # Create archive of configuration files
  log "INFO" "Creating configuration archive"
  
  local archive_file="/tmp/config-backup-$environment-$(date +%Y%m%d%H%M%S).tar.gz"
  
  if tar -czf "$archive_file" -C "$temp_dir" .; then
    # Upload archive to S3
    log "INFO" "Uploading configuration archive to S3"
    
    if aws s3 cp "$archive_file" "s3://$destination_bucket/$prefix/config-backup.tar.gz" \
      --region "$AWS_REGION" \
      --metadata "Environment=$environment,Timestamp=$(date +%Y%m%d%H%M%S),BackupType=configuration" > /dev/null 2>&1; then
      
      # Get file size and count
      total_size=$(stat -c%s "$archive_file")
      total_files=$(find "$temp_dir" -type f | wc -l)
      
      log "INFO" "Configuration archive uploaded successfully: $total_size bytes, $total_files files"
    else
      log "ERROR" "Failed to upload configuration archive to S3"
      result="failed"
    fi
  else
    log "ERROR" "Failed to create configuration archive"
    result="failed"
  fi
  
  # Clean up temporary files
  rm -rf "$temp_dir" "$archive_file"
  
  end_time=$(date +%s)
  duration=$((end_time - start_time))
  
  log "INFO" "Configuration backup completed in $duration seconds with status: $result"
  
  # Return result
  echo "{\"type\":\"configuration\",\"result\":\"$result\",\"duration\":$duration,\"total_size\":$total_size,\"total_files\":$total_files}"
}

# Cross-region replication
cross_region_replication() {
  local source_bucket="$1"
  local destination_bucket="$2"
  local prefix="$3"
  local secondary_region="$4"
  
  log "INFO" "Starting cross-region replication from $source_bucket to $destination_bucket in $secondary_region"
  
  local result="success"
  local start_time
  local end_time
  local duration
  local total_size=0
  local total_objects=0
  
  start_time=$(date +%s)
  
  # Check if destination bucket exists in secondary region
  if ! aws s3api head-bucket --bucket "$destination_bucket" --region "$secondary_region" 2>/dev/null; then
    log "INFO" "Creating destination bucket in secondary region: $destination_bucket"
    
    # Create bucket with versioning enabled
    if ! aws s3api create-bucket \
      --bucket "$destination_bucket" \
      --create-bucket-configuration LocationConstraint="$secondary_region" \
      --region "$secondary_region"; then
      
      log "ERROR" "Failed to create destination bucket: $destination_bucket"
      return "{\"type\":\"replication\",\"result\":\"failed\",\"message\":\"Failed to create destination bucket\"}"
    fi
    
    # Enable versioning
    aws s3api put-bucket-versioning \
      --bucket "$destination_bucket" \
      --versioning-configuration Status=Enabled \
      --region "$secondary_region"
    
    # Enable server-side encryption
    aws s3api put-bucket-encryption \
      --bucket "$destination_bucket" \
      --server-side-encryption-configuration '{
        "Rules": [
          {
            "ApplyServerSideEncryptionByDefault": {
              "SSEAlgorithm": "AES256"
            }
          }
        ]
      }' \
      --region "$secondary_region"
    
    # Add lifecycle rules for backup rotation
    aws s3api put-bucket-lifecycle-configuration \
      --bucket "$destination_bucket" \
      --lifecycle-configuration '{
        "Rules": [
          {
            "ID": "Backup Rotation",
            "Status": "Enabled",
            "Prefix": "'"$prefix"'/",
            "Expiration": {
              "Days": '"$BACKUP_RETENTION_DAYS"'
            }
          }
        ]
      }' \
      --region "$secondary_region"
    
    log "INFO" "Destination bucket created and configured: $destination_bucket"
  fi
  
  # Use aws s3 sync to copy objects
  log "INFO" "Replicating data to secondary region"
  
  local sync_result
  
  if sync_result=$(aws s3 sync "s3://$source_bucket/$prefix" "s3://$destination_bucket/$prefix" \
    --region "$secondary_region" \
    --metadata "ReplicationTimestamp=$(date +%Y%m%d%H%M%S),Environment=$ENVIRONMENT,Source=$source_bucket" \
    --metadata-directive REPLACE 2>&1); then
    
    # Get size and object count
    local replication_size
    local object_count
    
    replication_size=$(aws s3 ls --summarize --recursive "s3://$destination_bucket/$prefix" --region "$secondary_region" | grep "Total Size" | awk '{print $3}')
    object_count=$(aws s3 ls --summarize --recursive "s3://$destination_bucket/$prefix" --region "$secondary_region" | grep "Total Objects" | awk '{print $3}')
    
    replication_size=${replication_size:-0}
    object_count=${object_count:-0}
    
    total_size=$replication_size
    total_objects=$object_count
    
    log "INFO" "Replication completed: Size: $replication_size bytes, Objects: $object_count"
  else
    log "ERROR" "Failed to replicate data to secondary region"
    log "ERROR" "Error details: $sync_result"
    
    result="failed"
  fi
  
  end_time=$(date +%s)
  duration=$((end_time - start_time))
  
  log "INFO" "Cross-region replication completed in $duration seconds with status: $result"
  
  # Return result
  echo "{\"type\":\"replication\",\"source_bucket\":\"$source_bucket\",\"destination_bucket\":\"$destination_bucket\",\"secondary_region\":\"$secondary_region\",\"result\":\"$result\",\"duration\":$duration,\"total_size\":$total_size,\"total_objects\":$total_objects}"
}

# Clean up old backups
cleanup_old_backups() {
  local backup_type="$1"
  local retention_days="$2"
  
  log "INFO" "Starting cleanup of old backups (type: $backup_type, retention: $retention_days days)"
  
  local result="success"
  local start_time
  local end_time
  local duration
  local removed_count=0
  
  start_time=$(date +%s)
  
  # Calculate cutoff date
  local cutoff_date
  cutoff_date=$(date -d "$retention_days days ago" +%Y-%m-%d)
  
  case "$backup_type" in
    snapshot)
      log "INFO" "Cleaning up old RDS snapshots before $cutoff_date"
      
      # Get list of automated snapshots older than retention period
      local old_snapshots
      old_snapshots=$(aws rds describe-db-snapshots \
        --snapshot-type manual \
        --region "$AWS_REGION" \
        --query "DBSnapshots[?SnapshotCreateTime<'$cutoff_date' && DBInstanceIdentifier=='$DB_IDENTIFIER'].DBSnapshotIdentifier" \
        --output text)
      
      # Delete old snapshots
      for snapshot in $old_snapshots; do
        log "INFO" "Deleting old RDS snapshot: $snapshot"
        
        if aws rds delete-db-snapshot \
          --db-snapshot-identifier "$snapshot" \
          --region "$AWS_REGION" > /dev/null 2>&1; then
          
          log "INFO" "Deleted RDS snapshot: $snapshot"
          ((removed_count++))
        else
          log "ERROR" "Failed to delete RDS snapshot: $snapshot"
          result="partial"
        fi
      done
      
      # ElastiCache snapshots
      if [ -n "$ELASTICACHE_IDENTIFIER" ]; then
        log "INFO" "Cleaning up old ElastiCache snapshots before $cutoff_date"
        
        # Get list of ElastiCache snapshots older than retention period
        local old_elasticache_snapshots
        old_elasticache_snapshots=$(aws elasticache describe-snapshots \
          --region "$AWS_REGION" \
          --query "Snapshots[?NodeSnapshots[0].SnapshotCreateTime<'$cutoff_date'].SnapshotName" \
          --output text)
        
        # Delete old ElastiCache snapshots
        for snapshot in $old_elasticache_snapshots; do
          log "INFO" "Deleting old ElastiCache snapshot: $snapshot"
          
          if aws elasticache delete-snapshot \
            --snapshot-name "$snapshot" \
            --region "$AWS_REGION" > /dev/null 2>&1; then
            
            log "INFO" "Deleted ElastiCache snapshot: $snapshot"
            ((removed_count++))
          else
            log "ERROR" "Failed to delete ElastiCache snapshot: $snapshot"
            result="partial"
          fi
        done
      fi
      ;;
      
    s3)
      log "INFO" "Cleaning up old S3 backups before $cutoff_date"
      
      # List objects in backup bucket older than retention period
      local old_objects
      old_objects=$(aws s3api list-objects-v2 \
        --bucket "$BACKUP_BUCKET" \
        --region "$AWS_REGION" \
        --query "Contents[?LastModified<='$cutoff_date'].Key" \
        --output text)
      
      # Delete old objects
      for object in $old_objects; do
        log "INFO" "Deleting old S3 backup: $object"
        
        if aws s3 rm "s3://$BACKUP_BUCKET/$object" --region "$AWS_REGION" > /dev/null 2>&1; then
          log "INFO" "Deleted S3 object: $object"
          ((removed_count++))
        else
          log "ERROR" "Failed to delete S3 object: $object"
          result="partial"
        fi
      done
      
      # Delete old versions if versioning is enabled
      local versioning_status
      versioning_status=$(aws s3api get-bucket-versioning \
        --bucket "$BACKUP_BUCKET" \
        --region "$AWS_REGION" \
        --query 'Status' \
        --output text)
      
      if [ "$versioning_status" = "Enabled" ]; then
        log "INFO" "Cleaning up old versions in versioned bucket: $BACKUP_BUCKET"
        
        local old_versions
        old_versions=$(aws s3api list-object-versions \
          --bucket "$BACKUP_BUCKET" \
          --region "$AWS_REGION" \
          --query "Versions[?LastModified<='$cutoff_date'].[Key, VersionId]" \
          --output text)
        
        # Delete old versions
        while read -r key version_id; do
          if [ -n "$key" ] && [ -n "$version_id" ]; then
            log "INFO" "Deleting old version: $key ($version_id)"
            
            if aws s3api delete-object \
              --bucket "$BACKUP_BUCKET" \
              --key "$key" \
              --version-id "$version_id" \
              --region "$AWS_REGION" > /dev/null 2>&1; then
              
              log "INFO" "Deleted object version: $key ($version_id)"
              ((removed_count++))
            else
              log "ERROR" "Failed to delete object version: $key ($version_id)"
              result="partial"
            fi
          fi
        done <<< "$old_versions"
      fi
      ;;
      
    all)
      # Clean up all backup types
      cleanup_old_backups "snapshot" "$retention_days"
      cleanup_old_backups "s3" "$retention_days"
      ;;
      
    *)
      log "ERROR" "Unsupported backup type for cleanup: $backup_type"
      result="failed"
      ;;
  esac
  
  end_time=$(date +%s)
  duration=$((end_time - start_time))
  
  log "INFO" "Backup cleanup completed in $duration seconds with status: $result"
  log "INFO" "Removed $removed_count old backup items"
  
  # Return result
  echo "{\"type\":\"cleanup\",\"backup_type\":\"$backup_type\",\"retention_days\":$retention_days,\"result\":\"$result\",\"duration\":$duration,\"removed_count\":$removed_count}"
}

# Verify backup integrity
verify_backup_integrity() {
  local backup_result="$1"
  
  log "INFO" "Verifying backup integrity"
  
  local backup_type
  local result
  local verification_result="success"
  
  backup_type=$(echo "$backup_result" | jq -r '.type // "unknown"')
  result=$(echo "$backup_result" | jq -r '.result // "unknown"')
  
  if [ "$result" != "success" ]; then
    log "ERROR" "Backup result is not success: $result"
    verification_result="failed"
    return false
  fi
  
  case "$backup_type" in
    database)
      local snapshot_identifier
      snapshot_identifier=$(echo "$backup_result" | jq -r '.snapshot_identifier // empty')
      
      if [ -n "$snapshot_identifier" ]; then
        log "INFO" "Verifying database snapshot: $snapshot_identifier"
        
        local snapshot_status
        snapshot_status=$(aws rds describe-db-snapshots \
          --db-snapshot-identifier "$snapshot_identifier" \
          --region "$AWS_REGION" \
          --query 'DBSnapshots[0].Status' \
          --output text 2>/dev/null)
        
        if [ "$snapshot_status" = "available" ]; then
          log "INFO" "Database snapshot verification successful: $snapshot_identifier"
        else
          log "ERROR" "Database snapshot verification failed: $snapshot_identifier, Status: $snapshot_status"
          verification_result="failed"
        fi
      else
        log "INFO" "No snapshot identifier to verify"
      fi
      ;;
      
    s3)
      log "INFO" "Verifying S3 bucket backups"
      
      local buckets
      local buckets_json
      buckets_json=$(echo "$backup_result" | jq -r '.buckets // []')
      
      if [ "$buckets_json" != "[]" ]; then
        local bucket_count
        bucket_count=$(echo "$buckets_json" | jq length)
        
        log "INFO" "Verifying $bucket_count bucket backups"
        
        for i in $(seq 0 $((bucket_count - 1))); do
          local bucket
          local bucket_result
          
          bucket=$(echo "$buckets_json" | jq -r ".[$i].bucket // empty")
          bucket_result=$(echo "$buckets_json" | jq -r ".[$i].result // \"unknown\"")
          
          if [ "$bucket_result" != "success" ]; then
            log "ERROR" "Bucket backup verification failed: $bucket, Result: $bucket_result"
            verification_result="failed"
          else
            log "INFO" "Bucket backup verification successful: $bucket"
          fi
        done
      else
        log "WARN" "No bucket backups to verify"
        verification_result="warning"
      fi
      ;;
      
    elasticache)
      local snapshot_name
      snapshot_name=$(echo "$backup_result" | jq -r '.snapshot_name // empty')
      
      if [ -n "$snapshot_name" ]; then
        log "INFO" "Verifying ElastiCache snapshot: $snapshot_name"
        
        local snapshot_status
        snapshot_status=$(aws elasticache describe-snapshots \
          --snapshot-name "$snapshot_name" \
          --region "$AWS_REGION" \
          --query 'Snapshots[0].SnapshotStatus' \
          --output text 2>/dev/null)
        
        if [ "$snapshot_status" = "available" ]; then
          log "INFO" "ElastiCache snapshot verification successful: $snapshot_name"
        else
          log "ERROR" "ElastiCache snapshot verification failed: $snapshot_name, Status: $snapshot_status"
          verification_result="failed"
        fi
      else
        log "INFO" "No ElastiCache snapshot name to verify"
      fi
      ;;
      
    configuration)
      local total_files
      total_files=$(echo "$backup_result" | jq -r '.total_files // 0')
      
      if [ "$total_files" -gt 0 ]; then
        log "INFO" "Configuration backup verification successful: $total_files files"
      else
        log "WARN" "Configuration backup has no files"
        verification_result="warning"
      fi
      ;;
      
    replication)
      local total_objects
      total_objects=$(echo "$backup_result" | jq -r '.total_objects // 0')
      
      if [ "$total_objects" -gt 0 ]; then
        log "INFO" "Replication verification successful: $total_objects objects"
      else
        log "WARN" "Replication has no objects"
        verification_result="warning"
      fi
      ;;
      
    cleanup)
      local removed_count
      removed_count=$(echo "$backup_result" | jq -r '.removed_count // 0')
      
      log "INFO" "Cleanup verification: $removed_count items removed"
      ;;
      
    *)
      log "ERROR" "Unknown backup type for verification: $backup_type"
      verification_result="failed"
      ;;
  esac
  
  log "INFO" "Backup integrity verification result: $verification_result"
  
  # Return true/false based on verification result
  [ "$verification_result" = "success" ] || [ "$verification_result" = "warning" ]
}

# Generate backup report
generate_backup_report() {
  local backup_results="$1"
  
  log "INFO" "Generating backup report"
  
  local report_file="/tmp/backup-report-$ENVIRONMENT-$(date +%Y%m%d%H%M%S).json"
  local report_s3_key="reports/$ENVIRONMENT/backup-report-$(date +%Y%m%d%H%M%S).json"
  
  # Create report JSON
  cat > "$report_file" << EOF
{
  "environment": "$ENVIRONMENT",
  "backup_type": "$BACKUP_TYPE",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "results": $backup_results,
  "summary": {
    "overall_result": "$(echo "$backup_results" | jq -r 'map(.result) | if all(. == "success") then "success" elif any(. == "failed") then "failed" else "partial" end')",
    "total_duration": $(echo "$backup_results" | jq '[.[].duration] | add // 0'),
    "components": {
      "database": $(echo "$backup_results" | jq '[.[] | select(.type == "database")] | length'),
      "s3": $(echo "$backup_results" | jq '[.[] | select(.type == "s3")] | length'),
      "elasticache": $(echo "$backup_results" | jq '[.[] | select(.type == "elasticache")] | length'),
      "configuration": $(echo "$backup_results" | jq '[.[] | select(.type == "configuration")] | length'),
      "replication": $(echo "$backup_results" | jq '[.[] | select(.type == "replication")] | length'),
      "cleanup": $(echo "$backup_results" | jq '[.[] | select(.type == "cleanup")] | length')
    }
  }
}
EOF
  
  # Upload report to S3
  log "INFO" "Uploading backup report to S3: $report_s3_key"
  
  if aws s3 cp "$report_file" "s3://$BACKUP_BUCKET/$report_s3_key" \
    --region "$AWS_REGION" \
    --metadata "Environment=$ENVIRONMENT,BackupType=$BACKUP_TYPE,Timestamp=$(date +%Y%m%d%H%M%S)" > /dev/null 2>&1; then
    
    log "INFO" "Backup report uploaded successfully"
  else
    log "ERROR" "Failed to upload backup report to S3"
  fi
  
  # Return report file path
  echo "$report_file"
}

# Send notification
send_notification() {
  local backup_results="$1"
  local status="$2"
  
  log "INFO" "Sending backup completion notification"
  
  # Skip notification if disabled
  if [ "$NOTIFICATION_ENABLED" != "true" ]; then
    log "INFO" "Notifications are disabled"
    return true
  fi
  
  # Prepare notification message
  local subject="Backup Report: $ENVIRONMENT ($status)"
  local overall_result
  overall_result=$(echo "$backup_results" | jq -r 'map(.result) | if all(. == "success") then "SUCCESS" elif any(. == "failed") then "FAILED" else "PARTIAL SUCCESS" end')
  
  local message
  message=$(cat << EOF
Backup Report for Environment: $ENVIRONMENT
Status: $overall_result
Backup Type: $BACKUP_TYPE
Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)

Summary:
- Total Duration: $(echo "$backup_results" | jq '[.[].duration] | add // 0') seconds
- Database Backups: $(echo "$backup_results" | jq '[.[] | select(.type == "database")] | length')
- S3 Backups: $(echo "$backup_results" | jq '[.[] | select(.type == "s3")] | length')
- ElastiCache Backups: $(echo "$backup_results" | jq '[.[] | select(.type == "elasticache")] | length')
- Configuration Backups: $(echo "$backup_results" | jq '[.[] | select(.type == "configuration")] | length')

Details:
$(echo "$backup_results" | jq -r '.[] | "- " + .type + ": " + .result')

For more details, see the full report in:
s3://$BACKUP_BUCKET/reports/$ENVIRONMENT/backup-report-$(date +%Y%m%d%H%M%S).json
EOF
)
  
  local notification_sent=false
  
  # Send SNS notification if configured
  if [ -n "$NOTIFICATION_SNS_TOPIC" ]; then
    log "INFO" "Sending SNS notification to: $NOTIFICATION_SNS_TOPIC"
    
    if aws sns publish \
      --topic-arn "$NOTIFICATION_SNS_TOPIC" \
      --subject "$subject" \
      --message "$message" \
      --region "$AWS_REGION" > /dev/null 2>&1; then
      
      log "INFO" "SNS notification sent successfully"
      notification_sent=true
    else
      log "ERROR" "Failed to send SNS notification"
    fi
  fi
  
  # Send email notification if configured
  if [ -n "$NOTIFICATION_EMAIL" ]; then
    log "INFO" "Sending email notification to: $NOTIFICATION_EMAIL"
    
    # Check if SNS topic for email exists, otherwise create it
    local email_sns_topic
    email_sns_topic="arn:aws:sns:$AWS_REGION:$(aws sts get-caller-identity --query 'Account' --output text):moleculeflow-backup-notifications"
    
    # Check if topic exists
    if ! aws sns get-topic-attributes --topic-arn "$email_sns_topic" > /dev/null 2>&1; then
      log "INFO" "Creating SNS topic for email notifications"
      
      email_sns_topic=$(aws sns create-topic \
        --name "moleculeflow-backup-notifications" \
        --region "$AWS_REGION" \
        --query 'TopicArn' \
        --output text)
      
      # Subscribe email to topic
      aws sns subscribe \
        --topic-arn "$email_sns_topic" \
        --protocol email \
        --notification-endpoint "$NOTIFICATION_EMAIL" \
        --region "$AWS_REGION" > /dev/null 2>&1
      
      log "INFO" "Email subscription confirmation sent to $NOTIFICATION_EMAIL"
      log "INFO" "Email notifications will be sent after subscription confirmation"
    fi
    
    # Send notification
    if aws sns publish \
      --topic-arn "$email_sns_topic" \
      --subject "$subject" \
      --message "$message" \
      --region "$AWS_REGION" > /dev/null 2>&1; then
      
      log "INFO" "Email notification sent successfully"
      notification_sent=true
    else
      log "ERROR" "Failed to send email notification"
    fi
  fi
  
  # Send Slack notification if configured
  if [ -n "$NOTIFICATION_SLACK_WEBHOOK" ]; then
    log "INFO" "Sending Slack notification"
    
    local color
    case "$overall_result" in
      SUCCESS) color="#36a64f" ;; # Green
      PARTIAL*) color="#f2c744" ;; # Yellow
      FAILED) color="#d00000" ;; # Red
      *) color="#cccccc" ;; # Grey
    esac
    
    local slack_payload
    slack_payload=$(cat << EOF
{
  "attachments": [
    {
      "color": "$color",
      "pretext": "Backup Report for Environment: $ENVIRONMENT",
      "title": "Backup Status: $overall_result",
      "fields": [
        {
          "title": "Environment",
          "value": "$ENVIRONMENT",
          "short": true
        },
        {
          "title": "Backup Type",
          "value": "$BACKUP_TYPE",
          "short": true
        },
        {
          "title": "Timestamp",
          "value": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
          "short": true
        },
        {
          "title": "Duration",
          "value": "$(echo "$backup_results" | jq '[.[].duration] | add // 0') seconds",
          "short": true
        },
        {
          "title": "Details",
          "value": "$(echo "$backup_results" | jq -r '.[] | "• " + .type + ": " + .result' | tr '\n' '\n')",
          "short": false
        }
      ],
      "footer": "MoleculeFlow Backup Script",
      "ts": $(date +%s)
    }
  ]
}
EOF
)
    
    if curl -s -X POST -H 'Content-type: application/json' --data "$slack_payload" "$NOTIFICATION_SLACK_WEBHOOK" > /dev/null 2>&1; then
      log "INFO" "Slack notification sent successfully"
      notification_sent=true
    else
      log "ERROR" "Failed to send Slack notification"
    fi
  fi
  
  # Return whether notification was sent
  [ "$notification_sent" = true ]
}

# Main function
main() {
  local args=("$@")
  # Parse command line arguments
  parse_arguments "${args[@]}"
  
  # Set up logging
  LOG_FILE=$(setup_logging)
  
  log "INFO" "Starting backup job for environment: $ENVIRONMENT, type: $BACKUP_TYPE"
  
  # Check prerequisites from bootstrap.sh
  log "INFO" "Checking prerequisites"
  if ! check_prerequisites; then
    log "ERROR" "Prerequisites check failed"
    return 1
  fi
  
  # Load configuration
  if ! load_configuration "$ENVIRONMENT"; then
    log "ERROR" "Failed to load configuration"
    return 1
  fi
  
  # Initialize backup results array
  local backup_results=()
  
  # Perform backup operations based on backup type
  if [ "$BACKUP_TYPE" = "full" ] || [ "$BACKUP_TYPE" = "snapshot" ] || [ "$BACKUP_TYPE" = "incremental" ] || [ "$BACKUP_TYPE" = "logical" ]; then
    if [ -n "$DB_IDENTIFIER" ]; then
      # Generate snapshot identifier
      local snapshot_identifier="${DB_SNAPSHOT_PREFIX}-${ENVIRONMENT}-${BACKUP_TYPE}-$(date +%Y%m%d%H%M%S)"
      
      # Backup database
      local db_result
      db_result=$(backup_database "$DB_IDENTIFIER" "$BACKUP_TYPE" "$snapshot_identifier")
      
      backup_results+=("$db_result")
      
      # Verify backup integrity
      if ! verify_backup_integrity "$db_result"; then
        log "ERROR" "Database backup verification failed"
      fi
    else
      log "WARN" "Database identifier not configured, skipping database backup"
    fi
  fi
  
  # Backup S3 buckets
  if [ -n "$S3_BUCKETS" ]; then
    local s3_result
    s3_result=$(backup_s3_buckets $S3_BUCKETS)
    
    backup_results+=("$s3_result")
    
    # Verify backup integrity
    if ! verify_backup_integrity "$s3_result"; then
      log "ERROR" "S3 bucket backup verification failed"
    fi
  else
    log "WARN" "No S3 buckets configured for backup"
  fi
  
  # Backup ElastiCache
  if [ -n "$ELASTICACHE_IDENTIFIER" ]; then
    # Generate snapshot name
    local elasticache_snapshot_name="${ELASTICACHE_SNAPSHOT_PREFIX}-${ENVIRONMENT}-$(date +%Y%m%d%H%M%S)"
    
    local elasticache_result
    elasticache_result=$(backup_elasticache "$ELASTICACHE_IDENTIFIER" "$elasticache_snapshot_name")
    
    backup_results+=("$elasticache_result")
    
    # Verify backup integrity
    if ! verify_backup_integrity "$elasticache_result"; then
      log "ERROR" "ElastiCache backup verification failed"
    fi
  else
    log "INFO" "ElastiCache identifier not configured, skipping ElastiCache backup"
  fi
  
  # Backup configuration
  if [ "$CONFIG_BACKUP_ENABLED" = "true" ]; then
    local config_result
    config_result=$(backup_configuration "$ENVIRONMENT")
    
    backup_results+=("$config_result")
    
    # Verify backup integrity
    if ! verify_backup_integrity "$config_result"; then
      log "ERROR" "Configuration backup verification failed"
    fi
  else
    log "INFO" "Configuration backup disabled, skipping"
  fi
  
  # Cross-region replication
  if [ "$CROSS_REGION_REPLICATION" = "true" ] && [ -n "$SECONDARY_REGION" ]; then
    local destination_bucket="${CROSS_REGION_BUCKET:-$BACKUP_BUCKET-$SECONDARY_REGION}"
    
    local replication_result
    replication_result=$(cross_region_replication "$BACKUP_BUCKET" "$destination_bucket" "" "$SECONDARY_REGION")
    
    backup_results+=("$replication_result")
    
    # Verify backup integrity
    if ! verify_backup_integrity "$replication_result"; then
      log "ERROR" "Cross-region replication verification failed"
    fi
  fi
  
  # Clean up old backups
  local cleanup_result
  cleanup_result=$(cleanup_old_backups "$BACKUP_TYPE" "$BACKUP_RETENTION_DAYS")
  
  backup_results+=("$cleanup_result")
  
  # Format backup results as JSON array
  local backup_results_json
  backup_results_json="[$(printf "%s," "${backup_results[@]}" | sed 's/,$//')]"
  
  # Generate backup report
  local report_file
  report_file=$(generate_backup_report "$backup_results_json")
  
  # Determine overall status
  local overall_status
  overall_status=$(echo "$backup_results_json" | jq -r 'map(.result) | if all(. == "success") then "SUCCESS" elif any(. == "failed") then "FAILED" else "PARTIAL" end')
  
  # Send notification
  if ! send_notification "$backup_results_json" "$overall_status"; then
    log "WARN" "Failed to send backup notification"
  fi
  
  # Return appropriate exit code
  if [ "$overall_status" = "SUCCESS" ]; then
    log "INFO" "Backup job completed successfully"
    return 0
  elif [ "$overall_status" = "PARTIAL" ]; then
    log "WARN" "Backup job completed with partial success"
    return 2
  else
    log "ERROR" "Backup job failed"
    return 1
  fi
}

# Export backup function for use in scheduled jobs and CI/CD pipelines
export -f backup

# Run main function with passed arguments if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  main "$@"
  exit $?
fi