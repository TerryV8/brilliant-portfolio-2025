resource "openstack_networking_secgroup_v2" "soc_locked_down" {
  name        = "soc-locked-down"
  description = "Least-privilege SG; SSH allowed only if allow_ssh_cidr set"
}

resource "openstack_networking_secgroup_rule_v2" "egress_all" {
  direction         = "egress"
  ethertype         = "IPv4"
  security_group_id = openstack_networking_secgroup_v2.soc_locked_down.id
}

resource "openstack_networking_secgroup_rule_v2" "ingress_ssh" {
  for_each          = toset(var.allow_ssh_cidrs)
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 22
  port_range_max    = 22
  remote_ip_prefix  = each.value
  security_group_id = openstack_networking_secgroup_v2.soc_locked_down.id
}

resource "openstack_networking_secgroup_rule_v2" "ingress_http" {
  for_each          = toset(var.http_cidrs)
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 80
  port_range_max    = 80
  remote_ip_prefix  = each.value
  security_group_id = openstack_networking_secgroup_v2.soc_locked_down.id
}

resource "openstack_networking_secgroup_rule_v2" "ingress_https" {
  for_each          = toset(var.https_cidrs)
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 443
  port_range_max    = 443
  remote_ip_prefix  = each.value
  security_group_id = openstack_networking_secgroup_v2.soc_locked_down.id
}

# LB -> backend rule
data "openstack_networking_subnet_v2" "lb_vip" {
  count = var.lb_enabled && length(var.lb_vip_subnet_id) > 0 ? 1 : 0
  id    = var.lb_vip_subnet_id
}

resource "openstack_networking_secgroup_rule_v2" "ingress_from_lb" {
  count             = var.lb_enabled ? 1 : 0
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = var.lb_member_port
  port_range_max    = var.lb_member_port
  remote_ip_prefix  = data.openstack_networking_subnet_v2.lb_vip[0].cidr
  security_group_id = openstack_networking_secgroup_v2.soc_locked_down.id
}

# Optional FWaaS v2
resource "openstack_fw_rule_v2" "allow_http_from_lb" {
  count                = var.fw_enabled && var.lb_enabled ? 1 : 0
  name                 = "soc-allow-http-from-lb"
  protocol             = "tcp"
  action               = "allow"
  enabled              = true
  source_ip_address    = data.openstack_networking_subnet_v2.lb_vip[0].cidr
  destination_port     = tostring(var.lb_member_port)
}

resource "openstack_fw_policy_v2" "ingress" {
  count = var.fw_enabled && var.lb_enabled ? 1 : 0
  name  = "soc-ingress-policy"
  rules = [openstack_fw_rule_v2.allow_http_from_lb[0].id]
}

resource "openstack_fw_rule_v2" "egress_allow_all" {
  count   = var.fw_enabled && var.fw_egress_default_action == "allow" ? 1 : 0
  name    = "soc-egress-allow-all"
  action  = "allow"
  enabled = true
}

resource "openstack_fw_policy_v2" "egress" {
  count = var.fw_enabled && var.fw_egress_default_action == "allow" ? 1 : 0
  name  = "soc-egress-policy"
  rules = [openstack_fw_rule_v2.egress_allow_all[0].id]
}

resource "openstack_fw_group_v2" "soc" {
  count                        = var.fw_enabled ? 1 : 0
  name                         = "soc-fw-group"
  ingress_firewall_policy_id   = var.lb_enabled ? openstack_fw_policy_v2.ingress[0].id : null
  egress_firewall_policy_id    = var.fw_egress_default_action == "allow" ? openstack_fw_policy_v2.egress[0].id : null
  ports                        = var.fw_attach_ports
  admin_state_up               = true
}
