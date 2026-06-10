import pandas as pd
import json
import os

def normalize_aws(file_path):
    """Transforms raw AWS data into the canonical schema."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Missing file: {file_path}")
        
    df = pd.read_csv(file_path)
    
    normalized = pd.DataFrame()
    # 1. Standardize Timestamps
    normalized['timestamp'] = pd.to_datetime(df['lineItem/UsageStartDate'])
    normalized['cloud_provider'] = 'AWS'
    
    # 2. Map Canonical Service Categories
    service_map = {
        'AmazonEC2': 'COMPUTE',
        'AmazonStorage': 'STORAGE',
        'AmazonNetwork': 'NETWORK'
    }
    normalized['unified_category'] = df['productCode'].map(service_map).fillna('OTHER')
    
    # 3. Standardize Cost Metric
    normalized['cost'] = df['lineItem/UnblendedCost']
    
    # 4. Flatten and Standardize Tags
    normalized['normalized_env'] = df['resourceTags/user:Environment'].str.lower().fillna('unknown')
    normalized['normalized_team'] = df['resourceTags/user:Team'].str.lower().fillna('unknown')
    
    # Carry over ground truth evaluation labels
    normalized['is_anomaly'] = df['is_anomaly']
    normalized['anomaly_type'] = df['anomaly_type']
    
    return normalized

def normalize_gcp(file_path):
    """Transforms raw GCP data into the canonical schema."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Missing file: {file_path}")
        
    df = pd.read_csv(file_path)
    
    normalized = pd.DataFrame()
    normalized['timestamp'] = pd.to_datetime(df['usage_start_time'])
    normalized['cloud_provider'] = 'GCP'
    
    service_map = {
        'Compute Engine': 'COMPUTE',
        'Cloud Storage': 'STORAGE',
        'Cloud Network': 'NETWORK'
    }
    normalized['unified_category'] = df['service/description'].map(service_map).fillna('OTHER')
    normalized['cost'] = df['cost']
    
    normalized['normalized_env'] = df['labels/env'].str.lower().fillna('unknown')
    normalized['normalized_team'] = df['labels/owner'].str.lower().fillna('unknown')
    
    normalized['is_anomaly'] = df['is_anomaly']
    normalized['anomaly_type'] = df['anomaly_type']
    
    return normalized

def normalize_azure(file_path):
    """Transforms raw Azure data into the canonical schema and parses embedded JSON strings."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Missing file: {file_path}")
        
    df = pd.read_csv(file_path)
    
    normalized = pd.DataFrame()
    normalized['timestamp'] = pd.to_datetime(df['UsageDateTime'])
    normalized['cloud_provider'] = 'Azure'
    
    service_map = {
        'Virtual Machines': 'COMPUTE',
        'Storage': 'STORAGE',
        'Network': 'NETWORK'
    }
    normalized['unified_category'] = df['MeterCategory'].map(service_map).fillna('OTHER')
    normalized['cost'] = df['CostInBillingCurrency']
    
    # Parse Azure's nested JSON tags string
    envs = []
    teams = []
    for tag_str in df['Tags']:
        try:
            tag_dict = json.loads(tag_str)
            envs.append(str(tag_dict.get('env', 'unknown')).lower())
            teams.append(str(tag_dict.get('team', 'unknown')).lower())
        except (json.JSONDecodeError, TypeError):
            envs.append('unknown')
            teams.append('unknown')
            
    normalized['normalized_env'] = envs
    normalized['normalized_team'] = teams
    
    normalized['is_anomaly'] = df['is_anomaly']
    normalized['anomaly_type'] = df['anomaly_type']
    
    return normalized

def run_pipeline():
    """Main execution orchestrator to read, transform, and merge all datasets."""
    print("Beginning multi-cloud cost pipeline normalization...")
    
    aws_clean = normalize_aws("data/raw data/aws_raw_billing.csv")
    gcp_clean = normalize_gcp("data/raw data/gcp_raw_billing.csv")
    azure_clean = normalize_azure("data/raw data/azure_raw_billing.csv")
    
    # Combine everything into a single dataframe
    unified_df = pd.concat([aws_clean, gcp_clean, azure_clean], ignore_index=True)
    
    # Sort chronologically to maintain historical order for downstream time-series engines
    unified_df = unified_df.sort_values(by='timestamp').reset_index(drop=True)
    
    output_filename = "unified_billing.csv"
    unified_df.to_csv(output_filename, index=False)
    print(f"Pipeline complete! Created clean canonical dataset: '{output_filename}' ({len(unified_df)} rows).")

if __name__ == "__main__":
    run_pipeline()