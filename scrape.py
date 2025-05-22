import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
from datetime import datetime
import os
from typing import List


def extract_leading_digits(input_string):
    match = re.match(r'^\d+', input_string)
    return match.group(0) if match else ''

def scrape_drivers_wiki(
        output_dir: str = "/Users/bartosz/f1_data",
        category: str = "f1",
        ):
    
    file_name_mapping = {
        "f1":"f1_drivers_wiki",
        "f2":"f2_drivers_wiki",
        "f3":"f3_drivers_wiki"
    }

    url_mapping = {
        "f1":"https://en.wikipedia.org/wiki/List_of_Formula_One_drivers",
        "f2":"https://en.wikipedia.org/wiki/List_of_FIA_Formula_2_Championship_drivers",
        "f3":"https://en.wikipedia.org/wiki/List_of_FIA_Formula_3_Championship_drivers"
    }

    today_date = datetime.today().strftime('%d-%m-%Y')
    
    file_path = f"{output_dir}/{file_name_mapping[category]}_{today_date}.parquet"
    
    # Remove files that match 'f1_drivers_wiki_' but have a date other than today's
    for file in os.listdir(output_dir):
        if file.endswith(".parquet") and file_name_mapping[category] in file:
            if today_date not in file:
                os.remove(os.path.join(output_dir, file))
                print(f"Removed outdated file: {file}")
    
    # Check if today's file already exists
    if os.path.exists(file_path):
        print("File already exists for today. Aborting scrape.")
        return
    

    url = url_mapping[category]
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    tables = soup.find_all('table', {'class': 'wikitable'})
    driver_table = tables[1]
    
    # Extract headers
    header_row = driver_table.find('tr')
    headers = [cell.text.strip() for cell in header_row.find_all('th')]
    
    # Extract data
    data = []
    for row in driver_table.find_all('tr')[1:]:
        cells = row.find_all('td')
        if cells:
            driver_data = [cell.text.strip() for cell in cells]
            data.append(driver_data)
    
    # Create DataFrame
    df = pd.DataFrame(data, columns=headers)
    
    # Function to extract leading digits

    
    if category == "f1":
        df = df.rename(columns={"Points[a]": "Points"})
        
        columns_to_clean = [
            "Race entries", "Race starts", "Pole positions", "Race wins", 
            "Podiums", "Fastest laps", "Points", "Drivers' Championships"
        ]

        for column in columns_to_clean:
            if column in df.columns:
                if column == "Drivers' Championships":
                    df[column] = df[column].str.extract(r'(\d)')
                df[column] = df[column].apply(extract_leading_digits)
        if "Driver name" in df.columns:
            df["Driver name"] = df["Driver name"].str.replace(r'[~*^]', '', regex=True)
            df["Driver name"] = df["Driver name"].str.replace(r'\[.*?\]', '', regex=True)
            df["Driver name"] = df["Driver name"].str.strip()
        
        df['Race entries'] = df['Race entries'].astype(int)
        df['Race starts'] = df['Race starts'].astype(int)
        df['Pole positions'] = df['Pole positions'].astype(int)
        df['Race wins'] = df['Race wins'].astype(int)
        df['Podiums'] = df['Podiums'].astype(int)
        df['Fastest laps'] = df['Fastest laps'].astype(int)
        df['Points'] = df['Points'].astype(float)
        df["Drivers' Championships"] = df["Drivers' Championships"].astype(int)
        

    
    if category == "f2":
        df = df.rename(columns={"Championshiptitles": "Championship titles", "Fastestlaps[a]":"Fastest laps"})

        columns_to_clean = ["Entries", "Starts", "Poles", "Sprint wins", "Feature Wins", "Total wins", "Podiums", "Fastest laps", "Points"]

        for column in columns_to_clean:
            if column in df.columns:
                df[column] = df[column].apply(extract_leading_digits)


    
    
    # Save to parquet
    df.to_parquet(file_path)
    print("Parquet file created:", file_path)



def scrape_f1_standings(
        league: List[str] = ["f1", "f2", "f3", "f1academy"],
        years: List[int] = list(range(1950, datetime.today().year)),
        categories: List[str] = ["drivers", "team", "fastest-laps"]
        ):


    link_mappings = {
        "f1":f"https://www.formula1.com/en/results/{year}/{category}",
        "f2":f"https://www.fiaformula2.com/Standings/Driver?seasonId={year - 1843}",
        "f3":f"https://www.fiaformula3.com/Standings/Driver?seasonId={year - 1843}",
        "f1academy":f"https://www.f1academy.com/Racing-Series/Standings/Driver?seasonId={year - 2023 + 1}"
    }
    pass

scrape_drivers_wiki()