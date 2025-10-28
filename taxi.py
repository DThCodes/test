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

# Part (a): Web scraping and preparing new daily data
url = "https://island.is/listi-yfir-rekstrarleyfishafa-i-leigubilaakstri"
response = requests.get(url)

# Get the current date
current_date = datetime.now().date() # Use date() for date comparison
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

    new_data_list = []
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

                # Prepare a dictionary to hold the data for the new row
                new_row_data = {}

                # Populate the dictionary based on the scraped column indices
                for col_name, index in scraped_col_indices.items():
                    if index != -1 and index < len(row_data):
                        new_row_data[col_name] = row_data[index]
                    else:
                        new_row_data[col_name] = "" # Ensure all expected columns are present

                # Special handling for Kennitala padding
                if "Kennitala" in new_row_data:
                     kennitala = new_row_data["Kennitala"]
                     if len(kennitala) == 9:
                         new_row_data["Kennitala"] = "0" + kennitala

                # Add the "Uppfært af Samgöngustofu" and "Date" columns
                new_row_data["Uppfært af Samgöngustofu"] = extracted_value_truncated
                new_row_data["Date"] = current_date # Store as date object for easier comparison

                new_data_list.append(new_row_data)

    # Convert the list of dictionaries to a pandas DataFrame
    new_df = pd.DataFrame(new_data_list)

    # Generate the 'ID' column for the new data
    def generate_id(row):
        id_parts = [str(row['Nafn'])]
        if pd.notna(row['Stöð']) and str(row['Stöð']).strip() != '' and str(row['Stöð']).lower() != 'nan':
            id_parts.append(str(row['Stöð']).replace('.0', '')) # Ensure string and remove .0 if present
        if pd.notna(row['Stöðvarnúmer']) and str(row['Stöðvarnúmer']).strip() != '' and str(row['Stöðvarnúmer']).lower() != 'nan':
            id_parts.append(str(row['Stöðvarnúmer']).replace('.0', '')) # Ensure string and remove .0 if present
        return " - ".join(id_parts)

    new_df['ID'] = new_df.apply(generate_id, axis=1)

    # Ensure 'Stöð' column is string type and replace "nan" with empty string in new_df
    # Corrected escape sequence
    new_df['Stöð'] = new_df['Stöð'].astype(str).replace(r'\.0$', '', regex=True).replace('nan', '')


    # Part (b): Update the summary CSV file

    summary_filename = "taxi_licenses_summary.csv"

    # Define the columns expected in the summary file
    summary_cols = ['Nafn', 'First appearance', 'Last appearance', 'ID']

    # Check if the summary file exists
    if os.path.exists(summary_filename):
        # Read the existing summary file with specific error handling for parsing
        try:
            summary_df = pd.read_csv(summary_filename, on_bad_lines='warn') # Use warn for bad lines
            # Ensure all expected columns are present after reading, add if missing
            for col in ['First appearance', 'Last appearance', 'ID']:
                if col not in summary_df.columns:
                    summary_df[col] = pd.NaT # Add missing date columns as NaT
            # Convert date columns to datetime objects for comparison
            summary_df['First appearance'] = pd.to_datetime(summary_df['First appearance'], format='%d.%m.%Y', errors='coerce').dt.date
            summary_df['Last appearance'] = pd.to_datetime(summary_df['Last appearance'], format='%d.%m.%Y', errors='coerce').dt.date

            # Drop 'Kennitala' and 'Stöð' columns if they exist in the read summary_df
            columns_to_drop = ['Kennitala', 'Stöð']
            for col in columns_to_drop:
                if col in summary_df.columns:
                    summary_df = summary_df.drop(columns=[col])

        except pd.errors.EmptyDataError:
             print(f"Warning: Summary file '{summary_filename}' is empty. Starting with an empty summary.")
             summary_df = pd.DataFrame(columns=summary_cols) # Use defined columns
        except FileNotFoundError: # Should be caught by os.path.exists, but good practice
             print(f"Warning: Summary file '{summary_filename}' not found. Starting with an empty summary.")
             summary_df = pd.DataFrame(columns=summary_cols) # Use defined columns
        except Exception as e:
            print(f"Error reading existing summary file: {e}. Starting with an empty summary.")
            summary_df = pd.DataFrame(columns=summary_cols) # Use defined columns
    else:
        # If summary file doesn't exist, create an empty DataFrame with the correct columns
        summary_df = pd.DataFrame(columns=summary_cols) # Use defined columns


    # Prepare new data for merging - Ensure 'Date' is in datetime.date for consistent comparison later
    new_data_for_merge = new_df[['ID', 'Nafn', 'Date']].copy()


    # Combine existing summary data and new daily data for calculating min/max dates and retaining original Nafn
    # We need to keep the 'Nafn' associated with the earliest date for each ID
    # First, combine all data that has an ID and a valid Date, including existing summary and new data
    combined_data_for_merge = pd.concat([
        summary_df[['ID', 'Nafn', 'First appearance']].rename(columns={'First appearance': 'Date'}),
        new_data_for_merge[['ID', 'Nafn', 'Date']]
    ]).dropna(subset=['ID', 'Date'])

    # Sort by ID and Date to easily find the first appearance and associated Nafn
    combined_data_for_merge = combined_data_for_merge.sort_values(by=['ID', 'Date'])

    # Group by ID to find the min and max dates and the Nafn from the earliest date
    updated_summary_df = combined_data_for_merge.groupby('ID').agg(
        First_appearance=('Date', 'min'),
        Last_appearance=('Date', 'max'),
        Nafn=('Nafn', 'first') # Get the Nafn associated with the earliest date
    ).reset_index()

    # Rename the columns to match the desired output
    updated_summary_df = updated_summary_df.rename(columns={'First_appearance': 'First appearance', 'Last_appearance': 'Last appearance'})

    # Select and reorder columns for the final summary DataFrame
    summary_columns_order = ['Nafn', 'First appearance', 'Last appearance', 'ID']
    updated_summary_df = updated_summary_df[summary_columns_order]


    # Format date columns back to 'dd.mm.yyyy' format for saving
    updated_summary_df['First appearance'] = updated_summary_df['First appearance'].apply(lambda x: x.strftime('%d.%m.%Y') if pd.notna(x) else '')
    updated_summary_df['Last appearance'] = updated_summary_df['Last appearance'].apply(lambda x: x.strftime('%d.%m.%Y') if pd.notna(x) else '')

    # Sort the DataFrame by the 'Nafn' column in ascending order
    updated_summary_df = updated_summary_df.sort_values(by='Nafn', ascending=True)

    # Save the updated summary data to taxi_licenses_summary.csv
    updated_summary_df.to_csv(summary_filename, index=False)

    print(f"Updated summary data successfully saved to {summary_filename}")

    # Part (c): Save daily data to a dated file and move to year directory
    daily_filename_temp = "taxi_licenses_daily_scrape_temp.csv" # Temporary filename for daily data
    dated_filename = f"taxi_license_{current_date_yyyymmdd}.csv" # Desired dated filename
    year_directory = f"./{current_year}"
    dated_filepath = os.path.join(year_directory, dated_filename)

    try:
        # Remove the 'ID' column before saving the daily data
        new_df_no_id = new_df.drop(columns=['ID'])

        # Save the new_df (daily scraped data without ID) to a temporary CSV file
        new_df_no_id.to_csv(daily_filename_temp, index=False, encoding='utf-8')

        # Create the year directory if it doesn't exist
        if not os.path.exists(year_directory):
            os.makedirs(year_directory)

        # Move the daily data file
        if os.path.exists(daily_filename_temp):
            os.rename(daily_filename_temp, dated_filepath) # Use the correct source filename: daily_filename_temp
            print(f"Renamed '{daily_filename_temp}' to '{dated_filename}' and moved to '{year_directory}'")
        else:
            print(f"Error: '{daily_filename_temp}' not found for renaming and moving.")

    except Exception as e:
        print(f"An error occurred during daily file saving/moving: {e}")


else:
    print(f"Failed to retrieve data from {url}. Status code: {response.status_code}")
