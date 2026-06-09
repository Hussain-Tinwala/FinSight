import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest

def engineer_features(df):
    """
    Transforms raw time-series data into rich tabular features for ML.
    """
    df = df.copy()
    
    # 1. Date Features
    df['day_of_week'] = df['timestamp'].dt.dayofweek
    df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
    
    # We must group by the streams so rolling math doesn't bleed across AWS and GCP
    grouped = df.groupby(['cloud_provider', 'unified_category'])
    
    # 2. Rolling Features
    # We shift by 1 so today's prediction doesn't include today's cost in the baseline
    df['rolling_mean_7d'] = grouped['cost'].transform(
        lambda x: x.shift(1).rolling(window=7, min_periods=1).mean()
    )
    df['rolling_std_7d'] = grouped['cost'].transform(
        lambda x: x.shift(1).rolling(window=7, min_periods=1).std()
    ).fillna(0)
    
    # 3. The "Secret Sauce" Ratio Features
    df['cost_ratio'] = df['cost'] / (df['rolling_mean_7d'] + 1e-5) # Add tiny number to prevent divide-by-zero
    
    # Drop rows where we couldn't calculate rolling features (the very first day)
    return df.fillna(0)

def run_ml_detection():
    print("Loading Tier 1 scored data...")
    df = pd.read_csv("scored_billing.csv")
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    print("Engineering ML features (cost_ratio, day_of_week, rolling means)...")
    df_features = engineer_features(df)
    
    # Prepare output column
    df_features['ml_is_anomaly'] = 0
    
    # The features we want the Isolation Forest to look at
    feature_cols = ['cost', 'cost_ratio', 'day_of_week', 'rolling_std_7d']
    
    grouped = df_features.groupby(['cloud_provider', 'unified_category'])
    
    print("Training and scoring Isolation Forests per service stream...")
    for (provider, category), group in grouped:
        X = group[feature_cols].values
        
        # contamination = 0.05 means we assume roughly 5% of our historical data is anomalous
        model = IsolationForest(contamination=0.05, random_state=42, n_estimators=100)
        
        # Train and predict in one step
        preds = model.fit_predict(X)
        
        # iForest outputs -1 for anomaly, 1 for normal. Let's map it to 1 and 0.
        mapped_preds = np.where(preds == -1, 1, 0)
        
        # Assign predictions back to our main dataframe
        df_features.loc[group.index, 'ml_is_anomaly'] = mapped_preds

    # --- Evaluation ---
    true_anomalies = df_features[df_features['is_anomaly'] == 1]
    
    # Let's see what Tier 1 (Stats) caught vs Tier 2 (ML)
    caught_by_stat = df_features[(df_features['is_anomaly'] == 1) & (df_features['stat_is_anomaly'] == 1)]
    caught_by_ml = df_features[(df_features['is_anomaly'] == 1) & (df_features['ml_is_anomaly'] == 1)]
    
    print("-" * 30)
    print("Tier 2 Detection Results:")
    print(f"Total True Anomalies Injected: {len(true_anomalies)}")
    print(f"Caught by Tier 1 (Z-Score): {len(caught_by_stat)} ({(len(caught_by_stat)/len(true_anomalies))*100:.1f}%)")
    print(f"Caught by Tier 2 (iForest): {len(caught_by_ml)} ({(len(caught_by_ml)/len(true_anomalies))*100:.1f}%)")
    
    # Save for the Deep Learning module
    df_features.to_csv("ml_scored_billing.csv", index=False)
    print("Saved scored dataset to 'ml_scored_billing.csv'")

if __name__ == "__main__":
    run_ml_detection()