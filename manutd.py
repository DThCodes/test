import requests
from bs4 import BeautifulSoup
import csv
import re
from datetime import datetime
import os
import pandas as pd
import numpy as np

# Define start and end months for the season
SEASON_START_MONTH = 8 # August
SEASON_END_MONTH = 6 # June

# Get the current date
now = datetime.now()
current_year = now.year
current_month = now.month

# Determine the season string based on the current month
if current_month >= SEASON_START_MONTH:
    season_string = f"{current_year}-{current_year + 1}"
else:
    season_string = f"{current_year - 1}-{current_year}"


# Fetch the webpage
url = "https://www.bbc.com/sport/football/premier-league/table"
response = requests.get(url)

if response.status_code == 200:
    html_content = response.text
    print("Successfully downloaded HTML content.")
else:
    print(f"Failed to download HTML content. Status code: {response.status_code}")
    html_content = None

# Parse the HTML
if html_content:
    soup = BeautifulSoup(html_content, 'html.parser')
    print("Successfully created BeautifulSoup object.")
else:
    print("HTML content is not available.")
    soup = None

# Find the table
football_table = None
if soup:
    tables = soup.find_all('table')
    if tables:
        # Try finding the table using the data-testid or class attribute found in the previous step
        football_table = soup.find('table', {'data-testid': 'football-table'})

        if football_table:
            print("Successfully found the football standings table using data-testid.")
        else:
            # If data-testid didn't work, try the class attribute.
            if tables and 'class' in tables[0].attrs:
                football_table = soup.find('table', class_=tables[0].attrs['class'][0])
                if football_table:
                    print(f"Successfully found the football standings table using class: {tables[0].attrs['class'][0]}.")
                else:
                    print("Could not find the football standings table using data-testid or class.")
            else:
                 print("Could not find the football standings table using data-testid or class.")
    else:
        print("No tables found on the page.")

# Find the row
manchester_united_row = None
if football_table:
    rows = football_table.find_all('tr')
    for row in rows:
        if "Manchester United" in row.get_text():
            manchester_united_row = row
            break

    if manchester_united_row:
        print("Successfully found the row for Manchester United.")
    else:
        print("Could not find the row for Manchester United.")
else:
    print("Error: football_table is None. Cannot proceed to find row.")

# Extract data
extracted_data = []
if manchester_united_row:
    cells = manchester_united_row.find_all(['td', 'th'])
    extracted_data = [cell.get_text(strip=True) for cell in cells]
    # Remove the last element (form data)
    if extracted_data:
        extracted_data = extracted_data[:-1]

    # Split position and team
    if extracted_data:
        position_team = extracted_data[0]
        match = re.match(r'(\d+)([A-Za-z\s]+)', position_team)
        if match:
            position = match.group(1)
            team = match.group(2).strip() # Strip whitespace from team name
            extracted_data[0:1] = [position, team] # Replace the combined element with split elements

    # At this point, extracted_data should be something like:
    # [position, "", team, played, won, drawn, lost, goals_for, goals_against, goal_difference, points]
    print(f"Extracted data: {extracted_data}")

    # Insert an empty string between position and team
    if len(extracted_data) > 1:
         extracted_data.insert(1, "")

    print("Extracted data for Manchester United (processed):")
    print(extracted_data)
else:
    print("Error: Manchester United row is not available.")


# --- Part A: Write to manchester_united_data.csv ---
csv_filename_data = "manchester_united_data.csv"
header_data = ["season", "position", "", "team", "played", "won", "drawn", "lost", "goals", "goal difference", "points", "goals for", "goals against", "points per game", "last result", "form", "gf", "ga", "games scored in", "clean sheets"]
new_row_data = [] # Initialize new_row_data

if extracted_data:
    try:
        # Assuming extracted_data is now:
        # [position, "", team, played, won, drawn, lost, goals_for, goals_against, goal_difference, points]
        # The indices in extracted_data are relative to the list after initial processing

        played = int(extracted_data[3])
        points = int(extracted_data[10]) # Correct index for points
        goals_for = int(extracted_data[7]) # Correct index for goals_for
        goals_against = int(extracted_data[8]) # Correct index for goals_against
        goal_difference = int(extracted_data[9]) # Correct index for goal_difference
        combined_goals = f"{goals_for}:{goals_against}"


        points_per_game = round(points / played, 2) if played > 0 else 0 # Added rounding

        # Construct the new row for _data.csv with the desired columns and order
        # Desired order: season, position, "", team, played, won, drawn, lost, goals, goal difference, points, goals for, goals against, points per game
        new_row_data_base = [
            season_string,          # season
            extracted_data[0],      # position
            "",                     # empty column
            extracted_data[2],      # team
            extracted_data[3],      # played
            extracted_data[4],      # won
            extracted_data[5],      # drawn
            extracted_data[6],      # lost
            combined_goals,         # goals (combined)
            extracted_data[9],      # goal_difference (from extracted_data)
            extracted_data[10],     # points (from extracted_data)
            goals_for,              # goals for (calculated)
            goals_against,          # goals against (calculated)
            points_per_game         # points per game (calculated)
        ]

        # Load existing data to calculate form, gf, ga, games scored in, and clean sheets
        existing_data_list = []
        if os.path.exists(csv_filename_data):
            with open(csv_filename_data, 'r', newline='') as csvfile:
                reader = csv.reader(csvfile)
                try:
                    # Skip the header row when reading existing data if it exists
                    header_row = next(reader)
                    if header_row != header_data:
                         existing_data_list.append(header_row) # Keep non-matching header
                    for row in reader:
                        existing_data_list.append(row)
                except csv.Error as e:
                    print(f"Error reading CSV file {csv_filename_data}: {e}")
                    existing_data_list = [] # Reset existing_data if there's an error
                except StopIteration:
                     pass # Handle empty file case

        # Create a temporary DataFrame with existing and new data to calculate indicators
        # Ensure all rows in existing_data_list have the same number of columns as header_data
        padded_existing_data = []
        for row in existing_data_list:
            if len(row) < len(header_data):
                padded_row = row + [''] * (len(header_data) - len(row))
                padded_existing_data.append(padded_row)
            else:
                padded_existing_data.append(row)

        temp_df_data = pd.DataFrame(padded_existing_data, columns=header_data)

        # Ensure temp_df_data has all columns from header_data before concatenation
        for col in header_data:
            if col not in temp_df_data.columns:
                temp_df_data[col] = np.nan # Add missing columns with NaN values

        # Create a DataFrame for the new row with all header columns
        new_row_df = pd.DataFrame([new_row_data_base], columns=header_data[:14])
        # Add placeholder columns for the calculated fields (last result, form, gf, ga, games scored in, clean sheets)
        for col in header_data[14:]:
            new_row_df[col] = np.nan


        temp_df_data = pd.concat([temp_df_data, new_row_df], ignore_index=True)

        # Ensure necessary columns are numeric for calculations
        temp_df_data['played'] = pd.to_numeric(temp_df_data['played'], errors='coerce')
        temp_df_data['points'] = pd.to_numeric(temp_df_data['points'], errors='coerce')
        temp_df_data['goals for'] = pd.to_numeric(temp_df_data['goals for'], errors='coerce')
        temp_df_data['goals against'] = pd.to_numeric(temp_df_data['goals against'], errors='coerce')
        temp_df_data['gf'] = pd.to_numeric(temp_df_data['gf'], errors='coerce')
        temp_df_data['ga'] = pd.to_numeric(temp_df_data['ga'], errors='coerce')

        # Sort by season and played
        temp_df_data = temp_df_data.sort_values(by=['season', 'played']).reset_index(drop=True)

        # Function to calculate 'last result'
        def calculate_last_result(row, df):
            if pd.isna(row['played']) or row['played'] == 0:
                return ''
            if row['played'] == 1:
                points = row['points']
                if points == 3:
                    return 'W'
                elif points == 1:
                    return 'D'
                else: # points == 0
                    return 'L'
            else:
                # Find the previous row for the same season
                current_season = row['season']
                current_played = row['played']
                previous_row = df[(df['season'] == current_season) & (df['played'] == current_played - 1)]
                if not previous_row.empty:
                    previous_points = previous_row.iloc[0]['points']
                    current_points = row['points']
                    point_diff = current_points - previous_points
                    if point_diff == 3:
                        return 'W'
                    elif point_diff == 1:
                        return 'D'
                    else: # point_diff == 0
                        return 'L'
                else:
                    return ''

        # Apply the function to create 'last result' column on temp_df_data
        temp_df_data['last result'] = temp_df_data.apply(lambda row: calculate_last_result(row, temp_df_data), axis=1)

        # Function to calculate 'form' (newest result first, oldest last, max 5 results)
        def calculate_form(row, df):
            if pd.isna(row['played']) or row['played'] == 0:
                return ''
            played = row['played']
            current_season = row['season']
            # Determine how many previous games to include (up to 4 previous + current)
            num_games = min(int(played), 5) # Limit to 5 games total
            start_played = played - num_games + 1
            if start_played < 1:
                 start_played = 1

            # Get results for the last 'num_games' played in the current season, in played order
            form_df = df[(df['season'] == current_season) & (df['played'] >= start_played) & (df['played'] <= played)].sort_values(by='played')

            # Get results in chronological order (oldest to newest)
            results = form_df['last result'].tolist()

            # Reverse the list to get newest first
            results.reverse()

            # Join with hyphens
            return "-".join(results)

        # Apply the function to create 'form' column on temp_df_data
        temp_df_data['form'] = temp_df_data.apply(lambda row: calculate_form(row, temp_df_data), axis=1)

        # Function to calculate 'gf' (goals for indicator)
        def calculate_gf(row, df):
            if pd.isna(row['played']) or row['played'] == 0:
                return 0 # Return 0 for played=0 or NaN
            if row['played'] == 1:
                goals_for = row['goals for']
                return 0 if goals_for == 0 else 1
            else:
                current_played = row['played']
                current_season = row['season']
                previous_row = df[(df['season'] == current_season) & (df['played'] == current_played - 1)]
                if not previous_row.empty:
                    current_goals_for = row['goals for']
                    previous_goals_for = previous_row.iloc[0]['goals for']
                    return 1 if current_goals_for > previous_goals_for else 0
                else:
                    return 0 # Should not happen if data is sorted and consecutive for a season

        # Apply the function to create 'gf' column on temp_df_data
        temp_df_data['gf'] = temp_df_data.apply(lambda row: calculate_gf(row, temp_df_data), axis=1)

        # Function to calculate 'ga' (goals against indicator)
        def calculate_ga(row, df):
            if pd.isna(row['played']) or row['played'] == 0:
                 return 0 # Return 0 for played=0 or NaN
            if row['played'] == 1:
                goals_against = row['goals against']
                return 1 if goals_against > 0 else 0
            else:
                current_played = row['played']
                current_season = row['season']
                previous_row = df[(df['season'] == current_season) & (df['played'] == current_played - 1)]
                if not previous_row.empty:
                    current_goals_against = row['goals against']
                    previous_goals_against = previous_row.iloc[0]['goals against']
                    return 1 if current_goals_against > previous_goals_against else 0
                else:
                    return 0 # Should not happen if data is sorted and consecutive for a season

        # Apply the function to create 'ga' column on temp_df_data
        temp_df_data['ga'] = temp_df_data.apply(lambda row: calculate_ga(row, temp_df_data), axis=1)


        # Function to calculate 'games scored in' (cumulative sum of gf, reset at played=1)
        def calculate_games_scored_in(df):
            games_scored = []
            current_sum = 0
            current_season = None
            for idx, row in df.iterrows():
                if pd.isna(row['played']):
                    games_scored.append('')
                    continue
                if row['season'] != current_season or row['played'] == 1:
                    current_sum = 1 if row['gf'] == 1 else 0
                    current_season = row['season']
                else:
                    current_sum += 1 if row['gf'] == 1 else 0
                games_scored.append(current_sum)
            return games_scored

        # Apply the function to create 'games scored in' column on temp_df_data
        temp_df_data['games scored in'] = calculate_games_scored_in(temp_df_data)

        # Function to calculate 'clean sheets' (cumulative sum of ga=0, reset at played=1)
        def calculate_clean_sheets(df):
            clean_sheets = []
            current_sum = 0
            current_season = None
            for idx, row in df.iterrows():
                if pd.isna(row['played']):
                    clean_sheets.append('')
                    continue
                if row['season'] != current_season or row['played'] == 1:
                    current_sum = 1 if row['ga'] == 0 else 0  # 1 if no goals conceded, 0 if conceded
                    current_season = row['season']
                else:
                    current_sum += 1 if row['ga'] == 0 else 0  # 1 if no goals conceded, 0 if conceded
                clean_sheets.append(current_sum)
            return clean_sheets

        # Apply the function to create 'clean sheets' column on temp_df_data
        temp_df_data['clean sheets'] = calculate_clean_sheets(temp_df_data)


        # Extract the last row (the newly added data with calculated indicators)
        new_row_data = temp_df_data.iloc[-1].tolist()

    except (ValueError, IndexError, KeyError) as e:
        print(f"Error calculating new columns for {csv_filename_data}: {e}")
        new_row_data = [] # If there's an error, new_row_data will remain empty or contain partial data.


# Check if the CSV file exists and read all rows
existing_data_data = []
if os.path.exists(csv_filename_data):
    with open(csv_filename_data, 'r', newline='') as csvfile:
        reader = csv.reader(csvfile)
        try:
            # Skip the header row when reading existing data if it exists
            header_row = next(reader)
            if header_row != header_data:
                 existing_data_data.append(header_row) # Keep non-matching header
            for row in reader:
                existing_data_data.append(row)
        except csv.Error as e:
            print(f"Error reading CSV file {csv_filename_data}: {e}")
            existing_data_data = [] # Reset existing_data if there's an error
        except StopIteration:
             pass # Handle empty file case

# Write to file
if new_row_data: # Check if new_row_data was successfully created
    # Check if a row with the same season and played value already exists
    row_exists = False
    if existing_data_data:
        for row in existing_data_data:
            if len(row) > 4 and row[0] == season_string and row[4] == str(played):
                row_exists = True
                break

    if not row_exists:
        with open(csv_filename_data, 'a', newline='') as csvfile: # Use 'a' to append
            writer = csv.writer(csvfile)
            # Write header only if the file is empty
            if not os.path.exists(csv_filename_data) or os.stat(csv_filename_data).st_size == 0:
                 writer.writerow(header_data)
                 print(f"Header successfully written to {csv_filename_data}")

            writer.writerow(new_row_data) # Write the new row
            print(f"New data successfully appended to {csv_filename_data}.")
    elif new_row_data != existing_data_data[-1]:
         # If row exists and is different from the last row, overwrite the file
         with open(csv_filename_data, 'w', newline='') as csvfile: # Use 'w' to overwrite
            writer = csv.writer(csvfile)
            writer.writerow(header_data) # Always write the header
            # Write existing data back, excluding the old row for the current season and played value
            for row in existing_data_data:
                 if len(row) > 4 and (row[0] != season_string or row[4] != str(played)):
                    writer.writerow(row)
            writer.writerow(new_row_data) # Write the new row
            print(f"Existing row for season {season_string} and played {played} updated in {csv_filename_data}.")
    else:
        print(f"New data is the same as the last row or existing row for season {season_string} and played {played} in {csv_filename_data}. Not appending or updating.")


else:
    print(f"No data to write to {csv_filename_data} due to calculation errors or no extracted data.")


# --- Part B: Write to manchester_united_data_sheets.csv ---
csv_filename_sheets = "manchester_united_data_sheets.csv"
header_sheets = ["season", "position", "", "team", "played", "won", "drawn", "lost", "goals", "goal difference", "points"]
new_row_sheets = [] # Initialize new_row_sheets

if extracted_data:
    try:
        # Construct the new row for _sheets.csv with the desired columns and order
        # Desired order: season, position, "", team, played, won, drawn, lost, goals, goal difference, points
        goals_for = int(extracted_data[7]) # Correct index for goals_for
        goals_against = int(extracted_data[8]) # Correct index for goals_against
        combined_goals = f"{goals_for}:{goals_against}"

        new_row_sheets = [
            season_string,          # season
            extracted_data[0],      # position
            "",                     # empty column
            extracted_data[2],      # team
            extracted_data[3],      # played
            extracted_data[4],      # won
            extracted_data[5],      # drawn
            extracted_data[6],      # lost
            combined_goals,         # goals (combined)
            extracted_data[9],      # goal_difference
            extracted_data[10]      # points
        ]

    except (ValueError, IndexError) as e:
         print(f"Error preparing data for {csv_filename_sheets}: {e}")
         new_row_sheets = [] # Clear new_row_sheets if there's an error


# Write to file
if new_row_sheets: # Ensure new_row_sheets is not empty
    try:
        # Check if the CSV file exists and is not empty
        file_exists_and_not_empty = os.path.exists(csv_filename_sheets) and os.stat(csv_filename_sheets).st_size > 0

        # Read the last row for comparison if the file exists and has data
        last_data_row_sheets = None
        if file_exists_and_not_empty:
            with open(csv_filename_sheets, 'r', newline='') as csvfile:
                reader = csv.reader(csvfile)
                try:
                    # Read all rows, including header
                    all_rows = list(reader)
                    if len(all_rows) > 1: # Check if there's more than just a header
                        last_data_row_sheets = all_rows[-1]
                except csv.Error as e:
                    print(f"Error reading CSV file {csv_filename_sheets} for comparison: {e}")
                    last_data_row_sheets = None # Reset last_data_row if there's an error

        # Check if the new row is different from the last data row
        if last_data_row_sheets is None or new_row_sheets != last_data_row_sheets:
             with open(csv_filename_sheets, 'a', newline='') as csvfile: # Use 'a' to append
                writer = csv.writer(csvfile)
                 # Write header only if the file is empty
                if not file_exists_and_not_empty:
                    writer.writerow(header_sheets)
                    print(f"Header successfully written to {csv_filename_sheets}")

                writer.writerow(new_row_sheets) # Write the new row
                print(f"New data successfully appended to {csv_filename_sheets}.")
        else:
            print(f"New data is the same as the last row in {csv_filename_sheets}. Not appending.")
    except Exception as e:
        print(f"Error writing to {csv_filename_sheets}: {e}")
else:
    print(f"No data to write to {csv_filename_sheets}.")
