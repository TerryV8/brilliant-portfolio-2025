output "security_group_id" {
  value       = openstack_networking_secgroup_v2.soc_locked_down.id
  description = "ID of the restrictive security group"
}

output "security_group_name" {
  value       = openstack_networking_secgroup_v2.soc_locked_down.name
  description = "Name of the restrictive security group"
}
