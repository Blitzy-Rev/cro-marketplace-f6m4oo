#!/usr/bin/env bash
#
# Bootstrap script for the Molecular Data Management and CRO Integration Platform
#
# This script verifies prerequisites, installs required tools, configures AWS credentials,
# and prepares the environment for deployment using Terraform and Ansible.
#
# Usage: ./bootstrap.sh -e|--environment <environment> [options]
#
# Version: 1.0.0
# Date: 2023-09-15
#

# Exit on error
set -e

# Global variables
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
LOG_FILE="${SCRIPT_DIR}/../logs/bootstrap_$(date +%Y%m%d_%H%M%S).log"
REQUIRED_TOOLS=("aws" "terraform" "ansible" "docker" "jq" "python3")
declare -A MIN_VERSIONS=(
  ["aws"]="2.0.0"
  ["terraform"]="1.5.0"
  ["ansible"]="2.14.0"
  ["docker"]="24.0.0"
  ["jq"]="1.6"
  ["python3"]="3.10.0"
)

# Setup logging
setup_logging() {
  mkdir -p "$(dirname "$LOG_FILE")"
  echo "$(date '+%Y-%m-%d %H:%M:%S') - Bootstrap script started" > "$LOG_FILE"
  echo "$(date '+%Y-%m-%d %H:%M:%S') - Environment: $ENVIRONMENT" >> "$LOG_FILE"
  echo "$(date '+%Y-%m-%d %H:%M:%S') - Parameters: $*" >> "$LOG_FILE"
  echo "$LOG_FILE"
}

# Logging function
log() {
  local level="$1"
  shift
  local message="$*"
  echo "$(date '+%Y-%m-%d %H:%M:%S') - [$level] $message" | tee -a "$LOG_FILE"
}

# Compare version strings
version_compare() {
  local version1="$1"
  local version2="$2"
  
  if [ "$version1" = "$version2" ]; then
    return 0  # Equal versions
  fi
  
  local IFS=.
  local i ver1=($version1) ver2=($version2)
  
  # Fill empty positions with zeros
  for ((i=${#ver1[@]}; i<${#ver2[@]}; i++)); do
    ver1[i]=0
  done
  for ((i=${#ver2[@]}; i<${#ver1[@]}; i++)); do
    ver2[i]=0
  done
  
  # Compare version segments
  for ((i=0; i<${#ver1[@]}; i++)); do
    if ((10#${ver1[i]} > 10#${ver2[i]})); then
      return 0  # version1 > version2
    elif ((10#${ver1[i]} < 10#${ver2[i]})); then
      return 1  # version1 < version2
    fi
  done
  
  return 0  # Equal versions (should not reach here)
}

# Check prerequisites
check_prerequisites() {
  log "INFO" "Checking prerequisites..."
  local missing_tools=()
  
  for tool in "${REQUIRED_TOOLS[@]}"; do
    if ! command -v "$tool" &> /dev/null; then
      log "WARN" "$tool is not installed"
      missing_tools+=("$tool")
    else
      local version
      case "$tool" in
        aws)
          version=$(aws --version 2>&1 | cut -d' ' -f1 | cut -d'/' -f2)
          ;;
        terraform)
          version=$(terraform version -json | jq -r '.terraform_version')
          ;;
        ansible)
          version=$(ansible --version | head -n1 | cut -d' ' -f2)
          ;;
        docker)
          version=$(docker --version | cut -d' ' -f3 | tr -d ',')
          ;;
        jq)
          version=$(jq --version | cut -d'-' -f2)
          ;;
        python3)
          version=$(python3 --version | cut -d' ' -f2)
          ;;
      esac
      
      if ! version_compare "$version" "${MIN_VERSIONS[$tool]}"; then
        log "WARN" "$tool version $version is less than required ${MIN_VERSIONS[$tool]}"
        missing_tools+=("$tool")
      else
        log "INFO" "$tool version $version ✓"
      fi
    fi
  done
  
  # Check AWS credentials
  if ! aws sts get-caller-identity &> /dev/null; then
    log "WARN" "AWS credentials are not configured properly"
    return 1
  else
    log "INFO" "AWS credentials are valid ✓"
  fi
  
  # Check for required environment variables
  if [ -z "$ENVIRONMENT" ]; then
    log "WARN" "ENVIRONMENT variable is not set"
    return 1
  fi
  
  if [ ${#missing_tools[@]} -eq 0 ]; then
    log "INFO" "All prerequisites are met ✓"
    return 0
  else
    log "WARN" "Missing prerequisites: ${missing_tools[*]}"
    export missing_tools
    return 1
  fi
}

# Install missing prerequisites
install_prerequisites() {
  local missing_tools=("$@")
  log "INFO" "Installing missing prerequisites: ${missing_tools[*]}"
  
  # Detect OS
  OS=""
  if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    if [ -f /etc/debian_version ]; then
      OS="debian"
    elif [ -f /etc/redhat-release ]; then
      OS="redhat"
    else
      OS="linux"
    fi
  elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
  else
    log "ERROR" "Unsupported OS: $OSTYPE"
    return 1
  fi
  
  log "INFO" "Detected OS: $OS"
  
  for tool in "${missing_tools[@]}"; do
    log "INFO" "Installing $tool..."
    
    case "$OS" in
      debian)
        case "$tool" in
          aws)
            curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
            unzip awscliv2.zip
            sudo ./aws/install
            rm -rf aws awscliv2.zip
            ;;
          terraform)
            wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
            echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
            sudo apt-get update && sudo apt-get install -y terraform
            ;;
          ansible)
            sudo apt-get update && sudo apt-get install -y ansible
            ;;
          docker)
            sudo apt-get update
            sudo apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release
            curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
            echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
            sudo apt-get update && sudo apt-get install -y docker-ce docker-ce-cli containerd.io
            sudo usermod -aG docker "$USER"
            ;;
          jq)
            sudo apt-get update && sudo apt-get install -y jq
            ;;
          python3)
            sudo apt-get update && sudo apt-get install -y python3 python3-pip
            ;;
        esac
        ;;
      redhat)
        case "$tool" in
          aws)
            curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
            unzip awscliv2.zip
            sudo ./aws/install
            rm -rf aws awscliv2.zip
            ;;
          terraform)
            sudo yum install -y yum-utils
            sudo yum-config-manager --add-repo https://rpm.releases.hashicorp.com/RHEL/hashicorp.repo
            sudo yum -y install terraform
            ;;
          ansible)
            sudo yum install -y ansible
            ;;
          docker)
            sudo yum install -y yum-utils
            sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
            sudo yum install -y docker-ce docker-ce-cli containerd.io
            sudo systemctl start docker
            sudo systemctl enable docker
            sudo usermod -aG docker "$USER"
            ;;
          jq)
            sudo yum install -y epel-release
            sudo yum install -y jq
            ;;
          python3)
            sudo yum install -y python3 python3-pip
            ;;
        esac
        ;;
      macos)
        # Check if Homebrew is installed
        if ! command -v brew &> /dev/null; then
          log "INFO" "Installing Homebrew..."
          /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        fi
        
        case "$tool" in
          aws)
            brew install awscli
            ;;
          terraform)
            brew install terraform
            ;;
          ansible)
            brew install ansible
            ;;
          docker)
            brew install --cask docker
            open -a Docker
            ;;
          jq)
            brew install jq
            ;;
          python3)
            brew install python
            ;;
        esac
        ;;
      *)
        log "ERROR" "Unsupported OS for automatic installation. Please install $tool manually."
        return 1
        ;;
    esac
    
    # Verify installation
    if ! command -v "$tool" &> /dev/null; then
      log "ERROR" "Failed to install $tool"
      return 1
    else
      log "INFO" "$tool installed successfully ✓"
    fi
  done
  
  log "INFO" "All prerequisites installed successfully ✓"
  return 0
}

# Setup AWS credentials
setup_aws_credentials() {
  local profile_name="$1"
  local region="$2"
  
  log "INFO" "Setting up AWS credentials for profile: $profile_name, region: $region"
  
  # Check if credentials already exist
  if aws configure list --profile "$profile_name" &> /dev/null; then
    log "INFO" "AWS profile $profile_name already exists"
    
    # Verify credentials are valid
    if aws sts get-caller-identity --profile "$profile_name" &> /dev/null; then
      log "INFO" "AWS credentials for profile $profile_name are valid ✓"
      
      # Set as default profile
      export AWS_PROFILE="$profile_name"
      export AWS_REGION="$region"
      log "INFO" "Set AWS_PROFILE=$profile_name and AWS_REGION=$region"
      
      return 0
    else
      log "WARN" "AWS credentials for profile $profile_name are invalid or expired"
    fi
  fi
  
  # Prompt for credentials
  log "INFO" "Please enter your AWS credentials for profile: $profile_name"
  read -p "AWS Access Key ID: " aws_access_key_id
  read -sp "AWS Secret Access Key: " aws_secret_access_key
  echo ""
  
  # Configure AWS CLI
  aws configure set aws_access_key_id "$aws_access_key_id" --profile "$profile_name"
  aws configure set aws_secret_access_key "$aws_secret_access_key" --profile "$profile_name"
  aws configure set region "$region" --profile "$profile_name"
  aws configure set output "json" --profile "$profile_name"
  
  # Verify credentials
  if aws sts get-caller-identity --profile "$profile_name" &> /dev/null; then
    log "INFO" "AWS credentials for profile $profile_name set up successfully ✓"
    
    # Set as default profile
    export AWS_PROFILE="$profile_name"
    export AWS_REGION="$region"
    log "INFO" "Set AWS_PROFILE=$profile_name and AWS_REGION=$region"
    
    return 0
  else
    log "ERROR" "Failed to set up AWS credentials for profile $profile_name"
    return 1
  fi
}

# Setup Terraform backend
setup_terraform_backend() {
  local environment="$1"
  local state_bucket="moleculeflow-terraform-state-$environment"
  local lock_table="moleculeflow-terraform-locks-$environment"
  local backend_file="${SCRIPT_DIR}/../terraform/backend-${environment}.tf"
  
  log "INFO" "Setting up Terraform backend for environment: $environment"
  
  # Create S3 bucket for Terraform state
  if ! aws s3api head-bucket --bucket "$state_bucket" 2>/dev/null; then
    log "INFO" "Creating S3 bucket for Terraform state: $state_bucket"
    
    # Create S3 bucket with versioning enabled
    if aws s3api create-bucket \
      --bucket "$state_bucket" \
      --create-bucket-configuration LocationConstraint="$AWS_REGION" \
      --region "$AWS_REGION"; then
      
      # Enable versioning
      aws s3api put-bucket-versioning \
        --bucket "$state_bucket" \
        --versioning-configuration Status=Enabled
      
      # Enable server-side encryption
      aws s3api put-bucket-encryption \
        --bucket "$state_bucket" \
        --server-side-encryption-configuration '{
          "Rules": [
            {
              "ApplyServerSideEncryptionByDefault": {
                "SSEAlgorithm": "AES256"
              }
            }
          ]
        }'
      
      log "INFO" "S3 bucket created and configured: $state_bucket ✓"
    else
      log "ERROR" "Failed to create S3 bucket: $state_bucket"
      return 1
    fi
  else
    log "INFO" "S3 bucket already exists: $state_bucket ✓"
  fi
  
  # Create DynamoDB table for state locking
  if ! aws dynamodb describe-table --table-name "$lock_table" &>/dev/null; then
    log "INFO" "Creating DynamoDB table for state locking: $lock_table"
    
    if aws dynamodb create-table \
      --table-name "$lock_table" \
      --attribute-definitions AttributeName=LockID,AttributeType=S \
      --key-schema AttributeName=LockID,KeyType=HASH \
      --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 \
      --region "$AWS_REGION"; then
      
      log "INFO" "DynamoDB table created: $lock_table ✓"
    else
      log "ERROR" "Failed to create DynamoDB table: $lock_table"
      return 1
    fi
  else
    log "INFO" "DynamoDB table already exists: $lock_table ✓"
  fi
  
  # Generate backend configuration file
  log "INFO" "Generating Terraform backend configuration file: $backend_file"
  
  mkdir -p "$(dirname "$backend_file")"
  cat > "$backend_file" << EOF
# Terraform backend configuration for $environment environment
# Generated by bootstrap.sh on $(date)

terraform {
  backend "s3" {
    bucket         = "$state_bucket"
    key            = "terraform.tfstate"
    region         = "$AWS_REGION"
    dynamodb_table = "$lock_table"
    encrypt        = true
  }
}
EOF
  
  log "INFO" "Terraform backend configuration generated: $backend_file ✓"
  return 0
}

# Setup environment variables
setup_environment_variables() {
  local environment="$1"
  local env_file="${SCRIPT_DIR}/../config/${environment}.env"
  
  log "INFO" "Setting up environment variables for: $environment"
  
  # Check if environment file exists
  if [ ! -f "$env_file" ]; then
    # Create config directory if it doesn't exist
    mkdir -p "$(dirname "$env_file")"
    
    # Create a default environment file if it doesn't exist
    log "INFO" "Environment file not found. Creating default environment file: $env_file"
    cat > "$env_file" << EOF
# Default environment configuration for $environment
# Generated by bootstrap.sh on $(date)

# AWS Configuration
AWS_REGION=${AWS_REGION_NAME}
AWS_PROFILE=${AWS_PROFILE_NAME}

# Application Configuration
APP_NAME=moleculeflow
APP_ENVIRONMENT=$environment
APP_DOMAIN=moleculeflow.example.com

# Infrastructure Configuration
VPC_CIDR=10.0.0.0/16
SUBNET_PUBLIC_CIDR=10.0.1.0/24,10.0.2.0/24,10.0.3.0/24
SUBNET_PRIVATE_CIDR=10.0.4.0/24,10.0.5.0/24,10.0.6.0/24

# Database Configuration
DB_INSTANCE_TYPE=db.r5.large
DB_STORAGE_GB=100
DB_MULTI_AZ=true

# ECS Configuration
ECS_CLUSTER_NAME=moleculeflow-$environment
ECS_INSTANCE_TYPE=t3.medium
ECS_MIN_INSTANCES=2
ECS_MAX_INSTANCES=10

# Lambda Configuration
LAMBDA_MEMORY_MB=1024
LAMBDA_TIMEOUT_SEC=30

# S3 Configuration
S3_LOGS_BUCKET=moleculeflow-logs-$environment
S3_DATA_BUCKET=moleculeflow-data-$environment
S3_DOCUMENTS_BUCKET=moleculeflow-documents-$environment

# Redis Configuration
REDIS_NODE_TYPE=cache.m5.large
REDIS_NUM_SHARDS=1
REDIS_REPLICAS_PER_SHARD=1

# Monitoring Configuration
ALARM_EMAIL=alerts@example.com
EOF
  fi
  
  # Load environment variables
  log "INFO" "Loading environment variables from: $env_file"
  
  while IFS='=' read -r key value || [ -n "$key" ]; do
    # Skip comments and empty lines
    if [[ "$key" =~ ^#.*$ ]] || [ -z "$key" ]; then
      continue
    fi
    
    # Trim whitespace
    key=$(echo "$key" | xargs)
    value=$(echo "$value" | xargs)
    
    # Export variable
    export "$key=$value"
    log "INFO" "Exported: $key=$value"
  done < "$env_file"
  
  # Set AWS environment variables if not already set
  if [ -z "$AWS_PROFILE" ]; then
    export AWS_PROFILE="${environment}"
    log "INFO" "Set AWS_PROFILE=$AWS_PROFILE"
  fi
  
  if [ -z "$AWS_REGION" ]; then
    export AWS_REGION="${AWS_REGION_NAME:-us-east-1}"
    log "INFO" "Set AWS_REGION=$AWS_REGION"
  fi
  
  # Set Terraform environment variables
  export TF_VAR_environment="$environment"
  export TF_VAR_region="$AWS_REGION"
  log "INFO" "Set TF_VAR_environment=$environment, TF_VAR_region=$AWS_REGION"
  
  # Set Ansible environment variables
  export ANSIBLE_HOST_KEY_CHECKING=False
  log "INFO" "Set ANSIBLE_HOST_KEY_CHECKING=False"
  
  log "INFO" "Environment variables set up successfully ✓"
  return 0
}

# Setup SSH keys for Ansible
setup_ssh_keys() {
  local environment="$1"
  local key_name="moleculeflow-${environment}"
  local key_file="${SCRIPT_DIR}/../ssh_keys/${key_name}"
  
  log "INFO" "Setting up SSH keys for environment: $environment"
  
  # Create directory for SSH keys
  mkdir -p "$(dirname "$key_file")"
  
  # Check if key already exists
  if [ -f "${key_file}" ] && [ -f "${key_file}.pub" ]; then
    log "INFO" "SSH key pair already exists: $key_name"
  else
    log "INFO" "Generating new SSH key pair: $key_name"
    
    # Generate new SSH key pair
    ssh-keygen -t rsa -b 4096 -f "$key_file" -N "" -C "moleculeflow-${environment}"
    
    if [ $? -ne 0 ]; then
      log "ERROR" "Failed to generate SSH key pair: $key_name"
      return 1
    fi
    
    log "INFO" "SSH key pair generated: $key_name ✓"
  fi
  
  # Set appropriate permissions
  chmod 600 "$key_file"
  
  # Check if key is already imported in AWS
  if ! aws ec2 describe-key-pairs --key-names "$key_name" &>/dev/null; then
    log "INFO" "Importing SSH public key to AWS EC2: $key_name"
    
    # Import public key to AWS EC2
    aws ec2 import-key-pair \
      --key-name "$key_name" \
      --public-key-material "fileb://${key_file}.pub"
    
    if [ $? -ne 0 ]; then
      log "ERROR" "Failed to import SSH public key to AWS EC2: $key_name"
      return 1
    fi
    
    log "INFO" "SSH public key imported to AWS EC2: $key_name ✓"
  else
    log "INFO" "SSH key already exists in AWS EC2: $key_name ✓"
  fi
  
  # Configure SSH agent
  log "INFO" "Configuring SSH agent with key: $key_name"
  
  # Start SSH agent if not already running
  if [ -z "$SSH_AUTH_SOCK" ]; then
    eval "$(ssh-agent -s)"
  fi
  
  # Add key to SSH agent
  ssh-add "$key_file"
  
  if [ $? -ne 0 ]; then
    log "ERROR" "Failed to add SSH key to agent: $key_name"
    return 1
  fi
  
  log "INFO" "SSH key added to agent: $key_name ✓"
  
  # Export SSH key path
  export ANSIBLE_SSH_PRIVATE_KEY_FILE="$key_file"
  log "INFO" "Set ANSIBLE_SSH_PRIVATE_KEY_FILE=$key_file"
  
  # Export SSH key name
  export TF_VAR_ssh_key_name="$key_name"
  log "INFO" "Set TF_VAR_ssh_key_name=$key_name"
  
  log "INFO" "SSH keys set up successfully ✓"
  return 0
}

# Setup Docker registry
setup_docker_registry() {
  local environment="$1"
  local registry_name="moleculeflow-${environment}"
  
  log "INFO" "Setting up Docker registry for environment: $environment"
  
  # Check if ECR registry exists
  local registry_url=""
  registry_url=$(aws ecr describe-repositories \
    --repository-names "$registry_name" \
    --query 'repositories[0].repositoryUri' \
    --output text 2>/dev/null)
  
  # Create ECR repository if it doesn't exist
  if [ $? -ne 0 ]; then
    log "INFO" "Creating ECR repository: $registry_name"
    
    registry_url=$(aws ecr create-repository \
      --repository-name "$registry_name" \
      --image-scanning-configuration scanOnPush=true \
      --query 'repository.repositoryUri' \
      --output text)
    
    if [ $? -ne 0 ]; then
      log "ERROR" "Failed to create ECR repository: $registry_name"
      return 1
    fi
    
    log "INFO" "ECR repository created: $registry_name ✓"
  else
    log "INFO" "ECR repository already exists: $registry_name ✓"
  fi
  
  # Get AWS account ID
  local aws_account_id
  aws_account_id=$(aws sts get-caller-identity --query 'Account' --output text)
  
  # Get ECR login password
  log "INFO" "Logging in to ECR registry: $registry_url"
  
  aws ecr get-login-password --region "$AWS_REGION" | \
    docker login --username AWS --password-stdin "${aws_account_id}.dkr.ecr.${AWS_REGION}.amazonaws.com"
  
  if [ $? -ne 0 ]; then
    log "ERROR" "Failed to log in to ECR registry: $registry_url"
    return 1
  fi
  
  log "INFO" "Logged in to ECR registry: $registry_url ✓"
  
  # Export registry URL
  export ECR_REPOSITORY_URL="$registry_url"
  export TF_VAR_ecr_repository_url="$registry_url"
  log "INFO" "Set ECR_REPOSITORY_URL=$registry_url"
  log "INFO" "Set TF_VAR_ecr_repository_url=$registry_url"
  
  log "INFO" "Docker registry set up successfully ✓"
  return 0
}

# Parse command line arguments
parse_arguments() {
  # Default values
  ENVIRONMENT=""
  FORCE_INSTALL=false
  SKIP_AWS_SETUP=false
  SKIP_SSH_SETUP=false
  SKIP_DOCKER_SETUP=false
  AWS_PROFILE_NAME=""
  AWS_REGION_NAME="us-east-1"
  
  # Parse arguments
  while [[ $# -gt 0 ]]; do
    case "$1" in
      -e|--environment)
        ENVIRONMENT="$2"
        shift 2
        ;;
      --force-install)
        FORCE_INSTALL=true
        shift
        ;;
      --skip-aws-setup)
        SKIP_AWS_SETUP=true
        shift
        ;;
      --skip-ssh-setup)
        SKIP_SSH_SETUP=true
        shift
        ;;
      --skip-docker-setup)
        SKIP_DOCKER_SETUP=true
        shift
        ;;
      --aws-profile)
        AWS_PROFILE_NAME="$2"
        shift 2
        ;;
      --aws-region)
        AWS_REGION_NAME="$2"
        shift 2
        ;;
      -h|--help)
        echo "Usage: $0 -e|--environment <environment> [options]"
        echo ""
        echo "Options:"
        echo "  -e, --environment <env>     Environment (dev, staging, prod)"
        echo "  --force-install             Force installation of missing prerequisites"
        echo "  --skip-aws-setup            Skip AWS credentials setup"
        echo "  --skip-ssh-setup            Skip SSH key setup"
        echo "  --skip-docker-setup         Skip Docker registry setup"
        echo "  --aws-profile <profile>     AWS profile name (default: environment name)"
        echo "  --aws-region <region>       AWS region (default: us-east-1)"
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
  if [ -z "$ENVIRONMENT" ]; then
    echo "Error: Environment not specified"
    echo "Use -e or --environment to specify environment (dev, staging, prod)"
    exit 1
  fi
  
  # Validate environment value
  if [ "$ENVIRONMENT" != "dev" ] && [ "$ENVIRONMENT" != "staging" ] && [ "$ENVIRONMENT" != "prod" ]; then
    echo "Error: Invalid environment: $ENVIRONMENT"
    echo "Valid environments are: dev, staging, prod"
    exit 1
  fi
  
  # Set AWS profile name if not specified
  if [ -z "$AWS_PROFILE_NAME" ]; then
    AWS_PROFILE_NAME="$ENVIRONMENT"
  fi
  
  # Export variables
  export ENVIRONMENT
  export FORCE_INSTALL
  export SKIP_AWS_SETUP
  export SKIP_SSH_SETUP
  export SKIP_DOCKER_SETUP
  export AWS_PROFILE_NAME
  export AWS_REGION_NAME
  
  return 0
}

# Main function
main() {
  # Parse arguments
  parse_arguments "$@"
  
  # Set up logging
  setup_logging "$@"
  
  log "INFO" "Starting bootstrap process for environment: $ENVIRONMENT"
  log "INFO" "AWS Profile: $AWS_PROFILE_NAME, AWS Region: $AWS_REGION_NAME"
  
  # Check prerequisites
  local prereq_status=0
  check_prerequisites || prereq_status=$?
  
  if [ $prereq_status -ne 0 ]; then
    if [ "$FORCE_INSTALL" = true ]; then
      log "INFO" "Force install enabled, attempting to install missing prerequisites"
      if ! install_prerequisites "${missing_tools[@]}"; then
        log "ERROR" "Failed to install prerequisites"
        return 1
      fi
    else
      log "ERROR" "Prerequisites check failed. Use --force-install to attempt automatic installation."
      return 1
    fi
  fi
  
  # Set up AWS credentials
  if [ "$SKIP_AWS_SETUP" != true ]; then
    if ! setup_aws_credentials "$AWS_PROFILE_NAME" "$AWS_REGION_NAME"; then
      log "ERROR" "Failed to set up AWS credentials"
      return 1
    fi
  else
    log "INFO" "Skipping AWS credentials setup"
    export AWS_PROFILE="$AWS_PROFILE_NAME"
    export AWS_REGION="$AWS_REGION_NAME"
  fi
  
  # Set up Terraform backend
  if ! setup_terraform_backend "$ENVIRONMENT"; then
    log "ERROR" "Failed to set up Terraform backend"
    return 1
  fi
  
  # Set up environment variables
  if ! setup_environment_variables "$ENVIRONMENT"; then
    log "ERROR" "Failed to set up environment variables"
    return 1
  fi
  
  # Set up SSH keys
  if [ "$SKIP_SSH_SETUP" != true ]; then
    if ! setup_ssh_keys "$ENVIRONMENT"; then
      log "ERROR" "Failed to set up SSH keys"
      return 1
    fi
  else
    log "INFO" "Skipping SSH key setup"
  fi
  
  # Set up Docker registry
  if [ "$SKIP_DOCKER_SETUP" != true ]; then
    if ! setup_docker_registry "$ENVIRONMENT"; then
      log "ERROR" "Failed to set up Docker registry"
      return 1
    fi
  else
    log "INFO" "Skipping Docker registry setup"
  fi
  
  log "INFO" "Bootstrap process completed successfully ✓"
  log "INFO" "You can now proceed with deployment using Terraform and Ansible"
  log "INFO" "Environment: $ENVIRONMENT"
  log "INFO" "AWS Profile: $AWS_PROFILE"
  log "INFO" "AWS Region: $AWS_REGION"
  
  return 0
}

# Make check_prerequisites function available for export
export -f check_prerequisites

# Run main function with passed arguments
main "$@"
exit $?