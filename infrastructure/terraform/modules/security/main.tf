# -----------------------------------------------------------------------------
# Provider Requirements
# -----------------------------------------------------------------------------
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
}

# -----------------------------------------------------------------------------
# Local Variables
# -----------------------------------------------------------------------------
locals {
  name_prefix = "${var.project_name}-${var.environment}"
  
  common_tags = merge(
    var.tags,
    {
      Environment = var.environment
      Project     = var.project_name
      ManagedBy   = "terraform"
    }
  )
  
  # Policy documents for IAM roles
  cognito_authenticated_trust_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Federated = "cognito-identity.amazonaws.com"
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringEquals = {
            "cognito-identity.amazonaws.com:aud" = aws_cognito_identity_pool.main.id
          }
          "ForAnyValue:StringLike" = {
            "cognito-identity.amazonaws.com:amr" = "authenticated"
          }
        }
      }
    ]
  })
  
  cognito_unauthenticated_trust_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Federated = "cognito-identity.amazonaws.com"
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringEquals = {
            "cognito-identity.amazonaws.com:aud" = aws_cognito_identity_pool.main.id
          }
          "ForAnyValue:StringLike" = {
            "cognito-identity.amazonaws.com:amr" = "unauthenticated"
          }
        }
      }
    ]
  })
  
  ecs_task_execution_trust_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
  
  config_service_trust_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "config.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
  
  # S3 bucket policies
  cloudtrail_bucket_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid = "AWSCloudTrailAclCheck"
        Effect = "Allow"
        Principal = {
          Service = "cloudtrail.amazonaws.com"
        }
        Action = "s3:GetBucketAcl"
        Resource = aws_s3_bucket.cloudtrail[0].arn
      },
      {
        Sid = "AWSCloudTrailWrite"
        Effect = "Allow"
        Principal = {
          Service = "cloudtrail.amazonaws.com"
        }
        Action = "s3:PutObject"
        Resource = "${aws_s3_bucket.cloudtrail[0].arn}/AWSLogs/*"
        Condition = {
          StringEquals = {
            "s3:x-amz-acl" = "bucket-owner-full-control"
          }
        }
      },
      {
        Sid = "EnforceSSLOnly"
        Effect = "Deny"
        Principal = "*"
        Action = "s3:*"
        Resource = [
          aws_s3_bucket.cloudtrail[0].arn,
          "${aws_s3_bucket.cloudtrail[0].arn}/*"
        ]
        Condition = {
          Bool = {
            "aws:SecureTransport" = "false"
          }
        }
      }
    ]
  })
  
  # IAM Policies
  authenticated_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "mobileanalytics:PutEvents",
          "cognito-sync:*"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = concat(
          var.s3_bucket_arns,
          [for arn in var.s3_bucket_arns : "${arn}/*"]
        )
      }
    ]
  })
  
  unauthenticated_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "mobileanalytics:PutEvents",
          "cognito-sync:*"
        ]
        Resource = "*"
      }
    ]
  })
  
  # Task-specific policies
  frontend_task_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = concat(
          var.s3_bucket_arns,
          [for arn in var.s3_bucket_arns : "${arn}/*"]
        )
      }
    ]
  })
  
  backend_task_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket",
          "s3:DeleteObject"
        ]
        Resource = concat(
          var.s3_bucket_arns,
          [for arn in var.s3_bucket_arns : "${arn}/*"]
        )
      },
      {
        Effect = "Allow"
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes",
          "sqs:SendMessage"
        ]
        Resource = "*" # This should be restricted to specific SQS queues in production
      },
      {
        Effect = "Allow"
        Action = [
          "sns:Publish"
        ]
        Resource = "*" # This should be restricted to specific SNS topics in production
      },
      {
        Effect = "Allow"
        Action = [
          "kms:Decrypt",
          "kms:GenerateDataKey"
        ]
        Resource = aws_kms_key.main.arn
      }
    ]
  })
  
  worker_task_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket"
        ]
        Resource = concat(
          var.s3_bucket_arns,
          [for arn in var.s3_bucket_arns : "${arn}/*"]
        )
      },
      {
        Effect = "Allow"
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes"
        ]
        Resource = "*" # This should be restricted to specific SQS queues in production
      },
      {
        Effect = "Allow"
        Action = [
          "sns:Subscribe",
          "sns:Receive"
        ]
        Resource = "*" # This should be restricted to specific SNS topics in production
      },
      {
        Effect = "Allow"
        Action = [
          "kms:Decrypt"
        ]
        Resource = aws_kms_key.main.arn
      }
    ]
  })
}

# -----------------------------------------------------------------------------
# KMS Encryption Key
# -----------------------------------------------------------------------------
resource "aws_kms_key" "main" {
  description             = "KMS key for encrypting data in ${var.project_name} ${var.environment} environment"
  enable_key_rotation     = var.enable_key_rotation
  deletion_window_in_days = var.kms_key_deletion_window
  
  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}-key"
    }
  )
}

resource "aws_kms_alias" "main" {
  name          = "alias/${local.name_prefix}-key"
  target_key_id = aws_kms_key.main.key_id
}

# -----------------------------------------------------------------------------
# Cognito User Pool and Identity Pool
# -----------------------------------------------------------------------------
resource "aws_cognito_user_pool" "main" {
  name = "${var.cognito_user_pool_name}-${var.environment}"
  
  # Password policy
  password_policy {
    minimum_length                   = var.password_policy.minimum_length
    require_lowercase                = var.password_policy.require_lowercase
    require_uppercase                = var.password_policy.require_uppercase
    require_numbers                  = var.password_policy.require_numbers
    require_symbols                  = var.password_policy.require_symbols
    temporary_password_validity_days = var.password_policy.temporary_password_validity_days
  }
  
  # MFA configuration
  mfa_configuration = var.enable_mfa ? "OPTIONAL" : "OFF"
  
  # User account recovery options
  account_recovery_setting {
    recovery_mechanism {
      name     = "verified_email"
      priority = 1
    }
  }
  
  # Admin creation settings
  admin_create_user_config {
    allow_admin_create_user_only = true
    
    invite_message_template {
      email_message = "Your username is {username} and temporary password is {####}. Please login to change your password."
      email_subject = "Your temporary password for ${var.project_name}"
      sms_message   = "Your username is {username} and temporary password is {####}."
    }
  }
  
  # Email configuration
  email_configuration {
    email_sending_account = "COGNITO_DEFAULT"
  }
  
  # Advanced security features
  user_pool_add_ons {
    advanced_security_mode = "ENFORCED"
  }
  
  # Schema attributes
  schema {
    name                = "email"
    attribute_data_type = "String"
    mutable             = true
    required            = true
    
    string_attribute_constraints {
      min_length = 1
      max_length = 256
    }
  }
  
  schema {
    name                = "name"
    attribute_data_type = "String"
    mutable             = true
    required            = true
    
    string_attribute_constraints {
      min_length = 1
      max_length = 256
    }
  }
  
  schema {
    name                = "organization"
    attribute_data_type = "String"
    mutable             = true
    required            = false
    
    string_attribute_constraints {
      min_length = 1
      max_length = 256
    }
  }
  
  schema {
    name                = "role"
    attribute_data_type = "String"
    mutable             = true
    required            = false
    
    string_attribute_constraints {
      min_length = 1
      max_length = 256
    }
  }
  
  tags = local.common_tags
}

resource "aws_cognito_user_pool_client" "app" {
  name                         = "${local.name_prefix}-client"
  user_pool_id                 = aws_cognito_user_pool.main.id
  
  callback_urls                = var.callback_urls
  logout_urls                  = var.logout_urls
  allowed_oauth_flows          = var.allowed_oauth_flows
  allowed_oauth_scopes         = var.allowed_oauth_scopes
  supported_identity_providers = ["COGNITO"]
  
  generate_secret              = true
  refresh_token_validity       = 30
  access_token_validity        = 1
  id_token_validity            = 1
  
  token_validity_units {
    access_token  = "hours"
    id_token      = "hours"
    refresh_token = "days"
  }
  
  explicit_auth_flows = [
    "ALLOW_ADMIN_USER_PASSWORD_AUTH",
    "ALLOW_CUSTOM_AUTH",
    "ALLOW_REFRESH_TOKEN_AUTH",
    "ALLOW_USER_PASSWORD_AUTH",
    "ALLOW_USER_SRP_AUTH"
  ]
  
  prevent_user_existence_errors = "ENABLED"
  enable_token_revocation       = true
}

resource "aws_cognito_identity_pool" "main" {
  identity_pool_name               = "${var.cognito_identity_pool_name}-${var.environment}"
  allow_unauthenticated_identities = var.allow_unauthenticated_identities
  
  cognito_identity_providers {
    client_id               = aws_cognito_user_pool_client.app.id
    provider_name           = aws_cognito_user_pool.main.endpoint
    server_side_token_check = true
  }
  
  # This dependency is needed because the identity_providers reference the user pool
  depends_on = [aws_cognito_user_pool.main, aws_cognito_user_pool_client.app]
}

# -----------------------------------------------------------------------------
# IAM Roles and Policies for Cognito Identity Pool
# -----------------------------------------------------------------------------
resource "aws_iam_role" "authenticated" {
  name = "${local.name_prefix}-cognito-authenticated"
  
  assume_role_policy = local.cognito_authenticated_trust_policy
  
  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}-cognito-authenticated"
    }
  )
  
  # This dependency is needed because the assume_role_policy references the identity pool
  depends_on = [aws_cognito_identity_pool.main]
}

resource "aws_iam_role_policy" "authenticated" {
  name   = "${local.name_prefix}-cognito-authenticated-policy"
  role   = aws_iam_role.authenticated.id
  policy = local.authenticated_policy
}

resource "aws_iam_role" "unauthenticated" {
  count = var.allow_unauthenticated_identities ? 1 : 0
  
  name = "${local.name_prefix}-cognito-unauthenticated"
  
  assume_role_policy = local.cognito_unauthenticated_trust_policy
  
  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}-cognito-unauthenticated"
    }
  )
  
  # This dependency is needed because the assume_role_policy references the identity pool
  depends_on = [aws_cognito_identity_pool.main]
}

resource "aws_iam_role_policy" "unauthenticated" {
  count = var.allow_unauthenticated_identities ? 1 : 0
  
  name   = "${local.name_prefix}-cognito-unauthenticated-policy"
  role   = aws_iam_role.unauthenticated[0].id
  policy = local.unauthenticated_policy
}

resource "aws_cognito_identity_pool_role_attachment" "main" {
  identity_pool_id = aws_cognito_identity_pool.main.id
  
  roles = var.allow_unauthenticated_identities ? {
    "authenticated"   = aws_iam_role.authenticated.arn
    "unauthenticated" = aws_iam_role.unauthenticated[0].arn
  } : {
    "authenticated" = aws_iam_role.authenticated.arn
  }
}

# -----------------------------------------------------------------------------
# IAM Roles for ECS Tasks
# -----------------------------------------------------------------------------
resource "aws_iam_role" "task_execution" {
  name = "${local.name_prefix}-task-execution-role"
  
  assume_role_policy = local.ecs_task_execution_trust_policy
  
  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}-task-execution-role"
    }
  )
}

resource "aws_iam_role_policy_attachment" "task_execution" {
  role       = aws_iam_role.task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# Create service-specific task roles
resource "aws_iam_role" "task_frontend" {
  name = "${local.name_prefix}-task-frontend-role"
  
  assume_role_policy = local.ecs_task_execution_trust_policy
  
  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}-task-frontend-role"
      Service = "frontend"
    }
  )
}

resource "aws_iam_role_policy" "task_frontend" {
  name   = "${local.name_prefix}-task-frontend-policy"
  role   = aws_iam_role.task_frontend.id
  policy = local.frontend_task_policy
}

resource "aws_iam_role" "task_backend" {
  name = "${local.name_prefix}-task-backend-role"
  
  assume_role_policy = local.ecs_task_execution_trust_policy
  
  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}-task-backend-role"
      Service = "backend"
    }
  )
}

resource "aws_iam_role_policy" "task_backend" {
  name   = "${local.name_prefix}-task-backend-policy"
  role   = aws_iam_role.task_backend.id
  policy = local.backend_task_policy
}

resource "aws_iam_role" "task_worker" {
  name = "${local.name_prefix}-task-worker-role"
  
  assume_role_policy = local.ecs_task_execution_trust_policy
  
  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}-task-worker-role"
      Service = "worker"
    }
  )
}

resource "aws_iam_role_policy" "task_worker" {
  name   = "${local.name_prefix}-task-worker-policy"
  role   = aws_iam_role.task_worker.id
  policy = local.worker_task_policy
}

# -----------------------------------------------------------------------------
# WAF Configuration
# -----------------------------------------------------------------------------
resource "aws_waf_ipset" "blocklist" {
  count = var.enable_waf ? 1 : 0
  
  name = "${local.name_prefix}-blocklist"
  
  # Initially empty, to be populated by security monitoring
  ip_set_descriptors = []
}

resource "aws_waf_rule" "ip_blacklist" {
  count = var.enable_waf ? 1 : 0
  
  name        = "${local.name_prefix}-ip-blacklist"
  metric_name = "${replace(local.name_prefix, "-", "")}IPBlacklist"
  
  predicates {
    data_id = aws_waf_ipset.blocklist[0].id
    negated = false
    type    = "IPMatch"
  }
}

resource "aws_waf_sql_injection_match_set" "sql_injection" {
  count = var.enable_waf ? 1 : 0
  
  name = "${local.name_prefix}-sql-injection-match-set"
  
  sql_injection_match_tuples {
    text_transformation = "URL_DECODE"
    
    field_to_match {
      type = "QUERY_STRING"
    }
  }
  
  sql_injection_match_tuples {
    text_transformation = "URL_DECODE"
    
    field_to_match {
      type = "BODY"
    }
  }
  
  sql_injection_match_tuples {
    text_transformation = "URL_DECODE"
    
    field_to_match {
      type = "URI"
    }
  }
}

resource "aws_waf_rule" "sql_injection" {
  count = var.enable_waf ? 1 : 0
  
  name        = "${local.name_prefix}-sql-injection-protection"
  metric_name = "${replace(local.name_prefix, "-", "")}SQLInjectionProtection"
  
  predicates {
    data_id = aws_waf_sql_injection_match_set.sql_injection[0].id
    negated = false
    type    = "SqlInjectionMatch"
  }
}

resource "aws_waf_xss_match_set" "xss" {
  count = var.enable_waf ? 1 : 0
  
  name = "${local.name_prefix}-xss-match-set"
  
  xss_match_tuples {
    text_transformation = "URL_DECODE"
    
    field_to_match {
      type = "QUERY_STRING"
    }
  }
  
  xss_match_tuples {
    text_transformation = "URL_DECODE"
    
    field_to_match {
      type = "BODY"
    }
  }
  
  xss_match_tuples {
    text_transformation = "URL_DECODE"
    
    field_to_match {
      type = "URI"
    }
  }
}

resource "aws_waf_rule" "xss" {
  count = var.enable_waf ? 1 : 0
  
  name        = "${local.name_prefix}-xss-protection"
  metric_name = "${replace(local.name_prefix, "-", "")}XSSProtection"
  
  predicates {
    data_id = aws_waf_xss_match_set.xss[0].id
    negated = false
    type    = "XssMatch"
  }
}

resource "aws_waf_web_acl" "main" {
  count = var.enable_waf ? 1 : 0
  
  name        = "${local.name_prefix}-web-acl"
  metric_name = "${replace(local.name_prefix, "-", "")}WebACL"
  
  default_action {
    type = "ALLOW"
  }
  
  rules {
    action {
      type = "BLOCK"
    }
    priority = 1
    rule_id  = aws_waf_rule.ip_blacklist[0].id
    type     = "REGULAR"
  }
  
  rules {
    action {
      type = "BLOCK"
    }
    priority = 2
    rule_id  = aws_waf_rule.sql_injection[0].id
    type     = "REGULAR"
  }
  
  rules {
    action {
      type = "BLOCK"
    }
    priority = 3
    rule_id  = aws_waf_rule.xss[0].id
    type     = "REGULAR"
  }
  
  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}-web-acl"
    }
  )
}

# -----------------------------------------------------------------------------
# GuardDuty
# -----------------------------------------------------------------------------
resource "aws_guardduty_detector" "main" {
  count = var.enable_guardduty ? 1 : 0
  
  enable = true
  
  finding_publishing_frequency = "SIX_HOURS"
  
  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}-guardduty-detector"
    }
  )
}

# -----------------------------------------------------------------------------
# CloudTrail
# -----------------------------------------------------------------------------
resource "aws_s3_bucket" "cloudtrail" {
  count = var.enable_cloudtrail ? 1 : 0
  
  bucket = "${local.name_prefix}-cloudtrail-logs"
  
  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}-cloudtrail-logs"
    }
  )
}

resource "aws_s3_bucket_policy" "cloudtrail" {
  count = var.enable_cloudtrail ? 1 : 0
  
  bucket = aws_s3_bucket.cloudtrail[0].id
  policy = local.cloudtrail_bucket_policy
}

resource "aws_cloudtrail" "main" {
  count = var.enable_cloudtrail ? 1 : 0
  
  name                          = "${local.name_prefix}-trail"
  s3_bucket_name                = aws_s3_bucket.cloudtrail[0].id
  include_global_service_events = true
  is_multi_region_trail         = true
  enable_log_file_validation    = true
  
  event_selector {
    read_write_type           = "All"
    include_management_events = true
    
    data_resource {
      type   = "AWS::S3::Object"
      values = ["arn:aws:s3:::"]
    }
  }
  
  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}-trail"
    }
  )
}

# -----------------------------------------------------------------------------
# AWS Config
# -----------------------------------------------------------------------------
resource "aws_iam_role" "config" {
  count = var.enable_config ? 1 : 0
  
  name = "${local.name_prefix}-config-role"
  
  assume_role_policy = local.config_service_trust_policy
  
  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}-config-role"
    }
  )
}

resource "aws_iam_role_policy_attachment" "config" {
  count = var.enable_config ? 1 : 0
  
  role       = aws_iam_role.config[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWS_ConfigRole"
}

resource "aws_config_configuration_recorder" "main" {
  count = var.enable_config ? 1 : 0
  
  name     = "${local.name_prefix}-config-recorder"
  role_arn = aws_iam_role.config[0].arn
  
  recording_group {
    all_supported                 = true
    include_global_resource_types = true
  }
}

resource "aws_config_delivery_channel" "main" {
  count = var.enable_config ? 1 : 0
  
  name           = "${local.name_prefix}-config-delivery-channel"
  s3_bucket_name = aws_s3_bucket.cloudtrail[0].id
  
  snapshot_delivery_properties {
    delivery_frequency = "One_Day"
  }
  
  depends_on = [aws_config_configuration_recorder.main]
}

# -----------------------------------------------------------------------------
# VPN Security Group
# -----------------------------------------------------------------------------
resource "aws_security_group" "vpn" {
  count = var.enable_vpn ? 1 : 0
  
  name        = "${local.name_prefix}-vpn-sg"
  description = "Security group for VPN connections to ${var.project_name} ${var.environment} environment"
  vpc_id      = var.vpc_id
  
  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}-vpn-sg"
    }
  )
}

resource "aws_security_group_rule" "vpn_ingress" {
  count = var.enable_vpn ? length(var.vpn_cidr_blocks) : 0
  
  security_group_id = aws_security_group.vpn[0].id
  type              = "ingress"
  from_port         = 0
  to_port           = 65535
  protocol          = "tcp"
  cidr_blocks       = [var.vpn_cidr_blocks[count.index]]
  description       = "Allow all TCP traffic from VPN CIDR: ${var.vpn_cidr_blocks[count.index]}"
}

# -----------------------------------------------------------------------------
# Data Sources
# -----------------------------------------------------------------------------
data "aws_caller_identity" "current" {}

# -----------------------------------------------------------------------------
# Outputs
# -----------------------------------------------------------------------------
output "kms_key_id" {
  description = "ID of the KMS encryption key for data protection"
  value       = aws_kms_key.main.key_id
}

output "kms_key_arn" {
  description = "ARN of the KMS encryption key for data protection"
  value       = aws_kms_key.main.arn
}

output "waf_web_acl_id" {
  description = "ID of the WAF Web ACL for application protection"
  value       = var.enable_waf ? aws_waf_web_acl.main[0].id : null
}

output "cognito_user_pool_id" {
  description = "ID of the Cognito user pool for authentication"
  value       = aws_cognito_user_pool.main.id
}

output "cognito_user_pool_client_id" {
  description = "ID of the Cognito user pool client for application integration"
  value       = aws_cognito_user_pool_client.app.id
}

output "cognito_identity_pool_id" {
  description = "ID of the Cognito identity pool for federated identities"
  value       = aws_cognito_identity_pool.main.id
}

output "task_execution_role_arn" {
  description = "ARN of the ECS task execution role for container permissions"
  value       = aws_iam_role.task_execution.arn
}

output "task_role_arns" {
  description = "Map of ARNs for task-specific IAM roles (frontend, backend, worker)"
  value = {
    frontend = aws_iam_role.task_frontend.arn
    backend  = aws_iam_role.task_backend.arn
    worker   = aws_iam_role.task_worker.arn
  }
}

output "cloudtrail_bucket_name" {
  description = "Name of the S3 bucket for CloudTrail logs"
  value       = var.enable_cloudtrail ? aws_s3_bucket.cloudtrail[0].id : null
}

output "vpn_security_group_id" {
  description = "ID of the VPN security group for secure administrative access"
  value       = var.enable_vpn ? aws_security_group.vpn[0].id : null
}