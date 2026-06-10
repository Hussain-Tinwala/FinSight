import pandas as pd
import numpy as np
from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix

def run_ensemble_evaluation():
    print("Loading scored data from previous tiers...")
    df = pd.read_csv("ml_scored_billing.csv")
    
    # For demonstration, let's simulate the Tier 3 (LSTM) vote. 
    # In production, this would be loaded from your PyTorch inference pipeline.
    # We'll assume the LSTM agrees with the iForest 80% of the time.
    np.random.seed(42)
    df['dl_is_anomaly'] = df['ml_is_anomaly'].copy()
    flip_mask = np.random.rand(len(df)) > 0.8
    df.loc[flip_mask, 'dl_is_anomaly'] = 1 - df.loc[flip_mask, 'dl_is_anomaly']
    
    # --- The Ensemble Routing Logic ---
    print("Applying Ensemble Voting Logic...")
    
    # Start with assuming everything is normal
    df['ensemble_is_anomaly'] = 0
    
    for index, row in df.iterrows():
        # Condition 1: The "Spike Override"
        # If Tier 1 (Stats) catches it, we almost always trust it. Stats rarely hallucinate sudden spikes.
        if row['stat_is_anomaly'] == 1:
            df.loc[index, 'ensemble_is_anomaly'] = 1
            
        # Condition 2: The "Subtle Consensus"
        # If Tier 1 missed it (because it's a slow drift), we require BOTH advanced ML models 
        # to agree it's an anomaly before we wake up an engineer.
        elif row['ml_is_anomaly'] == 1 and row['dl_is_anomaly'] == 1:
            df.loc[index, 'ensemble_is_anomaly'] = 1

    # --- Evaluation ---
    y_true = df['is_anomaly']
    
    print("\n" + "="*40)
    print("FINAL SYSTEM EVALUATION METRICS")
    print("="*40)
    
    # Evaluate Tier 1 (Stats Only)
    t1_p = precision_score(y_true, df['stat_is_anomaly'], zero_division=0)
    t1_r = recall_score(y_true, df['stat_is_anomaly'], zero_division=0)
    t1_f1 = f1_score(y_true, df['stat_is_anomaly'], zero_division=0)
    print(f"Tier 1 (Stats):     Precision: {t1_p:.2f} | Recall: {t1_r:.2f} | F1: {t1_f1:.2f}")
    
    # Evaluate Tier 2 (ML Only)
    t2_p = precision_score(y_true, df['ml_is_anomaly'], zero_division=0)
    t2_r = recall_score(y_true, df['ml_is_anomaly'], zero_division=0)
    t2_f1 = f1_score(y_true, df['ml_is_anomaly'], zero_division=0)
    print(f"Tier 2 (iForest):   Precision: {t2_p:.2f} | Recall: {t2_r:.2f} | F1: {t2_f1:.2f}")
    
    # Evaluate The Ensemble
    ens_p = precision_score(y_true, df['ensemble_is_anomaly'], zero_division=0)
    ens_r = recall_score(y_true, df['ensemble_is_anomaly'], zero_division=0)
    ens_f1 = f1_score(y_true, df['ensemble_is_anomaly'], zero_division=0)
    print(f"FINAL ENSEMBLE:     Precision: {ens_p:.2f} | Recall: {ens_r:.2f} | F1: {ens_f1:.2f}")
    
    print("-" * 40)
    # The Confusion Matrix tells us exactly how many false alarms we sent
    tn, fp, fn, tp = confusion_matrix(y_true, df['ensemble_is_anomaly']).ravel()
    print("Ensemble Business Impact:")
    print(f"Real Anomalies Caught (True Positives): {tp}")
    print(f"Anomalies Missed (False Negatives):     {fn}")
    print(f"False Alarms Sent (False Positives):    {fp} <-- Our goal is to keep this low!")
    
    # Save the final data for our LangGraph Agent later
    df.to_csv("final_evaluated_billing.csv", index=False)

if __name__ == "__main__":
    run_ensemble_evaluation()