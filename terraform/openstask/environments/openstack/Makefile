SHELL := /bin/bash
TF := terraform
ENV ?= openstack
VARS ?= terraform.tfvars
TF_DIR := .

.PHONY: fmt init validate plan apply destroy docs lint pre-commit

fmt:
	$(TF) fmt -recursive

init:
	cd $(TF_DIR) && $(TF) init

validate: init
	cd $(TF_DIR) && $(TF) validate

plan: init
	cd $(TF_DIR) && $(TF) plan -var-file=$(VARS)

apply: init
	cd $(TF_DIR) && $(TF) apply -auto-approve -var-file=$(VARS)

destroy: init
	cd $(TF_DIR) && $(TF) destroy -auto-approve -var-file=$(VARS)

# Generate docs with terraform-docs if installed
# brew install terraform-docs
# make docs
.docs-check:
	@command -v terraform-docs >/dev/null 2>&1 || { echo "terraform-docs not installed"; exit 0; }

docs: .docs-check
	terraform-docs markdown table $(TF_DIR) > README_MODULES.md || true

# Run repo linters similar to CI (best-effort)
lint:
	terraform fmt -recursive -check || true
	cd $(TF_DIR) && terraform validate || true
	command -v tflint >/dev/null 2>&1 && (cd $(TF_DIR) && tflint --init && tflint) || echo "tflint not installed"
	command -v tfsec >/dev/null 2>&1 && tfsec ../../ || echo "tfsec not installed"

# Convenience wrapper for pre-commit
pre-commit:
	command -v pre-commit >/dev/null 2>&1 || { echo "pre-commit not installed"; exit 1; }
	pre-commit run -a || true
