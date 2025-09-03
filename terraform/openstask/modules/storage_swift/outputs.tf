output "audit_container" {
  value       = openstack_objectstorage_container_v1.audit.name
  description = "Swift container name for SOC audit logs"
}

output "versions_container" {
  value       = openstack_objectstorage_container_v1.audit_versions.name
  description = "Swift versions container name"
}
