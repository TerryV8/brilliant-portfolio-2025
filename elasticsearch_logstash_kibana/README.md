# ELK (Elastic Stack) Integration

Purpose:
- Centralize SOC audit logs and IR reports in Elasticsearch.
- Provide Kibana searches/dashboards and simple KQL detections.

Proposed contents:
- filebeat/
  - filebeat.yml.j2 (template to ship soc_audit.log and reports)
- kibana/
  - ir_overview.ndjson (saved search + dashboard)
- playbooks/
  - elk_setup_beats.yml (install/configure Filebeat)
- README.md (this file)

Next steps:
1) Add Filebeat template to ship:
   - $SOC_AUDIT_LOG
   - artifacts/phishing/*.json
   - artifacts/endpoint/*.json
2) Create Kibana NDJSON with a simple IR dashboard.
3) Optional CI job to bulk-index audit lines.

Provide your ES endpoint (ES_URL) and API key (ES_API_KEY) to proceed.
