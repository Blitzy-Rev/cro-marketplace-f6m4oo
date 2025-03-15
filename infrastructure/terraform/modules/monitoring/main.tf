# ----------------------------------------------------------------------------
# Monitoring Module for Molecular Data Management and CRO Integration Platform
# ----------------------------------------------------------------------------
# This module provisions CloudWatch resources, alarms, and dashboards for
# comprehensive monitoring of the platform's performance, availability, and
# security. It implements various monitoring components to track system metrics,
# logs, and compliance data across all platform services.
# ----------------------------------------------------------------------------

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
}

# Create locals for resource naming and configuration
locals {
  environment_prefix = "${var.environment}-${var.monitoring.dashboard_name_prefix}"
  
  # Common tags for all resources
  monitoring_tags = merge(var.tags, {
    Module      = "Monitoring"
    Environment = var.environment
  })
  
  # Service dimensions for alarms
  frontend_service_dimensions = {
    ClusterName = var.compute_outputs.cluster_id
    ServiceName = var.compute_outputs.frontend_service_name
  }
  
  backend_service_dimensions = {
    ClusterName = var.compute_outputs.cluster_id
    ServiceName = var.compute_outputs.backend_service_name
  }
  
  molecule_service_dimensions = {
    ClusterName = var.compute_outputs.cluster_id
    ServiceName = var.compute_outputs.molecule_service_name
  }
  
  worker_service_dimensions = {
    ClusterName = var.compute_outputs.cluster_id
    ServiceName = var.compute_outputs.worker_service_name
  }
  
  # Database dimensions
  rds_dimensions = {
    DBInstanceIdentifier = var.database_outputs.rds_instance_id
  }
  
  elasticache_dimensions = {
    ReplicationGroupId = var.database_outputs.elasticache_replication_group_id
  }
  
  # S3 bucket dimensions
  document_bucket_dimensions = {
    BucketName = var.storage_outputs.document_bucket_id
  }
  
  csv_bucket_dimensions = {
    BucketName = var.storage_outputs.csv_bucket_id
  }
  
  results_bucket_dimensions = {
    BucketName = var.storage_outputs.results_bucket_id
  }
}

# ----------------------------------------------------------------------------
# SNS Topics for alerts
# ----------------------------------------------------------------------------

# Critical alerts (P1) - requires immediate attention
resource "aws_sns_topic" "critical_alarms" {
  name = "${local.environment_prefix}-critical-alarms"
  tags = local.monitoring_tags
}

# Warning alerts (P2) - requires attention within SLA
resource "aws_sns_topic" "warning_alarms" {
  name = "${local.environment_prefix}-warning-alarms"
  tags = local.monitoring_tags
}

# Info alerts (P3) - for awareness, non-critical
resource "aws_sns_topic" "info_alarms" {
  name = "${local.environment_prefix}-info-alarms"
  tags = local.monitoring_tags
}

# Subscription for critical alerts
resource "aws_sns_topic_subscription" "critical_email" {
  topic_arn = aws_sns_topic.critical_alarms.arn
  protocol  = "email"
  endpoint  = var.monitoring.alarm_email
}

# Subscription for warning alerts
resource "aws_sns_topic_subscription" "warning_email" {
  topic_arn = aws_sns_topic.warning_alarms.arn
  protocol  = "email"
  endpoint  = var.monitoring.alarm_email
}

# ----------------------------------------------------------------------------
# CloudWatch Alarms - ECS Services
# ----------------------------------------------------------------------------

# Frontend Service CPU Utilization Alarm
resource "aws_cloudwatch_metric_alarm" "frontend_cpu_high" {
  alarm_name          = "${local.environment_prefix}-frontend-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = var.monitoring.alarm_evaluation_periods
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = var.monitoring.alarm_period_seconds
  statistic           = "Average"
  threshold           = 70
  alarm_description   = "Frontend service CPU utilization is too high"
  alarm_actions       = [aws_sns_topic.warning_alarms.arn]
  ok_actions          = [aws_sns_topic.info_alarms.arn]
  dimensions          = local.frontend_service_dimensions
  tags                = local.monitoring_tags
}

# Frontend Service Memory Utilization Alarm
resource "aws_cloudwatch_metric_alarm" "frontend_memory_high" {
  alarm_name          = "${local.environment_prefix}-frontend-memory-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = var.monitoring.alarm_evaluation_periods
  metric_name         = "MemoryUtilization"
  namespace           = "AWS/ECS"
  period              = var.monitoring.alarm_period_seconds
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "Frontend service memory utilization is too high"
  alarm_actions       = [aws_sns_topic.warning_alarms.arn]
  ok_actions          = [aws_sns_topic.info_alarms.arn]
  dimensions          = local.frontend_service_dimensions
  tags                = local.monitoring_tags
}

# Backend Service CPU Utilization Alarm
resource "aws_cloudwatch_metric_alarm" "backend_cpu_high" {
  alarm_name          = "${local.environment_prefix}-backend-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = var.monitoring.alarm_evaluation_periods
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = var.monitoring.alarm_period_seconds
  statistic           = "Average"
  threshold           = 70
  alarm_description   = "Backend service CPU utilization is too high"
  alarm_actions       = [aws_sns_topic.warning_alarms.arn]
  ok_actions          = [aws_sns_topic.info_alarms.arn]
  dimensions          = local.backend_service_dimensions
  tags                = local.monitoring_tags
}

# Backend Service Memory Utilization Alarm
resource "aws_cloudwatch_metric_alarm" "backend_memory_high" {
  alarm_name          = "${local.environment_prefix}-backend-memory-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = var.monitoring.alarm_evaluation_periods
  metric_name         = "MemoryUtilization"
  namespace           = "AWS/ECS"
  period              = var.monitoring.alarm_period_seconds
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "Backend service memory utilization is too high"
  alarm_actions       = [aws_sns_topic.warning_alarms.arn]
  ok_actions          = [aws_sns_topic.info_alarms.arn]
  dimensions          = local.backend_service_dimensions
  tags                = local.monitoring_tags
}

# Molecule Service CPU Utilization Alarm
resource "aws_cloudwatch_metric_alarm" "molecule_cpu_high" {
  alarm_name          = "${local.environment_prefix}-molecule-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = var.monitoring.alarm_evaluation_periods
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = var.monitoring.alarm_period_seconds
  statistic           = "Average"
  threshold           = 60 # Lower threshold due to compute-intensive nature
  alarm_description   = "Molecule service CPU utilization is too high"
  alarm_actions       = [aws_sns_topic.warning_alarms.arn]
  ok_actions          = [aws_sns_topic.info_alarms.arn]
  dimensions          = local.molecule_service_dimensions
  tags                = local.monitoring_tags
}

# Molecule Service Memory Utilization Alarm
resource "aws_cloudwatch_metric_alarm" "molecule_memory_high" {
  alarm_name          = "${local.environment_prefix}-molecule-memory-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = var.monitoring.alarm_evaluation_periods
  metric_name         = "MemoryUtilization"
  namespace           = "AWS/ECS"
  period              = var.monitoring.alarm_period_seconds
  statistic           = "Average"
  threshold           = 75 # Lower threshold due to memory-intensive operations
  alarm_description   = "Molecule service memory utilization is too high"
  alarm_actions       = [aws_sns_topic.warning_alarms.arn]
  ok_actions          = [aws_sns_topic.info_alarms.arn]
  dimensions          = local.molecule_service_dimensions
  tags                = local.monitoring_tags
}

# Worker Service CPU Utilization Alarm
resource "aws_cloudwatch_metric_alarm" "worker_cpu_high" {
  alarm_name          = "${local.environment_prefix}-worker-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = var.monitoring.alarm_evaluation_periods
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = var.monitoring.alarm_period_seconds
  statistic           = "Average"
  threshold           = 70
  alarm_description   = "Worker service CPU utilization is too high"
  alarm_actions       = [aws_sns_topic.warning_alarms.arn]
  ok_actions          = [aws_sns_topic.info_alarms.arn]
  dimensions          = local.worker_service_dimensions
  tags                = local.monitoring_tags
}

# Worker Service Memory Utilization Alarm
resource "aws_cloudwatch_metric_alarm" "worker_memory_high" {
  alarm_name          = "${local.environment_prefix}-worker-memory-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = var.monitoring.alarm_evaluation_periods
  metric_name         = "MemoryUtilization"
  namespace           = "AWS/ECS"
  period              = var.monitoring.alarm_period_seconds
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "Worker service memory utilization is too high"
  alarm_actions       = [aws_sns_topic.warning_alarms.arn]
  ok_actions          = [aws_sns_topic.info_alarms.arn]
  dimensions          = local.worker_service_dimensions
  tags                = local.monitoring_tags
}

# ----------------------------------------------------------------------------
# CloudWatch Alarms - Database (RDS)
# ----------------------------------------------------------------------------

# RDS High CPU Utilization
resource "aws_cloudwatch_metric_alarm" "rds_cpu_high" {
  alarm_name          = "${local.environment_prefix}-rds-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = var.monitoring.alarm_evaluation_periods
  metric_name         = "CPUUtilization"
  namespace           = "AWS/RDS"
  period              = var.monitoring.alarm_period_seconds
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "RDS CPU utilization is too high"
  alarm_actions       = [aws_sns_topic.warning_alarms.arn]
  ok_actions          = [aws_sns_topic.info_alarms.arn]
  dimensions          = local.rds_dimensions
  tags                = local.monitoring_tags
}

# RDS High Database Connections
resource "aws_cloudwatch_metric_alarm" "rds_connections_high" {
  alarm_name          = "${local.environment_prefix}-rds-connections-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = var.monitoring.alarm_evaluation_periods
  metric_name         = "DatabaseConnections"
  namespace           = "AWS/RDS"
  period              = var.monitoring.alarm_period_seconds
  statistic           = "Maximum"
  threshold           = 100 # Adjust based on instance size and expected load
  alarm_description   = "RDS database connection count is too high"
  alarm_actions       = [aws_sns_topic.warning_alarms.arn]
  ok_actions          = [aws_sns_topic.info_alarms.arn]
  dimensions          = local.rds_dimensions
  tags                = local.monitoring_tags
}

# RDS Low Free Storage Space
resource "aws_cloudwatch_metric_alarm" "rds_storage_low" {
  alarm_name          = "${local.environment_prefix}-rds-storage-low"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = var.monitoring.alarm_evaluation_periods
  metric_name         = "FreeStorageSpace"
  namespace           = "AWS/RDS"
  period              = var.monitoring.alarm_period_seconds
  statistic           = "Average"
  threshold           = 10000000000 # 10 GB in bytes
  alarm_description   = "RDS free storage space is critically low"
  alarm_actions       = [aws_sns_topic.critical_alarms.arn]
  ok_actions          = [aws_sns_topic.info_alarms.arn]
  dimensions          = local.rds_dimensions
  tags                = local.monitoring_tags
}

# ----------------------------------------------------------------------------
# CloudWatch Alarms - ElastiCache
# ----------------------------------------------------------------------------

# ElastiCache High CPU Utilization
resource "aws_cloudwatch_metric_alarm" "elasticache_cpu_high" {
  alarm_name          = "${local.environment_prefix}-elasticache-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = var.monitoring.alarm_evaluation_periods
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ElastiCache"
  period              = var.monitoring.alarm_period_seconds
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "ElastiCache CPU utilization is too high"
  alarm_actions       = [aws_sns_topic.warning_alarms.arn]
  ok_actions          = [aws_sns_topic.info_alarms.arn]
  dimensions          = local.elasticache_dimensions
  tags                = local.monitoring_tags
}

# ElastiCache High Memory Usage
resource "aws_cloudwatch_metric_alarm" "elasticache_memory_high" {
  alarm_name          = "${local.environment_prefix}-elasticache-memory-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = var.monitoring.alarm_evaluation_periods
  metric_name         = "DatabaseMemoryUsagePercentage"
  namespace           = "AWS/ElastiCache"
  period              = var.monitoring.alarm_period_seconds
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "ElastiCache memory usage is too high"
  alarm_actions       = [aws_sns_topic.warning_alarms.arn]
  ok_actions          = [aws_sns_topic.info_alarms.arn]
  dimensions          = local.elasticache_dimensions
  tags                = local.monitoring_tags
}

# ElastiCache Cache Hit Rate Low
resource "aws_cloudwatch_metric_alarm" "elasticache_hit_rate_low" {
  alarm_name          = "${local.environment_prefix}-elasticache-hit-rate-low"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = var.monitoring.alarm_evaluation_periods
  metric_name         = "CacheHitRate"
  namespace           = "AWS/ElastiCache"
  period              = var.monitoring.alarm_period_seconds
  statistic           = "Average"
  threshold           = 0.5 # 50%
  alarm_description   = "ElastiCache hit rate is too low"
  alarm_actions       = [aws_sns_topic.warning_alarms.arn]
  ok_actions          = [aws_sns_topic.info_alarms.arn]
  dimensions          = local.elasticache_dimensions
  tags                = local.monitoring_tags
}

# ----------------------------------------------------------------------------
# CloudWatch Log Groups for Compliance and Custom Metrics
# ----------------------------------------------------------------------------

# API Access Log Group
resource "aws_cloudwatch_log_group" "api_access_logs" {
  name              = "${local.environment_prefix}-api-access-logs"
  retention_in_days = var.monitoring.log_retention_days
  tags              = local.monitoring_tags
}

# Audit Log Group for Compliance
resource "aws_cloudwatch_log_group" "audit_logs" {
  name              = "${local.environment_prefix}-audit-logs"
  retention_in_days = 2555 # 7 years for compliance (21 CFR Part 11)
  tags              = merge(local.monitoring_tags, {
    Compliance = "21CFR-Part-11,GDPR,SOC2"
  })
}

# Security Event Log Group
resource "aws_cloudwatch_log_group" "security_logs" {
  name              = "${local.environment_prefix}-security-logs"
  retention_in_days = 365 # 1 year for security events
  tags              = merge(local.monitoring_tags, {
    Compliance = "21CFR-Part-11,GDPR,SOC2"
  })
}

# Molecule Processing Log Group
resource "aws_cloudwatch_log_group" "molecule_processing_logs" {
  name              = "${local.environment_prefix}-molecule-processing-logs"
  retention_in_days = var.monitoring.log_retention_days
  tags              = local.monitoring_tags
}

# ----------------------------------------------------------------------------
# CloudWatch Log Metric Filters
# ----------------------------------------------------------------------------

# API Error Rate
resource "aws_cloudwatch_log_metric_filter" "api_errors" {
  name           = "${local.environment_prefix}-api-errors"
  pattern        = "{ $.level = \"ERROR\" }"
  log_group_name = var.compute_outputs.cloudwatch_log_groups["backend"]

  metric_transformation {
    name          = "APIErrorCount"
    namespace     = var.monitoring.metric_namespace
    value         = "1"
    default_value = "0"
  }
}

# Authentication Failures
resource "aws_cloudwatch_log_metric_filter" "auth_failures" {
  name           = "${local.environment_prefix}-auth-failures"
  pattern        = "{ $.event = \"authentication_failure\" }"
  log_group_name = aws_cloudwatch_log_group.security_logs.name

  metric_transformation {
    name          = "AuthFailureCount"
    namespace     = var.monitoring.metric_namespace
    value         = "1"
    default_value = "0"
  }
}

# Molecule Processing Errors
resource "aws_cloudwatch_log_metric_filter" "molecule_processing_errors" {
  name           = "${local.environment_prefix}-molecule-processing-errors"
  pattern        = "{ $.level = \"ERROR\" && $.service = \"molecule\" }"
  log_group_name = var.compute_outputs.cloudwatch_log_groups["molecule"]

  metric_transformation {
    name          = "MoleculeProcessingErrorCount"
    namespace     = var.monitoring.metric_namespace
    value         = "1"
    default_value = "0"
  }
}

# CSV Import Metrics
resource "aws_cloudwatch_log_metric_filter" "csv_import_time" {
  name           = "${local.environment_prefix}-csv-import-time"
  pattern        = "{ $.event = \"csv_import_complete\" }"
  log_group_name = var.compute_outputs.cloudwatch_log_groups["molecule"]

  metric_transformation {
    name          = "CSVImportTime"
    namespace     = var.monitoring.metric_namespace
    value         = "$.duration"
    default_value = "0"
  }
}

# Compliance Audit Events
resource "aws_cloudwatch_log_metric_filter" "compliance_events" {
  name           = "${local.environment_prefix}-compliance-events"
  pattern        = "{ $.compliance_event = true }"
  log_group_name = aws_cloudwatch_log_group.audit_logs.name

  metric_transformation {
    name          = "ComplianceEventCount"
    namespace     = var.monitoring.metric_namespace
    value         = "1"
    default_value = "0"
  }
}

# ----------------------------------------------------------------------------
# CloudWatch Alarms on Custom Metrics
# ----------------------------------------------------------------------------

# High API Error Rate Alarm
resource "aws_cloudwatch_metric_alarm" "high_api_error_rate" {
  alarm_name          = "${local.environment_prefix}-high-api-error-rate"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = var.monitoring.alarm_evaluation_periods
  metric_name         = "APIErrorCount"
  namespace           = var.monitoring.metric_namespace
  period              = var.monitoring.alarm_period_seconds
  statistic           = "Sum"
  threshold           = 10
  alarm_description   = "High number of API errors detected"
  alarm_actions       = [aws_sns_topic.critical_alarms.arn]
  ok_actions          = [aws_sns_topic.info_alarms.arn]
  tags                = local.monitoring_tags
}

# High Authentication Failure Rate Alarm
resource "aws_cloudwatch_metric_alarm" "high_auth_failures" {
  alarm_name          = "${local.environment_prefix}-high-auth-failures"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = var.monitoring.alarm_evaluation_periods
  metric_name         = "AuthFailureCount"
  namespace           = var.monitoring.metric_namespace
  period              = var.monitoring.alarm_period_seconds
  statistic           = "Sum"
  threshold           = 5
  alarm_description   = "High number of authentication failures detected"
  alarm_actions       = [aws_sns_topic.critical_alarms.arn]
  ok_actions          = [aws_sns_topic.info_alarms.arn]
  tags                = local.monitoring_tags
}

# High Molecule Processing Error Rate
resource "aws_cloudwatch_metric_alarm" "high_molecule_processing_errors" {
  alarm_name          = "${local.environment_prefix}-high-molecule-processing-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = var.monitoring.alarm_evaluation_periods
  metric_name         = "MoleculeProcessingErrorCount"
  namespace           = var.monitoring.metric_namespace
  period              = var.monitoring.alarm_period_seconds
  statistic           = "Sum"
  threshold           = 10
  alarm_description   = "High number of molecule processing errors detected"
  alarm_actions       = [aws_sns_topic.critical_alarms.arn]
  ok_actions          = [aws_sns_topic.info_alarms.arn]
  tags                = local.monitoring_tags
}

# Slow CSV Import Time
resource "aws_cloudwatch_metric_alarm" "slow_csv_import" {
  alarm_name          = "${local.environment_prefix}-slow-csv-import"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = var.monitoring.alarm_evaluation_periods
  metric_name         = "CSVImportTime"
  namespace           = var.monitoring.metric_namespace
  period              = var.monitoring.alarm_period_seconds
  statistic           = "Average"
  threshold           = 60 # 60 seconds per 10K molecules (SLA requirement)
  alarm_description   = "CSV import time exceeding threshold"
  alarm_actions       = [aws_sns_topic.warning_alarms.arn]
  ok_actions          = [aws_sns_topic.info_alarms.arn]
  tags                = local.monitoring_tags
}

# ----------------------------------------------------------------------------
# CloudWatch Dashboards
# ----------------------------------------------------------------------------

# System overview dashboard
resource "aws_cloudwatch_dashboard" "system_overview" {
  dashboard_name = "${local.environment_prefix}-system-overview"
  
  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "text"
        x      = 0
        y      = 0
        width  = 24
        height = 1
        properties = {
          markdown = "# Molecular Data Management Platform - System Overview"
        }
      },
      # ECS Services - CPU and Memory
      {
        type   = "metric"
        x      = 0
        y      = 1
        width  = 12
        height = 6
        properties = {
          view    = "timeSeries"
          stacked = false
          metrics = [
            ["AWS/ECS", "CPUUtilization", "ServiceName", var.compute_outputs.frontend_service_name, "ClusterName", var.compute_outputs.cluster_id],
            ["AWS/ECS", "CPUUtilization", "ServiceName", var.compute_outputs.backend_service_name, "ClusterName", var.compute_outputs.cluster_id],
            ["AWS/ECS", "CPUUtilization", "ServiceName", var.compute_outputs.molecule_service_name, "ClusterName", var.compute_outputs.cluster_id],
            ["AWS/ECS", "CPUUtilization", "ServiceName", var.compute_outputs.worker_service_name, "ClusterName", var.compute_outputs.cluster_id]
          ]
          title   = "ECS Services - CPU Utilization"
          region  = var.region
          period  = 300
          stat    = "Average"
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 1
        width  = 12
        height = 6
        properties = {
          view    = "timeSeries"
          stacked = false
          metrics = [
            ["AWS/ECS", "MemoryUtilization", "ServiceName", var.compute_outputs.frontend_service_name, "ClusterName", var.compute_outputs.cluster_id],
            ["AWS/ECS", "MemoryUtilization", "ServiceName", var.compute_outputs.backend_service_name, "ClusterName", var.compute_outputs.cluster_id],
            ["AWS/ECS", "MemoryUtilization", "ServiceName", var.compute_outputs.molecule_service_name, "ClusterName", var.compute_outputs.cluster_id],
            ["AWS/ECS", "MemoryUtilization", "ServiceName", var.compute_outputs.worker_service_name, "ClusterName", var.compute_outputs.cluster_id]
          ]
          title  = "ECS Services - Memory Utilization"
          region = var.region
          period = 300
          stat   = "Average"
        }
      },
      # Database Metrics
      {
        type   = "metric"
        x      = 0
        y      = 7
        width  = 8
        height = 6
        properties = {
          view    = "timeSeries"
          stacked = false
          metrics = [
            ["AWS/RDS", "CPUUtilization", "DBInstanceIdentifier", var.database_outputs.rds_instance_id]
          ]
          title   = "RDS - CPU Utilization"
          region  = var.region
          period  = 300
          stat    = "Average"
        }
      },
      {
        type   = "metric"
        x      = 8
        y      = 7
        width  = 8
        height = 6
        properties = {
          view    = "timeSeries"
          stacked = false
          metrics = [
            ["AWS/RDS", "DatabaseConnections", "DBInstanceIdentifier", var.database_outputs.rds_instance_id]
          ]
          title   = "RDS - Database Connections"
          region  = var.region
          period  = 300
          stat    = "Average"
        }
      },
      {
        type   = "metric"
        x      = 16
        y      = 7
        width  = 8
        height = 6
        properties = {
          view    = "timeSeries"
          stacked = false
          metrics = [
            ["AWS/ElastiCache", "CacheHitRate", "ReplicationGroupId", var.database_outputs.elasticache_replication_group_id]
          ]
          title   = "ElastiCache - Cache Hit Rate"
          region  = var.region
          period  = 300
          stat    = "Average"
        }
      },
      # Custom Business Metrics
      {
        type   = "metric"
        x      = 0
        y      = 13
        width  = 12
        height = 6
        properties = {
          view    = "timeSeries"
          stacked = false
          metrics = [
            [var.monitoring.metric_namespace, "CSVImportTime"]
          ]
          title   = "CSV Import Processing Time (seconds)"
          region  = var.region
          period  = 300
          stat    = "Average"
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 13
        width  = 12
        height = 6
        properties = {
          view    = "timeSeries"
          stacked = false
          metrics = [
            [var.monitoring.metric_namespace, "APIErrorCount"],
            [var.monitoring.metric_namespace, "MoleculeProcessingErrorCount"]
          ]
          title   = "Error Counts"
          region  = var.region
          period  = 300
          stat    = "Sum"
        }
      }
    ]
  })
}

# Compliance and Security Dashboard
resource "aws_cloudwatch_dashboard" "compliance_security" {
  dashboard_name = "${local.environment_prefix}-compliance-security"
  
  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "text"
        x      = 0
        y      = 0
        width  = 24
        height = 1
        properties = {
          markdown = "# Molecular Data Management Platform - Compliance & Security (21 CFR Part 11)"
        }
      },
      # Authentication & Authorization
      {
        type   = "metric"
        x      = 0
        y      = 1
        width  = 12
        height = 6
        properties = {
          view    = "timeSeries"
          stacked = false
          metrics = [
            [var.monitoring.metric_namespace, "AuthFailureCount"]
          ]
          title   = "Authentication Failures"
          region  = var.region
          period  = 300
          stat    = "Sum"
        }
      },
      {
        type   = "log"
        x      = 12
        y      = 1
        width  = 12
        height = 6
        properties = {
          query   = "fields @timestamp, @message\n| filter @message like /authentication_failure/\n| sort @timestamp desc\n| limit 20"
          region  = var.region
          title   = "Recent Authentication Failures"
          view    = "table"
          stacked = false
          logGroupNames = [aws_cloudwatch_log_group.security_logs.name]
        }
      },
      # Compliance Events
      {
        type   = "metric"
        x      = 0
        y      = 7
        width  = 12
        height = 6
        properties = {
          view    = "timeSeries"
          stacked = false
          metrics = [
            [var.monitoring.metric_namespace, "ComplianceEventCount"]
          ]
          title   = "Compliance Events"
          region  = var.region
          period  = 300
          stat    = "Sum"
        }
      },
      {
        type   = "log"
        x      = 12
        y      = 7
        width  = 12
        height = 6
        properties = {
          query   = "fields @timestamp, @message\n| filter @message like /compliance_event/\n| sort @timestamp desc\n| limit 20"
          region  = var.region
          title   = "Recent Compliance Events"
          view    = "table"
          stacked = false
          logGroupNames = [aws_cloudwatch_log_group.audit_logs.name]
        }
      }
    ]
  })
}

# ----------------------------------------------------------------------------
# CloudWatch Log Insights Saved Queries
# ----------------------------------------------------------------------------

# API Error Query
resource "aws_cloudwatch_query_definition" "api_errors" {
  name = "${local.environment_prefix}-api-errors"
  
  query_string = <<-EOT
    fields @timestamp, @message
    | filter @message like /ERROR/
    | parse @message /\{.*"service":"?([^,"]*)"?.*\}/ as service
    | parse @message /\{.*"error":"?([^,"]*)"?.*\}/ as error_type
    | stats count(*) as error_count by service, error_type, bin(30m)
    | sort error_count desc
  EOT
  
  log_group_names = [
    var.compute_outputs.cloudwatch_log_groups["backend"],
    var.compute_outputs.cloudwatch_log_groups["molecule"]
  ]
}

# Molecule Processing Performance Query
resource "aws_cloudwatch_query_definition" "molecule_processing" {
  name = "${local.environment_prefix}-molecule-processing"
  
  query_string = <<-EOT
    fields @timestamp, @message
    | filter @message like /csv_import_complete/
    | parse @message /\{.*"filename":"?([^,"]*)"?.*\}/ as filename
    | parse @message /\{.*"molecule_count":([0-9]+).*\}/ as molecule_count
    | parse @message /\{.*"duration":([0-9.]+).*\}/ as duration
    | parse @message /\{.*"success_count":([0-9]+).*\}/ as success_count
    | parse @message /\{.*"error_count":([0-9]+).*\}/ as error_count
    | stats avg(duration) as avg_duration, max(duration) as max_duration, 
            sum(molecule_count) as total_molecules, 
            sum(success_count) as total_success, 
            sum(error_count) as total_errors by filename
    | sort avg_duration desc
  EOT
  
  log_group_names = [
    var.compute_outputs.cloudwatch_log_groups["molecule"]
  ]
}

# Compliance Audit Query
resource "aws_cloudwatch_query_definition" "compliance_audit" {
  name = "${local.environment_prefix}-compliance-audit"
  
  query_string = <<-EOT
    fields @timestamp, @message
    | filter @message like /compliance_event/
    | parse @message /\{.*"event_type":"?([^,"]*)"?.*\}/ as event_type
    | parse @message /\{.*"user":"?([^,"]*)"?.*\}/ as user
    | parse @message /\{.*"resource":"?([^,"]*)"?.*\}/ as resource
    | parse @message /\{.*"action":"?([^,"]*)"?.*\}/ as action
    | stats count(*) as event_count by event_type, user, resource, action, bin(1d)
    | sort event_count desc
  EOT
  
  log_group_names = [
    aws_cloudwatch_log_group.audit_logs.name
  ]
}

# ----------------------------------------------------------------------------
# Outputs
# ----------------------------------------------------------------------------

output "dashboard_urls" {
  description = "URLs for accessing the CloudWatch dashboards"
  value = {
    system_overview       = "https://${var.region}.console.aws.amazon.com/cloudwatch/home?region=${var.region}#dashboards:name=${aws_cloudwatch_dashboard.system_overview.dashboard_name}"
    compliance_security   = "https://${var.region}.console.aws.amazon.com/cloudwatch/home?region=${var.region}#dashboards:name=${aws_cloudwatch_dashboard.compliance_security.dashboard_name}"
  }
}

output "alarm_topic_arn" {
  description = "ARN of the SNS topic for alarm notifications"
  value = aws_sns_topic.critical_alarms.arn
}

output "log_group_names" {
  description = "Names of the CloudWatch log groups created by this module"
  value = {
    api_access          = aws_cloudwatch_log_group.api_access_logs.name
    audit               = aws_cloudwatch_log_group.audit_logs.name
    security            = aws_cloudwatch_log_group.security_logs.name
    molecule_processing = aws_cloudwatch_log_group.molecule_processing_logs.name
  }
}

output "alarm_arns" {
  description = "ARNs of the CloudWatch alarms created by this module"
  value = {
    frontend_cpu_high        = aws_cloudwatch_metric_alarm.frontend_cpu_high.arn
    backend_cpu_high         = aws_cloudwatch_metric_alarm.backend_cpu_high.arn
    molecule_cpu_high        = aws_cloudwatch_metric_alarm.molecule_cpu_high.arn
    worker_cpu_high          = aws_cloudwatch_metric_alarm.worker_cpu_high.arn
    rds_cpu_high             = aws_cloudwatch_metric_alarm.rds_cpu_high.arn
    rds_storage_low          = aws_cloudwatch_metric_alarm.rds_storage_low.arn
    elasticache_cpu_high     = aws_cloudwatch_metric_alarm.elasticache_cpu_high.arn
    elasticache_memory_high  = aws_cloudwatch_metric_alarm.elasticache_memory_high.arn
    high_api_error_rate      = aws_cloudwatch_metric_alarm.high_api_error_rate.arn
    high_auth_failures       = aws_cloudwatch_metric_alarm.high_auth_failures.arn
  }
}

output "metric_namespace" {
  description = "Namespace used for custom CloudWatch metrics"
  value = var.monitoring.metric_namespace
}