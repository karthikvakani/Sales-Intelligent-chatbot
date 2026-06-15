"""
app.py
Main Streamlit application — Agentic AI Sales Intelligence Platform.

Run with:
    streamlit run app.py
"""

import sys
import os
import time
from pathlib import Path
from datetime import datetime

import streamlit as st

# ── Path setup (so all modules resolve correctly) ────────────────────────────
sys.path.insert(0, str(Path(__file__).parent))

# ── Streamlit page config (MUST be first st call) ────────────────────────────
st.set_page_config(
    page_title="Sales Intelligence Platform",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Global */
    .main { background-color: #f8fafc; }
    .block-container { padding-top: 1rem; max-width: 1200px; }
    
    /* Sidebar */
    [data-testid="stSidebar"] { background: #1a2b4a; }
    [data-testid="stSidebar"] .stMarkdown, 
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] .stSelectbox label { color: #e2e8f0 !important; }
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 { color: white !important; }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #2563eb, #1d4ed8);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        padding: 0.5rem 1.5rem;
        width: 100%;
        transition: all 0.2s;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #1d4ed8, #1e40af);
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(37,99,235,0.3);
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        border-radius: 6px 6px 0 0;
        font-weight: 500;
        color: #4b5563;
    }
    .stTabs [aria-selected="true"] {
        background-color: #eff6ff;
        color: #2563eb;
        font-weight: 600;
    }
    
    /* Expanders */
    .streamlit-expanderHeader { font-weight: 600; color: #1a2b4a; }
    
    /* Progress */
    .stProgress .st-bo { background-color: #2563eb; }
    
    /* Input fields */
    .stTextInput input, .stSelectbox select {
        border-radius: 8px;
        border-color: #d1d5db;
    }
    .stTextInput input:focus { border-color: #2563eb; box-shadow: 0 0 0 2px rgba(37,99,235,0.2); }
    
    /* Hide Streamlit branding */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ── Lazy imports (avoid slow startup) ────────────────────────────────────────
from ui.components import (
    render_header, render_confidence_badge, render_metric_row,
    render_section_card, render_sources_expander, render_pipeline_diagram,
    render_warnings_errors,
)
from config.settings import validate_keys
from utils.cache import clear_cache


# ── Session state initialisation ─────────────────────────────────────────────
def init_session():
    defaults = {
        "pipeline_result": None,
        "is_running": False,
        "run_history": [],
        "active_tab": 0,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session()


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🧠 Sales Intelligence")
    st.markdown("---")

    # ── API Key Status ────────────────────────────────────────────────────────
    st.markdown("### 🔑 API Key Status")
    key_status = validate_keys()
    key_icons = {
        "groq": ("LLaMA 3.3 (Groq)", "🤖"),
        "tavily": ("Tavily Search", "🔍"),
        "newsapi": ("News API", "📰"),
        "serpapi": ("SerpAPI", "🔎"),
    }
    for key, (label, icon) in key_icons.items():
        status = "✅" if key_status.get(key) else "❌"
        colour = "#86efac" if key_status.get(key) else "#fca5a5"
        st.markdown(
            f'<p style="color:{colour}; font-size:0.85rem; margin:2px 0">'
            f'{status} {icon} {label}</p>',
            unsafe_allow_html=True,
        )

    if not key_status.get("groq"):
        st.error("⚠️ GROQ_API_KEY is required. Add it to your .env file.")

    st.markdown("---")

    # ── Search Input ──────────────────────────────────────────────────────────
    st.markdown("### 🏢 Target Company")

    company_name = st.text_input(
        "Company Name",
        placeholder="e.g., Infosys, Zoho, Apple",
        help="Enter the full or common name of the company.",
    )

    country = st.selectbox(
        "Country",
        options=[
            "India", "United States", "United Kingdom", "Germany", "France",
            "Singapore", "Australia", "Canada", "Japan", "Brazil",
            "Netherlands", "Sweden", "Israel", "South Korea", "UAE",
            "Other",
        ],
        help="Country helps disambiguate companies with similar names.",
    )

    if country == "Other":
        country = st.text_input("Specify Country", placeholder="Enter country name")

    st.markdown("---")

    # ── Advanced Settings ─────────────────────────────────────────────────────
    with st.expander("⚙️ Advanced Settings", expanded=False):
        use_cache = st.checkbox("Use cached results (faster)", value=True)
        export_format = st.radio("Export Format", ["PDF", "Word (.docx)", "Both"])
        st.markdown("**RAG Settings**")
        top_k_display = st.slider("Chunks to retrieve", 5, 20, 10)
        rerank_k_display = st.slider("Chunks after rerank", 3, 10, 5)

        if st.button("🗑️ Clear Cache", use_container_width=True):
            n = clear_cache()
            st.success(f"Cleared {n} cached files")

    st.markdown("---")

    # ── Run Button ────────────────────────────────────────────────────────────
    run_disabled = (
        not company_name.strip()
        or not country
        or not key_status.get("groq")
        or st.session_state.is_running
    )

    if st.button(
        "🚀 Generate Intelligence Report",
        disabled=run_disabled,
        use_container_width=True,
    ):
        st.session_state.is_running = True
        st.session_state.pipeline_result = None
        st.rerun()

    st.markdown("---")

    # ── Run History ───────────────────────────────────────────────────────────
    if st.session_state.run_history:
        st.markdown("### 📜 Recent Searches")
        for entry in reversed(st.session_state.run_history[-5:]):
            st.markdown(
                f'<p style="color: #94a3b8; font-size:0.8rem; margin:2px 0">'
                f'• {entry["company"]} ({entry["country"]}) '
                f'<span style="color:#64748b">{entry["time"]}</span></p>',
                unsafe_allow_html=True,
            )

    # ── Architecture info ─────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 🏗️ Architecture")
    render_pipeline_diagram()


# ─────────────────────────────────────────────────────────────────────────────
# MAIN CONTENT
# ─────────────────────────────────────────────────────────────────────────────
render_header()

# ── Pipeline execution ────────────────────────────────────────────────────────
if st.session_state.is_running:
    st.markdown("---")
    progress_placeholder = st.empty()
    status_placeholder = st.empty()
    detail_placeholder = st.empty()

    with progress_placeholder.container():
        st.markdown(f"""
        <div style="background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 10px;
                    padding: 1.2rem 1.5rem; margin-bottom: 1rem;">
            <h3 style="color: #1e40af; margin: 0 0 0.5rem">
                ⚡ Running Multi-Agent Pipeline
            </h3>
            <p style="color: #3b82f6; margin: 0; font-size: 0.9rem">
                Company: <b>{company_name}</b> | Country: <b>{country}</b>
            </p>
        </div>
        """, unsafe_allow_html=True)

    progress_bar = st.progress(0, text="Initialising pipeline…")
    start_time = time.time()

    try:
        from agents.pipeline import run_pipeline

        def update_progress(pct: int, msg: str):
            progress_bar.progress(pct, text=msg)

        update_progress(5, "🔍 Research Agent: Fetching web data…")
        time.sleep(0.3)

        # Run the pipeline (blocking)
        result = run_pipeline(company_name.strip(), country.strip())

        elapsed = time.time() - start_time
        update_progress(100, f"✅ Complete in {elapsed:.1f}s")
        time.sleep(0.5)

        st.session_state.pipeline_result = result
        st.session_state.is_running = False

        # Add to history
        st.session_state.run_history.append({
            "company": company_name,
            "country": country,
            "time": datetime.now().strftime("%H:%M"),
            "confidence": result.get("confidence", "?"),
        })

        # ── Auto-export ───────────────────────────────────────────────────────
        report = result.get("report", {})
        if report and not result.get("errors"):
            try:
                from exports import export_pdf, export_docx
                export_paths = []
                if export_format in ("PDF", "Both"):
                    p = export_pdf(report, company_name, country)
                    export_paths.append(("PDF", p))
                if export_format in ("Word (.docx)", "Both"):
                    p = export_docx(report, company_name, country)
                    export_paths.append(("DOCX", p))
                result["_export_paths"] = export_paths
            except Exception as ex:
                result.setdefault("warnings", []).append(f"Export failed: {ex}")

        st.rerun()

    except Exception as exc:
        st.error(f"❌ Pipeline failed: {exc}")
        st.session_state.is_running = False
        import traceback
        with st.expander("Full traceback"):
            st.code(traceback.format_exc())


# ── Display results ────────────────────────────────────────────────────────────
elif st.session_state.pipeline_result:
    result = st.session_state.pipeline_result
    report = result.get("report", {})
    sections = report.get("sections", {})
    company = result.get("company_name", "")
    country_r = result.get("country", "")
    confidence = result.get("confidence", "unknown")
    errors = result.get("errors", [])
    warnings = result.get("warnings", [])

    # ── Stats row ─────────────────────────────────────────────────────────────
    web_count = len(result.get("web_results", []))
    news_count = len(result.get("news_results", []))
    chunk_count = len(result.get("retrieved_chunks", []))
    sources_count = len(report.get("sources", []))

    render_confidence_badge(confidence)

    render_metric_row([
        {"icon": "🌐", "value": str(web_count), "label": "Web Results", "colour": "#2563eb"},
        {"icon": "📰", "value": str(news_count), "label": "News Articles", "colour": "#0891b2"},
        {"icon": "🧩", "value": str(chunk_count), "label": "RAG Chunks", "colour": "#7c3aed"},
        {"icon": "📎", "value": str(sources_count), "label": "Sources Cited", "colour": "#059669"},
    ])

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Export download buttons ───────────────────────────────────────────────
    export_paths = result.get("_export_paths", [])
    if export_paths:
        st.markdown("### 📥 Download Report")
        dl_cols = st.columns(len(export_paths))
        for col, (fmt, path) in zip(dl_cols, export_paths):
            with col:
                if Path(path).exists():
                    with open(path, "rb") as f:
                        fname = Path(path).name
                        mime = "application/pdf" if fmt == "PDF" else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                        st.download_button(
                            label=f"⬇️ Download {fmt}",
                            data=f.read(),
                            file_name=fname,
                            mime=mime,
                            use_container_width=True,
                        )
        st.markdown("---")

    # ── Render warnings/errors ────────────────────────────────────────────────
    render_warnings_errors(warnings, errors)

    # ── Tabs for report sections ──────────────────────────────────────────────
    tab_labels = [
        "📋 Overview",
        "🏭 Industry",
        "📰 News",
        "💡 Opportunities",
        "🎯 Sales Strategy",
        "📊 Research Data",
        "🔍 Debug / RAG",
    ]
    tabs = st.tabs(tab_labels)

    # Tab 0: Overview
    with tabs[0]:
        st.markdown(f"## {company} — {country_r}")
        render_section_card(
            "Company Overview",
            sections.get("Company Overview", "Not available."),
            "🏢",
        )
        render_section_card(
            "Key Contacts Guidance",
            sections.get("Key Contacts Guidance", "Not available."),
            "👥",
        )
        render_section_card(
            "Competitive Context",
            sections.get("Competitive Context", "Not available."),
            "⚔️",
        )

    # Tab 1: Industry
    with tabs[1]:
        render_section_card(
            "Industry Information",
            sections.get("Industry Information", "Not available."),
            "🏭",
        )

    # Tab 2: News
    with tabs[2]:
        render_section_card(
            "Recent News & Events",
            sections.get("Recent News & Events", "No news found."),
            "📰",
        )

    # Tab 3: Opportunities
    with tabs[3]:
        render_section_card(
            "Potential Business Opportunities",
            sections.get("Potential Business Opportunities", "No opportunities identified."),
            "💡",
        )
        render_section_card(
            "Pain Points Identified",
            sections.get("Pain Points Identified", "No pain points identified."),
            "⚠️",
        )
        render_section_card(
            "Data Gaps",
            sections.get("Data Gaps", "No data gaps noted."),
            "🕳️",
        )

    # Tab 4: Sales Strategy
    with tabs[4]:
        sales_approach = sections.get("Suggested Sales Approach", {})
        if isinstance(sales_approach, dict):
            # Strategy overview
            if sales_approach.get("strategy"):
                st.info(f"**Overall Strategy:** {sales_approach['strategy']}")

            # Opening message
            if sales_approach.get("opening_message"):
                st.markdown("#### 💬 Suggested Opening Message")
                st.markdown(f"""
                <div style="background: #eff6ff; border-left: 4px solid #2563eb;
                            border-radius: 0 8px 8px 0; padding: 1rem 1.2rem;
                            font-style: italic; color: #1e40af;">
                    {sales_approach['opening_message']}
                </div>
                """, unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)

            # Talking points
            if sales_approach.get("talking_points"):
                st.markdown("#### 🗣️ Key Talking Points")
                for tp in sales_approach["talking_points"]:
                    st.markdown(f"✅ {tp}")

            # Avoid
            if sales_approach.get("avoid"):
                st.markdown("#### 🚫 What to Avoid")
                for a in sales_approach["avoid"]:
                    st.markdown(f"❌ {a}")

            # Timing
            if sales_approach.get("recommended_timing"):
                st.markdown("#### ⏰ Recommended Timing")
                st.markdown(sales_approach["recommended_timing"])
        else:
            render_section_card("Suggested Sales Approach", sales_approach, "🎯")

    # Tab 5: Research Data
    with tabs[5]:
        st.markdown("### 📊 Raw Data Collected")

        col1, col2 = st.columns(2)

        with col1:
            with st.expander(f"🌐 Web Results ({len(result.get('web_results', []))})", expanded=False):
                for r in result.get("web_results", []):
                    st.markdown(f"**[{r.get('title', 'No title')}]({r.get('url', '#')})**")
                    st.markdown(f"*Score: {r.get('score', 0):.2f}*")
                    st.markdown(r.get("content", "")[:300] + "…")
                    st.markdown("---")

            with st.expander(f"📰 News Results ({len(result.get('news_results', []))})", expanded=False):
                for r in result.get("news_results", []):
                    st.markdown(f"**[{r.get('title', 'No title')}]({r.get('url', '#')})**")
                    st.markdown(f"*{r.get('published_at', '')} — {r.get('source', '')}*")
                    st.markdown(r.get("content", "")[:300] + "…")
                    st.markdown("---")

        with col2:
            with st.expander(f"📖 Wikipedia ({len(result.get('wiki_results', []))})", expanded=False):
                for r in result.get("wiki_results", []):
                    st.markdown(f"**[{r.get('title')}]({r.get('url', '#')})**")
                    st.markdown(r.get("content", "")[:500] + "…")

            with st.expander(f"💰 Financial Data ({len(result.get('financial_results', []))})", expanded=False):
                for r in result.get("financial_results", []):
                    st.markdown(f"**{r.get('title', 'Financial Data')}**")
                    st.text(r.get("content", "Not available"))

            with st.expander(f"🗂️ CRM Records ({len(result.get('crm_results', []))})", expanded=False):
                crm = result.get("crm_results", [])
                if crm:
                    for r in crm:
                        raw = r.get("raw", {})
                        st.markdown(f"**Status:** {raw.get('account_status', 'N/A')}")
                        st.markdown(f"**Stage:** {raw.get('stage', 'N/A')}")
                        st.markdown(f"**Contact:** {raw.get('contact_name', 'N/A')} — {raw.get('contact_title', 'N/A')}")
                        st.markdown(f"**Last Contact:** {raw.get('last_contact', 'N/A')}")
                        st.markdown(f"**Notes:** {raw.get('notes', 'N/A')}")
                        st.markdown(f"**Est. Deal Size:** {raw.get('estimated_deal_size', 'N/A')}")
                else:
                    st.info("No CRM record found for this company.")

        st.markdown("---")
        st.markdown("### 📝 Research Agent Summary")
        with st.expander("View full research summary", expanded=False):
            st.markdown(result.get("research_summary", "Not available"))

    # Tab 6: Debug / RAG
    with tabs[6]:
        st.markdown("### 🔍 RAG Pipeline Details")

        chunks = result.get("retrieved_chunks", [])
        if chunks:
            st.markdown(f"**{len(chunks)} chunks retrieved and reranked**")
            st.markdown("""
            > These chunks were retrieved via FAISS (cosine similarity)
            > then reranked using a cross-encoder model before being passed to the LLM.
            """)
            for i, chunk in enumerate(chunks, 1):
                with st.expander(
                    f"Chunk {i} | {chunk['source_type'].upper()} | "
                    f"Cosine: {chunk['score']:.3f} | Rerank: {chunk['rerank_score']:.3f}",
                    expanded=False,
                ):
                    st.markdown(f"**Source:** {chunk['source']}")
                    st.markdown(f"**Type:** `{chunk['source_type']}`")
                    st.markdown(f"**Cosine Similarity:** `{chunk['score']:.4f}`")
                    st.markdown(f"**Cross-Encoder Score:** `{chunk['rerank_score']:.4f}`")
                    st.markdown("**Content:**")
                    st.text(chunk["content"])
        else:
            st.info("No RAG chunks available.")

        st.markdown("---")
        st.markdown("### 🗂️ Raw Analysis Output (JSON)")
        with st.expander("View raw LLM output", expanded=False):
            import json
            st.json(result.get("analysis_output", {}))

    # ── Sources ────────────────────────────────────────────────────────────────
    render_sources_expander(report.get("sources", []))


# ── Welcome / empty state ──────────────────────────────────────────────────────
else:
    st.markdown("""
    <div style="
        text-align: center;
        padding: 4rem 2rem;
        background: white;
        border-radius: 16px;
        border: 1px dashed #d1d5db;
        margin-top: 2rem;
    ">
        <div style="font-size: 4rem; margin-bottom: 1rem">🧠</div>
        <h2 style="color: #1a2b4a; margin-bottom: 0.5rem">
            Agentic AI Sales Intelligence Platform
        </h2>
        <p style="color: #6b7280; max-width: 500px; margin: 0 auto 2rem">
            Enter a company name and country in the sidebar, then click
            <b>Generate Intelligence Report</b> to launch the multi-agent pipeline.
        </p>
        <div style="display: flex; justify-content: center; gap: 1.5rem; flex-wrap: wrap">
            <div style="background: #eff6ff; border-radius: 8px; padding: 1rem 1.5rem; min-width: 160px">
                <div style="font-size: 1.5rem">🔍</div>
                <div style="font-weight: 600; color: #1e40af">Research Agent</div>
                <div style="font-size: 0.8rem; color: #3b82f6">Multi-source data collection</div>
            </div>
            <div style="background: #f0fdf4; border-radius: 8px; padding: 1rem 1.5rem; min-width: 160px">
                <div style="font-size: 1.5rem">🧩</div>
                <div style="font-weight: 600; color: #065f46">FAISS + Reranker</div>
                <div style="font-size: 0.8rem; color: #059669">Cosine + Cross-Encoder RAG</div>
            </div>
            <div style="background: #faf5ff; border-radius: 8px; padding: 1rem 1.5rem; min-width: 160px">
                <div style="font-size: 1.5rem">📊</div>
                <div style="font-weight: 600; color: #6b21a8">Analysis Agent</div>
                <div style="font-size: 0.8rem; color: #7c3aed">Sales intelligence & strategy</div>
            </div>
            <div style="background: #fff7ed; border-radius: 8px; padding: 1rem 1.5rem; min-width: 160px">
                <div style="font-size: 1.5rem">📄</div>
                <div style="font-weight: 600; color: #92400e">Export</div>
                <div style="font-size: 0.8rem; color: #d97706">PDF & Word report</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
