variable "os_region" { type = string default = "" }
variable "os_cloud" { type = string default = "" }

variable "container_name" { type = string default = "soc-audit-logs" }

variable "allow_ssh_cidrs" { type = list(string) default = [] }
variable "http_cidrs" { type = list(string) default = [] }
variable "https_cidrs" { type = list(string) default = [] }

variable "image_name" { type = string default = "Ubuntu 22.04" }
variable "flavor_name" { type = string default = "m1.small" }
variable "network_id" { type = string }
variable "keypair_name" { type = string }

variable "volume_name" { type = string default = "soc-apache-data" }
variable "volume_size_gb" { type = number default = 10 }
variable "volume_fs" { type = string default = "ext4" }
variable "volume_mountpoint" { type = string default = "/mnt/soc-data" }

# Number of Apache instances to launch
variable "instance_count" { type = number default = 2 }

# Basic input validations
validation {
  condition     = length(var.network_id) > 0 && length(var.keypair_name) > 0
  error_message = "'network_id' and 'keypair_name' must be provided."
}

validation {
  condition     = var.instance_count >= 1
  error_message = "'instance_count' must be >= 1."
}

validation {
  condition     = alltrue([for c in var.allow_ssh_cidrs : can(cidrnetmask(c))])
  error_message = "All entries in allow_ssh_cidrs must be valid IPv4 CIDR blocks."
}

validation {
  condition     = alltrue([for c in var.http_cidrs : can(cidrnetmask(c))])
  error_message = "All entries in http_cidrs must be valid IPv4 CIDR blocks."
}

validation {
  condition     = alltrue([for c in var.https_cidrs : can(cidrnetmask(c))])
  error_message = "All entries in https_cidrs must be valid IPv4 CIDR blocks."
}

variable "lb_enabled" { type = bool default = false }
variable "lb_vip_subnet_id" { type = string default = "" }
variable "assign_lb_floating_ip" { type = bool default = false }
variable "external_network_name" { type = string default = "" }

variable "fw_enabled" { type = bool default = false }
variable "fw_attach_ports" { type = list(string) default = [] }
variable "fw_ingress_default_action" { type = string default = "deny" }
variable "fw_egress_default_action" { type = string default = "allow" }

# Optional remote-exec against the Apache instance (not recommended vs cloud-init, but available)
variable "remote_exec_enabled" { type = bool default = false }
variable "remote_exec_user" { type = string default = "ubuntu" }
variable "remote_exec_private_key" {
  type        = string
  default     = ""
  sensitive   = true
  description = "PEM-formatted private key content for SSH auth"
}
variable "remote_exec_host" {
  type        = string
  default     = ""
  description = "Override SSH host (e.g., server Floating IP). If empty, uses first fixed IP."
}

# Optional: run an Ansible playbook after instance creation
variable "ansible_enabled" { type = bool default = false }
variable "ansible_playbook_path" {
  type        = string
  default     = ""
  description = "Path to ansible playbook to run (e.g., ./playbooks/site.yml)"
}
variable "ansible_user" { type = string default = "ubuntu" }
variable "ansible_private_key_path" {
  type        = string
  default     = ""
  description = "Path to SSH private key file used by Ansible. If empty, Ansible will use its defaults (e.g., ssh-agent)."
}
variable "ansible_extra_vars" { type = map(string) default = {} }

# Ansible timing/interpreter knobs
variable "ansible_sleep_seconds" { type = number default = 45 }
variable "ansible_python_interpreter" { type = string default = "python3" }

# Optional PostgreSQL database (self-managed)
variable "db_enabled" { type = bool default = true }
variable "db_name" { type = string default = "appdb" }
variable "db_user" { type = string default = "appuser" }
