import pandas as pd
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error
import os


def calculate_metrics(actual, predicted):
    mae = mean_absolute_error(actual, predicted)
    rmse = np.sqrt(mean_squared_error(actual, predicted))
    mape = np.mean(np.abs((actual - predicted) / actual)) * 100
    return round(mae, 2), round(rmse, 2), round(mape, 2)

cleaned_dir = 'data/processed/'
forecast_dir = 'data/processed/'

results = []

for file in os.listdir(cleaned_dir):
    if file.endswith('_cleaned.csv'):
        product_name = file.replace('_cleaned.csv', '')
        
        # Load actual and forecast data
        actual_df = pd.read_csv(os.path.join(cleaned_dir, file))
        forecast_df = pd.read_csv(os.path.join(forecast_dir, f"{product_name}_forecast.csv"))

        # Rename if needed
        actual_df = actual_df.rename(columns={"Date": "ds", "Units_Sold": "y"}) if 'Date' in actual_df.columns else actual_df
        actual_df['ds'] = pd.to_datetime(actual_df['ds'])
        forecast_df['ds'] = pd.to_datetime(forecast_df['ds'])

        # Filter forecast to only dates we have actuals for
        common_dates = actual_df['ds'].isin(forecast_df['ds'])
        merged = pd.merge(
            actual_df[common_dates],
            forecast_df[['ds', 'yhat']],
            on='ds',
            how='inner'
        )

        # Compute metrics
        mae, rmse, mape = calculate_metrics(merged['y'], merged['yhat'])
        results.append({
            'Product': product_name.replace('_', ' ').title(),
            'MAE': mae,
            'RMSE': rmse,
            'MAPE (%)': mape
        })
# Convert to DataFrame and save
results_df = pd.DataFrame(results)
os.makedirs('results/tables', exist_ok=True)
results_df.to_csv('results/tables/accuracy_summary.csv', index=False)

print("✅ Evaluation saved to results/tables/accuracy_summary.csv")
results_df.head()
