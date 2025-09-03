resource "openstack_lb_loadbalancer_v2" "soc" {
  count         = var.enabled ? 1 : 0
  name          = var.name
  vip_subnet_id = var.vip_subnet_id
}

resource "openstack_lb_listener_v2" "soc" {
  count           = var.enabled ? 1 : 0
  name            = "${var.name}-listener"
  protocol        = var.protocol
  protocol_port   = var.port
  loadbalancer_id = openstack_lb_loadbalancer_v2.soc[0].id
}

resource "openstack_lb_pool_v2" "soc" {
  count       = var.enabled ? 1 : 0
  name        = "${var.name}-pool"
  protocol    = var.protocol
  lb_method   = var.algorithm
  listener_id = openstack_lb_listener_v2.soc[0].id
}

resource "openstack_lb_member_v2" "members" {
  for_each      = var.enabled ? toset(var.member_addresses) : []
  address       = each.value
  protocol_port = var.member_port
  pool_id       = openstack_lb_pool_v2.soc[0].id
  subnet_id     = var.vip_subnet_id
}

resource "openstack_lb_monitor_v2" "soc" {
  count        = var.enabled ? 1 : 0
  pool_id      = openstack_lb_pool_v2.soc[0].id
  type         = var.protocol
  delay        = 10
  timeout      = 5
  max_retries  = 3
  http_method  = "GET"
  url_path     = var.health_url
  expected_codes = "200"
}

resource "openstack_networking_floatingip_v2" "lb" {
  count       = var.enabled && var.assign_floating_ip && length(var.external_network_name) > 0 ? 1 : 0
  pool        = var.external_network_name
  description = "SOC LB FIP"
}

resource "openstack_networking_floatingip_associate_v2" "lb" {
  count      = var.enabled && var.assign_floating_ip && length(var.external_network_name) > 0 ? 1 : 0
  floating_ip = openstack_networking_floatingip_v2.lb[0].address
  port_id     = openstack_lb_loadbalancer_v2.soc[0].vip_port_id
}
