from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text
from datetime import date, timedelta
from typing import Optional, List
from pydantic import BaseModel
import uvicorn

from backend.app.api.agent_rca import app_graph

# --- Database Setup ---
DB_URL = "postgresql://postgres:finops_password@localhost:5432/finops_intelligence"
engine = create_engine(DB_URL, pool_size=5, max_overflow=10)

app = FastAPI(
    title="Cloud FinOps Intelligence API",
    description="Middleware for serving ML-scored cloud billing data and forecasts.",
    version="1.0.0"
)

# Add CORS Middleware to unblock browser security
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"], # Vite defaults
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Data Validation Schemas ---
class SpendRecord(BaseModel):
    timestamp: str
    cloud_provider: str
    unified_category: str
    cost: float
    is_anomaly: int
    anomaly_type: str

class ForecastRecord(BaseModel):
    date: str
    predicted_cost: float
    lower_bound: float
    upper_bound: float
    model_used: str

class IncidentTrigger(BaseModel):
    date: str
    type: str
    stream: str

class RCALogResponse(BaseModel):
    status: str
    target_date: str
    topology: str
    report: str

# --- Endpoints ---

@app.get("/api/v1/health")
def health_check():
    """Verifies API and Database connectivity."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database connection failed: {str(e)}")

@app.get("/api/v1/spend", response_model=List[SpendRecord])
def get_actual_spend(
    provider: str = Query(..., description="E.g., AWS, GCP, Azure"),
    category: str = Query(..., description="E.g., COMPUTE, STORAGE, NETWORK"),
    start_date: date = Query(..., description="Start of the query window"),
    end_date: date = Query(..., description="End of the query window")
):
    """Fetches normalized historical spend and anomaly flags."""
    query = text("""
        SELECT timestamp, cloud_provider, unified_category, cost, is_anomaly, anomaly_type
        FROM cloud_spend
        WHERE cloud_provider = :provider 
          AND unified_category = :category
          AND timestamp >= :start_date 
          AND timestamp <= :end_date
        ORDER BY timestamp ASC;
    """)
    
    with engine.connect() as conn:
        result = conn.execute(query, {
            "provider": provider, 
            "category": category, 
            "start_date": start_date, 
            "end_date": end_date
        }).mappings().all()
        
    return [{"timestamp": str(r["timestamp"]), **r} for r in result]

# Note: In a full production setup, we would load the forecast from a new DB hypertable. 
# For this immediate module, we will mock the connection to the CSV we just generated.
import pandas as pd
@app.get("/api/v1/forecast", response_model=List[ForecastRecord])
def get_forecast():
    """Fetches the 90-day ensembled prediction boundary."""
    try:
        df = pd.read_csv("production_forecast.csv")
        return df.to_dict(orient="records")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Forecast data not yet generated.")

# --- NEW: AI Agent Core Integration Endpoint ---

@app.post("/api/v1/anomaly/rca", response_model=RCALogResponse)
async def trigger_root_cause_analysis(incident: IncidentTrigger):
    """
    Asynchronously invokes the LangGraph multi-agent state machine
    to generate an engineering root-cause analysis brief for a given anomaly.
    """
    print(f"[API Layer] Received RCA request for {incident.stream} on {incident.date}")
    
    # Structure the initial graph state using data sent from the request payload
    initial_state = {
        "anomaly_details": {
            "date": incident.date,
            "type": incident.type,
            "stream": incident.stream
        },
        "fetched_data": [],
        "analysis_notes": [],
        "final_rca_report": "",
        "next_step": ""
    }
    
    try:
        # Run the graph asynchronously to keep the main web server thread completely free
        graph_output = await app_graph.ainvoke(initial_state)
        
        return {
            "status": "success",
            "target_date": incident.date,
            "topology": incident.type,
            "report": graph_output.get("final_rca_report", "Analysis failed to yield text.")
        }
    except Exception as e:
        print(f"[API Layer Error] Graph execution failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AI Agent RCA Execution Failure: {str(e)}")

if __name__ == "__main__":
    print("--- Starting FinOps API Middleware with Integrated Agent Lifecycle ---")
    # uvicorn.run("api_main:app", host="0.0.0.0", port=8000, reload=True)
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)