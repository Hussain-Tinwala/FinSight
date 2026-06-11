import os
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
from sklearn.preprocessing import MinMaxScaler
from torch.utils.data import DataLoader, TensorDataset

# --- DYNAMIC PATH RESOLUTION ---
WORKER_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(os.path.dirname(WORKER_DIR))
DATA_DIR = os.path.join(ROOT_DIR, "data")

torch.manual_seed(42)
np.random.seed(42)

def create_sequences(data, seq_length):
    xs = []
    for i in range(len(data) - seq_length):
        x = data[i:(i + seq_length)]
        xs.append(x)
    return np.array(xs)

class LSTMAutoencoder(nn.Module):
    def __init__(self, n_features, hidden_dim=16):
        super(LSTMAutoencoder, self).__init__()
        self.n_features = n_features
        self.hidden_dim = hidden_dim
        
        self.encoder = nn.LSTM(input_size=n_features, hidden_size=hidden_dim, num_layers=1, batch_first=True)
        self.decoder = nn.LSTM(input_size=hidden_dim, hidden_size=hidden_dim, num_layers=1, batch_first=True)
        self.output_layer = nn.Linear(hidden_dim, n_features)

    def forward(self, x):
        _, (hidden, _) = self.encoder(x) 
        hidden = hidden[-1].unsqueeze(1).repeat(1, x.shape[1], 1)
        decoded, _ = self.decoder(hidden)
        reconstructed = self.output_layer(decoded)
        return reconstructed

def run_deep_learning_detection():
    # Safely resolve absolute path
    input_path = os.path.join(DATA_DIR, "ml_scored_billing.csv")
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Missing prerequisite data at {input_path}")

    print("Loading ML-scored data...")
    df = pd.read_csv(input_path)
    
    df_aws = df[(df['cloud_provider'] == 'AWS') & (df['unified_category'] == 'COMPUTE')].copy()
    df_aws = df_aws.sort_values('timestamp').reset_index(drop=True)
    
    features_to_scale = ['cost', 'cost_ratio', 'rolling_mean_7d']
    scaler = MinMaxScaler()
    df_aws[features_to_scale] = scaler.fit_transform(df_aws[features_to_scale])
    
    clean_data_mask = df_aws['is_anomaly'] == 0
    train_data = df_aws.loc[clean_data_mask, features_to_scale].values
    
    SEQ_LEN = 14
    X_train = create_sequences(train_data, SEQ_LEN)
    X_train_tensor = torch.FloatTensor(X_train)
    
    full_data = df_aws[features_to_scale].values
    X_full = create_sequences(full_data, SEQ_LEN)
    X_full_tensor = torch.FloatTensor(X_full)

    model = LSTMAutoencoder(n_features=len(features_to_scale), hidden_dim=8)
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
    
    print("Training LSTM Autoencoder (this will take a few seconds)...")
    epochs = 50
    model.train()
    for epoch in range(epochs):
        optimizer.zero_grad()
        output = model(X_train_tensor)
        loss = criterion(output, X_train_tensor) 
        loss.backward()
        optimizer.step()
        if (epoch+1) % 10 == 0:
            print(f"Epoch [{epoch+1}/{epochs}], Loss (MSE): {loss.item():.4f}")

    print("Scoring production data (Reconstruction Error)...")
    model.eval()
    with torch.no_grad():
        reconstructed = model(X_full_tensor)
        mse_scores = torch.mean((reconstructed - X_full_tensor)**2, dim=[1, 2]).numpy()
    
    padding = np.zeros(SEQ_LEN)
    full_mse_scores = np.concatenate([padding, mse_scores])
    df_aws['dl_mse_score'] = full_mse_scores
    
    threshold = np.percentile(mse_scores, 95)
    df_aws['dl_is_anomaly'] = (df_aws['dl_mse_score'] > threshold).astype(int)
    
    true_anomalies = df_aws[df_aws['is_anomaly'] == 1]
    caught = df_aws[(df_aws['is_anomaly'] == 1) & (df_aws['dl_is_anomaly'] == 1)]
    
    print("-" * 30)
    print("Tier 3 (Deep Learning) Detection Results for AWS COMPUTE:")
    print(f"MSE Anomaly Threshold chosen: {threshold:.4f}")
    print(f"Total True Anomalies Injected: {len(true_anomalies)}")
    print(f"Caught by Tier 3 (LSTM): {len(caught)} ({(len(caught)/max(1, len(true_anomalies)))*100:.1f}%)")

if __name__ == "__main__":
    run_deep_learning_detection()