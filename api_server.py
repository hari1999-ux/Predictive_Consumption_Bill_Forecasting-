from fastapi import FastAPI
import sqlite3
import pandas as pd
import xgboost as xgb
import warnings

warnings.filterwarnings('ignore')
app = FastAPI(title="Real-Time AI Prediction API")

@app.get("/predict")
def run_prediction():
    conn = sqlite3.connect('utility_data.db')
    df = pd.read_sql("SELECT * FROM customer_billing", conn)
    conn.close()
    
    # Feature Engineering
    customer_baselines = df.groupby('Customer id').agg(
        Hist_Avg_Usage=('Usage value', 'mean'),
        Hist_Avg_Bill=('bill amount', 'mean')
    ).reset_index()

    train_df = pd.merge(df, customer_baselines, on='Customer id')
    train_df['meter_type_encoded'] = train_df['meter type'].apply(lambda x: 0 if x == 'GA' else 1)
    train_df['Seasonal_Month'] = train_df['Month'] % 12
    features = ['Seasonal_Month', 'meter_type_encoded', 'Hist_Avg_Usage']

    X_train = train_df[features]
    y_usage = train_df['Usage value']
    y_bill = train_df['bill amount']

    model_usage = xgb.XGBRegressor(n_estimators=100, learning_rate=0.1, random_state=42)
    model_usage.fit(X_train, y_usage)
    
    model_bill = xgb.XGBRegressor(n_estimators=100, learning_rate=0.1, random_state=42)
    model_bill.fit(X_train, y_bill)

    base_customers = train_df[['Customer id', 'customer acct', 'Customer name', 'meter type', 
                               'meter_type_encoded', 'Hist_Avg_Usage']].drop_duplicates()
    
    all_predictions = []
    
    # Predict 120 months (10 years)
    for future_month in range(13, 133):
        temp_df = base_customers.copy()
        temp_df['Seasonal_Month'] = future_month % 12
        temp_df['Forecast_Year'] = 2025 + ((future_month - 1) // 12)
        
        X_future = temp_df[features]
        temp_df['Predicted_Usage'] = model_usage.predict(X_future).clip(min=0)
        temp_df['Predicted_Bill'] = model_bill.predict(X_future).clip(min=0)
        temp_df['Future_Month_Index'] = future_month
        all_predictions.append(temp_df)
        
    predictions_df = pd.concat(all_predictions, ignore_index=True)

    results = []
    for cid, group in predictions_df.groupby('Customer id'):
        cust_info = group.iloc[0]
        
        # Calculate Next Month Specifics
        next_month_bill = float(group[group['Future_Month_Index'] == 13]['Predicted_Bill'].sum())
        next_month_usage = float(group[group['Future_Month_Index'] == 13]['Predicted_Usage'].sum())
        
        customer_record = {
            "Customer id": str(cust_info['Customer id']),
            "Customer name": str(cust_info['Customer name']),
            "Meter Type": str(cust_info['meter type']),
            "Next Month Usage": round(next_month_usage, 2),
            "Next Month Bill": round(next_month_bill, 2)
        }
        
        # Aggregate Usage and Bill for years 2026 to 2035
        for yr in range(2026, 2036):
            yr_bill = float(group[group['Forecast_Year'] == yr]['Predicted_Bill'].sum())
            yr_usage = float(group[group['Forecast_Year'] == yr]['Predicted_Usage'].sum())
            customer_record[f"{yr} Usage"] = round(yr_usage, 2)
            customer_record[f"{yr} Bill"] = round(yr_bill, 2)
            
        results.append(customer_record)
        
    return results