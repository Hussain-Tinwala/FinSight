# This python script will build a clean, modular Python script. It will generate a synthetic dataset spanning 6 months (approx. 180 days) for three cloud providers (AWS, Azure, GCP) across three services (COMPUTE, STORAGE, NETWORK).

# It will explicitly inject:
# - Sudden Spikes (Global Anomalies)
# - Slow Creep (Drift Anomalies)
# - Sunday Deviations (Contextual Anomalies)

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

# Set random seed for reproducibility
np.random.seed(42)
random.seed(42)

def generate_base_timeline(days=180):
    """Generates a continuous sequence of daily timestamps."""
    start_date = datetime(2026, 1, 1)
    return [start_date + timedelta(days=i) for i in range(days)]

def calculate_daily_cost(date, base_cost, trend_rate, weekend_drop=0.30):
    """
    Applies the mathematical formula: Cost = Base + Trend + Seasonality + Noise
    """
    # 1. Base + Trend (Linear growth)
    days_elapsed = (date - datetime(2026, 1, 1)).days
    current_base = base_cost + (days_elapsed * trend_rate)
    
    # 2. Seasonality (Day of week effect: Sat=5, Sun=6)
    is_weekend = date.weekday() >= 5
    seasonality_factor = (1.0 - weekend_drop) if is_weekend else 1.0
    
    # 3. Noise (Random variance between -4% and +4%)
    noise = np.random.uniform(-0.04, 0.04) * current_base
    
    daily_spend = (current_base * seasonality_factor) + noise
    return max(0.0, round(daily_spend, 2))

def generate_provider_data(provider_name, services, timeline):
    """Generates clean, non-anomalous historical billing logs for a provider."""
    rows = []
    
    # Baseline configs per service type to make data realistic
    configs = {
        'COMPUTE': {'base': 1200, 'trend': 1.5, 'weekend_drop': 0.35},
        'STORAGE': {'base': 600, 'trend': 2.0, 'weekend_drop': 0.05}, # Storage doesn't drop much on weekends
        'NETWORK': {'base': 300, 'trend': 0.5, 'weekend_drop': 0.40}
    }
    
    for date in timeline:
        for service in services:
            cfg = configs[service]
            raw_cost = calculate_daily_cost(date, cfg['base'], cfg['trend'], cfg['weekend_drop'])
            
            # Add metadata unique to providers to simulate real-world raw logs
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
            else: # Azure
                row = {
                    "UsageDateTime": date.strftime("%Y-%m-%d 00:00:00"),
                    "MeterCategory": "Virtual Machines" if service == "COMPUTE" else service.capitalize(),
                    "CostInBillingCurrency": raw_cost,
                    "Tags": f'{{"env": "{random.choice(["Production", "Dev"])}", "team": "FinTech"}}'
                }
            
            # Ground truth flags (start completely clean)
            row["is_anomaly"] = 0
            row["anomaly_type"] = "none"
            rows.append(row)
            
    return pd.DataFrame(rows)

def inject_anomalies(df, date_col, cost_col, provider):
    """Intentionally modifies clean data to introduce targeted cost anomalies."""
    df[date_col] = pd.to_datetime(df[date_col])
    unique_dates = sorted(df[date_col].unique())
    
    # 1. Inject Sudden Spike (Global Anomaly) around Day 45
    spike_date = unique_dates[45]
    df.loc[(df[date_col] == spike_date) & (df.index % 3 == 0), cost_col] *= 3.5
    df.loc[(df[date_col] == spike_date) & (df.index % 3 == 0), "is_anomaly"] = 1
    df.loc[(df[date_col] == spike_date) & (df.index % 3 == 0), "anomaly_type"] = "spike"

    # 2. Inject Slow Creep (Drift) between Days 100 to 115
    for i, d in enumerate(unique_dates[100:115]):
        # Gradual multiplier ramping up from 1.05 to 1.45
        multiplier = 1.05 + (i * 0.025)
        mask = (df[date_col] == d) & (df.index % 2 == 0)
        df.loc[mask, cost_col] *= multiplier
        df.loc[mask, "is_anomaly"] = 1
        df.loc[mask, "anomaly_type"] = "drift"

    # 3. Inject Contextual Anomaly (Sunday Spend matching Weekday Spend) around Day 140
    sunday_date = unique_dates[140]
    while sunday_date.weekday() != 6: # Ensure it's a Sunday
        sunday_date += timedelta(days=1)
        
    # Remove the weekend drop by multiplying back up by ~1.5
    mask = (df[date_col] == sunday_date)
    df.loc[mask, cost_col] *= 1.55
    df.loc[mask, "is_anomaly"] = 1
    df.loc[mask, "anomaly_type"] = "contextual"
    
    return df

# Main Generation Routine
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
    
    # Save outputs
    aws_df.to_csv("aws_raw_billing.csv", index=False)
    gcp_df.to_csv("gcp_raw_billing.csv", index=False)
    azure_df.to_csv("azure_raw_billing.csv", index=False)
    print("Success! Generated 'aws_raw_billing.csv', 'gcp_raw_billing.csv', and 'azure_raw_billing.csv'.")