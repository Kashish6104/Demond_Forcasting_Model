import pandas as pd
from prophet import Prophet
import matplotlib.pyplot as plt
import os

# Folder paths
cleaned_data_dir = 'data/processed/'
forecast_dir = 'data/processed/'
plot_dir = 'results/forecast_charts/'

# Create output folders
os.makedirs(forecast_dir, exist_ok=True)
os.makedirs(plot_dir, exist_ok=True)

# Loop through all cleaned CSV files
for file in os.listdir(cleaned_data_dir):
    if file.endswith('_cleaned.csv'):
        product_name = file.replace('_cleaned.csv', '')
        path = os.path.join(cleaned_data_dir, file)
        
        print(f"🔄 Processing: {product_name}")

        # Load and rename columns
        df = pd.read_csv(path)
        df = df.rename(columns={"Date": "ds", "Units_Sold": "y"}) if 'Date' in df.columns else df

        # Convert date column
        df['ds'] = pd.to_datetime(df['ds'])

        # Fit model
        model = Prophet()
        model.fit(df)

        # Forecast
        future = model.make_future_dataframe(periods=30)
        forecast = model.predict(future)

        # Save forecast
        forecast_file = f"{forecast_dir}{product_name}_forecast.csv"
        forecast.to_csv(forecast_file, index=False)

        # Plot
        fig = model.plot(forecast)
        plt.title(f"{product_name.replace('_', ' ').title()} – Forecast (30 Days)")
        fig_path = f"{plot_dir}{product_name}_plot.png"
        fig.savefig(fig_path)
        plt.close()

        print(f"✅ Saved: {forecast_file} and {fig_path}")
