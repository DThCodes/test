from IPython import get_ipython
from IPython.display import display
import requests
from bs4 import BeautifulSoup
import csv
from io import StringIO
from datetime import datetime
import os
import pandas as pd # Import pandas for the second part

# Define the desired output column names and their corresponding expected scraped header names
OUTPUT_COLUMN_MAPPING = {
    "Nafn": "Nafn",
    "Kennitala": "Kennitala",
    "Stöð": "Stöð",
    "Stöðvarnúmer": "Stöðvarnúmer",
    "Forráðamaður, ef lögaðili": "Forráðamaður ef lögaðili" # Handle potential variation in header
}

# Part (a): Web scraping and saving to CSV
url = "https://island.is/listi-yfir-rekstrarleyfishafa-i-leigubilaakstri"
response = requests.get(url)

# Get the current date in dd.mm.yyyy format
current_date_ddmmyyyy = datetime.now().strftime("%d.%m.%Y")
# Get the current date in yyyy-mm-dd format for filename and directory
current_date_yyyymmdd = datetime.now().strftime("%Y-%m-%d")
current_year = datetime.now().strftime("%Y")


# Check if the request was successful
if response.status_code == 200:
    soup = BeautifulSoup(response.content, 'html.parser')

    table = soup.find('table', class_='_1wc4apv0 _1wc4apv5 _1ovv93d1o3 _1ovv93d1o4 b7a64p0')

    # Find the div element with the specific class
    target_element = soup.find('div', class_='_1wc4apv0 _1ovv93d1o3 hpuvl25')

    # Initialize extracted_value_truncated with a default value
    extracted_value_truncated = ""

    # If the target element is found, find the previous p element
    if target_element:
        previous_p_element = target_element.find_previous('p')
        if previous_p_element:
            extracted_value = previous_p_element.get_text(strip=True)
            # Remove the first 8 characters from the extracted value
            extracted_value_truncated = extracted_value[8:]
            print(f"Extracted and truncated value: {extracted_value_truncated}")
        else:
            print("No previous p element found.")
    else:
        print("Target element with the specified class not found.")

    data = []
    if table:
        rows = table.find_all('tr')
        if rows:
            # Get the header row (first row)
            header_row = rows[0]
            header_cols = header_row.find_all(['th', 'td'])
            header_names = [col.get_text(strip=True) for col in header_cols]

            # Create a mapping from desired output column names to their index in the scraped header
            scraped_col_indices = {}
            for output_col, scraped_header in OUTPUT_COLUMN_MAPPING.items():
                 try:
                     # Find the index of the scraped header name in the actual scraped headers
                     scraped_col_indices[output_col] = header_names.index(scraped_header)
                 except ValueError:
                     # If a required header is not found, print a warning or handle as needed
                     print(f"Warning: Scraped header '{scraped_header}' not found in table headers.")
                     scraped_col_indices[output_col] = -1 # Assign -1 to indicate column not found


            # Process the data rows (starting from the second row)
            for row in rows[1:]:
                cols = row.find_all(['th', 'td'])
                row_data = [col.get_text(strip=True) for col in cols]

                # Prepare a list to hold the data for the output row in the desired order (matching OUTPUT_COLUMNS order)
                reconstructed_row = [""] * len(OUTPUT_COLUMN_MAPPING)

                # Populate the reconstructed row based on the scraped column indices
                for output_col, index in scraped_col_indices.items():
                    if index != -1 and index < len(row_data):
                        # Find the correct position in the reconstructed row based on the desired OUTPUT_COLUMN_MAPPING order
                        try:
                           output_index = list(OUTPUT_COLUMN_MAPPING.keys()).index(output_col)
                           reconstructed_row[output_index] = row_data[index]
                        except ValueError:
                           pass # Should not happen if output_col is from OUTPUT_COLUMN_MAPPING.keys()


                # Special handling for Kennitala padding
                kennitala_index_in_output = list(OUTPUT_COLUMN_MAPPING.keys()).index("Kennitala")
                if kennitala_index_in_output < len(reconstructed_row):
                     kennitala = reconstructed_row[kennitala_index_in_output]
                     if len(kennitala) == 9:
                         reconstructed_row[kennitala_index_in_output] = "0" + kennitala


                # Add the "Uppfært af Samgöngustofu" and "Date" columns to the reconstructed row
                # Ensure these are added at the correct positions based on the desired output header order
                output_header = list(OUTPUT_COLUMN_MAPPING.keys()) + ["Uppfært af Samgöngustofu", "Date"]
                full_reconstructed_row = reconstructed_row + [extracted_value_truncated, current_date_ddmmyyyy]


                data.append(full_reconstructed_row)

    # Specify the filename for the daily CSV file
    filename = "taxi_licenses_date.csv"

    # Check if the file exists
    file_exists = os.path.exists(filename)

    # Open the CSV file
    # Use write mode ('w') if the file doesn't exist to write header and data
    # Use append mode ('a') if the file exists to append data
    with open(filename, 'a' if file_exists else 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)

        # If the file doesn't exist, write the header row using the defined header
        if not file_exists:
            writer.writerow(list(OUTPUT_COLUMN_MAPPING.keys()) + ["Uppfært af Samgöngustofu", "Date"]) # Use the defined output columns as header

        # Write the processed data rows
        writer.writerows(data)


    print(f"Data successfully saved to {filename}")

    # Part (b): Processing the CSV file (kept for continuity, assuming this is the next step)
    output_filename = "taxi_licenses_summary.csv"

    try:
        # Read the daily CSV file into a pandas DataFrame
        column_names = list(OUTPUT_COLUMN_MAPPING.keys()) + ["Uppfært af Samgöngustofu", "Date"]
        # Explicitly specify delimiter and quoting
        df = pd.read_csv(filename, header=0, names=column_names, dtype={'Kennitala': str}, on_bad_lines='skip', delimiter=',', quotechar='"') # Specify dtype for Kennitala, skip bad lines, delimiter, and quotechar


        # --- Troubleshooting Step: Print the first few 'Kennitala' values after reading ---
        print("First few 'Kennitala' values after reading output_data.csv:")
        print(df['Kennitala'].head())
        print("-" * 20)
        # --- Troubleshooting Step: Check a specific Kennitala value ---
        specific_kennitala = "109824139"
        if specific_kennitala in df['Kennitala'].values:
            print(f"'{specific_kennitala}' found in 'Kennitala' column.")
        elif "0" + specific_kennitala in df['Kennitala'].values:
             print(f"Padded '0{specific_kennitala}' found in 'Kennitala' column.")
        else:
            print(f"Neither '{specific_kennitala}' nor '0{specific_kennitala}' found in 'Kennitala' column.")
        print("-" * 20)


        # --- Troubleshooting Step: Print the column before conversion ---
        print("Original 'Date' column:")
        print(df['Date'].head())
        print("-" * 20)

        # Convert the 'Date' column to datetime objects
        df['Date'] = pd.to_datetime(df['Date'], format='%d.%m.%Y', errors='coerce')

        # --- Troubleshooting Step: Print the column after conversion ---
        print("'Date' column after conversion:")
        print(df['Date'].head())
        print("-" * 20)

        # --- Troubleshooting Step: Check for NaT values after conversion ---
        if df['Date'].isnull().any():
            print("Warning: Some dates in 'Date' could not be parsed and were converted to NaT.")
            print("-" * 20)

        # Generate the 'ID' column in Part b, ensuring columns are strings and handling missing values
        def generate_id(row):
            id_parts = [str(row['Nafn'])]
            if pd.notna(row['Stöð']) and str(row['Stöð']).strip() != '' and str(row['Stöð']).lower() != 'nan':
                id_parts.append(str(row['Stöð']).replace('.0', '')) # Ensure string and remove .0 if present
            if pd.notna(row['Stöðvarnúmer']) and str(row['Stöðvarnúmer']).strip() != '' and str(row['Stöðvarnúmer']).lower() != 'nan':
                id_parts.append(str(row['Stöðvarnúmer']).replace('.0', '')) # Ensure string and remove .0 if present
            return " - ".join(id_parts)

        df['ID'] = df.apply(generate_id, axis=1)

        # Ensure 'Stöð' column is string type for final output and replace "nan" with empty string
        df['Stöð'] = df['Stöð'].astype(str).replace(r'\.0$', '', regex=True).replace('nan', '')


        # Group by 'ID' to find the min and max dates for each unique ID
        grouped = df.dropna(subset=['Date']).groupby('ID')['Date'].agg(['min', 'max']).reset_index()

        # Rename the columns
        grouped = grouped.rename(columns={'min': 'First appearance', 'max': 'Last appearance'})

        # Merge with the original dataframe to include the 'Nafn', 'Kennitala', and 'Stöð' columns
        # Ensure we are merging with the necessary columns from the df
        merged_df = pd.merge(grouped, df[['ID', 'Nafn', 'Kennitala', 'Stöð']].drop_duplicates(subset=['ID']), on='ID', how='left')

        # Reorder columns to match the desired output order for taxi_licenses_summary.csv
        final_df = merged_df[['Nafn', 'Kennitala', 'Stöð', 'First appearance', 'Last appearance', 'ID']]

        # Sort the DataFrame by the 'Nafn' column in ascending order
        final_df = final_df.sort_values(by='Nafn', ascending=True)

        # Format the date columns back to 'dd.mm.yyyy' format for saving
        if not final_df['First appearance'].isnull().all():
            final_df['First appearance'] = final_df['First appearance'].dt.strftime('%d.%m.%Y')
        if not final_df['Last appearance'].isnull().all():
            final_df['Last appearance'] = final_df['Last appearance'].dt.strftime('%d.%m.%Y')

        # Save the processed data to the summary CSV file
        final_df.to_csv(output_filename, index=False)

        print(f"Processed and selected data successfully saved to {output_filename}")

        # Rename taxi_licenses_date.csv and move to a year directory
        dated_filename = f"taxi_license_{current_date_yyyymmdd}.csv"
        year_directory = f"./{current_year}"
        dated_filepath = os.path.join(year_directory, dated_filename)

        # Create the year directory if it doesn't exist
        if not os.path.exists(year_directory):
            os.makedirs(year_directory)

        # Move the daily data file
        if os.path.exists(filename):
            os.rename(filename, dated_filepath)
            print(f"Renamed '{filename}' to '{dated_filename}' and moved to '{year_directory}'")
        else:
            print(f"Error: '{filename}' not found for renaming and moving.")


    except FileNotFoundError:
        print(f"Error: The file '{filename}' was not found.")
    except KeyError as e:
        print(f"Error: A required column was not found in the file or during processing. {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
else:
    print(f"Failed to retrieve data from {url}. Status code: {response.status_code}")
