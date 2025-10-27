# combined_script.py
import requests
from bs4 import BeautifulSoup
import csv
import re
from datetime import datetime
import os

def scrape_premier_league_table():
    # Define start and end months for the season
    SEASON_START_MONTH = 8  # August
    SEASON_END_MONTH = 6   # June

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
    try:
        response = requests.get(url)
        response.raise_for_status()
        html_content = response.text
        print("Successfully downloaded HTML content.")
    except requests.exceptions.RequestException as e:
        print(f"Failed to download HTML content: {e}")
        return

    # Parse the HTML
    soup = BeautifulSoup(html_content, 'html.parser')
    print("Successfully created BeautifulSoup object.")

    # Find the table
    football_table = soup.find('table', {'data-testid': 'football-table'})
    if not football_table:
        tables = soup.find_all('table')
        if tables and 'class' in tables[0].attrs:
            football_table = soup.find('table', class_=tables[0].attrs['class'][0])
            if football_table:
                print(f"Successfully found the football standings table using class: {tables[0].attrs['class'][0]}.")
            else:
                print("Could not find the football standings table using data-testid or class.")
        else:
            print("No tables found on the page.")
        return

    # Find the row for Manchester United
    manchester_united_row = None
    rows = football_table.find_all('tr')
    for row in rows:
        if "Manchester United" in row.get_text():
            manchester_united_row = row
            break

    if not manchester_united_row:
        print("Could not find the row for Manchester United.")
        return

    print("Successfully found the row for Manchester United.")

    # Extract data
    cells = manchester_united_row.find_all(['td', 'th'])
    extracted_data = [cell.get_text(strip=True) for cell in cells]
    if extracted_data:
        extracted_data = extracted_data[:-1]  # Remove the last element (form data)

    # Split position and team
    if extracted_data:
        position_team = extracted_data[0]
        match = re.match(r'(\d+)([A-Za-z\s]+)', position_team)
        if match:
            position = match.group(1)
            team = match.group(2)
            extracted_data[0:1] = [position, team]

    # Combine goals for and against
    if len(extracted_data) >= 8:
        goals_for = extracted_data[6]
        goals_against = extracted_data[7]
        combined_goals = f"{goals_for}:{goals_against}"
        extracted_data[6:8] = [combined_goals]

    # Insert an empty string between position and team
    if len(extracted_data) > 1:
        extracted_data.insert(1, "")

    print("Extracted data for Manchester United (processed):")
    print(extracted_data)

    # Prepare the new row to be written
    new_row = [season_string] + extracted_data
    csv_filename = "manchester_united_data.csv"

    # Check if the CSV file exists and read the last row
    last_row = None
    if os.path.exists(csv_filename):
        with open(csv_filename, 'r', newline='') as csvfile:
            reader = csv.reader(csvfile)
            try:
                for row in reader:
                    last_row = row
            except csv.Error as e:
                print(f"Error reading CSV file: {e}")
                return

    # Compare the new row with the last row and append if different
    if extracted_data:
        if last_row is None or new_row != last_row:
            with open(csv_filename, 'a', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(new_row)
            print(f"New data successfully appended to {csv_filename}")
        else:
            print("New data is the same as the last row. Not appending.")
    else:
        print("No data to write to CSV.")

def download_comparison_csv():
    csv_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRdmUHYZXmPehb_47g0QPUEt8Dm3LBRoH70zkn6rZSkiuSUATmmyPtRLjhUH07d9-IvNjQHRf93HCMb/pub?gid=0&single=true&output=csv"
    local_filename = "man_utd_comparison_rounds_per_season_data.csv"

    try:
        response = requests.get(csv_url)
        response.raise_for_status()
        with open(local_filename, 'wb') as f:
            f.write(response.content)
        print(f"Successfully downloaded {local_filename}")
    except requests.exceptions.RequestException as e:
        print(f"Error downloading the file: {e}")
    except IOError as e:
        print(f"Error writing the file: {e}")

def main():
    print("Starting script execution...")
    scrape_premier_league_table()
    download_comparison_csv()
    print("Script execution completed.")

if __name__ == "__main__":
    main()
