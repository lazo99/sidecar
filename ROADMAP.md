# Roadmap

## v0.1 (MVP) — Current

✅ JWT authentication  
✅ Bitwarden Secrets Manager integration  
✅ Basic API proxy (Claude, OpenAI, GCP)  
✅ Audit logging  
✅ FastAPI server  
✅ Docker support  
✅ Cloud Run deployment  

## v0.2 (Beta)

- [ ] Admin-only authorization checks (separate admin token)
- [ ] Key rotation API with timestamp tracking
- [ ] Multi-tenancy support (key access control per user)
- [ ] Request/response filtering (mask sensitive data)
- [ ] Rate limiting per API/user
- [ ] Metrics endpoint (request counts, latencies)
- [ ] Improved error handling & retry logic
- [ ] Database for audit log persistence (vs JSONL)

## v0.3 (Production)

- [ ] MCP server mode (alongside HTTP)
- [ ] Web dashboard for key management (read-only audit view)
- [ ] Backup/restore procedures for audit logs
- [ ] Key expiry notifications
- [ ] Integration tests with real APIs
- [ ] Performance benchmarks
- [ ] Security audit & pentest results

## v1.0 (Stable)

- [ ] Kubernetes deployment (Helm chart)
- [ ] Service mesh integration (Istio)
- [ ] Certificate management (mTLS)
- [ ] Multi-region active-active setup
- [ ] Advanced analytics (usage trends, cost)
- [ ] Webhook notifications (key rotation alerts)
- [ ] API versioning (v1, v2, etc.)

## Future

- Cloud marketplace integration (AWS Secrets Manager, HashiCorp Vault)
- CLI tool for local development (`sidecar-cli`)
- GitHub Actions integration
- Terraform modules for GCP/AWS deployments
