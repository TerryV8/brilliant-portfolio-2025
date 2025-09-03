output "vpc_id" {
  value       = aws_vpc.this.id
  description = "VPC ID"
}

output "public_subnet_id" {
  value       = aws_subnet.public.id
  description = "Public subnet ID"
}

output "security_group_id" {
  value       = aws_security_group.ec2_sg.id
  description = "EC2 security group ID"
}

output "instance_id" {
  value       = aws_instance.this.id
  description = "EC2 instance ID"
}

output "public_ip" {
  value       = aws_instance.this.public_ip
  description = "EC2 public IP"
}

output "public_dns" {
  value       = aws_instance.this.public_dns
  description = "EC2 public DNS"
}
