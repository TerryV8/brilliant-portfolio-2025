variable "project" {
  description = "Project/name prefix for resources"
  type        = string
  default     = "demo"
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "eu-west-1"
}

variable "availability_zone" {
  description = "AZ for the public subnet"
  type        = string
  default     = "eu-west-1a"
}

variable "tags" {
  description = "Common tags"
  type        = map(string)
  default     = {}
}

variable "vpc_cidr" {
  description = "VPC CIDR"
  type        = string
  default     = "10.50.0.0/16"
}

variable "public_subnet_cidr" {
  description = "Public subnet CIDR"
  type        = string
  default     = "10.50.1.0/24"
}

variable "ssh_allowed_cidrs" {
  description = "CIDRs allowed to SSH into EC2"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "ssh_public_key" {
  description = "Optional SSH public key content to create a key pair"
  type        = string
  default     = null
}

variable "ami_id" {
  description = "AMI ID for EC2 instance"
  type        = string
  # e.g. Ubuntu 22.04 in eu-west-1. Update as needed.
  default     = "ami-0505148b8a26e0c16"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.micro"
}

variable "install_nginx" {
  description = "Install and start NGINX via user_data"
  type        = bool
  default     = true
}
