resource "openstack_compute_instance_v2" "apache" {
  name        = var.instance_index >= 0 ? "web-server-apache-${var.instance_index}" : "web-server-apache"
  image_name  = var.image_name
  flavor_name = var.flavor_name
  key_pair    = var.keypair_name

  security_groups = var.security_group_names

  network { uuid = var.network_id }

  user_data = <<-EOT
    #cloud-config
    package_update: true
    packages:
      - apache2
    runcmd:
      - systemctl enable apache2
      - systemctl restart apache2
      - echo "<h1>SOC Apache</h1>" > /var/www/html/index.html
      - |
        DEV=/dev/vdb
        MP="${var.volume_mountpoint}"
        FS="${var.volume_fs}"
        mkdir -p "$MP"
        if [ -b "$DEV" ]; then
          if ! blkid "$DEV" >/dev/null 2>&1; then
            mkfs -t "$FS" "$DEV"
          fi
          if ! grep -q "^$DEV\s\+$MP\s" /etc/fstab; then
            echo "$DEV $MP $FS defaults,nofail 0 2" >> /etc/fstab
          fi
          mount -a || true
        fi
  EOT
}

resource "openstack_blockstorage_volume_v3" "soc_data" {
  name = var.volume_name
  size = var.volume_size_gb
}

resource "openstack_compute_volume_attach_v2" "apache_data_attach" {
  instance_id = openstack_compute_instance_v2.apache.id
  volume_id   = openstack_blockstorage_volume_v3.soc_data.id
  device      = "/dev/vdb"
}
