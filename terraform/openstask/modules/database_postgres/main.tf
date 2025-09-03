resource "openstack_networking_secgroup_v2" "db" {
  name        = "soc-db-postgres"
  description = "Security group for PostgreSQL: default deny; allow 5432 from Apache SG"
}

resource "openstack_networking_secgroup_rule_v2" "db_egress_all" {
  direction         = "egress"
  ethertype         = "IPv4"
  security_group_id = openstack_networking_secgroup_v2.db.id
}

data "openstack_networking_secgroup_v2" "apache" {
  name = var.apache_security_group_name
}

resource "openstack_networking_secgroup_rule_v2" "db_ingress_pg" {
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = var.db_port
  port_range_max    = var.db_port
  security_group_id = openstack_networking_secgroup_v2.db.id
  remote_group_id   = data.openstack_networking_secgroup_v2.apache.id
}

resource "openstack_blockstorage_volume_v3" "db_data" {
  name = var.volume_name
  size = var.volume_size_gb
}

resource "openstack_compute_instance_v2" "postgres" {
  name        = "soc-postgres"
  image_name  = var.image_name
  flavor_name = var.flavor_name
  key_pair    = var.keypair_name

  security_groups = [openstack_networking_secgroup_v2.db.name]

  network { uuid = var.network_id }

  user_data = <<-EOT
    #cloud-config
    package_update: true
    packages:
      - postgresql
      - postgresql-contrib
    write_files:
      - path: /etc/postgresql/14/main/conf.d/10-listen.conf
        permissions: '0644'
        content: |
          listen_addresses = '*'
      - path: /etc/postgresql/14/main/conf.d/20-auth.conf
        permissions: '0644'
        content: |
          # Authentication rules managed by cloud-init; network access controlled via Security Group
          local   all             all                                     peer
          host    ${var.db_name}  ${var.db_user}  0.0.0.0/0               md5
    runcmd:
      - |
        DEV=/dev/vdb
        MP="${var.volume_mountpoint}"
        FS="${var.volume_fs}"
        if [ -b "$DEV" ]; then
          mkdir -p "$MP"
          if ! blkid "$DEV" >/dev/null 2>&1; then
            mkfs -t "$FS" "$DEV"
          fi
          if ! grep -q "^$DEV\\s\+$MP\\s" /etc/fstab; then
            echo "$DEV $MP $FS defaults,nofail 0 2" >> /etc/fstab
          fi
          mount -a || true
        fi
      - systemctl enable postgresql
      - systemctl restart postgresql
      - sudo -u postgres psql -tc "SELECT 1 FROM pg_roles WHERE rolname='${var.db_user}'" | grep -q 1 || sudo -u postgres psql -c "CREATE ROLE ${var.db_user} LOGIN;"
      - sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname='${var.db_name}'" | grep -q 1 || sudo -u postgres createdb -O ${var.db_user} ${var.db_name}
  EOT
}

resource "openstack_compute_volume_attach_v2" "db_data_attach" {
  instance_id = openstack_compute_instance_v2.postgres.id
  volume_id   = openstack_blockstorage_volume_v3.db_data.id
  device      = "/dev/vdb"
}
