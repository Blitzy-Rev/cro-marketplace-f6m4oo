# ---------------------------------------------------------------------------------------------------------------------
# AWS NETWORKING MODULE for Molecular Data Management and CRO Integration Platform
# ---------------------------------------------------------------------------------------------------------------------

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
}

# ---------------------------------------------------------------------------------------------------------------------
# LOCAL VARIABLES
# ---------------------------------------------------------------------------------------------------------------------
locals {
  # Create a map of common tags to apply to all resources
  common_tags = merge(
    var.tags,
    {
      Environment = var.environment
      Project     = var.project_name
      ManagedBy   = "terraform"
    }
  )
  
  # Calculate the number of availability zones to use
  az_count = min(length(var.availability_zones), length(var.public_subnet_cidrs), length(var.private_subnet_cidrs))
  
  # Create a list of route tables for VPC endpoint association
  all_route_tables = concat(
    [aws_route_table.public.id],
    aws_route_table.private[*].id
  )
}

# ---------------------------------------------------------------------------------------------------------------------
# VPC
# ---------------------------------------------------------------------------------------------------------------------
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = var.enable_dns_support
  enable_dns_hostnames = var.enable_dns_hostnames
  
  tags = merge(
    local.common_tags,
    {
      Name = "${var.project_name}-vpc-${var.environment}"
    }
  )
}

# ---------------------------------------------------------------------------------------------------------------------
# SUBNETS
# ---------------------------------------------------------------------------------------------------------------------
resource "aws_subnet" "public" {
  count = local.az_count
  
  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.public_subnet_cidrs[count.index]
  availability_zone       = var.availability_zones[count.index]
  map_public_ip_on_launch = true
  
  tags = merge(
    local.common_tags,
    {
      Name = "${var.project_name}-public-subnet-${var.availability_zones[count.index]}-${var.environment}"
      Type = "public"
    }
  )
}

resource "aws_subnet" "private" {
  count = local.az_count
  
  vpc_id            = aws_vpc.main.id
  cidr_block        = var.private_subnet_cidrs[count.index]
  availability_zone = var.availability_zones[count.index]
  
  tags = merge(
    local.common_tags,
    {
      Name = "${var.project_name}-private-subnet-${var.availability_zones[count.index]}-${var.environment}"
      Type = "private"
    }
  )
}

# ---------------------------------------------------------------------------------------------------------------------
# INTERNET GATEWAY
# ---------------------------------------------------------------------------------------------------------------------
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
  
  tags = merge(
    local.common_tags,
    {
      Name = "${var.project_name}-igw-${var.environment}"
    }
  )
}

# ---------------------------------------------------------------------------------------------------------------------
# NAT GATEWAY
# ---------------------------------------------------------------------------------------------------------------------
resource "aws_eip" "nat" {
  count = var.enable_nat_gateway ? local.az_count : 0
  
  domain = "vpc"
  
  tags = merge(
    local.common_tags,
    {
      Name = "${var.project_name}-nat-eip-${var.availability_zones[count.index]}-${var.environment}"
    }
  )
}

resource "aws_nat_gateway" "main" {
  count = var.enable_nat_gateway ? local.az_count : 0
  
  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id
  
  tags = merge(
    local.common_tags,
    {
      Name = "${var.project_name}-nat-gateway-${var.availability_zones[count.index]}-${var.environment}"
    }
  )
  
  # To ensure proper ordering, it is recommended to add an explicit dependency
  depends_on = [aws_internet_gateway.main]
}

# ---------------------------------------------------------------------------------------------------------------------
# ROUTE TABLES
# ---------------------------------------------------------------------------------------------------------------------
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
  
  tags = merge(
    local.common_tags,
    {
      Name = "${var.project_name}-public-rtb-${var.environment}"
      Type = "public"
    }
  )
}

resource "aws_route" "public_internet_gateway" {
  route_table_id         = aws_route_table.public.id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.main.id
}

resource "aws_route_table" "private" {
  count = local.az_count
  
  vpc_id = aws_vpc.main.id
  
  tags = merge(
    local.common_tags,
    {
      Name = "${var.project_name}-private-rtb-${var.availability_zones[count.index]}-${var.environment}"
      Type = "private"
    }
  )
}

resource "aws_route" "private_nat_gateway" {
  count = var.enable_nat_gateway ? local.az_count : 0
  
  route_table_id         = aws_route_table.private[count.index].id
  destination_cidr_block = "0.0.0.0/0"
  nat_gateway_id         = aws_nat_gateway.main[count.index].id
}

# ---------------------------------------------------------------------------------------------------------------------
# ROUTE TABLE ASSOCIATIONS
# ---------------------------------------------------------------------------------------------------------------------
resource "aws_route_table_association" "public" {
  count = local.az_count
  
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "private" {
  count = local.az_count
  
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private[count.index].id
}

# ---------------------------------------------------------------------------------------------------------------------
# SECURITY GROUPS
# ---------------------------------------------------------------------------------------------------------------------
resource "aws_security_group" "alb" {
  name        = "${var.project_name}-alb-sg-${var.environment}"
  description = "Security group for the application load balancer"
  vpc_id      = aws_vpc.main.id
  
  # Allow HTTP traffic from the internet
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow HTTP traffic from the internet"
  }
  
  # Allow HTTPS traffic from the internet
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow HTTPS traffic from the internet"
  }
  
  # Allow all outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound traffic"
  }
  
  tags = merge(
    local.common_tags,
    {
      Name = "${var.project_name}-alb-sg-${var.environment}"
    }
  )
}

resource "aws_security_group" "app" {
  name        = "${var.project_name}-app-sg-${var.environment}"
  description = "Security group for application containers"
  vpc_id      = aws_vpc.main.id
  
  # Allow HTTP traffic from the ALB security group
  ingress {
    from_port       = 8080
    to_port         = 8080
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
    description     = "Allow HTTP traffic from the ALB security group"
  }
  
  # Allow all outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound traffic"
  }
  
  tags = merge(
    local.common_tags,
    {
      Name = "${var.project_name}-app-sg-${var.environment}"
    }
  )
}

resource "aws_security_group" "db" {
  name        = "${var.project_name}-db-sg-${var.environment}"
  description = "Security group for database instances"
  vpc_id      = aws_vpc.main.id
  
  # Allow PostgreSQL traffic from the application security group
  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.app.id]
    description     = "Allow PostgreSQL traffic from the application security group"
  }
  
  # Allow outbound traffic only to VPC CIDR (stricter egress control)
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = [var.vpc_cidr]
    description = "Allow outbound traffic only within VPC"
  }
  
  tags = merge(
    local.common_tags,
    {
      Name = "${var.project_name}-db-sg-${var.environment}"
    }
  )
}

resource "aws_security_group" "redis" {
  name        = "${var.project_name}-redis-sg-${var.environment}"
  description = "Security group for Redis ElastiCache"
  vpc_id      = aws_vpc.main.id
  
  # Allow Redis traffic from the application security group
  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.app.id]
    description     = "Allow Redis traffic from the application security group"
  }
  
  # Allow outbound traffic only to VPC CIDR (stricter egress control)
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = [var.vpc_cidr]
    description = "Allow outbound traffic only within VPC"
  }
  
  tags = merge(
    local.common_tags,
    {
      Name = "${var.project_name}-redis-sg-${var.environment}"
    }
  )
}

# ---------------------------------------------------------------------------------------------------------------------
# NETWORK ACLs
# ---------------------------------------------------------------------------------------------------------------------
resource "aws_network_acl" "public" {
  vpc_id     = aws_vpc.main.id
  subnet_ids = aws_subnet.public[*].id
  
  # Allow HTTP inbound
  ingress {
    protocol   = "tcp"
    rule_no    = 100
    action     = "allow"
    cidr_block = "0.0.0.0/0"
    from_port  = 80
    to_port    = 80
  }
  
  # Allow HTTPS inbound
  ingress {
    protocol   = "tcp"
    rule_no    = 110
    action     = "allow"
    cidr_block = "0.0.0.0/0"
    from_port  = 443
    to_port    = 443
  }
  
  # Allow ephemeral ports inbound (for return traffic)
  ingress {
    protocol   = "tcp"
    rule_no    = 120
    action     = "allow"
    cidr_block = "0.0.0.0/0"
    from_port  = 1024
    to_port    = 65535
  }
  
  # Allow all outbound traffic
  egress {
    protocol   = "-1"
    rule_no    = 100
    action     = "allow"
    cidr_block = "0.0.0.0/0"
    from_port  = 0
    to_port    = 0
  }
  
  tags = merge(
    local.common_tags,
    {
      Name = "${var.project_name}-public-nacl-${var.environment}"
      Type = "public"
    }
  )
}

resource "aws_network_acl" "private" {
  vpc_id     = aws_vpc.main.id
  subnet_ids = aws_subnet.private[*].id
  
  # Allow inbound traffic from VPC CIDR
  ingress {
    protocol   = "-1"
    rule_no    = 100
    action     = "allow"
    cidr_block = var.vpc_cidr
    from_port  = 0
    to_port    = 0
  }
  
  # Allow inbound traffic from ephemeral ports (for return traffic from internet via NAT)
  ingress {
    protocol   = "tcp"
    rule_no    = 110
    action     = "allow"
    cidr_block = "0.0.0.0/0"
    from_port  = 1024
    to_port    = 65535
  }
  
  # Allow outbound traffic to VPC CIDR
  egress {
    protocol   = "-1"
    rule_no    = 100
    action     = "allow"
    cidr_block = var.vpc_cidr
    from_port  = 0
    to_port    = 0
  }
  
  # Allow outbound traffic to the internet (for updates, etc.)
  egress {
    protocol   = "-1"
    rule_no    = 110
    action     = "allow"
    cidr_block = "0.0.0.0/0"
    from_port  = 0
    to_port    = 0
  }
  
  tags = merge(
    local.common_tags,
    {
      Name = "${var.project_name}-private-nacl-${var.environment}"
      Type = "private"
    }
  )
}

# ---------------------------------------------------------------------------------------------------------------------
# VPC ENDPOINTS
# ---------------------------------------------------------------------------------------------------------------------
# Data source to get current region
data "aws_region" "current" {}

# S3 Gateway Endpoint
resource "aws_vpc_endpoint" "s3" {
  count = var.enable_vpc_endpoints ? 1 : 0
  
  vpc_id            = aws_vpc.main.id
  service_name      = "com.amazonaws.${data.aws_region.current.name}.s3"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = local.all_route_tables
  
  tags = merge(
    local.common_tags,
    {
      Name = "${var.project_name}-s3-endpoint-${var.environment}"
    }
  )
}

# DynamoDB Gateway Endpoint
resource "aws_vpc_endpoint" "dynamodb" {
  count = var.enable_vpc_endpoints ? 1 : 0
  
  vpc_id            = aws_vpc.main.id
  service_name      = "com.amazonaws.${data.aws_region.current.name}.dynamodb"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = local.all_route_tables
  
  tags = merge(
    local.common_tags,
    {
      Name = "${var.project_name}-dynamodb-endpoint-${var.environment}"
    }
  )
}

# Interface Endpoints for AWS Services
resource "aws_vpc_endpoint" "interface" {
  count = var.enable_vpc_endpoints ? length(var.interface_endpoints) : 0
  
  vpc_id              = aws_vpc.main.id
  service_name        = "com.amazonaws.${data.aws_region.current.name}.${var.interface_endpoints[count.index]}"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = aws_subnet.private[*].id
  security_group_ids  = [aws_security_group.app.id]
  private_dns_enabled = true
  
  tags = merge(
    local.common_tags,
    {
      Name = "${var.project_name}-${var.interface_endpoints[count.index]}-endpoint-${var.environment}"
    }
  )
}

# ---------------------------------------------------------------------------------------------------------------------
# FLOW LOGS
# ---------------------------------------------------------------------------------------------------------------------
# IAM Role for VPC Flow Logs
resource "aws_iam_role" "flow_logs" {
  count = var.enable_flow_logs ? 1 : 0
  
  name = "${var.project_name}-flow-logs-role-${var.environment}"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "vpc-flow-logs.amazonaws.com"
        }
      }
    ]
  })
  
  tags = merge(
    local.common_tags,
    {
      Name = "${var.project_name}-flow-logs-role-${var.environment}"
    }
  )
}

# IAM Policy for VPC Flow Logs
resource "aws_iam_role_policy" "flow_logs" {
  count = var.enable_flow_logs ? 1 : 0
  
  name = "${var.project_name}-flow-logs-policy-${var.environment}"
  role = aws_iam_role.flow_logs[0].id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogGroups",
          "logs:DescribeLogStreams"
        ]
        Effect   = "Allow"
        Resource = "*"
      }
    ]
  })
}

# CloudWatch Log Group for Flow Logs
resource "aws_cloudwatch_log_group" "flow_logs" {
  count = var.enable_flow_logs ? 1 : 0
  
  name              = "/aws/vpc-flow-logs/${var.project_name}-${var.environment}"
  retention_in_days = var.flow_log_retention
  
  tags = merge(
    local.common_tags,
    {
      Name = "${var.project_name}-flow-logs-${var.environment}"
    }
  )
}

# VPC Flow Log
resource "aws_flow_log" "main" {
  count = var.enable_flow_logs ? 1 : 0
  
  iam_role_arn             = aws_iam_role.flow_logs[0].arn
  log_destination          = aws_cloudwatch_log_group.flow_logs[0].arn
  traffic_type             = "ALL"
  vpc_id                   = aws_vpc.main.id
  log_destination_type     = "cloud-watch-logs"
  max_aggregation_interval = 60
  
  tags = merge(
    local.common_tags,
    {
      Name = "${var.project_name}-vpc-flow-log-${var.environment}"
    }
  )
  
  depends_on = [
    aws_iam_role.flow_logs,
    aws_cloudwatch_log_group.flow_logs
  ]
}