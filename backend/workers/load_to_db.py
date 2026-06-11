import os
import sys
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# 1. DYNAMIC PATH RESOLUTION
WORKER_DIR = os.path.dirname(os.path.abspath(__file__))   # FinSight/backend/workers
BACKEND_DIR = os.path.dirname(WORKER_DIR)                 # FinSight/backend
ROOT_DIR = os.path.dirname(BACKEND_DIR)                   # FinSight Root

# 2. EXPLICITLY LOAD ENVIRONMENTAL CONFIGURATIONS FROM BACKEND/.ENV
dotenv_path = os.path.join(BACKEND_DIR, ".env")
load_dotenv(dotenv_path)

# Extract database string from environment, scrubbing hardcoded credentials from the fallback
DB_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://YOUR_DB_USER:YOUR_DB_PASSWORD@localhost:5432/finops_intelligence"
)

def load_multi_tenant_data():
    """
    Ingests flat unified metrics, maps rows dynamically to an active multi-tenant 
    database organization account, and writes rows to the relational spend hypertable.
    """
    print("--- Starting FinSight Multi-Tenant Telemetry Ingestion Worker ---")
    
    csv_path = os.path.join(ROOT_DIR, "data", "unified_billing.csv")
    
    if not os.path.exists(csv_path):
        print(f"[Storage Error] Preprocessed metrics file missing at target path: {csv_path}")
        print("Please ensure your data preprocessing pipelines have been executed.")
        return

    print(f"[Database Connection] Initializing pool parameters for destination target...")
    engine = create_engine(DB_URL)

    # 3. TENANT ISOLATION SAFEGUARD LOGIC
    try:
        with engine.connect() as conn:
            tenant = conn.execute(
                text("SELECT id, name FROM organizations ORDER BY created_at ASC LIMIT 1")
            ).mappings().fetchone()
    except Exception as e:
        print(f"[Database Error] Failed to establish connection to database cluster: {str(e)}")
        return

    if not tenant:
        print("[Tenant Mapping Failure] Ingestion halted: No registered corporate organizations found.")
        return

    target_org_id = str(tenant["id"])
    print(f"[Tenant Isolation] Mapped ingestion run to client organization account: {tenant['name']} ({target_org_id})")

    print(f"[File I/O] Loading source telemetry: {csv_path}")
    df = pd.read_csv(csv_path)
    
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['organization_id'] = target_org_id

    schema_mapped_df = pd.DataFrame({
        'organization_id': df['organization_id'],
        'timestamp': df['timestamp'],
        'cloud_provider': df['cloud_provider'],
        'unified_category': df['unified_category'],
        'cost': df['cost'],
        'normalized_env': df['normalized_env'],
        'normalized_team': df['normalized_team'],
        'is_anomaly': df['is_anomaly'],
        'anomaly_type': df['anomaly_type']
    })

    print(f"[Database Write-Back] Streaming {len(schema_mapped_df)} rows directly into 'cloud_spend'...")
    
    try:
        schema_mapped_df.to_sql(
            'cloud_spend', engine, if_exists='append', index=False, method='multi', chunksize=1000
        )
        print("--- Success: Multi-tenant billing data successfully synchronized in database ---")
    except Exception as e:
        print(f"[Write Failure] Transaction rolled back due to error during batch insert: {str(e)}")

if __name__ == "__main__":
    load_multi_tenant_data()