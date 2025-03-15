# ----------------------------------------------------------------------------------------------------------------------
# CLOUDWATCH DASHBOARDS
# Defines a set of CloudWatch dashboards for monitoring the Molecular Data Management and CRO Integration Platform.
# Each dashboard provides a specific view of the system for different stakeholders and use cases.
# ----------------------------------------------------------------------------------------------------------------------

locals {
  # Dashboard names
  dashboard_names = {
    executive  = "${var.monitoring.dashboard_name_prefix}-${var.environment}-executive"
    operational = "${var.monitoring.dashboard_name_prefix}-${var.environment}-operational"
    technical  = "${var.monitoring.dashboard_name_prefix}-${var.environment}-technical"
    security   = "${var.monitoring.dashboard_name_prefix}-${var.environment}-security"
    molecule   = "${var.monitoring.dashboard_name_prefix}-${var.environment}-molecule-processing"
    cro        = "${var.monitoring.dashboard_name_prefix}-${var.environment}-cro-integration"
  }

  # Common metric period and stat definitions
  metric_defaults = {
    period = 300
    stat   = "Average"
    region = var.region
  }

  # Service identifiers
  services = {
    frontend  = var.compute_outputs.frontend_service_name
    backend   = var.compute_outputs.backend_service_name
    molecule  = var.compute_outputs.molecule_service_name
    worker    = var.compute_outputs.worker_service_name
  }

  # Database identifiers
  databases = {
    primary = var.database_outputs.rds_instance_id
    redis   = var.database_outputs.elasticache_replication_group_id
  }

  # Storage identifiers
  storage = {
    document = var.storage_outputs.document_bucket_id
    csv      = var.storage_outputs.csv_bucket_id
    results  = var.storage_outputs.results_bucket_id
  }

  # Dashboard widget definitions
  metric_widgets = {
    # System Status Widgets
    system_status = {
      type   = "metric"
      width  = 24
      height = 6
      properties = {
        title  = "System Service Status"
        view   = "timeSeries"
        stacked = false
        metrics = [
          ["AWS/ECS", "CPUUtilization", "ServiceName", local.services.frontend, "ClusterName", "${var.monitoring.dashboard_name_prefix}-${var.environment}", { label = "Frontend" }],
          ["AWS/ECS", "CPUUtilization", "ServiceName", local.services.backend, "ClusterName", "${var.monitoring.dashboard_name_prefix}-${var.environment}", { label = "Backend" }],
          ["AWS/ECS", "CPUUtilization", "ServiceName", local.services.molecule, "ClusterName", "${var.monitoring.dashboard_name_prefix}-${var.environment}", { label = "Molecule Service" }],
          ["AWS/ECS", "CPUUtilization", "ServiceName", local.services.worker, "ClusterName", "${var.monitoring.dashboard_name_prefix}-${var.environment}", { label = "Worker Service" }]
        ]
        period = local.metric_defaults.period
        stat   = local.metric_defaults.stat
        region = local.metric_defaults.region
        yAxis = {
          left = {
            min = 0
            max = 100
          }
        }
      }
    }

    # SLA Compliance Widget
    sla_compliance = {
      type   = "metric"
      width  = 12
      height = 6
      properties = {
        title  = "SLA Compliance"
        view   = "timeSeries"
        stacked = false
        metrics = [
          ["${var.monitoring.metric_namespace}", "APIResponseTime", { label = "API Response Time (ms)", stat = "p95" }],
          ["${var.monitoring.metric_namespace}", "CSVProcessingTime", { label = "CSV Processing Time (s per 10k)", stat = "Average" }],
          ["${var.monitoring.metric_namespace}", "AIPredictionTime", { label = "AI Prediction Time (s per 100)", stat = "Average" }]
        ]
        period = local.metric_defaults.period
        region = local.metric_defaults.region
        annotations = {
          horizontal = [
            {
              value = 500,
              label = "API SLA (500ms)",
              color = "#ff9900"
            },
            {
              value = 30,
              label = "CSV SLA (30s per 10k)",
              color = "#ff9900"
            },
            {
              value = 120,
              label = "AI SLA (2min per 100)",
              color = "#ff9900"
            }
          ]
        }
      }
    }

    # Active Users Widget
    active_users = {
      type   = "metric"
      width  = 12
      height = 6
      properties = {
        title  = "Active Users"
        view   = "timeSeries"
        stacked = false
        metrics = [
          ["${var.monitoring.metric_namespace}", "ConcurrentUsers", { label = "Total Users" }],
          ["${var.monitoring.metric_namespace}", "ConcurrentUsers", "UserType", "Pharma", { label = "Pharma Users" }],
          ["${var.monitoring.metric_namespace}", "ConcurrentUsers", "UserType", "CRO", { label = "CRO Users" }]
        ]
        period = local.metric_defaults.period
        stat   = local.metric_defaults.stat
        region = local.metric_defaults.region
      }
    }

    # CPU Utilization Widgets
    cpu_utilization = {
      type   = "metric"
      width  = 12
      height = 6
      properties = {
        title  = "CPU Utilization"
        view   = "timeSeries"
        stacked = false
        metrics = [
          ["AWS/ECS", "CPUUtilization", "ServiceName", local.services.frontend, "ClusterName", "${var.monitoring.dashboard_name_prefix}-${var.environment}", { label = "Frontend" }],
          ["AWS/ECS", "CPUUtilization", "ServiceName", local.services.backend, "ClusterName", "${var.monitoring.dashboard_name_prefix}-${var.environment}", { label = "Backend" }],
          ["AWS/ECS", "CPUUtilization", "ServiceName", local.services.molecule, "ClusterName", "${var.monitoring.dashboard_name_prefix}-${var.environment}", { label = "Molecule Service" }],
          ["AWS/ECS", "CPUUtilization", "ServiceName", local.services.worker, "ClusterName", "${var.monitoring.dashboard_name_prefix}-${var.environment}", { label = "Worker Service" }]
        ]
        period = local.metric_defaults.period
        stat   = local.metric_defaults.stat
        region = local.metric_defaults.region
        yAxis = {
          left = {
            min = 0
            max = 100
          }
        }
      }
    }

    # Memory Utilization Widgets
    memory_utilization = {
      type   = "metric"
      width  = 12
      height = 6
      properties = {
        title  = "Memory Utilization"
        view   = "timeSeries"
        stacked = false
        metrics = [
          ["AWS/ECS", "MemoryUtilization", "ServiceName", local.services.frontend, "ClusterName", "${var.monitoring.dashboard_name_prefix}-${var.environment}", { label = "Frontend" }],
          ["AWS/ECS", "MemoryUtilization", "ServiceName", local.services.backend, "ClusterName", "${var.monitoring.dashboard_name_prefix}-${var.environment}", { label = "Backend" }],
          ["AWS/ECS", "MemoryUtilization", "ServiceName", local.services.molecule, "ClusterName", "${var.monitoring.dashboard_name_prefix}-${var.environment}", { label = "Molecule Service" }],
          ["AWS/ECS", "MemoryUtilization", "ServiceName", local.services.worker, "ClusterName", "${var.monitoring.dashboard_name_prefix}-${var.environment}", { label = "Worker Service" }]
        ]
        period = local.metric_defaults.period
        stat   = local.metric_defaults.stat
        region = local.metric_defaults.region
        yAxis = {
          left = {
            min = 0
            max = 100
          }
        }
      }
    }

    # API Request Rate Widget
    api_request_rate = {
      type   = "metric"
      width  = 12
      height = 6
      properties = {
        title  = "API Request Rate"
        view   = "timeSeries"
        stacked = false
        metrics = [
          ["AWS/ApiGateway", "Count", "Stage", "prod", { label = "API Requests/Minute", stat = "Sum" }]
        ]
        period = 60
        region = local.metric_defaults.region
      }
    }

    # API Latency Widget
    api_latency = {
      type   = "metric"
      width  = 12
      height = 6
      properties = {
        title  = "API Latency (p95)"
        view   = "timeSeries"
        stacked = false
        metrics = [
          ["AWS/ApiGateway", "Latency", "Stage", "prod", { label = "API Latency", stat = "p95" }]
        ]
        period = local.metric_defaults.period
        region = local.metric_defaults.region
        annotations = {
          horizontal = [
            {
              value = 500,
              label = "SLA Threshold (500ms)",
              color = "#ff9900"
            }
          ]
        }
      }
    }

    # API Error Rate Widget
    api_error_rate = {
      type   = "metric"
      width  = 12
      height = 6
      properties = {
        title  = "API Error Rate"
        view   = "timeSeries"
        stacked = false
        metrics = [
          ["AWS/ApiGateway", "5XXError", "Stage", "prod", { label = "5XX Errors", stat = "Sum" }],
          ["AWS/ApiGateway", "4XXError", "Stage", "prod", { label = "4XX Errors", stat = "Sum" }]
        ]
        period = local.metric_defaults.period
        region = local.metric_defaults.region
      }
    }

    # RDS Database Metrics
    db_cpu_utilization = {
      type   = "metric"
      width  = 12
      height = 6
      properties = {
        title  = "Database CPU Utilization"
        view   = "timeSeries"
        stacked = false
        metrics = [
          ["AWS/RDS", "CPUUtilization", "DBInstanceIdentifier", local.databases.primary, { label = "Primary DB" }]
        ]
        period = local.metric_defaults.period
        stat   = local.metric_defaults.stat
        region = local.metric_defaults.region
        yAxis = {
          left = {
            min = 0
            max = 100
          }
        }
      }
    }

    db_connections = {
      type   = "metric"
      width  = 12
      height = 6
      properties = {
        title  = "Database Connections"
        view   = "timeSeries"
        stacked = false
        metrics = [
          ["AWS/RDS", "DatabaseConnections", "DBInstanceIdentifier", local.databases.primary, { label = "Active Connections" }]
        ]
        period = local.metric_defaults.period
        stat   = local.metric_defaults.stat
        region = local.metric_defaults.region
      }
    }

    db_queue_depth = {
      type   = "metric"
      width  = 12
      height = 6
      properties = {
        title  = "Database Disk Queue Depth"
        view   = "timeSeries"
        stacked = false
        metrics = [
          ["AWS/RDS", "DiskQueueDepth", "DBInstanceIdentifier", local.databases.primary, { label = "Queue Depth" }]
        ]
        period = local.metric_defaults.period
        stat   = local.metric_defaults.stat
        region = local.metric_defaults.region
      }
    }

    # ElastiCache Redis Metrics
    cache_cpu_utilization = {
      type   = "metric"
      width  = 12
      height = 6
      properties = {
        title  = "Cache CPU Utilization"
        view   = "timeSeries"
        stacked = false
        metrics = [
          ["AWS/ElastiCache", "CPUUtilization", "ReplicationGroupId", local.databases.redis, { label = "Redis CPU" }]
        ]
        period = local.metric_defaults.period
        stat   = local.metric_defaults.stat
        region = local.metric_defaults.region
        yAxis = {
          left = {
            min = 0
            max = 100
          }
        }
      }
    }

    cache_hit_ratio = {
      type   = "metric"
      width  = 12
      height = 6
      properties = {
        title  = "Cache Hit Ratio"
        view   = "timeSeries"
        stacked = false
        metrics = [
          ["AWS/ElastiCache", "CacheHitRate", "ReplicationGroupId", local.databases.redis, { label = "Hit Ratio" }]
        ]
        period = local.metric_defaults.period
        stat   = local.metric_defaults.stat
        region = local.metric_defaults.region
        yAxis = {
          left = {
            min = 0
            max = 100
          }
        }
      }
    }

    # S3 Bucket Metrics
    s3_bucket_size = {
      type   = "metric"
      width  = 8
      height = 6
      properties = {
        title  = "S3 Bucket Size"
        view   = "timeSeries"
        stacked = false
        metrics = [
          ["AWS/S3", "BucketSizeBytes", "BucketName", local.storage.document, "StorageType", "StandardStorage", { label = "Document Storage" }],
          ["AWS/S3", "BucketSizeBytes", "BucketName", local.storage.csv, "StorageType", "StandardStorage", { label = "CSV Storage" }],
          ["AWS/S3", "BucketSizeBytes", "BucketName", local.storage.results, "StorageType", "StandardStorage", { label = "Results Storage" }]
        ]
        period = 86400 # Daily metrics for S3
        stat   = local.metric_defaults.stat
        region = local.metric_defaults.region
      }
    }

    s3_object_count = {
      type   = "metric"
      width  = 8
      height = 6
      properties = {
        title  = "S3 Object Count"
        view   = "timeSeries"
        stacked = false
        metrics = [
          ["AWS/S3", "NumberOfObjects", "BucketName", local.storage.document, "StorageType", "AllStorageTypes", { label = "Document Objects" }],
          ["AWS/S3", "NumberOfObjects", "BucketName", local.storage.csv, "StorageType", "AllStorageTypes", { label = "CSV Objects" }],
          ["AWS/S3", "NumberOfObjects", "BucketName", local.storage.results, "StorageType", "AllStorageTypes", { label = "Results Objects" }]
        ]
        period = 86400 # Daily metrics for S3
        stat   = local.metric_defaults.stat
        region = local.metric_defaults.region
      }
    }

    # Business Metrics - Note: These would be custom metrics pushed to CloudWatch
    molecule_upload_rate = {
      type   = "metric"
      width  = 12
      height = 6
      properties = {
        title  = "Molecule Upload Rate"
        view   = "timeSeries"
        stacked = false
        metrics = [
          ["${var.monitoring.metric_namespace}", "MoleculeUploads", { label = "Molecules Uploaded", stat = "Sum" }]
        ]
        period = local.metric_defaults.period
        region = local.metric_defaults.region
      }
    }

    cro_submission_rate = {
      type   = "metric"
      width  = 12
      height = 6
      properties = {
        title  = "CRO Submission Rate"
        view   = "timeSeries"
        stacked = false
        metrics = [
          ["${var.monitoring.metric_namespace}", "CROSubmissions", { label = "Submissions", stat = "Sum" }]
        ]
        period = local.metric_defaults.period
        region = local.metric_defaults.region
      }
    }

    processing_success_rate = {
      type   = "metric"
      width  = 12
      height = 6
      properties = {
        title  = "Processing Success Rate"
        view   = "timeSeries"
        stacked = false
        metrics = [
          ["${var.monitoring.metric_namespace}", "ProcessingSuccessRate", { label = "Success Rate (%)" }]
        ]
        period = local.metric_defaults.period
        stat   = local.metric_defaults.stat
        region = local.metric_defaults.region
        yAxis = {
          left = {
            min = 0
            max = 100
          }
        }
      }
    }

    molecule_processing_time = {
      type   = "metric"
      width  = 12
      height = 6
      properties = {
        title  = "Molecule Processing Time"
        view   = "timeSeries"
        stacked = false
        metrics = [
          ["${var.monitoring.metric_namespace}", "CSVProcessingTime", { label = "Processing Time (s)", stat = "Average" }]
        ]
        period = local.metric_defaults.period
        region = local.metric_defaults.region
        annotations = {
          horizontal = [
            {
              value = 30,
              label = "SLA Threshold (30s per 10k)",
              color = "#ff9900"
            }
          ]
        }
      }
    }

    ai_prediction_time = {
      type   = "metric"
      width  = 12
      height = 6
      properties = {
        title  = "AI Prediction Time"
        view   = "timeSeries"
        stacked = false
        metrics = [
          ["${var.monitoring.metric_namespace}", "AIPredictionTime", { label = "Prediction Time (s)", stat = "Average" }]
        ]
        period = local.metric_defaults.period
        region = local.metric_defaults.region
        annotations = {
          horizontal = [
            {
              value = 120,
              label = "SLA Threshold (2min per 100)",
              color = "#ff9900"
            }
          ]
        }
      }
    }

    results_delivery_time = {
      type   = "metric"
      width  = 12
      height = 6
      properties = {
        title  = "Results Delivery Time"
        view   = "timeSeries"
        stacked = false
        metrics = [
          ["${var.monitoring.metric_namespace}", "ResultsDeliveryTime", { label = "Delivery Time (hr)", stat = "Average" }]
        ]
        period = local.metric_defaults.period
        region = local.metric_defaults.region
        annotations = {
          horizontal = [
            {
              value = 24,
              label = "SLA Threshold (24hr)",
              color = "#ff9900"
            }
          ]
        }
      }
    }

    # Authentication Metrics
    auth_success_failure = {
      type   = "metric"
      width  = 12
      height = 6
      properties = {
        title  = "Authentication Events"
        view   = "timeSeries"
        stacked = false
        metrics = [
          ["${var.monitoring.metric_namespace}", "AuthenticationSuccess", { label = "Successful Logins", stat = "Sum" }],
          ["${var.monitoring.metric_namespace}", "AuthenticationFailure", { label = "Failed Logins", stat = "Sum" }]
        ]
        period = local.metric_defaults.period
        region = local.metric_defaults.region
      }
    }

    # Document Processing
    document_processing = {
      type   = "metric"
      width  = 12
      height = 6
      properties = {
        title  = "Document Processing"
        view   = "timeSeries"
        stacked = false
        metrics = [
          ["${var.monitoring.metric_namespace}", "DocumentsProcessed", { label = "Documents Processed", stat = "Sum" }],
          ["${var.monitoring.metric_namespace}", "DocumentProcessingTime", { label = "Processing Time (s)", stat = "Average" }]
        ]
        period = local.metric_defaults.period
        region = local.metric_defaults.region
      }
    }
  }

  # Dashboard layouts - defining the widgets for each dashboard type
  dashboard_layouts = {
    # Executive Dashboard Layout - High-level system health and business KPIs
    executive = [
      local.metric_widgets.system_status,
      {
        type = "text",
        width = 24,
        height = 1,
        properties = {
          markdown = "# Business Metrics"
        }
      },
      local.metric_widgets.molecule_upload_rate,
      local.metric_widgets.cro_submission_rate,
      {
        type = "text",
        width = 24,
        height = 1,
        properties = {
          markdown = "# Performance Metrics"
        }
      },
      local.metric_widgets.processing_success_rate,
      local.metric_widgets.sla_compliance,
      local.metric_widgets.active_users
    ]

    # Operational Dashboard Layout - Service health and API performance
    operational = [
      local.metric_widgets.system_status,
      {
        type = "text",
        width = 24,
        height = 1,
        properties = {
          markdown = "# API Performance"
        }
      },
      local.metric_widgets.api_request_rate,
      local.metric_widgets.api_latency,
      local.metric_widgets.api_error_rate,
      {
        type = "text",
        width = 24,
        height = 1,
        properties = {
          markdown = "# Database Performance"
        }
      },
      local.metric_widgets.db_cpu_utilization,
      local.metric_widgets.db_connections,
      {
        type = "text",
        width = 24,
        height = 1,
        properties = {
          markdown = "# Integration Status"
        }
      },
      local.metric_widgets.molecule_processing_time,
      local.metric_widgets.ai_prediction_time
    ]

    # Technical Dashboard Layout - Detailed resource utilization
    technical = [
      {
        type = "text",
        width = 24,
        height = 1,
        properties = {
          markdown = "# Compute Resources"
        }
      },
      local.metric_widgets.cpu_utilization,
      local.metric_widgets.memory_utilization,
      {
        type = "text",
        width = 24,
        height = 1,
        properties = {
          markdown = "# Database Resources"
        }
      },
      local.metric_widgets.db_cpu_utilization,
      local.metric_widgets.db_connections,
      local.metric_widgets.db_queue_depth,
      {
        type = "text",
        width = 24,
        height = 1,
        properties = {
          markdown = "# Cache Resources"
        }
      },
      local.metric_widgets.cache_cpu_utilization,
      local.metric_widgets.cache_hit_ratio,
      {
        type = "text",
        width = 24,
        height = 1,
        properties = {
          markdown = "# Storage Resources"
        }
      },
      local.metric_widgets.s3_bucket_size,
      local.metric_widgets.s3_object_count
    ]

    # Security Dashboard Layout - Auth events, security metrics
    security = [
      {
        type = "text",
        width = 24,
        height = 1,
        properties = {
          markdown = "# Authentication Monitoring"
        }
      },
      local.metric_widgets.auth_success_failure,
      {
        type = "metric",
        width = 12,
        height = 6,
        properties = {
          title = "Login Attempts by Location",
          view = "timeSeries",
          stacked = true,
          metrics = [
            ["${var.monitoring.metric_namespace}", "AuthenticationAttempts", "Region", "NA", { label = "North America", stat = "Sum" }],
            ["${var.monitoring.metric_namespace}", "AuthenticationAttempts", "Region", "EU", { label = "Europe", stat = "Sum" }],
            ["${var.monitoring.metric_namespace}", "AuthenticationAttempts", "Region", "APAC", { label = "Asia Pacific", stat = "Sum" }],
            ["${var.monitoring.metric_namespace}", "AuthenticationAttempts", "Region", "Other", { label = "Other Regions", stat = "Sum" }]
          ],
          period = local.metric_defaults.period,
          region = local.metric_defaults.region
        }
      },
      {
        type = "text",
        width = 24,
        height = 1,
        properties = {
          markdown = "# API Security"
        }
      },
      local.metric_widgets.api_error_rate,
      {
        type = "metric",
        width = 24,
        height = 6,
        properties = {
          title = "Authorization Failures",
          view = "timeSeries",
          stacked = false,
          metrics = [
            ["${var.monitoring.metric_namespace}", "AuthorizationFailure", { label = "Permission Denied", stat = "Sum" }]
          ],
          period = local.metric_defaults.period,
          region = local.metric_defaults.region
        }
      },
      {
        type = "metric",
        width = 24,
        height = 6,
        properties = {
          title = "API Access Patterns",
          view = "timeSeries",
          stacked = true,
          metrics = [
            ["${var.monitoring.metric_namespace}", "APIAccess", "Endpoint", "Molecules", { label = "Molecule API", stat = "Sum" }],
            ["${var.monitoring.metric_namespace}", "APIAccess", "Endpoint", "Libraries", { label = "Library API", stat = "Sum" }],
            ["${var.monitoring.metric_namespace}", "APIAccess", "Endpoint", "CRO", { label = "CRO API", stat = "Sum" }],
            ["${var.monitoring.metric_namespace}", "APIAccess", "Endpoint", "Users", { label = "User API", stat = "Sum" }]
          ],
          period = local.metric_defaults.period,
          region = local.metric_defaults.region
        }
      }
    ]

    # Molecule Processing Dashboard Layout
    molecule = [
      {
        type = "text",
        width = 24,
        height = 1,
        properties = {
          markdown = "# Upload Statistics"
        }
      },
      local.metric_widgets.molecule_upload_rate,
      local.metric_widgets.processing_success_rate,
      {
        type = "text",
        width = 24,
        height = 1,
        properties = {
          markdown = "# Processing Performance"
        }
      },
      local.metric_widgets.molecule_processing_time,
      local.metric_widgets.ai_prediction_time,
      {
        type = "text",
        width = 24,
        height = 1,
        properties = {
          markdown = "# Processing Resources"
        }
      },
      {
        type = "metric",
        width = 12,
        height = 6,
        properties = {
          title = "Molecule Service Performance",
          view = "timeSeries",
          stacked = false,
          metrics = [
            ["AWS/ECS", "CPUUtilization", "ServiceName", local.services.molecule, "ClusterName", "${var.monitoring.dashboard_name_prefix}-${var.environment}", { label = "CPU Utilization" }],
            ["AWS/ECS", "MemoryUtilization", "ServiceName", local.services.molecule, "ClusterName", "${var.monitoring.dashboard_name_prefix}-${var.environment}", { label = "Memory Utilization" }]
          ],
          period = local.metric_defaults.period,
          stat = local.metric_defaults.stat,
          region = local.metric_defaults.region,
          yAxis = {
            left = {
              min = 0,
              max = 100
            }
          }
        }
      },
      {
        type = "metric",
        width = 12,
        height = 6,
        properties = {
          title = "Worker Service Performance",
          view = "timeSeries",
          stacked = false,
          metrics = [
            ["AWS/ECS", "CPUUtilization", "ServiceName", local.services.worker, "ClusterName", "${var.monitoring.dashboard_name_prefix}-${var.environment}", { label = "CPU Utilization" }],
            ["AWS/ECS", "MemoryUtilization", "ServiceName", local.services.worker, "ClusterName", "${var.monitoring.dashboard_name_prefix}-${var.environment}", { label = "Memory Utilization" }]
          ],
          period = local.metric_defaults.period,
          stat = local.metric_defaults.stat,
          region = local.metric_defaults.region,
          yAxis = {
            left = {
              min = 0,
              max = 100
            }
          }
        }
      },
      {
        type = "metric",
        width = 24,
        height = 6,
        properties = {
          title = "Property Distribution",
          view = "bar",
          stacked = false,
          metrics = [
            ["${var.monitoring.metric_namespace}", "PropertyDistribution", "Property", "LogP", { label = "LogP", stat = "Average" }],
            ["${var.monitoring.metric_namespace}", "PropertyDistribution", "Property", "MolecularWeight", { label = "Molecular Weight", stat = "Average" }],
            ["${var.monitoring.metric_namespace}", "PropertyDistribution", "Property", "TPSA", { label = "TPSA", stat = "Average" }],
            ["${var.monitoring.metric_namespace}", "PropertyDistribution", "Property", "HBD", { label = "HBD", stat = "Average" }],
            ["${var.monitoring.metric_namespace}", "PropertyDistribution", "Property", "HBA", { label = "HBA", stat = "Average" }]
          ],
          period = local.metric_defaults.period,
          region = local.metric_defaults.region
        }
      }
    ]

    # CRO Integration Dashboard Layout
    cro = [
      {
        type = "text",
        width = 24,
        height = 1,
        properties = {
          markdown = "# Submission Statistics"
        }
      },
      local.metric_widgets.cro_submission_rate,
      local.metric_widgets.results_delivery_time,
      {
        type = "text",
        width = 24,
        height = 1,
        properties = {
          markdown = "# Processing Time"
        }
      },
      local.metric_widgets.document_processing,
      {
        type = "metric",
        width = 12,
        height = 6,
        properties = {
          title = "Communication Response Time",
          view = "timeSeries",
          stacked = false,
          metrics = [
            ["${var.monitoring.metric_namespace}", "CommunicationResponseTime", "UserType", "CRO", { label = "CRO Response Time (hr)", stat = "Average" }],
            ["${var.monitoring.metric_namespace}", "CommunicationResponseTime", "UserType", "Pharma", { label = "Pharma Response Time (hr)", stat = "Average" }]
          ],
          period = local.metric_defaults.period,
          region = local.metric_defaults.region
        }
      },
      {
        type = "text",
        width = 24,
        height = 1,
        properties = {
          markdown = "# CRO Submission Status"
        }
      },
      {
        type = "metric",
        width = 24,
        height = 6,
        properties = {
          title = "Submission Status Distribution",
          view = "pie",
          metrics = [
            ["${var.monitoring.metric_namespace}", "SubmissionStatus", "Status", "Pending", { label = "Pending" }],
            ["${var.monitoring.metric_namespace}", "SubmissionStatus", "Status", "In Progress", { label = "In Progress" }],
            ["${var.monitoring.metric_namespace}", "SubmissionStatus", "Status", "Completed", { label = "Completed" }],
            ["${var.monitoring.metric_namespace}", "SubmissionStatus", "Status", "Failed", { label = "Failed" }]
          ],
          period = local.metric_defaults.period,
          stat = "Sum",
          region = local.metric_defaults.region
        }
      },
      {
        type = "metric",
        width = 24,
        height = 6,
        properties = {
          title = "Submission Flow",
          view = "timeSeries",
          stacked = true,
          metrics = [
            ["${var.monitoring.metric_namespace}", "SubmissionCreated", { label = "New Submissions", stat = "Sum" }],
            ["${var.monitoring.metric_namespace}", "SubmissionApproved", { label = "Approved Submissions", stat = "Sum" }],
            ["${var.monitoring.metric_namespace}", "ResultsDelivered", { label = "Results Delivered", stat = "Sum" }]
          ],
          period = local.metric_defaults.period,
          region = local.metric_defaults.region
        }
      }
    ]
  }
}

# Create CloudWatch Dashboards
resource "aws_cloudwatch_dashboard" "executive_dashboard" {
  dashboard_name = local.dashboard_names.executive
  dashboard_body = jsonencode({
    widgets = local.dashboard_layouts.executive
  })
}

resource "aws_cloudwatch_dashboard" "operational_dashboard" {
  dashboard_name = local.dashboard_names.operational
  dashboard_body = jsonencode({
    widgets = local.dashboard_layouts.operational
  })
}

resource "aws_cloudwatch_dashboard" "technical_dashboard" {
  dashboard_name = local.dashboard_names.technical
  dashboard_body = jsonencode({
    widgets = local.dashboard_layouts.technical
  })
}

resource "aws_cloudwatch_dashboard" "security_dashboard" {
  dashboard_name = local.dashboard_names.security
  dashboard_body = jsonencode({
    widgets = local.dashboard_layouts.security
  })
}

resource "aws_cloudwatch_dashboard" "molecule_dashboard" {
  dashboard_name = local.dashboard_names.molecule
  dashboard_body = jsonencode({
    widgets = local.dashboard_layouts.molecule
  })
}

resource "aws_cloudwatch_dashboard" "cro_dashboard" {
  dashboard_name = local.dashboard_names.cro
  dashboard_body = jsonencode({
    widgets = local.dashboard_layouts.cro
  })
}