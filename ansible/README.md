# Ansible: Python DevOps SOC

This Ansible content demonstrates SOC-oriented automation using your Python utilities.

- Role `soc_audit`: ensures JSONL audit log and emits a test audit event via your Python CLI.
- Role `ownership_restore`: runs your ownership restore tool in dry-run or apply mode.

## Quick start (localhost)

- Inventory: `ansible/inventory.ini`
- Playbook: `ansible/playbooks/soc_ops.yml`

Run dry-run ownership audit and emit a test audit event:

```
ansible-playbook -i ansible/inventory.ini ansible/playbooks/soc_ops.yml \
  -e "soc_audit_log=./soc_audit_log.jsonl" \
  -e "ownership_owner=$(whoami)" \
  -e "ownership_root={{ playbook_dir }}/.." \
  -e "ownership_apply=false"
```

Apply ownership changes (requires privileges):

```
sudo ansible-playbook -i ansible/inventory.ini ansible/playbooks/soc_ops.yml \
  -e "ownership_owner=$(whoami)" \
  -e "ownership_root={{ playbook_dir }}/.." \
  -e "ownership_apply=true"
```

Variables:
- `soc_audit_log`: Path to JSONL audit log (default: `soc_audit_log.jsonl`)
- `ownership_owner`: Target owner username
- `ownership_group`: Optional group
- `ownership_root`: Path to audit/fix (default: repo root)
- `ownership_apply`: `true` to change, `false` for dry-run
