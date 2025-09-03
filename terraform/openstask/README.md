# Terraform Best Practices and Tips

This repository contains a modular OpenStack SOC automation. Use these practices to keep the stack robust, secure, and maintainable.

## Structure overview

- `modules/`: Reusable modules (`compute_apache/`, `network_security/`, `storage_swift/`, etc.)
- `environments/openstack/`: Environment wiring, variables, providers, and docs
- `gitlab/`: CI pipeline (`pipeline.yml`) with quality gates and optional Vault integration

## Versions and providers

- Pin Terraform and providers in `versions.tf` to ensure reproducible builds.
- Run `terraform -version` in CI and locally to verify consistency.

## State and workspaces

- Use remote backends (S3+Locking, GCS, GitLab-managed, etc.) in real projects for collaboration and locking.
- Use `terraform workspace` to isolate environments (e.g., `dev`, `preprod`, `prod`).

```bash
terraform workspace new dev || true
terraform workspace select dev
```

> Note: Backend configuration is left to the deployer; this repo initializes with `-backend=false` in validation jobs to avoid environment coupling.

## Variables and tfvars

- Keep sensitive variables out of VCS. Use CI variables or Vault to inject secrets.
- Provide a `terraform.tfvars` or `-var-file` per workspace.

## Secrets management

- High-level architecture (Mermaid):

```mermaid
flowchart TB
  subgraph Modules
    A[storage_swift]\nSwift containers
    B[network_security]\nSG + optional FWaaS
    C[compute_apache]\nApache + volume
    D[load_balancer]\nOctavia listener/pool
  end

  subgraph Environment (openstack)
    E[variables.tf]\ninputs + validation
    F[main.tf]\nwiring + Ansible/remote-exec
    G[outputs.tf]
  end

  E --> F --> G
  F --> A
  F --> B
  F --> C
  F --> D
  D -->|VIP subnet rule| B
  C -->|members| D
```

- Prefer GitLab protected/masked variables for quick start.
- For enterprise setups, use HashiCorp Vault with GitLab OIDC to fetch secrets at runtime (see `gitlab/pipeline.yml` `vault_fetch_secrets`).
- Never commit SSH private keys or vault passwords.

## Networking tips (OpenStack)

- Use Neutron Routers (not AWS-style route tables). Ensure:
  - Router has external gateway to your public network.
  - Tenant subnet(s) are attached as router interfaces.
- For custom routes, use the Neutron "extra routes" extension if available.

## Security groups and CIDRs

- Default-deny SG; allow ingress explicitly.
- Use list-based variables: `allow_ssh_cidrs`, `http_cidrs`, `https_cidrs` to restrict access by source networks.
- When LB is enabled, keep backend `http_cidrs = []` to force traffic via the LB.

## Load balancer

- Octavia LB with listener, pool, and monitor.
- Optionally associate a floating IP to the VIP for internet ingress.
- Backend members are sourced from instance fixed IPs.

## Scaling compute instances

- Scale via `instance_count`.
- Recommended: suffix instance names with index for clarity (e.g., `web-server-apache-0`, `-1`).
- Outputs expose lists of instance IDs and IPs for downstream wiring.

## Provisioning and Ansible

- Primary provisioning is via cloud-init for idempotence.
- Optional `remote-exec` exists for smoke checks.
- Optional post-provision Ansible: `ansible_enabled = true` runs `ansible-playbook` per instance after a configurable sleep. See `environments/openstack/README.md` for exact commands.

## Validation and linting

- Run locally:

```bash
terraform fmt -recursive
cd environments/openstack
terraform init -backend=false
terraform validate
```

- CI also runs: flake8, bandit, ansible-lint (if playbooks present), `tfsec`, and `tflint`.

## Tagging and naming

- Use consistent prefixes and tags (if supported) to aid cost allocation and cleanup.
- Keep resource names descriptive (service-purpose-scope), e.g., `web-server-apache`.

## Troubleshooting

- `openstack` CLI: verify network, router, and floating IP connectivity.
- SG/CIDR mismatches are common—confirm your source IP and LB subnet rules.
- Ansible timeouts: increase `ansible_sleep_seconds` or ensure SSH reachability (floating IPs, NAT, VPN).

## Cleanup

```bash
env TF_LOG="" terraform destroy -auto-approve
```

> Note: Swift containers with versioning may require elevated privileges to delete if retention policies are in place.
