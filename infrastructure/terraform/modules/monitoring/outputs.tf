# infrastructure/terraform/modules/monitoring/outputs.tf
# ----------------------------------------------------------------------------------------------------------------------
# OUTPUTS
# Defines output variables for the Terraform monitoring module that provisions CloudWatch resources,
# Prometheus, Grafana, and AlertManager for comprehensive monitoring of the Molecular Data Management and CRO Integration Platform.
# These outputs are used by the root module and other modules to reference monitoring resources.
# ----------------------------------------------------------------------------------------------------------------------

locals {
  # Block containing local variables for constructing dashboard URLs and organizing outputs
  dashboard_url_base = "https://${var.region}.console.aws.amazon.com/cloudwatch/home?region=${var.region}#dashboards:name="
}

# Output URLs for accessing the CloudWatch dashboards
output "dashboard_urls" {
  description = "URLs for accessing the CloudWatch dashboards"
  value = local.output_dashboard_urls()
}

# Output ARNs of the SNS topics for alarm notifications
output "alarm_topic_arns" {
  description = "ARNs of the SNS topics for alarm notifications"
  value = local.output_alarm_topic_arns()
}

# Output names of the CloudWatch log groups created by this module
output "log_group_names" {
  description = "Names of the CloudWatch log groups created by this module"
  value = local.output_log_group_names()
}

# Output ARNs of the CloudWatch alarms created by this module
output "alarm_arns" {
  description = "ARNs of the CloudWatch alarms created by this module"
  value = local.output_alarm_arns()
}

# Output the namespace used for custom CloudWatch metrics
output "metric_namespace" {
  description = "Namespace used for custom CloudWatch metrics"
  value = local.output_metric_namespace()
}

# Output the URL for accessing the Grafana UI
output "grafana_url" {
  description = "URL for accessing the Grafana UI"
  value = local.output_grafana_url()
}

# Output the URL for accessing the Prometheus UI
output "prometheus_url" {
  description = "URL for accessing the Prometheus UI"
  value = local.output_prometheus_url()
}

# Output the URL for accessing the AlertManager UI
output "alertmanager_url" {
  description = "URL for accessing the AlertManager UI"
  value = local.output_alertmanager_url()
}

# Output URLs for accessing specific Grafana dashboards
output "grafana_dashboard_urls" {
  description = "URLs for accessing specific Grafana dashboards"
  value = local.output_grafana_dashboard_urls()
}

# Output ARNs of the SNS topics for different alert severities
output "alert_topic_arns" {
  description = "ARNs of the SNS topics for different alert severities"
  value = local.output_alert_topic_arns()
}

# Output names of the ECS services for monitoring components
output "monitoring_service_names" {
  description = "Names of the ECS services for monitoring components"
  value = local.output_monitoring_service_names()
}

# Function to output URLs for accessing the CloudWatch dashboards
locals {
  output_dashboard_urls = {
    system_overview       = "${local.dashboard_url_base}${aws_cloudwatch_dashboard.executive_dashboard.dashboard_name}"
    operational           = "${local.dashboard_url_base}${aws_cloudwatch_dashboard.operational_dashboard.dashboard_name}"
    technical             = "${local.dashboard_url_base}${aws_cloudwatch_dashboard.technical_dashboard.dashboard_name}"
    security              = "${local.dashboard_url_base}${aws_cloudwatch_dashboard.security_dashboard.dashboard_name}"
    molecule_processing   = "${local.dashboard_url_base}${aws_cloudwatch_dashboard.molecule_dashboard.dashboard_name}"
    cro_integration       = "${local.dashboard_url_base}${aws_cloudwatch_dashboard.cro_dashboard.dashboard_name}"
  }
}

# Function to output ARNs of the SNS topics for alarm notifications
locals {
  output_alarm_topic_arns = {
    critical = aws_sns_topic.critical_alarms.arn
    warning  = aws_sns_topic.warning_alarms.arn
    info     = aws_sns_topic.info_alarms.arn
  }
}

# Function to output names of the CloudWatch log groups created by this module
locals {
  output_log_group_names = {
    monitoring = aws_cloudwatch_log_group.monitoring_logs.name
    prometheus = aws_cloudwatch_log_group.prometheus_logs.name
    alertmanager = aws_cloudwatch_log_group.alertmanager_logs.name
  }
}

# Function to output ARNs of the CloudWatch alarms created by this module
locals {
  output_alarm_arns = {
    cpu_utilization_alarm = aws_cloudwatch_metric_alarm.cpu_utilization_alarm.arn
    memory_utilization_alarm = aws_cloudwatch_metric_alarm.memory_utilization_alarm.arn
    api_error_rate_alarm = aws_cloudwatch_metric_alarm.api_error_rate_alarm.arn
  }
}

# Function to output the namespace used for custom CloudWatch metrics
locals {
  output_metric_namespace = var.monitoring.metric_namespace
}

# Function to output the URL for accessing the Grafana UI
locals {
  output_grafana_url = var.monitoring.enable_grafana ? "http://${aws_ecs_service.grafana.name}.${var.region}.elb.amazonaws.com" : ""
}

# Function to output the URL for accessing the Prometheus UI
locals {
  output_prometheus_url = var.monitoring.enable_prometheus ? "http://${aws_ecs_service.prometheus.name}.${var.region}.elb.amazonaws.com" : ""
}

# Function to output the URL for accessing the AlertManager UI
locals {
  output_alertmanager_url = var.monitoring.enable_alertmanager ? "http://${aws_ecs_service.alertmanager.name}.${var.region}.elb.amazonaws.com" : ""
}

# Function to output URLs for accessing specific Grafana dashboards
locals {
  output_grafana_dashboard_urls = {
    system_health = var.monitoring.enable_grafana ? "http://${aws_ecs_service.grafana.name}.${var.region}.elb.amazonaws.com/dashboards/f/system-health" : ""
    molecule_processing = var.monitoring.enable_grafana ? "http://${aws_ecs_service.grafana.name}.${var.region}.elb.amazonaws.com/dashboards/f/molecule-processing" : ""
    cro_integration = var.monitoring.enable_grafana ? "http://${aws_ecs_service.grafana.name}.${var.region}.elb.amazonaws.com/dashboards/f/cro-integration" : ""
  }
}

# Function to output ARNs of the SNS topics for different alert severities
locals {
  output_alert_topic_arns = {
    critical_alerts = aws_sns_topic.critical_alerts.arn
    high_priority_alerts = aws_sns_topic.high_priority_alerts.arn
    medium_priority_alerts = aws_sns_topic.medium_priority_alerts.arn
    low_priority_alerts = aws_sns_topic.low_priority_alerts.arn
  }
}

# Function to output names of the ECS services for monitoring components
locals {
  output_monitoring_service_names = {
    grafana = aws_ecs_service.grafana.name
    prometheus = aws_ecs_service.prometheus.name
    alertmanager = aws_ecs_service.alertmanager.name
  }
}