# ----------------------------------------------------------------------------------------------------------------------
# REQUIRED PARAMETERS
# These variables must be set when using this module.
# ----------------------------------------------------------------------------------------------------------------------

variable "environment" {
  description = "Environment name (dev, staging, prod) for resource naming and tagging"
  type        = string
}

variable "region" {
  description = "AWS region for resource deployment"
  type        = string
}

variable "tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
}

# ----------------------------------------------------------------------------------------------------------------------
# OPTIONAL PARAMETERS
# These variables have defaults, but may be overridden.
# ----------------------------------------------------------------------------------------------------------------------

variable "monitoring" {
  description = "Monitoring configuration settings"
  type = object({
    # CloudWatch Settings
    alarm_email                = string
    dashboard_name_prefix      = string
    log_retention_days         = number
    enable_detailed_monitoring = bool
    metric_namespace           = string
    alarm_evaluation_periods   = number
    alarm_period_seconds       = number
    
    # Prometheus Settings
    enable_prometheus          = bool
    prometheus_version         = string
    prometheus_retention_days  = number
    scrape_interval_seconds    = number
    
    # Grafana Settings
    enable_grafana             = bool
    grafana_version            = string
    grafana_admin_password     = string
    
    # AlertManager Settings
    enable_alertmanager        = bool
    alertmanager_version       = string
    slack_webhook_url          = string
    pagerduty_service_key      = string
  })
  default = {
    # CloudWatch Settings
    alarm_email                = "alerts@example.com"
    dashboard_name_prefix      = "molecule-platform"
    log_retention_days         = 30
    enable_detailed_monitoring = true
    metric_namespace           = "MoleculePlatform"
    alarm_evaluation_periods   = 3
    alarm_period_seconds       = 60
    
    # Prometheus Settings
    enable_prometheus          = true
    prometheus_version         = "2.45.0"
    prometheus_retention_days  = 15
    scrape_interval_seconds    = 30
    
    # Grafana Settings
    enable_grafana             = true
    grafana_version            = "9.5.1"
    grafana_admin_password     = "ChangeMe123!" # This should be overridden in production
    
    # AlertManager Settings
    enable_alertmanager        = true
    alertmanager_version       = "0.25.0"
    slack_webhook_url          = ""  # Should be provided in actual deployment
    pagerduty_service_key      = ""  # Should be provided in actual deployment
  }
}

# ----------------------------------------------------------------------------------------------------------------------
# MODULE DEPENDENCIES
# These variables contain outputs from other modules that this module requires.
# ----------------------------------------------------------------------------------------------------------------------

variable "compute_outputs" {
  description = "Outputs from the compute module for monitoring ECS services and load balancers"
  type = object({
    cluster_id              = string
    frontend_service_name   = string
    backend_service_name    = string
    molecule_service_name   = string
    worker_service_name     = string
    alb_arn                 = string
    cloudwatch_log_groups   = map(string)
  })
}

variable "database_outputs" {
  description = "Outputs from the database module for monitoring RDS and ElastiCache instances"
  type = object({
    rds_instance_id              = string
    rds_read_replica_ids         = list(string)
    elasticache_replication_group_id = string
  })
}

variable "storage_outputs" {
  description = "Outputs from the storage module for monitoring S3 buckets"
  type = object({
    document_bucket_id = string
    csv_bucket_id      = string
    results_bucket_id  = string
    backup_bucket_id   = string
  })
}