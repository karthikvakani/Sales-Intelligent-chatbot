"""
agents/pipeline.py
LangGraph orchestration — defines the multi-agent graph:

  START → research_agent → analysis_agent → END

Each node is a pure function (AgentState → AgentState).
State is passed between nodes; both agents see and build on shared context.
"""

from langgraph.graph import StateGraph, END

from agents.research_agent import research_agent_node
from agents.analysis_agent import analysis_agent_node
from utils.state import AgentState
from utils.logger import logger


def _should_continue(state: AgentState) -> str:
    """
    Conditional edge: if the research agent hit a total failure,
    skip the analysis agent and go straight to END.
    """
    if state.get("errors") and not state.get("research_summary"):
        logger.warning("Skipping analysis agent due to empty research summary")
        return "end"
    return "analysis"


def build_pipeline() -> StateGraph:
    """
    Build and compile the LangGraph multi-agent pipeline.
    Returns a compiled graph ready for invocation.
    """
    graph = StateGraph(AgentState)

    # ── Register nodes ────────────────────────────────────────────────────────
    graph.add_node("research_agent", research_agent_node)
    graph.add_node("analysis_agent", analysis_agent_node)

    # ── Entry point ───────────────────────────────────────────────────────────
    graph.set_entry_point("research_agent")

    # ── Conditional routing after research ───────────────────────────────────
    graph.add_conditional_edges(
        "research_agent",
        _should_continue,
        {
            "analysis": "analysis_agent",
            "end": END,
        },
    )

    # ── Analysis → END ────────────────────────────────────────────────────────
    graph.add_edge("analysis_agent", END)

    compiled = graph.compile()
    logger.info("LangGraph pipeline compiled: research_agent → analysis_agent → END")
    return compiled


def run_pipeline(company_name: str, country: str) -> AgentState:
    """
    Execute the full multi-agent pipeline and return the final state.
    """
    initial_state: AgentState = {
        "company_name": company_name,
        "country": country,
        "web_results": [],
        "news_results": [],
        "wiki_results": [],
        "financial_results": [],
        "crm_results": [],
        "all_documents": [],
        "retrieved_chunks": [],
        "research_summary": "",
        "analysis_output": {},
        "report": {},
        "export_path": None,
        "errors": [],
        "warnings": [],
        "confidence": "unknown",
        "status": "Initialising pipeline…",
    }

    graph = build_pipeline()
    logger.info(f"Running pipeline for '{company_name}' in '{country}'")

    try:
        final_state = graph.invoke(initial_state)
        logger.info(f"Pipeline completed for '{company_name}'")
        return final_state
    except Exception as exc:
        logger.error(f"Pipeline fatal error: {exc}")
        initial_state["errors"].append(f"Pipeline fatal error: {exc}")
        initial_state["status"] = f"❌ Pipeline failed: {exc}"
        return initial_state
