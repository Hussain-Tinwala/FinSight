import os
import random
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text

# Connect to your local database
DB_URL = "postgresql://postgres:finops_password@localhost:5432/finops_intelligence"
engine = create_engine(DB_URL)

def inject_live_anomaly(org_id: str):
    print(f"--- Incoming AWS EventBridge Webhook Detected ---")
    print(f"Processing telemetry for Organization: {org_id}")
    
    # We use a date close to our mock "present day" so it shows up on the edge of your graph
    target_date = "2026-06-28" 
    
    # 1. Simulate a massive $18,000 cost overrun caused by a Dev team spinning up expensive GPUs
    massive_cost = round(random.uniform(15000, 19000), 2)
    
    query = text("""
        INSERT INTO cloud_spend 
        (organization_id, timestamp, cloud_provider, unified_category, cost, normalized_env, normalized_team, is_anomaly, anomaly_type)
        VALUES 
        (:org_id, :target_date, 'AWS', 'COMPUTE', :cost, 'dev', 'ai-research', 1, 'massive_spike')
    """)
    
    with engine.begin() as conn:
        conn.execute(query, {
            "org_id": org_id,
            "target_date": target_date,
            "cost": massive_cost
        })
        
    print(f"✅ ML Tier 3 Anomaly Triggered: $ {massive_cost} spike logged on {target_date}.")
    print("👉 Go click 'Re-Sync' on your React Dashboard to see the real-time update!")

if __name__ == "__main__":
    # COPY YOUR ORGANIZATION ID FROM YOUR DASHBOARD HEADER AND PASTE IT HERE
    # YOUR_ORG_ID = "PASTE_YOUR_ORG_ID_HERE" 
    YOUR_ORG_ID = "88c8fd16-af3e-4187-8447-0c18a2184412" 
    inject_live_anomaly(YOUR_ORG_ID)