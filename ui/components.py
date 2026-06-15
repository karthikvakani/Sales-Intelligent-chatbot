"""
ui/components.py
Reusable Streamlit UI components for the Sales Intelligence Platform.
"""

import streamlit as st
from datetime import datetime


def render_header():
    """Render the top navigation header."""
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #1a2b4a 0%, #2563eb 100%);
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        display: flex;
        align-items: center;
        gap: 1rem;
    ">
        <div>
            <h1 style="color: white; margin: 0; font-size: 1.8rem; font-weight: 700;">
                🧠 Agentic AI Sales Intelligence Platform
            </h1>
            <p style="color: #bfdbfe; margin: 0.3rem 0 0; font-size: 0.9rem;">
                Powered by LLaMA 3.3 70B · LangGraph · FAISS · Cross-Encoder Reranking
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_confidence_badge(level: str):
    """Display a colour-coded confidence badge."""
    config = {
        "high": ("🟢", "#065f46", "#d1fae5", "High Confidence"),
        "medium": ("🟡", "#92400e", "#fef3c7", "Medium Confidence"),
        "low": ("🔴", "#7f1d1d", "#fee2e2", "Low Confidence — Limited Data"),
        "unknown": ("⚪", "#374151", "#f3f4f6", "Confidence Unknown"),
    }
    icon, text_c, bg_c, label = config.get(level.lower(), config["unknown"])
    st.markdown(f"""
    <div style="
        display: inline-block;
        background: {bg_c};
        color: {text_c};
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        margin-bottom: 1rem;
    ">{icon} {label}</div>
    """, unsafe_allow_html=True)


def render_metric_row(metrics: list[dict]):
    """
    Render a row of metric cards.
    Each dict: {"label": str, "value": str, "icon": str, "colour": str}
    """
    cols = st.columns(len(metrics))
    for col, m in zip(cols, metrics):
        with col:
            colour = m.get("colour", "#2563eb")
            st.markdown(f"""
            <div style="
                background: white;
                border: 1px solid #e5e7eb;
                border-left: 4px solid {colour};
                border-radius: 8px;
                padding: 1rem;
                text-align: center;
                box-shadow: 0 1px 3px rgba(0,0,0,0.07);
            ">
                <div style="font-size: 1.5rem">{m.get('icon', '')}</div>
                <div style="font-size: 1.4rem; font-weight: 700; color: #111827">
                    {m.get('value', '')}
                </div>
                <div style="font-size: 0.75rem; color: #6b7280; margin-top: 2px">
                    {m.get('label', '')}
                </div>
            </div>
            """, unsafe_allow_html=True)


def render_section_card(title: str, content, icon: str = "📄"):
    """Render a full report section inside a styled card."""
    st.markdown(f"""
    <div style="
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 10px;
        padding: 1.2rem 1.5rem 0.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    ">
        <h3 style="color: #1a2b4a; margin: 0 0 0.8rem; font-size: 1.05rem; display: flex; align-items: center; gap: 0.5rem;">
            {icon} {title}
        </h3>
    """, unsafe_allow_html=True)
    _render_content(content)
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)


def _render_content(content):
    """Recursively render different content types."""
    if isinstance(content, str):
        st.markdown(content)
    elif isinstance(content, list):
        for item in content:
            if isinstance(item, dict):
                _render_dict_item(item)
            elif isinstance(item, str):
                st.markdown(f"• {item}")
    elif isinstance(content, dict):
        _render_dict_item(content)


def _render_dict_item(d: dict):
    """Render a dictionary as a structured block."""
    # Special handling for business opportunities
    if "opportunity" in d:
        confidence = d.get("confidence", "medium")
        conf_colours = {"high": "#065f46", "medium": "#92400e", "low": "#7f1d1d"}
        conf_bg = {"high": "#d1fae5", "medium": "#fef3c7", "low": "#fee2e2"}
        c = conf_colours.get(confidence, "#374151")
        bg = conf_bg.get(confidence, "#f3f4f6")
        src = d.get("source", "")
        src_html = f'<a href="{src}" target="_blank" style="font-size:0.75rem; color:#2563eb">{src[:60]}…</a>' if src else ""
        st.markdown(f"""
        <div style="background:{bg}; border-left: 4px solid {c}; border-radius: 6px;
                    padding: 0.8rem 1rem; margin: 0.5rem 0;">
            <b style="color:{c}">🎯 {d.get('opportunity', '')}</b><br>
            <span style="font-size: 0.9rem">{d.get('rationale', '')}</span><br>
            {src_html}
            <span style="background: white; border: 1px solid {c}; color: {c};
                         font-size: 0.7rem; padding: 1px 6px; border-radius: 10px;
                         margin-top: 4px; display: inline-block;">
                Confidence: {confidence.upper()}
            </span>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Generic dict
        for k, v in d.items():
            if isinstance(v, (list, dict)):
                st.markdown(f"**{k.replace('_', ' ').title()}:**")
                _render_content(v)
            else:
                st.markdown(f"**{k.replace('_', ' ').title()}:** {v}")


def render_sources_expander(sources: list[str]):
    """Render collapsible sources section."""
    if not sources:
        return
    with st.expander(f"📎 {len(sources)} Sources & References", expanded=False):
        for i, src in enumerate(sources, 1):
            st.markdown(f"{i}. [{src}]({src})" if src.startswith("http") else f"{i}. {src}")


def render_pipeline_diagram():
    """Render a simple ASCII/HTML pipeline architecture overview."""
    st.markdown("""
    <div style="
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 1rem 1.5rem;
        font-family: monospace;
        font-size: 0.82rem;
        color: #374151;
        margin-bottom: 1rem;
    ">
    <b>🏗️ Pipeline Architecture</b><br><br>
    Input (Company + Country)<br>
    &nbsp;&nbsp;&nbsp;↓<br>
    <b>🔍 Research Agent</b> (LangGraph Node 1)<br>
    &nbsp;&nbsp;&nbsp;├─ Web Search (Tavily / DuckDuckGo)<br>
    &nbsp;&nbsp;&nbsp;├─ News API / Tavily News<br>
    &nbsp;&nbsp;&nbsp;├─ Wikipedia<br>
    &nbsp;&nbsp;&nbsp;├─ yfinance (public companies)<br>
    &nbsp;&nbsp;&nbsp;└─ CRM Mock Lookup<br>
    &nbsp;&nbsp;&nbsp;↓<br>
    <b>📦 RAG Pipeline</b><br>
    &nbsp;&nbsp;&nbsp;├─ RecursiveCharacterTextSplitter (chunk)<br>
    &nbsp;&nbsp;&nbsp;├─ SentenceTransformers (embed)<br>
    &nbsp;&nbsp;&nbsp;├─ FAISS IndexFlatIP (cosine similarity)<br>
    &nbsp;&nbsp;&nbsp;└─ CrossEncoder reranking → Top-K chunks<br>
    &nbsp;&nbsp;&nbsp;↓<br>
    <b>📊 Analysis & Sales Agent</b> (LangGraph Node 2)<br>
    &nbsp;&nbsp;&nbsp;├─ Second RAG pass (sales signals)<br>
    &nbsp;&nbsp;&nbsp;└─ llama-3.3-70b-versatile (Groq)<br>
    &nbsp;&nbsp;&nbsp;↓<br>
    Structured Report → PDF / DOCX Export
    </div>
    """, unsafe_allow_html=True)


def render_warnings_errors(warnings: list, errors: list):
    """Render warnings and errors in expandable sections."""
    if errors:
        with st.expander(f"❌ {len(errors)} Error(s)", expanded=True):
            for e in errors:
                st.error(e)
    if warnings:
        with st.expander(f"⚠️ {len(warnings)} Warning(s)", expanded=False):
            for w in warnings:
                st.warning(w)
