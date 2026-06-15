# 🧠 Agentic AI Sales Intelligence Platform

A production-quality multi-agent RAG pipeline that automates B2B company research and generates actionable sales intelligence reports.

## 🏗️ Architecture

```
Input (Company + Country)
    ↓
🔍 Research Agent  (LangGraph Node 1)
    ├─ Web Search      → Tavily (primary) / DuckDuckGo (fallback)
    ├─ News            → NewsAPI (primary) / Tavily News (fallback)
    ├─ Wikipedia       → Disambiguated company lookup
    ├─ Financial       → yfinance (public companies)
    └─ CRM             → Mock CRM (replace with Salesforce/HubSpot)
    ↓
📦 RAG Pipeline
    ├─ RecursiveCharacterTextSplitter  (chunk_size=512, overlap=64)
    ├─ SentenceTransformers (all-MiniLM-L6-v2)  → embeddings
    ├─ FAISS IndexFlatIP  (cosine similarity via L2-norm + inner product)
    └─ CrossEncoder (ms-marco-MiniLM-L-6-v2)  → reranking
    ↓
📊 Analysis & Sales Agent  (LangGraph Node 2)
    ├─ Second RAG pass (sales-signal focused retrieval)
    └─ llama-3.3-70b-versatile via Groq
    ↓
📄 Structured Report → PDF + Word export
```

## 📁 Project Structure

```
sales_intelligence/
├── app.py                    # Streamlit entry point
├── requirements.txt
├── .env.example              # Template — copy to .env
├── design_notes.md           # Section 5: design-only items
│
├── config/
│   └── settings.py           # Centralised env-var config
│
├── agents/
│   ├── llm_client.py         # Groq LLM wrapper (cached)
│   ├── research_agent.py     # LangGraph Node 1
│   ├── analysis_agent.py     # LangGraph Node 2
│   └── pipeline.py           # LangGraph graph assembly & execution
│
├── rag/
│   ├── chunker.py            # RecursiveCharacterTextSplitter
│   ├── vector_store.py       # FAISS cosine similarity store
│   └── reranker.py           # Cross-encoder reranking
│
├── tools/
│   ├── web_search.py         # Tavily + DuckDuckGo + prompt-injection sanitiser
│   ├── news_search.py        # NewsAPI + Tavily News
│   ├── wikipedia_search.py   # Wikipedia with disambiguation
│   ├── financial_data.py     # yfinance
│   └── crm_mock.py           # Mock CRM (swap for real CRM API)
│
├── exports/
│   ├── pdf_exporter.py       # ReportLab PDF
│   └── docx_exporter.py      # python-docx Word
│
└── ui/
    └── components.py         # Reusable Streamlit components
```


### 1. Clone & Install

```bash
git clone <repo-url>
cd sales_intelligence
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and fill in your API keys
```

**Required keys:**
| Key | Where to get it | Required? |
|-----|----------------|-----------|
| `GROQ_API_KEY` | https://console.groq.com | ✅ Yes |
| `TAVILY_API_KEY` | https://tavily.com | ✅ Recommended |
| `NEWS_API_KEY` | https://newsapi.org | Optional |
| `SERP_API_KEY` | https://serpapi.com | Optional |

> The app works with only `GROQ_API_KEY` + `TAVILY_API_KEY`.
> Without `NEWS_API_KEY`, news falls back to Tavily news search.

### 3. Run the App

```bash
streamlit run app.py
```

Open http://localhost:8501 in your browser.

## 🖥️ Usage

1. Enter a **company name** (e.g., "Infosys", "Zoho", "Apple") in the sidebar
2. Select the **country** to disambiguate same-name companies
3. Click **Generate Intelligence Report**
4. Wait ~30–60 seconds for the pipeline to complete
5. Browse the tabbed report: Overview, Industry, News, Opportunities, Sales Strategy
6. Download the **PDF** or **Word** export

## 🔑 Key Technical Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| LLM | llama-3.3-70b-versatile (Groq) | Fast inference, open-weight, per spec |
| Orchestration | LangGraph | Native state machine; conditional edges for fault tolerance |
| Chunking | RecursiveCharacterTextSplitter | Respects sentence/paragraph boundaries |
| Vector DB | FAISS IndexFlatIP | Exact cosine search; no server required |
| Reranking | ms-marco-MiniLM-L-6-v2 | Strong MRR on MS MARCO; 23M params (fast) |
| Embedding | all-MiniLM-L6-v2 | Good quality/speed tradeoff; 80M params |

## ⚠️ Constraints & Notes

- **LinkedIn**: Not scraped (ToS violation). Acknowledged per Section 6.
- **Private companies**: Financial data degrades gracefully if no yfinance ticker found.
- **Rate limits**: Tenacity retry/backoff applied to all external API calls.
- **Prompt injection**: All web content sanitised via regex + LLM system prompt guardrails.
- **API keys**: Never committed. Use `.env` (git-ignored).

## 📝 Design Notes

See `design_notes.md` for the Section 5 design-only topics:
- Scalability (concurrent requests, async tools, caching)
- Security (key management, PII, prompt injection)
- Observability (tracing, logging, alerting)
- Cost optimisation (model routing, token budgeting)
- CRM integration approach
