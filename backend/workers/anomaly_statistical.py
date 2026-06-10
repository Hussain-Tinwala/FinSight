import pandas as pd
import numpy as np
from statsmodels.tsa.seasonal import STL

def calculate_stl_zscore(series, period=7):
    """
    Decomposes the time series and calculates Z-scores on the residuals.
    """
    # If we have less than two full seasonal periods, we can't reliably use STL
    if len(series) < period * 2:
        return np.zeros(len(series))
        
    # 1. Decompose the series (period=7 for weekly seasonality)
    stl = STL(series, period=period, robust=True)
    result = stl.fit()
    
    # 2. Extract the residual (noise)
    residual = result.resid
    
    # 3. Calculate Z-score of the residual
    # We use expanding/rolling metrics to avoid leaking future data into past predictions
    rolling_mean = residual.rolling(window=14, min_periods=1).mean()
    rolling_std = residual.rolling(window=14, min_periods=1).std()
    
    # Fill NaN std dev with a small number to avoid division by zero
    rolling_std = rolling_std.replace(0, 1e-5).fillna(1e-5)
    
    z_scores = (residual - rolling_mean) / rolling_std
    
    return z_scores.fillna(0)

def run_statistical_detection():
    print("Loading normalized billing data from TimescaleDB (via CSV for this step)...")
    # In a live app, we query TimescaleDB here. For this script, we'll read our unified CSV.
    df = pd.read_csv("unified_billing.csv")
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Sort chronologically to ensure time-series math works
    df = df.sort_values('timestamp').reset_index(drop=True)
    
    # Prepare an output column for our predictions
    df['stat_z_score'] = 0.0
    df['stat_is_anomaly'] = 0
    
    # We must group by cloud_provider AND unified_category
    # (AWS Compute behaves differently than GCP Storage)
    grouped = df.groupby(['cloud_provider', 'unified_category'])
    
    print("Running STL Decomposition and Z-Score analysis per service stream...")
    for (provider, category), group in grouped:
        # We need a daily aggregated series for STL to work cleanly
        daily_series = group.groupby(group['timestamp'].dt.date)['cost'].sum()
        
        # Calculate Z-scores on the residuals
        z_scores = calculate_stl_zscore(daily_series, period=7)
        
        # Map the daily Z-scores back to the original granular dataframe rows
        for date, z in z_scores.items():
            mask = (df['cloud_provider'] == provider) & \
                   (df['unified_category'] == category) & \
                   (df['timestamp'].dt.date == date)
            
            df.loc[mask, 'stat_z_score'] = z
            
            # Flag as anomaly if Z-score > 3 (spike) or < -3 (sudden drop)
            if abs(z) > 3.0:
                df.loc[mask, 'stat_is_anomaly'] = 1

    # Evaluate how well our statistical engine did against the ground truth labels we injected
    true_anomalies = df[df['is_anomaly'] == 1]
    caught_anomalies = df[(df['is_anomaly'] == 1) & (df['stat_is_anomaly'] == 1)]
    
    print("-" * 30)
    print("Tier 1 Detection Results:")
    print(f"Total True Anomalies Injected: {len(true_anomalies)}")
    print(f"Anomalies Caught by STL+Z-Score: {len(caught_anomalies)}")
    print(f"Detection Rate: {(len(caught_anomalies)/len(true_anomalies))*100:.1f}%")
    
    # Save the scored dataset for the next module
    df.to_csv("scored_billing.csv", index=False)
    print("Saved scored dataset to 'scored_billing.csv'")

if __name__ == "__main__":
    run_statistical_detection()