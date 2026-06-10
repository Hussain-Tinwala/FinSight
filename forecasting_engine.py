import pandas as pd
import numpy as np
from prophet import Prophet
import lightgbm as lgb
import warnings
warnings.filterwarnings('ignore')

def prepare_forecast_data():
    """Loads our final evaluated dataset and prepares it for the models."""
    df = pd.read_csv("final_evaluated_billing.csv")
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Let's isolate AWS COMPUTE for this R&D forecasting module
    df_stream = df[(df['cloud_provider'] == 'AWS') & (df['unified_category'] == 'COMPUTE')].copy()
    
    # Aggregate to daily intervals since forecasting 90 days out hourly is massive overkill
    daily_df = df_stream.groupby(df_stream['timestamp'].dt.date).agg({
        'cost': 'sum',
        'is_anomaly': 'max' # keep track if an anomaly happened that day
    }).reset_index()
    
    daily_df.columns = ['date', 'cost', 'had_anomaly']
    daily_df['date'] = pd.to_datetime(daily_df['date'])
    daily_df = daily_df.sort_values('date').reset_index(drop=True)
    
    # CRITICAL FINOPS TRICK: Clean historical anomalies before forecasting!
    # If we leave a massive $5,000 accidental spike in the history, Prophet will think 
    # that spike is part of our normal trajectory and ruin the future forecast.
    daily_df['cleaned_cost'] = daily_df['cost']
    # Smooth out anomalous days by replacing them with a rolling median
    rolling_median = daily_df['cost'].rolling(window=7, min_periods=1, center=True).median()
    daily_df.loc[daily_df['had_anomaly'] == 1, 'cleaned_cost'] = rolling_median
    
    return daily_df

def run_prophet_forecast(train_df, horizon=90):
    """Trains Meta Prophet and predicts into the future with confidence intervals."""
    # Prophet strictly requires columns to be named 'ds' (datestamp) and 'y' (target value)
    prophet_df = train_df[['date', 'cleaned_cost']].rename(columns={'date': 'ds', 'cleaned_cost': 'y'})
    
    # Initialize Prophet with a 90% confidence interval width
    model = Prophet(
        yearly_seasonality=False, 
        weekly_seasonality=True, 
        daily_seasonality=False,
        interval_width=0.90,
        changepoint_prior_scale=0.05 # Controls trend flexibility
    )
    model.fit(prophet_df)
    
    # Create empty dataframe stretching 'horizon' days into the future
    future = model.make_future_dataframe(periods=horizon, freq='D')
    forecast = model.predict(future)
    
    # Extract the columns we care about
    result = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].rename(columns={
        'ds': 'date',
        'yhat': 'prophet_forecast',
        'yhat_lower': 'prophet_lower',
        'yhat_upper': 'prophet_upper'
    })
    return result

def run_lightgbm_forecast(train_df, horizon=90):
    """Engineers lag features and projects future spend using LightGBM."""
    df = train_df.copy()
    
    # Create time-series lag features (What did it cost 1 day ago? 7 days ago?)
    df['lag_1'] = df['cleaned_cost'].shift(1)
    df['lag_7'] = df['cleaned_cost'].shift(7)
    df['lag_14'] = df['cleaned_cost'].shift(14)
    
    # Create rolling statistical features
    df['rolling_mean_7'] = df['cleaned_cost'].shift(1).rolling(7).mean()
    df['day_of_week'] = df['date'].dt.dayofweek
    
    # Drop rows with NaN caused by shifting
    features_df = df.dropna().reset_index(drop=True)
    
    feature_cols = ['lag_1', 'lag_7', 'lag_14', 'rolling_mean_7', 'day_of_week']
    X_train = features_df[feature_cols]
    y_train = features_df['cleaned_cost']
    
    # Train the Gradient Boosting Regressor
    model = lgb.LGBMRegressor(n_estimators=50, max_depth=5, learning_rate=0.05, random_state=42)
    model.fit(X_train, y_train)
    
    # To forecast multi-horizon recursively, we must step forward day-by-day
    last_known_date = df['date'].max()
    future_rows = []
    
    # Work with a mutable copy of the underlying dataframe to iteratively calculate lags
    working_df = df.copy()
    
    print(f"Recursively building LightGBM predictions out to {horizon} days...")
    for step in range(1, horizon + 1):
        next_date = last_known_date + pd.Timedelta(days=step)
        
        # Build the feature vector for this future day based on previous predictions
        lag_1 = working_df.iloc[-1]['cleaned_cost']
        lag_7 = working_df.iloc[-7]['cleaned_cost'] if len(working_df) >= 7 else lag_1
        lag_14 = working_df.iloc[-14]['cleaned_cost'] if len(working_df) >= 14 else lag_1
        rolling_mean_7 = working_df.iloc[-7:]['cleaned_cost'].mean()
        day_of_week = next_date.dayofweek
        
        X_next = np.array([[lag_1, lag_7, lag_14, rolling_mean_7, day_of_week]])
        pred_cost = model.predict(X_next)[0]
        
        # Append the prediction into our working dataframe so the NEXT step can use it as a lag!
        new_row = pd.DataFrame([{
            'date': next_date, 
            'cost': pred_cost, 
            'cleaned_cost': pred_cost, 
            'had_anomaly': 0
        }])
        working_df = pd.concat([working_df, new_row], ignore_index=True)
        
        future_rows.append({
            'date': next_date,
            'lgb_forecast': max(0, pred_cost)
        })
        
    return pd.DataFrame(future_rows)

if __name__ == "__main__":
    print("Preparing clean historical time-series data...")
    daily_billing = prepare_forecast_data()
    
    print("\nExecuting Model A: Meta Prophet...")
    prophet_results = run_prophet_forecast(daily_billing, horizon=90)
    
    print("\nExecuting Model B: LightGBM Regressor...")
    lgb_results = run_lightgbm_forecast(daily_billing, horizon=90)
    
    # Merge results together for comparative inspection
    final_forecast = pd.merge(prophet_results, lgb_results, on='date', how='left')
    
    print("\n" + "="*50)
    print("MULTI-HORIZON FORECAST ENGINE PREVIEW (AWS COMPUTE)")
    print("="*50)
    
    # Let's inspect tactical horizons
    for horizon in [7, 30, 90]:
        target_date = daily_billing['date'].max() + pd.Timedelta(days=horizon)
        row = final_forecast[final_forecast['date'] == target_date].iloc[0]
        print(f"\nHorizon: {horizon}-Day Lookahead (Target Date: {target_date.strftime('%Y-%m-%d')})")
        print(f" -> Prophet Prediction: ${row['prophet_forecast']:.2f} (Range: ${row['prophet_lower']:.2f} - ${row['prophet_upper']:.2f})")
        print(f" -> LightGBM Prediction: ${row['lgb_forecast']:.2f}")