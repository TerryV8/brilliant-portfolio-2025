variable "image_name" { type = string }
variable "flavor_name" { type = string }
variable "network_id" { type = string }
variable "keypair_name" { type = string }

variable "security_group_names" {
  description = "List of security group names to attach to the instance"
  type        = list(string)
  default     = []
}

variable "volume_name" { type = string default = "soc-apache-data" }
variable "volume_size_gb" { type = number default = 10 }
variable "volume_fs" { type = string default = "ext4" }
variable "volume_mountpoint" { type = string default = "/mnt/soc-data" }

# Optional: index passed from environment when module is created with count
variable "instance_index" {
  type        = number
  default     = -1
  description = "Index of the instance when module is instantiated with count; -1 means single instance."
}
