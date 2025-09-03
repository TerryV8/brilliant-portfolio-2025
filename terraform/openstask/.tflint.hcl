# TFLint configuration
# Docs: https://github.com/terraform-linters/tflint

plugin "terraform" {
  enabled = true
}

config {
  module = true
  force  = false
}

# Example rules configuration. Tune as needed.
rule "terraform_unused_declarations" { enabled = true }
rule "terraform_comment_syntax"      { enabled = true }
rule "terraform_deprecated_interpolation" { enabled = true }

# OpenStack-specific rules can be added via custom plugins if available.
