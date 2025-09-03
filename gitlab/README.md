# GitLab CI for Python DevOps SOC

This folder contains a GitLab CI pipeline tailored to Python-based SOC/DevOps tasks.
It leverages the Python utilities in this repo to emit SOC audit events and perform an ownership audit.

## How to use

1) At your repo root, create a minimal `.gitlab-ci.yml`:

```yaml
include:
  - local: 'gitlab/pipeline.yml'
```

2) Optionally set CI/CD variables in GitLab UI:
- `SOC_AUDIT_LOG`: custom path for JSONL audit log (default: `soc_audit_log.jsonl`)
- `OWNERSHIP_OWNER`: target owner for the ownership audit (default falls back to `ci`)
- `OWNERSHIP_GROUP`: optional target group

## What the pipeline does

- `audit_event`: emits a test SOC audit event using `yt_neuralnine/main_script_argument_soc.py` and stores the JSONL as an artifact.
- `ownership_dry_run`: runs `use_cases_soc/main_ownership_restore_soc.py` in dry-run mode against the repo path for safe auditing.
- `async_emit`: runs the async emitter demo to showcase concurrent JSONL writes.
- `compile_check`: compiles Python sources to bytecode for a quick sanity check without extra deps.

A manual `ownership_apply` job is provided for completeness, but is disabled by default because
changing OS ownership is typically not possible nor advisable on shared runners.
