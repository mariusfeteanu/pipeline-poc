# Event-Driven Enterprise RAG Platform (Merged with Streaming RAG)

## High-Level Description
Build an **event-driven enterprise RAG platform** where documents and structured data (Snowflake) are ingested and **streamed via Kafka**, **indexed** into a vector database using **Dagster** asset jobs, and **served** through a FastAPI gateway that performs retrieval → rerank → LLM generation with **observability, evaluation, and governance** (including “right-to-be-forgotten”). It’s designed to feel like a real corporate system: batch + streaming, infra-as-code, SLAs, dashboards, CI/CD, and clear security boundaries.

---

## Detailed Description
1. **Ingest & Normalize**
   - Batch loaders pull PDFs/HTML from S3/MinIO and selected tables from Snowflake.
   - Incremental changes (new/updated docs, CDC from tables) are emitted as **Kafka** events.

2. **Chunk, Embed, Index (Asset-aware)**
   - **Dagster** materializes assets: parse → chunk → embed → **upsert** into a vector DB (idempotent; versioned).
   - Exactly-once semantics via message keys/checkpoints; support backfills.

3. **Serve Answers with Citations**
   - **FastAPI** service: retrieve (vector search) → optional **rerank** → compose context → call LLM → return answer + sources.
   - Response caching (Redis) and rate limiting; per-request **OpenTelemetry** traces and **Prometheus** metrics.

4. **LLMOps & Evaluation**
   - Nightly eval job (Dagster) runs a labeled test set for faithfulness/groundedness, latency, and cost.
   - **Grafana** dashboards (+ Langfuse/Phoenix/Arize optional) for SLOs (e.g., p95), eval scores, tokens/£.

5. **Governance & Deletion**
   - API to perform RTBF: deletes raw docs, chunks, embeddings, and invalidates caches; emits audit logs.

6. **Security & IaC**
   - OIDC auth on the gateway; scoped secrets; least-privileged roles.
   - **Terraform** to provision cloud resources; **GitHub Actions** for CI/CD.

> **Stretch:** add **MCP** (Model Context Protocol) adapters so MCP-aware clients can call your platform tools safely:
> - `mcp-docstore` (semantic search over your vector DB).
> - `mcp-governance` (deletion/audit operations).

---

## Components & Software Options

| Component | Role | Baseline Choice (fits your stack) | Alternatives |
|---|---|---|---|
| Object storage | Raw docs & artifacts | **S3 / MinIO** | GCS, Azure Blob |
| Warehouse | Structured data source | **Snowflake** | BigQuery, Redshift |
| Change/events | Stream updates | **Kafka** (MSK/Confluent/Redpanda) | Debezium CDC, Pulsar |
| Orchestration | Asset pipelines, backfills | **Dagster** | Airflow (+ OpenLineage) |
| Parsing/chunking | Convert PDFs/HTML → chunks | **Unstructured.io + custom** | Apache Tika, trafilatura |
| Embeddings | Vectorization | **OpenAI / bge** (local) | Cohere, Voyage, Jina |
| Vector DB | Store & search vectors | **Weaviate** or **Qdrant** | Pinecone, Milvus |
| Reranking | Improve retrieval | **Cohere Rerank** / **bge-rerank** | Jina, Voyage |
| RAG framework | Retrieval pipeline & tracing | **LlamaIndex** or **LangChain** | Haystack |
| LLM serving | Generate answers | **Hosted** (OpenAI/Anthropic) | **Local** (vLLM + Llama 3.x), Bedrock |
| API gateway | Serve queries/auth | **FastAPI** | Flask, gRPC |
| Cache | Response/context cache | **Redis** | Memcached |
| Observability | Metrics/traces | **Prometheus + Grafana + OTel** | Langfuse, Phoenix, Arize |
| Eval harness | Quality/cost/latency checks | **RAGAS / DeepEval / custom** | Vectara Open RAG Eval, Promptfoo |
| Secrets/config | Secure credentials | **AWS Secrets Manager** | Vault, GCP Secret Manager |
| CI/CD | Build/test/deploy | **GitHub Actions** | GitLab CI, CircleCI |
| IaC | Provision infra | **Terraform** | Pulumi, CDK |
| Access control | Users & scopes | **OIDC (Auth0/Cognito)** | Keycloak |
| Governance | RTBF & audit | **Custom svc + logs** | OpenLineage (+ custom) |
| (Stretch) MCP | Standard tool access | **Custom MCP servers** | Existing servers (files, fetch, GitHub) |

---

## Milestones (1–7 days each)

**M1 (2–3 days) – Repo & Infra Skeleton**  
- Terraform scaffold (networking, buckets, Kafka cluster placeholder), GitHub Actions, base Dockerfiles.  
- **Deliverables:** repo bootstrapped; CI builds; `terraform plan` clean.

**M2 (2–4 days) – Ingestion & Eventing**  
- Batch doc loader (S3/MinIO), Snowflake table sampler; emit **Kafka** events with stable schemas (Schema Registry).  
- **Deliverables:** sample events produced; topics + schemas documented.

**M3 (2–4 days) – Dagster Asset Pipeline (Chunk → Embed → Index)**  
- Asset jobs: parsing, chunking, embedding, vector upsert (idempotent, versioned).  
- **Deliverables:** first corpus indexed; backfill run reproducible.

**M4 (1–3 days) – Retrieval API (Baseline RAG)**  
- **FastAPI** endpoint: retrieve → generate; citations; simple Redis cache.  
- **Deliverables:** E2E smoke tests; baseline p95 latency measured.

**M5 (2–3 days) – Reranking & Quality Uplift**  
- Add reranker; tune `top_k`/chunk size; measure delta on initial test set.  
- **Deliverables:** short eval report showing quality gains vs baseline.

**M6 (2–4 days) – Observability (Metrics & Traces)**  
- OTel traces across retrieve→rerank→LLM; Prom metrics (QPS, p50/p95, errors, tokens/£); Grafana dashboards + alerts.  
- **Deliverables:** live dashboards; alert thresholds.

**M7 (2–4 days) – Evaluation Harness & Nightly Job**  
- Labeled Q&A set; RAGAS/DeepEval pipeline; pass/fail gates; trend charts.  
- **Deliverables:** nightly run artifact; CI badge; eval trends visible.

**M8 (2–4 days) – Streaming Re-index & Backfills**  
- Consume Kafka change events → incremental re-chunk/re-embed with checkpoints (exactly-once).  
- **Deliverables:** update a doc/row and see index reflect within SLA.

**M9 (2–3 days) – Governance: RTBF & Audit**  
- Delete API removes raw + derived artifacts (chunks, vectors), clears caches; emits audit log entries.  
- **Deliverables:** RTBF test passes within SLA; audit trail recorded.

**M10 (1–2 days) – Security Hardening**  
- OIDC on gateway; role scopes; secrets from manager; rate limits and WAF basics.  
- **Deliverables:** end-to-end auth flow; least-privileged policies.

**M11 (1–3 days) – Cost & Performance Tuning**  
- Token/cost meters; caching strategies; model/provider swaps; choose default “cost profile.”  
- **Deliverables:** table of p50/p95, tokens/req, £/1k queries; tuning notes.

**M12 (2–3 days) – Release & Docs**  
- “Run it yourself” script; architecture diagram; dashboards screenshots; screen-recorded demo; résumé bullets.  
- **Deliverables:** tagged `v1.0`, complete README, demo link.

**(Stretch) M13 (1–3 days) – MCP Adapters**  
- `mcp-docstore` (semantic search) + `mcp-governance` (deletions/audit) with scopes/consent; calls show in metrics/audit.  
- **Deliverables:** MCP clients can call your tools; observability wired.

---
