import pandas as pd
import os

# Create Data directory if it doesn't exist
os.makedirs('Data', exist_ok=True)

# Load the original CSV file, specifying 'HUSMERKING' and 'SVFNR' as string columns
df = pd.read_csv('https://fasteignaskra.is/Stadfangaskra.csv', dtype={'HUSMERKING': 'string', 'SVFNR': 'string'})

# Select the desired columns for part a
selected_columns_df_a = df[['SVFNR', 'POSTNR', 'HEITI_NF', 'HEITI_TGF', 'HUSMERKING']].copy()

# Attempt to fill blank HEITI_TGF based on other entries for the same street and postal code for part a
selected_columns_df_a['HEITI_TGF'] = selected_columns_df_a.groupby(['POSTNR', 'HEITI_NF'])['HEITI_TGF'].transform(lambda x: x.fillna(x.dropna().iloc[0]) if not x.dropna().empty else x)


# Save the new DataFrame to a CSV file for part a
selected_columns_df_a.to_csv('Data/stadfangaskra_trimmed.csv', index=False)

print("New CSV file 'Data/stadfangaskra_trimmed.csv' created successfully!")

# Select the desired columns for part b
selected_columns_df_b = df[['POSTNR', 'HEITI_NF', 'HEITI_TGF', 'HUSMERKING']].copy()

# Attempt to fill blank HEITI_TGF based on other entries for the same street and postal code for part b
selected_columns_df_b['HEITI_TGF'] = selected_columns_df_b.groupby(['POSTNR', 'HEITI_NF'])['HEITI_TGF'].transform(lambda x: x.fillna(x.dropna().iloc[0]) if not x.dropna().empty else x)


# Append 'HUSMERKING' to 'HEITI_NF' and 'HEITI_TGF' only if it exists
selected_columns_df_b['HEITI_NF'] = selected_columns_df_b.apply(lambda row: f"{row['HEITI_NF']} {row['HUSMERKING']}" if pd.notna(row['HUSMERKING']) and row['HUSMERKING'] != '' else row['HEITI_NF'], axis=1)
selected_columns_df_b['HEITI_TGF'] = selected_columns_df_b.apply(lambda row: f"{row['HEITI_TGF']} {row['HUSMERKING']}" if pd.notna(row['HUSMERKING']) and row['HUSMERKING'] != '' and pd.notna(row['HEITI_TGF']) else row['HEITI_TGF'], axis=1)


# Drop the original 'HUSMERKING' column
selected_columns_df_b = selected_columns_df_b.drop('HUSMERKING', axis=1)

# Remove duplicate entries based on 'POSTNR' and 'HEITI_NF'
selected_columns_df_b = selected_columns_df_b.drop_duplicates(subset=['POSTNR', 'HEITI_NF'])

# Sort the DataFrame by 'POSTNR' and then 'HEITI_NF'
selected_columns_df_b = selected_columns_df_b.sort_values(by=['POSTNR', 'HEITI_NF'])


# Save the new DataFrame to a CSV file for part b
selected_columns_df_b.to_csv('Data/icelandic_addresses.csv', index=False)

print("New CSV file 'Data/icelandic_addresses.csv' created successfully!")
