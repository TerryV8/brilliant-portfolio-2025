variable "image_name" { type = string default = "Ubuntu 22.04" }
variable "flavor_name" { type = string default = "m1.small" }
variable "network_id" { type = string }
variable "keypair_name" { type = string }

variable "volume_name" { type = string default = "soc-postgres-data" }
variable "volume_size_gb" { type = number default = 20 }
variable "volume_fs" { type = string default = "ext4" }
variable "volume_mountpoint" { type = string default = "/var/lib/postgresql" }

variable "db_name" { type = string default = "appdb" }
variable "db_user" { type = string default = "appuser" }
# NOTE: Do not pass password via TF state in production; inject via Ansible/Vault.
variable "db_port" { type = number default = 5432 }

# Security: allow ingress from Apache SG via remote_group_id
# Pass Apache security group NAME; module will resolve ID
variable "apache_security_group_name" { type = string }
