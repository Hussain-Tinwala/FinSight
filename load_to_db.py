import pandas as pd
from sqlalchemy import create_engine

def load_data_to_timescale():
    print("Connecting to TimescaleDB...")
    # SQLAlchemy connection string: postgresql://user:password@host:port/database
    engine = create_engine('postgresql://postgres:finops_password@localhost:5432/finops_intelligence')
    
    print("Loading normalized CSV...")
    df = pd.read_csv("unified_billing.csv")
    
    # Ensure timestamp is a proper datetime object for PostgreSQL TIMESTAMPTZ
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    print(f"Inserting {len(df)} rows into the hypertable. This might take a few seconds...")
    # Push the data to the 'cloud_spend' table
    # if_exists='append' ensures we don't overwrite the hypertable structure
    df.to_sql('cloud_spend', engine, if_exists='append', index=False, method='multi', chunksize=1000)
    
    print("Success! Unified billing data is now indexed in TimescaleDB.")

if __name__ == "__main__":
    load_data_to_timescale()