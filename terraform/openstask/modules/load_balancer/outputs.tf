output "vip_address" { value = one(openstack_lb_loadbalancer_v2.soc[*].vip_address) }
output "vip_port_id" { value = one(openstack_lb_loadbalancer_v2.soc[*].vip_port_id) }
output "floating_ip" { value = one(openstack_networking_floatingip_v2.lb[*].address) }
