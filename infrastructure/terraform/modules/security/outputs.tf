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