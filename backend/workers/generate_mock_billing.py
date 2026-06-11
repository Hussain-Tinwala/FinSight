import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

# --- DYNAMIC PATH RESOLUTION ---
WORKER_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(os.path.dirname(WORKER_DIR))
RAW_DATA_DIR = os.path.join(ROOT_DIR, "data", "raw_data")

# Ensure target directory exists
os.makedirs(RAW_DATA_DIR, exist_ok=True)

np.random.seed(42)
random.seed(42)

def generate_base_timeline(days=180):
    start_date = datetime(2026, 1, 1)
    return [start_date + timedelta(days=i) for i in range(days)]

def calculate_daily_cost(date, base_cost, trend_rate, weekend_drop=0.30):
    days_elapsed = (date - datetime(2026, 1, 1)).days
    current_base = base_cost + (days_elapsed * trend_rate)
    is_weekend = date.weekday() >= 5
    seasonality_factor = (1.0 - weekend_drop) if is_weekend else 1.0
    noise = np.random.uniform(-0.04, 0.04) * current_base
    daily_spend = (current_base * seasonality_factor) + noise
    return max(0.0, round(daily_spend, 2))

def generate_provider_data(provider_name, services, timeline):
    rows = []
    configs = {
        'COMPUTE': {'base': 1200, 'trend': 1.5, 'weekend_drop': 0.35},
        'STORAGE': {'base': 600, 'trend': 2.0, 'weekend_drop': 0.05}, 
        'NETWORK': {'base': 300, 'trend': 0.5, 'weekend_drop': 0.40}
    }
    
    for date in timeline:
        for service in services:
            cfg = configs[service]
            raw_cost = calculate_daily_cost(date, cfg['base'], cfg['trend'], cfg['weekend_drop'])
            
            if provider_name == "AWS":
                row = {
                    "lineItem/UsageStartDate": date.strftime("%Y-%m-%d 00:00:00"),
                    "productCode": f"Amazon{service.capitalize() if service != 'COMPUTE' else 'EC2'}",
                    "lineItem/UnblendedCost": raw_cost,
                    "lineItem/NetUnblendedCost": raw_cost,
                    "resourceTags/user:Environment": random.choice(["production", "production", "staging"]),
                    "resourceTags/user:Team": random.choice(["CoreEngine", "DataPlatform"])
                }
            elif provider_name == "GCP":
                row = {
                    "usage_start_time": date.strftime("%Y-%m-%d 00:00:00"),
                    "service/description": f"Compute Engine" if service == "COMPUTE" else f"Cloud {service.capitalize()}",
                    "cost": raw_cost,
                    "labels/env": random.choice(["prod", "prod", "dev"]),
                    "labels/owner": random.choice(["core-team", "analytics"])
                }
            else: 
                row = {
                    "UsageDateTime": date.strftime("%Y-%m-%d 00:00:00"),
                    "MeterCategory": "Virtual Machines" if service == "COMPUTE" else service.capitalize(),
                    "CostInBillingCurrency": raw_cost,
                    "Tags": f'{{"env": "{random.choice(["Production", "Dev"])}", "team": "FinTech"}}'
                }
            
            row["is_anomaly"] = 0
            row["anomaly_type"] = "none"
            rows.append(row)
            
    return pd.DataFrame(rows)

def inject_anomalies(df, date_col, cost_col, provider):
    df[date_col] = pd.to_datetime(df[date_col])
    unique_dates = sorted(df[date_col].unique())
    
    spike_date = unique_dates[45]
    df.loc[(df[date_col] == spike_date) & (df.index % 3 == 0), cost_col] *= 3.5
    df.loc[(df[date_col] == spike_date) & (df.index % 3 == 0), "is_anomaly"] = 1
    df.loc[(df[date_col] == spike_date) & (df.index % 3 == 0), "anomaly_type"] = "spike"

    for i, d in enumerate(unique_dates[100:115]):
        multiplier = 1.05 + (i * 0.025)
        mask = (df[date_col] == d) & (df.index % 2 == 0)
        df.loc[mask, cost_col] *= multiplier
        df.loc[mask, "is_anomaly"] = 1
        df.loc[mask, "anomaly_type"] = "drift"

    sunday_date = unique_dates[140]
    while sunday_date.weekday() != 6: 
        sunday_date += timedelta(days=1)
        
    mask = (df[date_col] == sunday_date)
    df.loc[mask, cost_col] *= 1.55
    df.loc[mask, "is_anomaly"] = 1
    df.loc[mask, "anomaly_type"] = "contextual"
    
    return df

if __name__ == "__main__":
    timeline = generate_base_timeline(180)
    services = ['COMPUTE', 'STORAGE', 'NETWORK']
    
    print("Generating raw cloud billing data...")
    aws_df = generate_provider_data("AWS", services, timeline)
    gcp_df = generate_provider_data("GCP", services, timeline)
    azure_df = generate_provider_data("Azure", services, timeline)
    
    print("Injecting systemic FinOps anomalies...")
    aws_df = inject_anomalies(aws_df, "lineItem/UsageStartDate", "lineItem/UnblendedCost", "AWS")
    gcp_df = inject_anomalies(gcp_df, "usage_start_time", "cost", "GCP")
    azure_df = inject_anomalies(azure_df, "UsageDateTime", "CostInBillingCurrency", "Azure")
    
    # Save to absolute raw_data directory
    aws_df.to_csv(os.path.join(RAW_DATA_DIR, "aws_raw_billing.csv"), index=False)
    gcp_df.to_csv(os.path.join(RAW_DATA_DIR, "gcp_raw_billing.csv"), index=False)
    azure_df.to_csv(os.path.join(RAW_DATA_DIR, "azure_raw_billing.csv"), index=False)
    print(f"Success! Generated raw billing files in {RAW_DATA_DIR}.")