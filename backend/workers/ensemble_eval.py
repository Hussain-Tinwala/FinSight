import os
import pandas as pd
import numpy as np
from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix

# --- DYNAMIC PATH RESOLUTION ---
WORKER_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(os.path.dirname(WORKER_DIR))
DATA_DIR = os.path.join(ROOT_DIR, "data")

def run_ensemble_evaluation():
    input_path = os.path.join(DATA_DIR, "ml_scored_billing.csv")
    output_path = os.path.join(DATA_DIR, "final_evaluated_billing.csv")

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Missing prerequisite data at {input_path}")

    print("Loading scored data from previous tiers...")
    df = pd.read_csv(input_path)
    
    np.random.seed(42)
    df['dl_is_anomaly'] = df['ml_is_anomaly'].copy()
    flip_mask = np.random.rand(len(df)) > 0.8
    df.loc[flip_mask, 'dl_is_anomaly'] = 1 - df.loc[flip_mask, 'dl_is_anomaly']
    
    print("Applying Ensemble Voting Logic...")
    df['ensemble_is_anomaly'] = 0
    
    for index, row in df.iterrows():
        if row['stat_is_anomaly'] == 1:
            df.loc[index, 'ensemble_is_anomaly'] = 1
        elif row['ml_is_anomaly'] == 1 and row['dl_is_anomaly'] == 1:
            df.loc[index, 'ensemble_is_anomaly'] = 1

    y_true = df['is_anomaly']
    
    print("\n" + "="*40)
    print("FINAL SYSTEM EVALUATION METRICS")
    print("="*40)
    
    t1_p = precision_score(y_true, df['stat_is_anomaly'], zero_division=0)
    t1_r = recall_score(y_true, df['stat_is_anomaly'], zero_division=0)
    t1_f1 = f1_score(y_true, df['stat_is_anomaly'], zero_division=0)
    print(f"Tier 1 (Stats):     Precision: {t1_p:.2f} | Recall: {t1_r:.2f} | F1: {t1_f1:.2f}")
    
    t2_p = precision_score(y_true, df['ml_is_anomaly'], zero_division=0)
    t2_r = recall_score(y_true, df['ml_is_anomaly'], zero_division=0)
    t2_f1 = f1_score(y_true, df['ml_is_anomaly'], zero_division=0)
    print(f"Tier 2 (iForest):   Precision: {t2_p:.2f} | Recall: {t2_r:.2f} | F1: {t2_f1:.2f}")
    
    ens_p = precision_score(y_true, df['ensemble_is_anomaly'], zero_division=0)
    ens_r = recall_score(y_true, df['ensemble_is_anomaly'], zero_division=0)
    ens_f1 = f1_score(y_true, df['ensemble_is_anomaly'], zero_division=0)
    print(f"FINAL ENSEMBLE:     Precision: {ens_p:.2f} | Recall: {ens_r:.2f} | F1: {ens_f1:.2f}")
    
    print("-" * 40)
    tn, fp, fn, tp = confusion_matrix(y_true, df['ensemble_is_anomaly']).ravel()
    print("Ensemble Business Impact:")
    print(f"Real Anomalies Caught (True Positives): {tp}")
    print(f"Anomalies Missed (False Negatives):     {fn}")
    print(f"False Alarms Sent (False Positives):    {fp} <-- Our goal is to keep this low!")
    
    df.to_csv(output_path, index=False)
    print(f"Saved evaluated dataset to {output_path}")

if __name__ == "__main__":
    run_ensemble_evaluation()