# Module: storage_swift

Creates OpenStack Swift containers for SOC audit logs with object versioning for tamper-evidence.

Resources:
- openstack_objectstorage_container_v1.audit
- openstack_objectstorage_container_v1.audit_versions
- audit_with_versioning metadata to enable versioning via X-Versions-Location

Inputs:
- container_name (string)

Outputs:
- audit_container
- versions_container
