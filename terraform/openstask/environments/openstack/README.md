# Environment: OpenStack SOC baseline

This environment composes reusable modules to provision:
- Swift containers for SOC audit logs with versioning
- Restrictive Security Group (+ optional FWaaS)
- Apache server with cloud-init and a data volume
- Octavia Load Balancer with health checks and optional Floating IP
- PostgreSQL database VM (optional) with SG-to-SG restricted ingress

## Prereqs
- Terraform >= 1.4
- OpenStack provider >= 1.54
- Auth via clouds.yaml (set `os_cloud`) or OS_* env vars

## Quick start

```bash
cd terraform/environments/openstack
terraform init
terraform plan -var-file=terraform.tfvars.example \
  -var "network_id=<TENANT_NET_UUID>" \
  -var "keypair_name=<KEYPAIR>"
```

## Notes
- Keep instance `http_cidrs` empty (i.e., `[]`) when LB is enabled; traffic should come via the LB.
- Swift versioning is enabled using `X-Versions-Location`.
- FWaaS v2 is optional and may not be available on all clouds.

---

## Design and Security Rationale

- __Swift audit logging__: Two containers are created: a primary container for JSONL logs and a `${name}-versions` container. Setting `X-Versions-Location` on the primary container makes object updates preserve prior versions in the versions container, providing tamper-evidence.
- __Default-deny security__: The security group denies all by default; ingress is explicitly allowed per-port using CIDRs (`allow_ssh_cidrs`, `http_cidrs`, `https_cidrs`). When the LB is enabled, backend HTTP ingress is tightened to only allow from the LB VIP subnet.
- __Optional FWaaS v2__: For environments supporting Neutron FWaaS v2, you can define firewall rules and attach a firewall group to ports for policy-based control beyond SGs.
- __Immutable provisioning__: Apache and the data volume are configured via cloud-init at boot (idempotent). Remote-exec is provided for smoke checks but should not be the primary configuration mechanism.

## Scaling servers (instance_count)

- `instance_count` controls how many Apache instances are created.
- Outputs like `apache_instance_id` and `apache_fixed_ips` become lists aligned to each instance.
- The load balancer automatically attaches all instances using their first fixed IP.
- Instance names are suffixed with an index for clarity (e.g., `web-server-apache-0`).

## Remote-exec (optional)

- Disabled by default. Enable via:
  - `remote_exec_enabled = true`
  - Supply `remote_exec_private_key` (PEM content) and `remote_exec_user` (e.g., `ubuntu`).
  - Recommend setting `remote_exec_host` to a reachable Floating IP.
- Commands performed:
  - Refresh apt metadata (if apt present).
  - Assert Apache service is active (`apache2` or `httpd`).
  - Curl localhost.
  - Write `/var/tmp/remote-exec-status` marker.

## Load balancer tips

- When `lb_enabled = true`:
  - Keep instance `http_cidr = ""` to avoid exposing backends directly.
  - Ensure `lb_vip_subnet_id` is reachable by the backends.
  - Set `assign_lb_floating_ip = true` and `external_network_name` to expose the VIP publicly.

## Example tfvars snippet

```hcl
os_cloud              = "mycloud"
os_region             = "GRA"

container_name        = "soc-audit"

network_id            = "<tenant-net-uuid>"
keypair_name          = "soc-key"

image_name            = "Ubuntu 22.04"
flavor_name           = "b2-7"
instance_count        = 2

# Security
allow_ssh_cidrs       = ["203.0.113.0/24"]
http_cidrs            = []   # empty when LB enabled
https_cidrs           = []   # not used by Apache example

# Volume
volume_name           = "soc-data"
volume_size_gb        = 10
volume_fs             = "ext4"
volume_mountpoint     = "/mnt/soc-data"

# Load balancer
lb_enabled            = true
lb_vip_subnet_id      = "<vip-subnet-uuid>"
assign_lb_floating_ip = true
external_network_name = "Ext-Net"

# Remote exec (optional)
remote_exec_enabled   = false
remote_exec_user      = "ubuntu"
# remote_exec_private_key = <<EOF
# -----BEGIN OPENSSH PRIVATE KEY-----
# ...
# -----END OPENSSH PRIVATE KEY-----
# EOF
# remote_exec_host = "198.51.100.12"

# Database (optional)
db_enabled            = true
db_name               = "appdb"
db_user               = "appuser"
```

## Troubleshooting

- __Cannot SSH for remote-exec__: Ensure a Floating IP is associated and `remote_exec_host` is set; verify SG allows SSH from your CIDR.
- __LB health checks failing__: Confirm backends are reachable from LB subnet and Apache is listening on port 80. Verify SG rule allowing LB subnet to backend.
- __Swift versioning not showing__: Ensure the Swift cluster has the versions middleware enabled; some providers may restrict it.
- __Apache cannot reach PostgreSQL__: Ensure `db_enabled = true`, both attach to the same tenant `network_id`, and Security Group rule allows 5432 from the Apache SG. Verify Ansible received `db_host` and that your app has the required client driver.

## Cleanup

```bash
terraform destroy -auto-approve
```

This will remove the LB, instances, security resources, and Swift containers (including versions). If containers are protected by policy, deletion may require elevated permissions.

---

## Ansible Post-Provision (optional)

You can have Terraform run an Ansible playbook against each created instance after provisioning.

1) Enable and configure in your tfvars:

```hcl
ansible_enabled            = true
ansible_playbook_path      = "./playbooks/apache.yml"
ansible_user               = "ubuntu"
ansible_private_key_path   = "~/.ssh/thekey.pem"
ansible_sleep_seconds      = 45
ansible_python_interpreter = "/usr/bin/python3"
```

2) What runs (per instance):

```bash
sleep 45
ansible-playbook \
  -i "<INSTANCE_IP>," \
  -u "ubuntu" \
  --private-key "~/.ssh/thekey.pem" \
  -e host_ip="<INSTANCE_IP>" \
  -e ansible_python_interpreter="/usr/bin/python3" \
  ./playbooks/apache.yml
```

Notes:
- Ensure the instance IP is reachable from where Terraform runs (Floating IP recommended) and SG allows SSH from your source IP.
- Host key checking is disabled by default in the provisioner for convenience. For stricter security, pin host keys.
- With `instance_count > 1`, the playbook runs once per instance.

### Database connection variables

When `db_enabled = true`, the Ansible step receives extra variables:

- `db_host`: private IP of the PostgreSQL VM
- `db_port`: default 5432
- `db_name`: application database name
- `db_user`: application DB user

Provide `db_password` securely via CI (GitLab protected variable) or Vault and reference it in your playbook; do not store DB passwords in Terraform state.

## Variables quick reference (selected)

- __Auth__: `os_cloud`, `os_region`
- __Storage__: `container_name`
- __Compute__: `image_name`, `flavor_name`, `network_id`, `keypair_name`, `instance_count`, volume vars
- __Security__: `allow_ssh_cidrs`, `http_cidrs`, `https_cidrs`
- __LB__: `lb_enabled`, `lb_vip_subnet_id`, `assign_lb_floating_ip`, `external_network_name`
- __Remote-exec__: `remote_exec_*`
- __Ansible__: `ansible_*`

Refer to `variables.tf` for complete descriptions and defaults.

## Architecture overview

- __Swift__: Primary container for JSONL logs + `${name}-versions` container with `X-Versions-Location` for tamper-evidence.
- __Security Group__: Default deny; explicit ingress via supplied CIDRs; LB subnet-to-backend rule when LB is enabled.
- __Compute__: One or more Apache servers (`instance_count`), bootstrapped via cloud-init; attached Cinder volume mounted idempotently.
- __Load Balancer__: Octavia LB with listener/pool/monitor; optional Floating IP; members sourced from the instance first fixed IP.
- __Database__: Single PostgreSQL VM with dedicated SG allowing TCP 5432 only from the Apache SG (SG-to-SG rule). Data stored on a dedicated Cinder volume.

## Usage examples

Plan with essential vars:

```bash
terraform plan \
  -var-file=terraform.tfvars.example \
  -var "network_id=<TENANT_NET_UUID>" \
  -var "keypair_name=<KEYPAIR>" \
  -var "instance_count=2"
```

Apply with Ansible enabled:

```bash
terraform apply \
  -var "ansible_enabled=true" \
  -var "ansible_playbook_path=./playbooks/apache.yml" \
  -var "ansible_private_key_path=~/.ssh/thekey.pem" \
  -var "ansible_python_interpreter=/usr/bin/python3"
```

Generate module docs (requires terraform-docs):

```bash
make docs
cat README_MODULES.md
```

Run local linters and hooks:

```bash
make lint        # tf fmt/validate, tflint, tfsec (best effort)
make pre-commit  # runs configured pre-commit hooks
```

## Secrets management best practices

- __Prefer CI-managed secrets__: Use GitLab protected & masked variables for OpenStack creds, SSH keys, and Ansible vault passwords.
- __Optional HashiCorp Vault__: Fetch secrets at job runtime using GitLab OIDC (JWT) to avoid long-lived tokens and storing secrets in the repo.
- __No secrets in code__: Do not commit PEM keys or vault passwords; reference files created at job runtime (e.g., `~/.ssh/thekey.pem`).
- __Least privilege__: Create a dedicated CI user/role in OpenStack with only required permissions.

GitLab CI example (see `gitlab/pipeline.yml`):
- `vault_fetch_secrets` uses Vault OIDC to retrieve `kv/ansible/ssh:private_key` and writes it to `.secrets/ssh/thekey.pem` (artifact scoped for 1h).
- Subsequent jobs can use `~/.ssh/thekey.pem` or `${CI_PROJECT_DIR}/.secrets/ssh/thekey.pem` for `ansible-playbook`.

## CI/CD quality gates (overview)

- __Lint__: flake8 for Python style; bandit for Python security.
- __Test__: pytest (allowed to pass even if no tests yet), ansible-lint if `playbooks/` exists, Terraform fmt/validate, tfsec & tflint (best-effort).
- __Envs__: `dev` -> `preprod` -> `prod` (manual) stages for the SOC ownership script.

Additional scanners:
- __Gitleaks__: secret scanning over repo contents.
- __Checkov__: Terraform policy-as-code checks in addition to tfsec/tflint.

These gates provide code quality hygiene while keeping local onboarding simple.

### Secrets management: practical recipes

- __What not to do__
  - Do not put secrets (SSH keys, DB passwords) in `terraform.tfvars`, state, or repo.

- __GitLab protected variables (quick start)__
  - Define variables in your project/group settings:
    - `OS_CLOUD`/`OS_USERNAME`/... (or use `clouds.yaml`); already covered in CI.
    - `ANSIBLE_SSH_PRIVATE_KEY` (PEM) if not using Vault.
    - `DB_PASSWORD` for the application database.
  - In your local shell before `terraform apply` with Ansible enabled, export:
    ```bash
    export DB_PASSWORD="<value from GitLab>"
    ```
  - Update your Ansible playbook to reference `db_password` via extra vars or env:
    ```yaml
    - name: Configure app
      vars:
        db_password: "{{ lookup('env', 'DB_PASSWORD') }}"
      template:
        src: app.conf.j2
        dest: /etc/app/app.conf
    ```

- __Vault with GitLab OIDC (preferred in enterprise)__
  - Store `kv/db/app` with key `password` in Vault.
  - Extend the existing `vault_fetch_secrets` job to also fetch DB password and expose it as an artifact or masked variable:
    ```yaml
    vault_fetch_secrets:
      stage: secrets
      image: hashicorp/vault:1.15
      script:
        - vault login -method=jwt role="$VAULT_ROLE" jwt="$CI_JOB_JWT_V2"
        - mkdir -p .secrets/db
        - vault kv get -field=password kv/db/app > .secrets/db/password
      artifacts:
        paths: [ .secrets/db/password ]
        expire_in: 1h
        when: always
    ```
  - In your Ansible job or local run, export `DB_PASSWORD` from the artifact before running playbooks:
    ```bash
    export DB_PASSWORD="$(cat .secrets/db/password)"
    ```

- __Ansible Vault (optional)__
  - Encrypt an inventory/group_vars file that contains `db_password`:
    ```bash
    ansible-vault create group_vars/all/vault.yml  # add db_password: "..."
    ```
  - In CI, set `ANSIBLE_VAULT_PASSWORD` (protected/masked) and use:
    ```bash
    echo "$ANSIBLE_VAULT_PASSWORD" > .secrets/vault.pass
    ansible-playbook --vault-password-file .secrets/vault.pass ...
    ```

- __Local developer ergonomics__
  - Use `direnv` or a `.env` file ignored by git to export `DB_PASSWORD` for local runs.
  - Ensure `.gitignore` contains patterns for `.secrets/`, `*.pem`, `vault.pass`, etc. (already present).

- __How Terraform and Ansible tie together here__
  - Terraform never stores `db_password`.
  - Terraform passes non-sensitive DB connection vars (`db_host`, `db_port`, `db_name`, `db_user`).
  - Your Ansible playbook reads `DB_PASSWORD` at runtime and templates the app config.
