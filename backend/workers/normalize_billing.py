import pandas as pd
import json
import os

# --- DYNAMIC PATH RESOLUTION ---
WORKER_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(os.path.dirname(WORKER_DIR))
DATA_DIR = os.path.join(ROOT_DIR, "data")
RAW_DATA_DIR = os.path.join(DATA_DIR, "raw_data")

def normalize_aws(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Missing file: {file_path}")
        
    df = pd.read_csv(file_path)
    normalized = pd.DataFrame()
    normalized['timestamp'] = pd.to_datetime(df['lineItem/UsageStartDate'])
    normalized['cloud_provider'] = 'AWS'
    
    service_map = {'AmazonEC2': 'COMPUTE', 'AmazonStorage': 'STORAGE', 'AmazonNetwork': 'NETWORK'}
    normalized['unified_category'] = df['productCode'].map(service_map).fillna('OTHER')
    normalized['cost'] = df['lineItem/UnblendedCost']
    normalized['normalized_env'] = df['resourceTags/user:Environment'].str.lower().fillna('unknown')
    normalized['normalized_team'] = df['resourceTags/user:Team'].str.lower().fillna('unknown')
    normalized['is_anomaly'] = df['is_anomaly']
    normalized['anomaly_type'] = df['anomaly_type']
    
    return normalized

def normalize_gcp(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Missing file: {file_path}")
        
    df = pd.read_csv(file_path)
    normalized = pd.DataFrame()
    normalized['timestamp'] = pd.to_datetime(df['usage_start_time'])
    normalized['cloud_provider'] = 'GCP'
    
    service_map = {'Compute Engine': 'COMPUTE', 'Cloud Storage': 'STORAGE', 'Cloud Network': 'NETWORK'}
    normalized['unified_category'] = df['service/description'].map(service_map).fillna('OTHER')
    normalized['cost'] = df['cost']
    normalized['normalized_env'] = df['labels/env'].str.lower().fillna('unknown')
    normalized['normalized_team'] = df['labels/owner'].str.lower().fillna('unknown')
    normalized['is_anomaly'] = df['is_anomaly']
    normalized['anomaly_type'] = df['anomaly_type']
    
    return normalized

def normalize_azure(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Missing file: {file_path}")
        
    df = pd.read_csv(file_path)
    normalized = pd.DataFrame()
    normalized['timestamp'] = pd.to_datetime(df['UsageDateTime'])
    normalized['cloud_provider'] = 'Azure'
    
    service_map = {'Virtual Machines': 'COMPUTE', 'Storage': 'STORAGE', 'Network': 'NETWORK'}
    normalized['unified_category'] = df['MeterCategory'].map(service_map).fillna('OTHER')
    normalized['cost'] = df['CostInBillingCurrency']
    
    envs, teams = [], []
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
    print("Beginning multi-cloud cost pipeline normalization...")
    
    aws_clean = normalize_aws(os.path.join(RAW_DATA_DIR, "aws_raw_billing.csv"))
    gcp_clean = normalize_gcp(os.path.join(RAW_DATA_DIR, "gcp_raw_billing.csv"))
    azure_clean = normalize_azure(os.path.join(RAW_DATA_DIR, "azure_raw_billing.csv"))
    
    unified_df = pd.concat([aws_clean, gcp_clean, azure_clean], ignore_index=True)
    unified_df = unified_df.sort_values(by='timestamp').reset_index(drop=True)
    
    output_path = os.path.join(DATA_DIR, "unified_billing.csv")
    unified_df.to_csv(output_path, index=False)
    print(f"Pipeline complete! Created clean canonical dataset: '{output_path}' ({len(unified_df)} rows).")

if __name__ == "__main__":
    run_pipeline()