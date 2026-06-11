import os
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest

# --- DYNAMIC PATH RESOLUTION ---
WORKER_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(os.path.dirname(WORKER_DIR))
DATA_DIR = os.path.join(ROOT_DIR, "data")

def engineer_features(df):
    """Transforms raw time-series data into rich tabular features for ML."""
    df = df.copy()
    
    df['day_of_week'] = df['timestamp'].dt.dayofweek
    df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
    
    grouped = df.groupby(['cloud_provider', 'unified_category'])
    
    df['rolling_mean_7d'] = grouped['cost'].transform(
        lambda x: x.shift(1).rolling(window=7, min_periods=1).mean()
    )
    df['rolling_std_7d'] = grouped['cost'].transform(
        lambda x: x.shift(1).rolling(window=7, min_periods=1).std()
    ).fillna(0)
    
    df['cost_ratio'] = df['cost'] / (df['rolling_mean_7d'] + 1e-5) 
    
    return df.fillna(0)

def run_ml_detection():
    # Safely resolve absolute paths
    input_path = os.path.join(DATA_DIR, "scored_billing.csv")
    output_path = os.path.join(DATA_DIR, "ml_scored_billing.csv")

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Missing prerequisite data at {input_path}")

    print("Loading Tier 1 scored data...")
    df = pd.read_csv(input_path)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    print("Engineering ML features (cost_ratio, day_of_week, rolling means)...")
    df_features = engineer_features(df)
    
    df_features['ml_is_anomaly'] = 0
    feature_cols = ['cost', 'cost_ratio', 'day_of_week', 'rolling_std_7d']
    
    grouped = df_features.groupby(['cloud_provider', 'unified_category'])
    
    print("Training and scoring Isolation Forests per service stream...")
    for (provider, category), group in grouped:
        X = group[feature_cols].values
        model = IsolationForest(contamination=0.05, random_state=42, n_estimators=100)
        preds = model.fit_predict(X)
        mapped_preds = np.where(preds == -1, 1, 0)
        df_features.loc[group.index, 'ml_is_anomaly'] = mapped_preds

    true_anomalies = df_features[df_features['is_anomaly'] == 1]
    caught_by_stat = df_features[(df_features['is_anomaly'] == 1) & (df_features['stat_is_anomaly'] == 1)]
    caught_by_ml = df_features[(df_features['is_anomaly'] == 1) & (df_features['ml_is_anomaly'] == 1)]
    
    print("-" * 30)
    print("Tier 2 Detection Results:")
    print(f"Total True Anomalies Injected: {len(true_anomalies)}")
    print(f"Caught by Tier 1 (Z-Score): {len(caught_by_stat)} ({(len(caught_by_stat)/max(1, len(true_anomalies)))*100:.1f}%)")
    print(f"Caught by Tier 2 (iForest): {len(caught_by_ml)} ({(len(caught_by_ml)/max(1, len(true_anomalies)))*100:.1f}%)")
    
    df_features.to_csv(output_path, index=False)
    print(f"Saved scored dataset to {output_path}")

if __name__ == "__main__":
    run_ml_detection()