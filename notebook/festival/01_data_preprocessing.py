import pandas as pd

# Load your main dataset
df = pd.read_csv('data/faviy_dairy_cleaned_extended_with_festivals.csv')
df['date'] = pd.to_datetime(df['Date'])

# Filter festival days
festival_df = df[df['Festival_Flag'] == 1]

# Get unique festival dates and convert to Series
unique_festival_dates = pd.Series(sorted(festival_df['Date'].drop_duplicates()))

# Create festival DataFrame
festivals_csv = pd.DataFrame({
    'holiday': [f'Festival_{i+1}' for i in range(len(unique_festival_dates))],
    'date': unique_festival_dates.dt.strftime('%Y-%m-%d')
})

# Save to CSV
festivals_csv.to_csv('data/festival/festivals.csv', index=False)
print("✅ festivals.csv created successfully!")

