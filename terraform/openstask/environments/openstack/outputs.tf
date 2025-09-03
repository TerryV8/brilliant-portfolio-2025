output "audit_container" { value = module.storage_swift.audit_container }
output "versions_container" { value = module.storage_swift.versions_container }
output "security_group_id" { value = module.network_security.security_group_id }

# With instance_count, these are lists per instance
output "apache_instance_id" {
  description = "List of instance IDs for each Apache VM"
  value       = [for m in module.compute_apache : m.instance_id]
}

output "apache_fixed_ips" {
  description = "List of lists of fixed IPs per Apache VM"
  value       = [for m in module.compute_apache : m.fixed_ips]
}

output "lb_vip_address" { value = try(module.load_balancer.vip_address, null) }
output "lb_floating_ip" { value = try(module.load_balancer.floating_ip, null) }
