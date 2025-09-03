variable "allow_ssh_cidrs" { description = "CIDRs allowed to SSH" type = list(string) default = [] }
variable "http_cidrs" { description = "CIDRs allowed to HTTP" type = list(string) default = [] }
variable "https_cidrs" { description = "CIDRs allowed to HTTPS" type = list(string) default = [] }
variable "lb_enabled" { description = "Whether LB is enabled (to add SG rule from LB subnet)" type = bool default = false }
variable "lb_member_port" { description = "Backend port (e.g., 80)" type = number default = 80 }
variable "lb_vip_subnet_id" { description = "Subnet ID of LB VIP for CIDR discovery" type = string default = "" }

variable "fw_enabled" { description = "Enable FWaaS v2" type = bool default = false }
variable "fw_attach_ports" { description = "Ports to attach FW group to" type = list(string) default = [] }
variable "fw_ingress_default_action" { description = "Ingress default action" type = string default = "deny" }
variable "fw_egress_default_action" { description = "Egress default action" type = string default = "allow" }
