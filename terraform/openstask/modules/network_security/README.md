# Module: network_security

Creates a restrictive Security Group and optional rules for SSH/HTTP/HTTPS. Optionally adds an ingress rule that allows only the Octavia LB subnet to reach the backend port. Includes optional Neutron FWaaS v2 rule/policy/group (if supported by cloud).
