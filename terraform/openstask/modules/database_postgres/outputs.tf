output "db_private_ip" {
  value = try(openstack_compute_instance_v2.postgres.network[0].fixed_ip_v4, null)
}

output "db_port" {
  value = var.db_port
}

output "db_name" {
  value = var.db_name
}

output "db_user" {
  value = var.db_user
}
