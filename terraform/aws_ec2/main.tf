terraform {
  required_version = ">= 1.3.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
  }
  # backend "s3" {}
}

provider "aws" {
  region = var.aws_region
}

# --- Networking ---
resource "aws_vpc" "this" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true
  tags = merge(var.tags, { Name = "${var.project}-vpc" })
}

resource "aws_internet_gateway" "this" {
  vpc_id = aws_vpc.this.id
  tags   = merge(var.tags, { Name = "${var.project}-igw" })
}

resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.this.id
  cidr_block              = var.public_subnet_cidr
  map_public_ip_on_launch = true
  availability_zone       = var.availability_zone
  tags                    = merge(var.tags, { Name = "${var.project}-public-subnet" })
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.this.id
  tags   = merge(var.tags, { Name = "${var.project}-public-rt" })
}

resource "aws_route" "igw" {
  route_table_id         = aws_route_table.public.id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.this.id
}

resource "aws_route_table_association" "public" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}

# --- Security Group ---
resource "aws_security_group" "ec2_sg" {
  name        = "${var.project}-ec2-sg"
  description = "Allow SSH and HTTP"
  vpc_id      = aws_vpc.this.id

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = var.ssh_allowed_cidrs
  }

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, { Name = "${var.project}-ec2-sg" })
}

# --- Optional Key Pair ---
resource "aws_key_pair" "this" {
  count      = var.ssh_public_key == null ? 0 : 1
  key_name   = "${var.project}-key"
  public_key = var.ssh_public_key
}

# --- IAM Role for SSM (no SSH needed) ---
resource "aws_iam_role" "ssm_role" {
  name               = "${var.project}-ec2-ssm-role"
  assume_role_policy = data.aws_iam_policy_document.ec2_assume.json
  tags               = var.tags
}

data "aws_iam_policy_document" "ec2_assume" {
  statement {
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role_policy_attachment" "ssm_core" {
  role       = aws_iam_role.ssm_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "ssm_profile" {
  name = "${var.project}-ec2-ssm-profile"
  role = aws_iam_role.ssm_role.name
}

# --- EC2 Instance ---
locals {
  user_data = var.install_nginx ? <<-EOT
              #!/bin/bash
              set -euo pipefail
              apt-get update -y || yum -y update || true
              # Try install nginx for Debian/Ubuntu
              if command -v apt-get >/dev/null 2>&1; then
                apt-get install -y nginx
                systemctl enable nginx || true
                systemctl start nginx || true
              elif command -v yum >/dev/null 2>&1; then
                amazon-linux-extras install -y nginx1 || yum install -y nginx || true
                systemctl enable nginx || true
                systemctl start nginx || true
              fi
              echo "Hello from ${var.project}" > /usr/share/nginx/html/index.html || true
              EOT : null
}

resource "aws_instance" "this" {
  ami                         = var.ami_id
  instance_type               = var.instance_type
  subnet_id                   = aws_subnet.public.id
  vpc_security_group_ids      = [aws_security_group.ec2_sg.id]
  key_name                    = length(aws_key_pair.this) > 0 ? aws_key_pair.this[0].key_name : null
  iam_instance_profile        = aws_iam_instance_profile.ssm_profile.name
  associate_public_ip_address = true
  user_data                   = local.user_data

  tags = merge(var.tags, { Name = "${var.project}-ec2" })
}
