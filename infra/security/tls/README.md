# TLS / mTLS Hardening (Phase 10)

This folder provides implementation-ready guidance for **TLS everywhere** and **mTLS for internal services**.

## TLS everywhere

- Public-facing API (`api`): run behind a TLS-terminating gateway (preferred) or enable Uvicorn TLS directly.
- Internal services (`ingestion`, `processing`): require TLS for all HTTP/GRPC connections.

## mTLS (internal)

Recommended pattern (auditability > convenience):
- Use a service mesh (Istio/Linkerd) or Envoy sidecars to enforce mTLS at the network layer.
- Rotate certs via a private CA (e.g., `step-ca`) or enterprise PKI.

## No plaintext secrets

- Use env vars injected by the runtime (Kubernetes secrets/Hashicorp Vault/Cloud secret manager).
- Never commit `.env` values containing real secrets.

## At-rest encryption

Database:
- Prefer full-disk encryption for DB volumes (cloud KMS / LUKS) + restricted access.
- Optional: column-level encryption for any sensitive fields using application-layer envelope encryption.

Object storage (S3/MinIO):
- Enable server-side encryption (SSE) and enforce via bucket policies where supported.
- Support key rotation via KMS-managed keys.




