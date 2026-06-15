# Design Notes — Agentic AI Sales Intelligence Platform

## 1. Scalability

**Serving hundreds of concurrent research requests:**

- **Horizontal scaling via Kubernetes**: Each LangGraph pipeline run is stateless (all state passed through `AgentState`). Deploy as Docker containers behind a load balancer; auto-scale based on CPU/memory.
- **Async tool calls**: The current implementation calls data sources sequentially. In production, use `asyncio.gather()` to parallelise Tavily, NewsAPI, Wikipedia, and yfinance calls, reducing per-request latency by ~60–70%.
- **Task queuing**: Use Celery + Redis to dequeue pipeline jobs and return results via SSE/WebSocket to the Streamlit frontend. This decouples the UI from the blocking pipeline.
- **FAISS sharing**: For popular companies, the FAISS index can be pre-built and cached in Redis or object storage (S3). Subsequent requests for the same company skip the embedding step entirely.
- **Model serving**: Groq already provides hosted inference. For further cost control at scale, route shorter tasks (extraction, classification) to `llama-3.1-8b-instant` and reserve `llama-3.3-70b-versatile` for synthesis.

---

## 2. Security

- **API key management**: Store all keys in a secrets manager (AWS Secrets Manager, HashiCorp Vault). Inject at runtime via environment variables — never in source code or Docker images. Rotate keys on a schedule.
- **PII handling**: Sales data may include contact names and email addresses. Apply field-level encryption for PII fields in the CRM integration. Implement data retention policies; purge cached results after the configured TTL.
- **Prompt injection from scraped web content**: All scraped text is sanitised (`tools/web_search.py::sanitise_text`) before being placed in LLM context. The LLM system prompts explicitly instruct the model to treat retrieved chunks as untrusted external data and ignore any embedded instructions. A secondary content filter (moderation endpoint or keyword blocklist) can be applied before passing to the LLM.
- **Rate limiting**: Apply per-user and per-organisation rate limits at the API gateway layer to prevent abuse and runaway API costs.

---

## 3. Observability

- **Distributed tracing**: Instrument the LangGraph pipeline with OpenTelemetry spans. Each agent node becomes a traced operation with attributes (company, country, token count, latency). Export to Jaeger or Datadog APM.
- **LangSmith integration**: LangChain/LangGraph natively supports LangSmith for full multi-agent run tracing — inputs, outputs, intermediate steps, and token usage per node.
- **Structured logging**: Replace the current loguru setup with a JSON log emitter. Ship to a log aggregator (Elastic, Loki) and create dashboards for: pipeline success rate, p50/p95 latency, confidence distribution, and tool failure rates.
- **Alerting**: Alert on: pipeline error rate > 5%, LLM latency > 30s, cache miss rate > 80% (signals heavy uncached usage), and confidence level "low" > 30% of runs (signals data quality issues).

---

## 4. Cost Optimisation

- **Research result caching**: The current TTL cache (`utils/cache.py`) stores per-company, per-source results for 24 hours. This directly addresses the "duplicated effort" problem. A shared Redis cache across all users means the 100th sales rep researching the same company gets instant results.
- **Model routing**: Use `llama-3.1-8b-instant` for the extraction/chunking reasoning tasks and reserve `llama-3.3-70b-versatile` for the final synthesis step. Estimated cost reduction: 60–70%.
- **Token budgeting**: Measure token usage per pipeline run using `tiktoken`. Set hard limits per section (e.g., max 2,000 tokens for context, 1,500 for output). Log and alert on runs exceeding budget.
- **Deduplication before embedding**: Deduplicate chunks by content hash before indexing to reduce FAISS index size and embedding API calls.
- **Batch embedding**: When processing multiple companies in bulk, use the sentence-transformers batch encode API (already supported in the current implementation via `show_progress_bar=False`).

---

## 5. Internal CRM Integration

**Assumption**: CRM data exists in Salesforce, HubSpot, or Dynamics 365.

**Mock implementation**: `tools/crm_mock.py` provides a static sample dataset with realistic records (account status, deal stage, last contact, estimated deal size, notes).

**Production integration approach**:
1. **Auth**: OAuth 2.0 service account for the CRM API; credentials stored in secrets manager.
2. **Lookup**: On pipeline start, query the CRM for the company by name + country with fuzzy matching (Jaro-Winkler similarity).
3. **Data returned**: Account status, deal stage, contact details, last interaction, notes, and associated opportunities.
4. **Write-back**: After generating the report, optionally create a CRM activity log entry ("AI research report generated — [date]") on the account record.
5. **Privacy**: CRM data is never stored in the vector index; it is injected directly into the LLM prompt as structured context with a clear provenance label.

---

## Known Limitations & What Would Be Improved With More Time

1. **Parallel tool execution**: Implement `asyncio.gather()` for concurrent API calls (currently sequential).
2. **LLM evaluation**: Add a RAGAS-based evaluation pipeline to measure faithfulness, answer relevance, and context precision on a held-out test set of company research queries.
3. **LinkedIn constraint**: LinkedIn ToS prohibits scraping. In production, use the LinkedIn Marketing API (requires partnership) or a licensed data provider (ZoomInfo, Apollo.io) for firmographic and contact data.
4. **Conflicting source resolution**: When sources conflict (e.g., different revenue figures), the current system notes the conflict in the prompt. A production system would use a source reliability ranking and date-based recency weighting.
5. **Streaming output**: Use Streamlit's `st.write_stream()` with Groq's streaming API to display the report as it is generated, rather than waiting for the full pipeline to complete.
6. **Multi-language support**: Add language detection and translation for companies with non-English web presence.
