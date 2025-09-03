variable "enabled" { type = bool default = false }
variable "name" { type = string default = "soc-lb" }
variable "vip_subnet_id" { type = string }
variable "protocol" { type = string default = "HTTP" }
variable "port" { type = number default = 80 }
variable "algorithm" { type = string default = "ROUND_ROBIN" }
variable "member_port" { type = number default = 80 }
variable "health_url" { type = string default = "/" }
variable "member_addresses" { type = list(string) }
variable "assign_floating_ip" { type = bool default = false }
variable "external_network_name" { type = string default = "" }
