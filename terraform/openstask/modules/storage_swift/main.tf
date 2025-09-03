resource "openstack_objectstorage_container_v1" "audit" {
  name         = var.container_name
  content_type = "application/json"
  metadata = {
    purpose = "soc-audit-logs"
  }
}

resource "openstack_objectstorage_container_v1" "audit_versions" {
  name = "${var.container_name}-versions"
}

resource "openstack_objectstorage_container_v1" "audit_with_versioning" {
  name = openstack_objectstorage_container_v1.audit.name
  metadata = {
    "X-Versions-Location" = openstack_objectstorage_container_v1.audit_versions.name
  }
  depends_on = [openstack_objectstorage_container_v1.audit_versions]
}
