import pandas as pd
import os

df = pd.read_csv('data/faviy_dairy_cleaned_extended_with_festivals.csv')
df["Date"] = pd.to_datetime(df["Date"])

#os.mkdir("data/processed",exist_ok=True)
products = df["Product_Name"].unique()
print("Found Product:",products)

for i in products:
    product_df = df[df["Product_Name"] == i]
    
    daily = product_df.groupby("Date")["Units_Sold"].sum().reset_index()
    daily = daily.sort_values(["Date"])
    
    daily["Units_Sold"]  = daily["Units_Sold"].rolling(window=7,min_periods=1).mean()
    
    prophet_df = daily.rename({
        
        "Date":"ds",
        "Units_Sold" :'y'
    }) 
    
    safe_name = i.lower().replace(" ","_").replace("(","").replace(")","").replace("/","_")
    path = f'data/processed/{safe_name}_cleaned.csv'
    prophet_df.to_csv(path,index=False)
    print(f"✅ {i} → cleaned data saved to {path}")