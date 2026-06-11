import os
from typing import TypedDict, List, Dict, Any
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

load_dotenv()

# Database Connection Pool Configuration
DB_URL = os.getenv("DATABASE_URL", "postgresql://YOUR_USER:YOUR_PASSWORD@localhost:5432/finops_intelligence")

db_engine = create_engine(
    DB_URL,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800
)

# Define the Graph State Structure
class AgentState(TypedDict):
    anomaly_details: Dict[str, Any]
    fetched_data: List[Dict[str, Any]]
    analysis_notes: List[str]
    final_rca_report: str
    next_step: str

def get_llm():
    # Utilizing temperature=0.0 to ensure strict deterministic structural evaluation
    return ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.0)


def data_fetcher_node(state: AgentState) -> Dict[str, Any]:
    """Node 1: Queries the PostgreSQL database to pull live contextual transaction logs around the event."""
    print("[Node: Data Fetcher] Pulling historical data from database...")
    anomaly = state["anomaly_details"]
    target_date = anomaly["date"]
    org_id = anomaly.get("organization_id")
    
    # Extract the specific cloud provider and category from the stream name (e.g., "AWS-COMPUTE")
    stream = anomaly.get("stream", "AWS-COMPUTE")
    provider, category = stream.split("-")
    
    # FIX: Tightly scoped SQL query using organization, provider, and category filters
    query = text("""
        SELECT CAST(timestamp AS text), cost, normalized_team, normalized_env, cloud_provider, unified_category
        FROM cloud_spend
        WHERE organization_id = :org_id
          AND cloud_provider = :provider
          AND unified_category = :category
          AND timestamp >= CAST(:target_date AS date) - INTERVAL '2 days'
          AND timestamp <= CAST(:target_date AS date) + INTERVAL '1 day'
        ORDER BY timestamp ASC;
    """)
    
    try:
        with db_engine.connect() as conn:
            result = conn.execute(query, {
                "org_id": org_id, 
                "provider": provider, 
                "category": category, 
                "target_date": target_date
            }).mappings().all()
            
        db_records = [
            {
                "timestamp": r["timestamp"],
                "cloud_provider": r["cloud_provider"],
                "unified_category": r["unified_category"],
                "cost": float(r["cost"]),
                "normalized_env": r["normalized_env"],
                "normalized_team": r["normalized_team"]
            }
            for r in result
        ]
        
        notes = [f"Successfully fetched {len(db_records)} scoped records for {provider} {category}."]
        return {"fetched_data": db_records, "analysis_notes": notes}
        
    except Exception as e:
        print(f"Database extraction pipeline failed: {str(e)}")
        return {"fetched_data": [], "analysis_notes": [f"Database extraction error: {str(e)}"]}
    
    


def triage_analyst_node(state: AgentState) -> Dict[str, Any]:
    """Node 2: Generates fine-grained ownership analysis utilizing Gemini inference parsing."""
    print("[Node: Triage Analyst] Running architectural verification checks...")
    fetched_data = state["fetched_data"]
    notes = list(state["analysis_notes"])
    
    if not fetched_data:
        notes.append("Skipping LLM evaluation: No telemetry records available in the database for this timeframe.")
        return {"analysis_notes": notes, "next_step": "generate_report"}
        
    prompt = f"""
    You are an Expert Enterprise Cloud FinOps Principal Engineer.
    Analyze these raw database cost logs containing an unblended spending anomaly:
    {fetched_data}
    
    Tasks:
    1. Identify the exact team (normalized_team) and environment (normalized_env) that caused the cost spike.
    2. Quantify the absolute dollar jump.
    3. Output a highly precise engineering diagnostic breakdown detailing the responsible parties.
    """
    
    # NEW: Fault Tolerance Block to prevent 500 Server Errors
    try:
        llm = get_llm()
        response = llm.invoke([
            SystemMessage(content="You analyze live enterprise cloud spend records to assign ownership blame and cost variance analytics."),
            HumanMessage(content=prompt)
        ])
        summary = response.content
    except Exception as e:
        print(f"[CRITICAL LLM FAILURE] {str(e)}")
        summary = f"**AI Engine Failure:** Could not reach the Gemini API. \n\nDiagnostic Data: {str(e)}\n\nPlease verify your GEMINI_API_KEY in the .env file and check your internet connection."
    
    notes.append(f"Triage Analysis Complete:\n{summary}")
    
    # Always route to report generation so the user sees either the result or the error safely
    next_step = "generate_report" 
    return {"analysis_notes": notes, "next_step": next_step}



def report_writer_node(state: AgentState) -> Dict[str, Any]:
    """Node 3: Assembles and structures the technical RCA payload markdown output."""
    print("[Node: Report Writer] Generating human-readable structural brief...")
    notes = state["analysis_notes"]
    anomaly = state["anomaly_details"]
    
    report = f"""=== FINOPS ROOT CAUSE ANALYSIS REPORT ===
Target Event Date: {anomaly['date']}
Identified Topology: {anomaly.get('type', 'Spike Variance Detected')}
Platform Stream: {anomaly.get('stream', 'Multi-Vendor Architecture')}

Executive Summary of Investigation:
{notes[-1] if notes else 'No triage notes compiled.'}

Action Item Matrix:
1. Alert the engineering leads directly responsible for the highlighted team.
2. Cross-reference AWS Auto-Scaling Group scaling logs matching the target timestamp.
3. Validate lifecycle configuration policies for orphan storage mounts or non-terminated compute threads.
========================================="""
    
    return {"final_rca_report": report}

# --- Routing Transitions ---

def route_after_triage(state: AgentState) -> str:
    if state["next_step"] == "generate_report":
        print("   -> Route Condition Met: Production priority verified. Transferring control to Writer Agent.")
        return "report_writer"
    else:
        print("   -> Route Condition Met: Operational condition metrics low or outside analysis scope. Exiting graph.")
        return END

# --- Build & Compile the Structural Graph Workflow ---

workflow = StateGraph(AgentState)

workflow.add_node("data_fetcher", data_fetcher_node)
workflow.add_node("triage_analyst", triage_analyst_node)
workflow.add_node("report_writer", report_writer_node)

workflow.set_entry_point("data_fetcher")
workflow.add_edge("data_fetcher", "triage_analyst")

workflow.add_conditional_edges(
    "triage_analyst",
    route_after_triage,
    {
        "report_writer": "report_writer",
        END: END
    }
)

workflow.add_edge("report_writer", END)
app_graph = workflow.compile()