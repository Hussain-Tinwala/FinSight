import pandas as pd
import numpy as np
from prophet import Prophet
import lightgbm as lgb
import warnings

# Suppress Prophet logs for clean terminal output
warnings.filterwarnings("ignore")

def calculate_wmape(y_true, y_pred):
    """Calculates Weighted Mean Absolute Percentage Error."""
    sum_abs_error = np.sum(np.abs(y_true - y_pred))
    sum_actuals = np.sum(np.abs(y_true))
    if sum_actuals == 0:
        return 0.0
    return sum_abs_error / sum_actuals

def prepare_data_for_routing(file_path="final_evaluated_billing.csv"):
    """Loads and pre-cleans historical anomalies via rolling median."""
    df = pd.read_csv(file_path)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Isolate a single stream for the module (AWS Compute)
    df_stream = df[(df['cloud_provider'] == 'AWS') & (df['unified_category'] == 'COMPUTE')].copy()
    daily_df = df_stream.groupby(df_stream['timestamp'].dt.date).agg({'cost': 'sum', 'is_anomaly': 'max'}).reset_index()
    daily_df.columns = ['date', 'cost', 'had_anomaly']
    daily_df['date'] = pd.to_datetime(daily_df['date'])
    daily_df = daily_df.sort_values('date').reset_index(drop=True)
    
    # Pre-clean known anomalies so they don't skew the forecast
    daily_df['cleaned_cost'] = daily_df['cost']
    rolling_median = daily_df['cost'].rolling(window=7, min_periods=1, center=True).median()
    daily_df.loc[daily_df['had_anomaly'] == 1, 'cleaned_cost'] = rolling_median
    
    return daily_df

def backtest_models(df, validation_days=30):
    """Executes the Sliding Window Backtest to determine the best model."""
    split_idx = len(df) - validation_days
    train_df = df.iloc[:split_idx].copy()
    val_df = df.iloc[split_idx:].copy()
    
    # --- Prophet Backtest ---
    prophet_train = train_df[['date', 'cleaned_cost']].rename(columns={'date': 'ds', 'cleaned_cost': 'y'})
    m_prophet = Prophet(yearly_seasonality=False, weekly_seasonality=True, daily_seasonality=False)
    m_prophet.fit(prophet_train)
    future = m_prophet.make_future_dataframe(periods=validation_days, freq='D')
    prophet_forecast = m_prophet.predict(future)
    prophet_preds = prophet_forecast['yhat'].iloc[-validation_days:].values
    prophet_wmape = calculate_wmape(val_df['cleaned_cost'].values, prophet_preds)
    
    # --- LightGBM Backtest ---
    lgb_df = train_df.copy()
    lgb_df['lag_1'] = lgb_df['cleaned_cost'].shift(1)
    lgb_df['lag_7'] = lgb_df['cleaned_cost'].shift(7)
    lgb_df['rolling_mean_7'] = lgb_df['cleaned_cost'].shift(1).rolling(7).mean()
    lgb_df['day_of_week'] = lgb_df['date'].dt.dayofweek
    lgb_train = lgb_df.dropna().reset_index(drop=True)
    
    m_lgb = lgb.LGBMRegressor(n_estimators=50, max_depth=5, learning_rate=0.05, random_state=42)
    feature_cols = ['lag_1', 'lag_7', 'rolling_mean_7', 'day_of_week']
    m_lgb.fit(lgb_train[feature_cols], lgb_train['cleaned_cost'])
    
    # Walk-forward validation for LGBM
    lgb_preds = []
    working_df = train_df.copy()
    for step in range(validation_days):
        next_date = val_df['date'].iloc[step]
        lag_1 = working_df.iloc[-1]['cleaned_cost']
        lag_7 = working_df.iloc[-7]['cleaned_cost'] if len(working_df) >= 7 else lag_1
        rolling_mean_7 = working_df.iloc[-7:]['cleaned_cost'].mean()
        
        pred = m_lgb.predict(np.array([[lag_1, lag_7, rolling_mean_7, next_date.dayofweek]]))[0]
        lgb_preds.append(pred)
        new_row = pd.DataFrame([{'date': next_date, 'cleaned_cost': pred}])
        working_df = pd.concat([working_df, new_row], ignore_index=True)
        
    lgb_wmape = calculate_wmape(val_df['cleaned_cost'].values, np.array(lgb_preds))
    
    return prophet_wmape, lgb_wmape

def generate_production_forecast(df, best_model, horizon=90):
    """Retrains the winning model on ALL data and generates the future forecast."""
    forecast_rows = []
    
    if best_model == 'Prophet':
        prophet_df = df[['date', 'cleaned_cost']].rename(columns={'date': 'ds', 'cleaned_cost': 'y'})
        m = Prophet(yearly_seasonality=False, weekly_seasonality=True, interval_width=0.90)
        m.fit(prophet_df)
        future = m.make_future_dataframe(periods=horizon, freq='D')
        forecast = m.predict(future)
        
        for idx, row in forecast.iloc[-horizon:].iterrows():
            forecast_rows.append({
                'date': row['ds'],
                'predicted_cost': max(0, row['yhat']),
                'lower_bound': max(0, row['yhat_lower']),
                'upper_bound': max(0, row['yhat_upper']),
                'model_used': 'Prophet'
            })
            
    else:  # LightGBM
        # Calculate historical residuals for manual confidence intervals
        df['lag_1'] = df['cleaned_cost'].shift(1)
        df['lag_7'] = df['cleaned_cost'].shift(7)
        df['rolling_mean_7'] = df['cleaned_cost'].shift(1).rolling(7).mean()
        df['day_of_week'] = df['date'].dt.dayofweek
        lgb_train = df.dropna().reset_index(drop=True)
        
        m = lgb.LGBMRegressor(n_estimators=50, max_depth=5, learning_rate=0.05, random_state=42)
        feature_cols = ['lag_1', 'lag_7', 'rolling_mean_7', 'day_of_week']
        m.fit(lgb_train[feature_cols], lgb_train['cleaned_cost'])
        
        # Calculate residual standard deviation for bounds
        train_preds = m.predict(lgb_train[feature_cols])
        residual_std = np.std(lgb_train['cleaned_cost'] - train_preds)
        
        working_df = df.copy()
        last_date = df['date'].max()
        
        for step in range(1, horizon + 1):
            next_date = last_date + pd.Timedelta(days=step)
            lag_1 = working_df.iloc[-1]['cleaned_cost']
            lag_7 = working_df.iloc[-7]['cleaned_cost']
            rolling_mean_7 = working_df.iloc[-7:]['cleaned_cost'].mean()
            
            pred = m.predict(np.array([[lag_1, lag_7, rolling_mean_7, next_date.dayofweek]]))[0]
            new_row = pd.DataFrame([{'date': next_date, 'cleaned_cost': pred}])
            working_df = pd.concat([working_df, new_row], ignore_index=True)
            
            forecast_rows.append({
                'date': next_date,
                'predicted_cost': max(0, pred),
                'lower_bound': max(0, pred - (1.645 * residual_std)), # ~90% confidence interval
                'upper_bound': max(0, pred + (1.645 * residual_std)),
                'model_used': 'LightGBM'
            })
            
    return pd.DataFrame(forecast_rows)

if __name__ == "__main__":
    print("--- Starting FinOps Ensemble Routing ---")
    df = prepare_data_for_routing()
    
    print("1. Running Sliding Window Backtest (Last 30 Days)...")
    prophet_err, lgb_err = backtest_models(df, validation_days=30)
    
    print(f"   -> Prophet WMAPE:  {prophet_err:.2%}")
    print(f"   -> LightGBM WMAPE: {lgb_err:.2%}")
    
    best_model = 'Prophet' if prophet_err < lgb_err else 'LightGBM'
    print(f"2. Routing Decision: {best_model} selected.")
    
    print("3. Generating 90-Day Production Forecast...")
    final_forecast_df = generate_production_forecast(df, best_model, horizon=90)
    
    final_forecast_df.to_csv("production_forecast.csv", index=False)
    print("--- Success: forecast saved to production_forecast.csv ---")