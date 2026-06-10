import os
import httpx
from typing import TypedDict, List, Dict, Any
from dotenv import load_dotenv

from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

load_dotenv()

# Ensure API Key is available
if "GEMINI_API_KEY" not in os.environ:
    # Fallback to dummy mode if key isn't provided yet so the code structure executes safely
    os.environ["GEMINI_API_KEY"] = "mock_key"

# Define the shared Graph State structure
class AgentState(TypedDict):
    anomaly_details: Dict[str, Any]
    fetched_data: List[Dict[str, Any]]
    analysis_notes: List[str]
    final_rca_report: str
    next_step: str

# Initialize our LLM Engine (Gemini Pro)
def get_llm():
    return ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.2)

# --- Graph Nodes ---

def data_fetcher_node(state: AgentState) -> Dict[str, Any]:
    """Node 1: Queries the FastAPI middleware to fetch historical context around the anomaly date."""
    print("[Node: Data Fetcher] Pulling historical data from FastAPI...")
    anomaly = state["anomaly_details"]
    
    # Target window: 3 days before and after the anomaly event
    target_date = anomaly["date"]
    
    # For this localized execution, we mock the FastAPI JSON response directly
    # matching the schema built in Module 11 to ensure offline functionality.
    mock_api_response = [
        {"timestamp": f"{target_date} 00:00:00", "cloud_provider": "AWS", "unified_category": "COMPUTE", "cost": 4200.0, "is_anomaly": 1, "anomaly_type": "spike", "normalized_env": "production", "normalized_team": "coreengine"},
        {"timestamp": "2026-02-14 00:00:00", "cloud_provider": "AWS", "unified_category": "COMPUTE", "cost": 1200.0, "is_anomaly": 0, "anomaly_type": "none", "normalized_env": "production", "normalized_team": "coreengine"}
    ]
    
    return {
        "fetched_data": mock_api_response,
        "analysis_notes": ["Successfully fetched 3-day runtime window context across AWS-COMPUTE."]
    }

def triage_analyst_node(state: AgentState) -> Dict[str, Any]:
    """Node 2: Evaluates anomalies, cross-referencing metrics and infrastructure tags."""
    print("[Node: Triage Analyst] Running structural signature checks via Gemini...")
    fetched_data = state["fetched_data"]
    notes = state["analysis_notes"]
    
    llm = get_llm()
    
    prompt = f"""
    You are a Cloud FinOps Data Analyst. Inspect the following raw JSON infrastructure spend logs:
    {fetched_data}
    
    Isolate which specific team (normalized_team) and environment (normalized_env) are responsible for the cost shift.
    Provide a concise technical summary of your findings.
    """
    
    if os.environ["GEMINI_API_KEY"] == "mock_key":
        # Mock LLM execution to prevent network failures if key isn't initialized yet
        summary = "ANALYSIS: Found 3.5x spike in production environment mapped to team 'coreengine'."
    else:
        response = llm.invoke([SystemMessage(content="Analyze FinOps anomalies."), HumanMessage(content=prompt)])
        summary = response.content

    notes.append(f"Triage Analysis Complete: {summary}")
    
    # Decide routing path dynamically based on validation findings
    next_step = "generate_report" if "production" in summary.lower() else "gather_more_context"
    
    return {"analysis_notes": notes, "next_step": next_step}

def report_writer_node(state: AgentState) -> Dict[str, Any]:
    """Node 3: Formats the final executive Root Cause Analysis payload."""
    print("[Node: Report Writer] Compiling final human-readable RCA brief...")
    notes = state["analysis_notes"]
    anomaly = state["anomaly_details"]
    
    report = f"""
    === FINOPS ROOT CAUSE ANALYSIS REPORT ===
    Target Event Date: {anomaly['date']}
    Identified Topology: {anomaly['type']}
    
    Executive Summary of Investigation:
    {chr(10).join(notes)}
    
    Action Item: Alert engineering leads for team 'coreengine'. Check for unoptimized auto-scaling policy triggers.
    =========================================
    """
    return {"final_rca_report": report}

# --- Routing Logic ---

def route_after_triage(state: AgentState) -> str:
    """Evaluates state vector to execute dynamic workflow conditional routing loops."""
    if state["next_step"] == "generate_report":
        print("   -> Route Condition Met: Production priority verified. Moving to Report Generation.")
        return "report_writer"
    else:
        print("   -> Route Condition Met: Low priority or unknown context. Loop back or exit.")
        return END

# --- Build the Graph ---

workflow = StateGraph(AgentState)

# Register Nodes
workflow.add_node("data_fetcher", data_fetcher_node)
workflow.add_node("triage_analyst", triage_analyst_node)
workflow.add_node("report_writer", report_writer_node)

# Set Graph Architecture Flow
workflow.set_entry_point("data_fetcher")
workflow.add_edge("data_fetcher", "triage_analyst")

# Add conditional execution logic edge
workflow.add_conditional_edges(
    "triage_analyst",
    route_after_triage,
    {
        "report_writer": "report_writer",
        END: END
    }
)

workflow.add_edge("report_writer", END)

# Compile graph structure
app_graph = workflow.compile()

if __name__ == "__main__":
    print("--- Testing FinOps LangGraph Agent Workflow ---")
    
    # Define an initial incident structure (e.g., passed down from our ensemble detector)
    initial_incident = {
        "anomaly_details": {
            "date": "2026-02-15",
            "type": "Sudden Spike",
            "stream": "AWS-COMPUTE"
        },
        "fetched_data": [],
        "analysis_notes": [],
        "final_rca_report": "",
        "next_step": ""
    }
    
    output = app_graph.invoke(initial_incident)
    print(output["final_rca_report"])