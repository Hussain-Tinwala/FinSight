import os
import pandas as pd
import numpy as np
from statsmodels.tsa.seasonal import STL

# --- DYNAMIC PATH RESOLUTION ---
WORKER_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(os.path.dirname(WORKER_DIR))
DATA_DIR = os.path.join(ROOT_DIR, "data")

def calculate_stl_zscore(series, period=7):
    """Decomposes the time series and calculates Z-scores on the residuals."""
    if len(series) < period * 2:
        return np.zeros(len(series))
        
    stl = STL(series, period=period, robust=True)
    result = stl.fit()
    residual = result.resid
    
    rolling_mean = residual.rolling(window=14, min_periods=1).mean()
    rolling_std = residual.rolling(window=14, min_periods=1).std()
    rolling_std = rolling_std.replace(0, 1e-5).fillna(1e-5)
    z_scores = (residual - rolling_mean) / rolling_std
    
    return z_scores.fillna(0)

def run_statistical_detection():
    input_path = os.path.join(DATA_DIR, "unified_billing.csv")
    output_path = os.path.join(DATA_DIR, "scored_billing.csv")

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Missing prerequisite data at {input_path}")

    print("Loading normalized billing data...")
    df = pd.read_csv(input_path)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp').reset_index(drop=True)
    
    df['stat_z_score'] = 0.0
    df['stat_is_anomaly'] = 0
    grouped = df.groupby(['cloud_provider', 'unified_category'])
    
    print("Running STL Decomposition and Z-Score analysis per service stream...")
    for (provider, category), group in grouped:
        daily_series = group.groupby(group['timestamp'].dt.date)['cost'].sum()
        z_scores = calculate_stl_zscore(daily_series, period=7)
        
        for date, z in z_scores.items():
            mask = (df['cloud_provider'] == provider) & \
                   (df['unified_category'] == category) & \
                   (df['timestamp'].dt.date == date)
            
            df.loc[mask, 'stat_z_score'] = z
            if abs(z) > 3.0:
                df.loc[mask, 'stat_is_anomaly'] = 1

    true_anomalies = df[df['is_anomaly'] == 1]
    caught_anomalies = df[(df['is_anomaly'] == 1) & (df['stat_is_anomaly'] == 1)]
    
    print("-" * 30)
    print("Tier 1 Detection Results:")
    print(f"Total True Anomalies Injected: {len(true_anomalies)}")
    print(f"Anomalies Caught by STL+Z-Score: {len(caught_anomalies)}")
    print(f"Detection Rate: {(len(caught_anomalies)/max(1, len(true_anomalies)))*100:.1f}%")
    
    df.to_csv(output_path, index=False)
    print(f"Saved scored dataset to {output_path}")

if __name__ == "__main__":
    run_statistical_detection()