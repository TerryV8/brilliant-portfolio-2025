output "instance_id" { value = openstack_compute_instance_v2.apache.id }
output "fixed_ips" { value = openstack_compute_instance_v2.apache.network[*].fixed_ip_v4 }
