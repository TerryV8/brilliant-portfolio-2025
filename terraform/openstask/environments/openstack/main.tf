# Storage: Swift audit containers with versioning
module "storage_swift" {
  source         = "../../modules/storage_swift"
  container_name = var.container_name
}

# Optional: run an Ansible playbook against each instance after creation
resource "null_resource" "apache_ansible_apply" {
  count = var.ansible_enabled ? var.instance_count : 0

  triggers = {
    instance_id = module.compute_apache[count.index].instance_id
    ip_hash     = join(",", module.compute_apache[count.index].fixed_ips)
    playbook    = var.ansible_playbook_path
    user        = var.ansible_user
    keypath     = var.ansible_private_key_path
  }

  provisioner "local-exec" {
    interpreter = ["/bin/bash", "-lc"]
    command = <<-EOC
      set -euo pipefail
      HOST="${length(module.compute_apache[count.index].fixed_ips) > 0 ? module.compute_apache[count.index].fixed_ips[0] : ""}"
      INV="${length(module.compute_apache[count.index].fixed_ips) > 0 ? module.compute_apache[count.index].fixed_ips[0] : ""},"
      USER="${var.ansible_user}"
      KEY="${var.ansible_private_key_path}"
      PKARG=""
      if [[ -n "$KEY" ]]; then PKARG="--private-key $KEY"; fi
      if [[ -z "${var.ansible_playbook_path}" ]]; then echo "ansible_playbook_path not set"; exit 1; fi
      export ANSIBLE_HOST_KEY_CHECKING=False
      DBHOST="${var.db_enabled ? module.database_postgres[0].db_private_ip : ""}"
      DBPORT="${var.db_enabled ? module.database_postgres[0].db_port : 5432}"
      DBNAME="${var.db_enabled ? var.db_name : ""}"
      DBUSER="${var.db_enabled ? var.db_user : ""}"
      sleep ${var.ansible_sleep_seconds}
      ansible-playbook -i "$INV" -u "$USER" $PKARG \
        -e host_ip="$HOST" \
        -e db_host="$DBHOST" -e db_port="$DBPORT" -e db_name="$DBNAME" -e db_user="$DBUSER" \
        -e ansible_python_interpreter="${var.ansible_python_interpreter}" \
        "${var.ansible_playbook_path}"
    EOC
  }
}

# Network security: SG baseline (+ optional FWaaS and LB-to-backend rule)
module "network_security" {
  source                    = "../../modules/network_security"
  allow_ssh_cidrs           = var.allow_ssh_cidrs
  http_cidrs                = var.http_cidrs
  https_cidrs               = var.https_cidrs
  lb_enabled                = var.lb_enabled
  lb_member_port            = 80
  lb_vip_subnet_id          = var.lb_vip_subnet_id
  fw_enabled                = var.fw_enabled
  fw_attach_ports           = var.fw_attach_ports
  fw_ingress_default_action = var.fw_ingress_default_action
  fw_egress_default_action  = var.fw_egress_default_action
}

# Database: PostgreSQL (optional, self-managed)
module "database_postgres" {
  count                = var.db_enabled ? 1 : 0
  source               = "../../modules/database_postgres"
  image_name           = var.image_name
  flavor_name          = var.flavor_name
  network_id           = var.network_id
  keypair_name         = var.keypair_name
  volume_name          = "soc-postgres-data"
  volume_size_gb       = 20
  volume_fs            = "ext4"
  volume_mountpoint    = "/var/lib/postgresql"
  db_name              = var.db_name
  db_user              = var.db_user
  apache_security_group_name = module.network_security.security_group_name
}

# Compute: Apache server(s) + data volume
module "compute_apache" {
  count             = var.instance_count
  source            = "../../modules/compute_apache"
  image_name        = var.image_name
  flavor_name       = var.flavor_name
  network_id        = var.network_id
  keypair_name      = var.keypair_name
  security_group_names = [module.network_security.security_group_name]
  volume_name       = var.volume_name
  volume_size_gb    = var.volume_size_gb
  volume_fs         = var.volume_fs
  volume_mountpoint = var.volume_mountpoint
  instance_index    = count.index
}

# Optional remote-exec verification on the Apache instance
resource "null_resource" "apache_remote_exec" {
  count = var.remote_exec_enabled ? var.instance_count : 0

  triggers = {
    instance_id = module.compute_apache[count.index].instance_id
    ip_hash     = join(",", module.compute_apache[count.index].fixed_ips)
  }

  connection {
    type        = "ssh"
    user        = var.remote_exec_user
    private_key = var.remote_exec_private_key
    host        = var.remote_exec_host != "" ? var.remote_exec_host : (length(module.compute_apache[count.index].fixed_ips) > 0 ? module.compute_apache[count.index].fixed_ips[0] : "")
  }

  provisioner "remote-exec" {
    inline = [
      # ensure package metadata is fresh (no-op if cloud-init has done this)
      "sudo bash -lc 'command -v apt && sudo apt-get update -y || true'",
      # verify apache service is up (Debian/Ubuntu or RHEL/CentOS)
      "sudo bash -lc 'systemctl is-active --quiet apache2 || systemctl is-active --quiet httpd'",
      # simple local HTTP check
      "curl -fsS http://127.0.0.1/ >/dev/null",
      # place a marker for audit/debug
      "echo remote-exec-ok | sudo tee /var/tmp/remote-exec-status >/dev/null"
    ]
  }
}

# Load Balancer: Octavia (optional)
module "load_balancer" {
  source               = "../../modules/load_balancer"
  enabled              = var.lb_enabled
  name                 = "soc-lb"
  vip_subnet_id        = var.lb_vip_subnet_id
  protocol             = "HTTP"
  port                 = 80
  algorithm            = "ROUND_ROBIN"
  member_port          = 80
  health_url           = "/"
  member_addresses     = compact([for m in module.compute_apache : try(m.fixed_ips[0], null)])
  assign_floating_ip   = var.assign_lb_floating_ip
  external_network_name = var.external_network_name
}
