import streamlit as st
from datetime import datetime
import pandas as pd
import plotting as fsp
import re
import io
from rapidfuzz import process
from scrape import scrape_drivers_wiki
import unidecode
import time
from matplotlib import colormaps
from matplotlib.collections import LineCollection
import scrape as fss
import os

today = datetime.today()

dir = "/Users/bartosz/f1_data"

def normalize_name(name):
    return unidecode.unidecode(name).lower()

def fuzzy_match(name, choices):
    # Get the best match with its score
    match, score, _ = process.extractOne(name, choices)
    return match

# Default wide mode
st.set_page_config(layout="wide")

st.header("🏎️ Formula Stats - Dashboard")
st.text("F1 data analysis made simple.")

# Create tabs
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs(["Visuals", "Schedule", "Drivers List", "Standings", "Records", "Circuits", "Guide", "About"])

st.sidebar.title("Choose Options:")
st.sidebar.text("Options change dynamically to show correct events and sessions for the selected year.")
# Step 1: choose year
year = st.sidebar.selectbox("Year", list(range(2018, today.year + 1))[::-1])

# Load the schedule
schedule = pd.read_parquet(f"/Users/bartosz/f1_data/{year}/schedule.parquet", columns=["EventName", "EventDate", "Session1", "Session2", "Session3", "Session4", "Session5"])

# Filter events that happened or are happening
# Remove events that contain the word "testing" (case insensitive)
event_list = [
    event for event in schedule[schedule["EventDate"] <= today]["EventName"].to_list()
    if "testing" not in event.lower() and "pre-season" not in event.lower()
]


# Step 2: choose event based on the year
event = st.sidebar.selectbox("Event", event_list)

# Create a dictionary, excluding empty values (None, "None", and "")
sessions = {
    row["EventName"]: [
        row[col] for col in ["Session5", "Session4", "Session3", "Session2", "Session1"] 
        if pd.notna(row[col]) and row[col] not in ["None", ""]
    ]
    for _, row in schedule.iterrows()
}

# Remove events with no valid sessions
sessions = {event: sess for event, sess in sessions.items() if sess}

# Step 3: choose session based on the event
session = st.sidebar.selectbox("Session", sessions[event])
session = re.sub(r"\s+", "_", session).lower()

# Visualisations
with tab1:
    st.subheader("Visualisations", help="Detailed information about how each plot works can be found in the guide tab.")

    teams_colors = fsp.get_teams_colors(dir, year, event, session)

    page = st.selectbox("Select Graphics",
                                ["Lap Time Distributions",
                                "Pace Comparisons",
                                "Whole Race",
                                "Telemetry",
                                "Weather Data"
                                ])

    df_schedule = pd.read_parquet(f"{dir}/{year}/schedule.parquet", columns=["EventName", "EventDate", "DirName"])
    dir_name = df_schedule[df_schedule["EventName"] == event]["DirName"].iloc[0]

    if page == "Lap Time Distributions":
        st.text("Default threshold for outliers removal is calculated based on Q1, Q3 and IQR.")

        # Load data based on the chose parameters
        df_laps = pd.read_parquet(
            f"{dir}/{year}/{dir_name}/{session}/laps.parquet",
            columns=["LapTime", "Team", "Driver", "Compound", "CompoundColor"]
        )
        df_laps["Lap Time (s)"] = df_laps["LapTime"].dt.total_seconds()
        df_laps['Compound'] = df_laps['Compound'].replace('nan', 'No Data')

        df_results = pd.read_parquet(
            f"{dir}/{year}/{dir_name}/{session}/results.parquet",
            columns=["Abbreviation", "TeamColorFastf1", "TeamName"]
        )

        
        
        # Plot team lap time distribution
        st.subheader("Team Lap Time Distribution")
        remove_outliers = st.radio("Remove Outliers Team Lap Time:", ["Yes", "No"], horizontal=True)
        fig = fsp.plot_team_lap_time_dist(df_laps, year, event, session, teams_colors, remove_outliers)
        st.pyplot(fig)

        img_buffer = io.BytesIO()
        fig.savefig(img_buffer, format="png", bbox_inches="tight", pad_inches=0.1, dpi=300)
        img_buffer.seek(0)

        st.download_button(
            label="Download Team Lap Time Dist",
            data=img_buffer,
            file_name=f"team_lap_time_dist_{year}_{event.replace(' ', '_').lower()}_{session}.png",
            mime="image/png"
        )



        # Plot point scorere lap time distribution
        st.subheader("Point Scorers Lap Time Distribution")  
        col1, col2 = st.columns(2)
        with col1:
            remove_outliers = st.radio("Remove Outliers Violin Point Scorers:", ["Yes", "No"], horizontal=True)
        with col2:
            show_tyre_compounds = st.radio("Show Tyre Compounds", ["Yes", "No"], horizontal=True)

        fig = fsp.plot_violin_dist_point_socrers(df_laps, df_results, year, event, session, teams_colors, remove_outliers, show_tyre_compounds)
        st.pyplot(fig)

        img_buffer = io.BytesIO()
        fig.savefig(img_buffer, format="png", bbox_inches="tight", pad_inches=0.1, dpi=300)
        img_buffer.seek(0)

        st.download_button(
            label="Download Violin Point Scorers",
            data=img_buffer,
            file_name=f"violin_point_scorers_{year}_{event.replace(' ', '_').lower()}_{session}.png",
            mime="image/png"
        )



        # Plot drivers lap time distribution
        st.subheader("Drivers Lap Time Distribution")
        st.text("Only drivers for whom there is enough valid data are displayed.")

        fig = fsp.plot_drivers_lap_time_dist(df_laps, df_results, year, event, session, teams_colors, remove_outliers)
        st.pyplot(fig)

        img_buffer = io.BytesIO()
        fig.savefig(img_buffer, format="png", bbox_inches="tight", pad_inches=0.1, dpi=300)
        img_buffer.seek(0)

        st.download_button(
            label="Download Drivers Lap Time Dist",
            data=img_buffer,
            file_name=f"drivers_lap_time_dist_{year}_{event.replace(' ', '_').lower()}_{session}.png",
            mime="image/png"
        )




    if page == "Pace Comparisons":
        # Load data based on the chose parameters
        df_laps = pd.read_parquet(
            f"{dir}/{year}/{dir_name}/{session}/laps.parquet",
            columns=["LapNumber", "LapTime", "Team"]
        )
        df_laps["Lap Time (s)"] = df_laps["LapTime"].dt.total_seconds()

        df_results = pd.read_parquet(
            f"{dir}/{year}/{dir_name}/{session}/results.parquet",
            columns=["Abbreviation", "TeamColorFastf1", "TeamName"]
        )
        df_telemetry = pd.read_parquet(
            f"{dir}/{year}/{dir_name}/{session}/telemetry_data.parquet")
        
        team_mean_speed_dict = {team: float(speed) for team, speed in df_telemetry.groupby("Team")["Speed"].mean().round(2).items()}
        team_max_speed_dict = {team: float(speed) for team, speed in df_telemetry.groupby("Team")["Speed"].max().round(2).items()}
        
        if st.toggle('Show Graphic Options'):
            
            col1, col2 = st.columns(2)
            with col1:
                lap = st.radio("Select Lap", ["Average", "Fastest", "Specific"], horizontal=True)
                remove_outliers = st.radio("Remove Outliers Team Pace Comp:", ["Yes", "No"], horizontal=True)

            with col2:
                lap_number = None
                if lap == "Specific":
                    available_laps = [int(lap) for lap in df_laps[df_laps["LapTime"].notna()]["LapNumber"].tolist()]
                    lap_number = st.selectbox("Select Lap", available_laps)

            fig = fsp.plot_team_pace_comparison(df_laps, df_results, year, event, session, teams_colors, lap, lap_number, remove_outliers)
        else:
            fig = fsp.plot_team_pace_comparison(df_laps, df_results, year, event, session, teams_colors)
        st.pyplot(fig)

        img_buffer = io.BytesIO()
        fig.savefig(img_buffer, format="png", bbox_inches="tight", pad_inches=0.1, dpi=300)
        img_buffer.seek(0)

        st.download_button(
            label="Download Team Pace Comparison",
            data=img_buffer,
            file_name=f"team_pace_comparison_{year}_{event.replace(' ', '_').lower()}_{session}.png",
            mime="image/png"
        )



    if page == "Weather Data":
        elements_to_plot = st.multiselect(
            "Select What To Plot:",
            ["Air Temp", "Track Temp", "Rainfall", "Air Pressure", "Relative Humidity", "Wind Direction", "Wind Speed"])
        
        st.text("Order of choosing will change the order in which elements appear on the plot.")

        df_weather = pd.read_parquet(f"{dir}/{year}/{dir_name}/{session}/weather.parquet")
        
        fig = fsp.plot_weather_data(df_weather, year, event, session, elements_to_plot)

        st.pyplot(fig)

        img_buffer = io.BytesIO()
        fig.savefig(img_buffer, format="png", bbox_inches="tight", pad_inches=0.1, dpi=300)
        img_buffer.seek(0)

        st.download_button(
            label="Download Weather Data",
            data=img_buffer,
            file_name=f"weather_data_{year}_{event.replace(' ', '_').lower()}_{session}.png",
            mime="image/png"
        )
    
    
    







# Schedule
with tab2:
    st.subheader(f"Event schedule for {year}")

    # Load the data
    df_schedule = pd.read_parquet(
    f"/Users/bartosz/f1_data/{year}/schedule.parquet",
    columns=["RoundNumber", "Country", "Location", "OfficialEventName", "EventDate", "EventName", "EventFormat"]
    )

    # Convert the EventDate column to datetime and set errors='coerce' to turn invalid dates to NaT
    df_schedule["EventDate"] = pd.to_datetime(df_schedule["EventDate"], errors="coerce")

    # Remove the time part by converting to date only
    df_schedule["EventDate"] = df_schedule["EventDate"].dt.date

    # Rename columns as needed
    df_schedule = df_schedule.rename(columns={
        "RoundNumber": "Round", 
        "OfficialEventName": "Official Name", 
        "EventDate": "Date", 
        "EventName": "Name", 
        "EventFormat": "Format"
    })

    df_schedule["Format"] = df_schedule["Format"].apply(lambda x: "Sprint" if x in ["sprint_qualifying", "sprint_shootout"] else x.title())
    st.dataframe(df_schedule, hide_index=True, use_container_width=True)









# Drivers
with tab3:
    tab1, tab2, tab3, tab4 = st.tabs(["F1", "F2", "F3", "F1 Academy"])
    today = datetime.today().strftime('%d-%m-%Y')

    with tab1:
        
        if not os.path.exists(f"/Users/bartosz/f1_data/f1_drivers_wiki_{today}.parquet"):
            fss.scrape_drivers_wiki(category="f1")

        df_f1_drivers = pd.read_parquet(f"/Users/bartosz/f1_data/f1_drivers_wiki_{today}.parquet")
        df_schedule = pd.read_parquet(f"{dir}/{year}/schedule.parquet", columns=["EventName", "EventDate", "DirName"])
        dir_name = df_schedule[df_schedule["EventName"] == event]["DirName"].iloc[0]
        
        df_results = pd.read_parquet(
                f"{dir}/{year}/{dir_name}/{session}/results.parquet",
                columns=["FullName"]
            )
        
        which_drivers = st.radio("Current or all drivers:", ["Current", "All"], horizontal=True)

        if which_drivers == "Current":
            choices = df_f1_drivers["Driver name"].to_list()
            df_f1_drivers = df_f1_drivers[df_f1_drivers["Driver name"].isin(
                    [fuzzy_match(df_results["FullName"][i], choices) for i in range(len(df_results["FullName"]))]
                )]

        
        height = (len(df_results["FullName"].to_list())+1) * 35
        st.dataframe(df_f1_drivers, hide_index=True, row_height=35, height=height, use_container_width=True)

    with tab2:
        if not os.path.exists(f"/Users/bartosz/f1_data/f2_drivers_wiki_{today}.parquet"):
            fss.scrape_drivers_wiki(category="f2")
        df_f2_drivers = pd.read_parquet(f"/Users/bartosz/f1_data/f2_drivers_wiki_{today}.parquet")
        st.dataframe(df_f2_drivers, hide_index=True, row_height=35, height=height, use_container_width=True)

    with tab3:
        if not os.path.exists(f"/Users/bartosz/f1_data/f3_drivers_wiki_{today}.parquet"):
            fss.scrape_drivers_wiki(category="f3")
        df_f3_drivers = pd.read_parquet(f"/Users/bartosz/f1_data/f3_drivers_wiki_{today}.parquet")
        st.dataframe(df_f3_drivers, hide_index=True, row_height=35, height=height, use_container_width=True)







# Records
with tab5:
    df_f1_drivers = df_f1_drivers = pd.read_parquet(f"/Users/bartosz/f1_data/f1_drivers_wiki_{datetime.today().strftime('%d-%m-%Y')}.parquet")
    
    driver, wins = df_f1_drivers[["Driver name", "Race wins"]].loc[df_f1_drivers["Race wins"].idxmax()].values
    st.subheader(f"Most Wins: {driver} - {wins} wins")
    
    driver, starts = df_f1_drivers[["Driver name", "Race starts"]].loc[df_f1_drivers["Race starts"].idxmax()].values
    st.subheader(f"Most Race Starts: {driver} - {starts} race starts")

    driver, pole_positions = df_f1_drivers[["Driver name", "Pole positions"]].loc[df_f1_drivers["Pole positions"].idxmax()].values
    st.subheader(f"Most Pole Positions: {driver} - {pole_positions} pole positions")

    driver, race_entries = df_f1_drivers[["Driver name", "Race entries"]].loc[df_f1_drivers["Race entries"].idxmax()].values
    st.subheader(f"Most Race Entries: {driver} - {race_entries} race entries")






# Circuits
with tab6:
    page = st.selectbox("Select Graphics:", ["Gear Shifts Information"])
    st.subheader("Gear Shifts Per Lap", help="Detailed information about how each plot works can be found in the guide tab.")

    df_schedule = pd.read_parquet(f"{dir}/{year}/schedule.parquet", columns=["EventName", "EventDate", "DirName"])
    dir_name = df_schedule[df_schedule["EventName"] == event]["DirName"].iloc[0]

    
    if page == "Gear Shifts Information":
        comparison = st.radio("Comparison", ["No", "Yes"])
        col1, col2 = st.columns(2)
        if comparison == "No":
            with col1:

                df_results = pd.read_parquet(
                    f"{dir}/{year}/{dir_name}/{session}/results.parquet",
                    columns=["Abbreviation", "TeamColorFastf1", "TeamName"]
                )

                driver = st.selectbox("Pick Driver:", list(df_results["Abbreviation"]))
            
            with col2:

                df_laps = pd.read_parquet(
                    f"{dir}/{year}/{dir_name}/{session}/laps.parquet",
                    columns=["LapNumber", "LapTime", "Team", "Driver"]
                )

                lap = st.selectbox("Pick Lap:", list(range(1, int(df_laps["LapNumber"].max()+1))))

            
            df_telemetry = pd.read_parquet(
                f"{dir}/{year}/{dir_name}/{session}/telemetry_data.parquet",
                filters=[('driver', '=', driver), ('lap', '=', lap)])

        
            fig = fsp.plot_gear_shifts_on_circuit(df_telemetry, df_laps, year, event, session, lap, driver, True, 122.3)
            st.pyplot(fig)

            img_buffer = io.BytesIO()
            fig.savefig(img_buffer, format="png", bbox_inches="tight", pad_inches=0.1, dpi=300)
            img_buffer.seek(0)

            st.download_button(
                label="Download Gear Shifts Per Lap",
                data=img_buffer,
                file_name=f"gear_shitfs_per_lap_{year}_{event.replace(' ', '_').lower()}_{session}_{driver}_{lap}.png",
                mime="image/png"
            )

            fig = fsp.plot_speed_over_lap(df_telemetry, df_laps, year, event, session, lap, driver, True, 122.3)
            st.pyplot(fig)

            st.download_button(
                label="Download Speed Over Lap",
                data=img_buffer,
                file_name=f"speed_over_lap{year}_{event.replace(' ', '_').lower()}_{session}_{driver}_{lap}.png",
                mime="image/png"
            )
        
        else:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                df_results = pd.read_parquet(
                    f"{dir}/{year}/{dir_name}/{session}/results.parquet",
                    columns=["Abbreviation", "TeamColorFastf1", "TeamName"]
                )

                driver_1 = st.selectbox("Driver 1:", list(df_results["Abbreviation"]))
            
            with col2:
                driver_2 = st.selectbox("Driver 2:", list(df_results["Abbreviation"]))
                
            
            with col3:
                df_laps = pd.read_parquet(
                    f"{dir}/{year}/{dir_name}/{session}/laps.parquet",
                    columns=["LapNumber", "LapTime", "Team", "Driver"]
                )

                lap_1 = st.selectbox("Lap Driver 1:", list(range(1, int(df_laps["LapNumber"].max()+1))))
            
            with col4:

                lap_2 = st.selectbox("Lap Driver 2:", list(range(1, int(df_laps["LapNumber"].max()+1))))
            
            df_telemetry = pd.read_parquet(
                f"{dir}/{year}/{dir_name}/{session}/telemetry_data.parquet",
                filters=[('driver', 'in', [driver_1, driver_2]), ('lap', 'in', [lap_1, lap_2])])
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig = fsp.plot_gear_shifts_on_circuit(df_telemetry, df_laps, year, event, session, lap_1, driver_1, True, 122.3)
                st.pyplot(fig)

                fig = fsp.plot_speed_over_lap(df_telemetry, df_laps, year, event, session, lap_1, driver_1, True, 122.3)
                st.pyplot(fig)

            with col2:
                fig = fsp.plot_gear_shifts_on_circuit(df_telemetry, df_laps, year, event, session, lap_2, driver_2, True, 122.3)
                st.pyplot(fig)

                fig = fsp.plot_speed_over_lap(df_telemetry, df_laps, year, event, session, lap_2, driver_2, True, 122.3)
                st.pyplot(fig)



# Guide
with tab7:
    st.subheader("Guide")
    st.subheader("Work in progress!")



# About
with tab8:
    st.subheader("About")
    st.text("Created and mainted by Bartosz Tylczynski. Using data from FastF1 and OpenF1 API.")






disclaimer = """
<div style="text-align: center;">
    <h2>Disclaimer</h2>
    <p>
        Formula Stats is an independent platform and is not affiliated with, endorsed by, or in any way officially connected to Formula 1, F1, the FIA (Fédération Internationale de l'Automobile), or any other Formula 1-related entities.<br>
        All trademarks, logos, team names, driver names are the property of their respective owners.<br>
        Formula Stats provides data and analysis based on publicly available information and does not represent any official Formula 1 organization.
    </p>
    <p>
        For any inquiries or concerns regarding the content presented on this platform, please contact us at bartosz.tylczynski@gmail.com.
    </p>
</div>
"""
st.markdown(disclaimer, unsafe_allow_html=True)



# Testing debugging
if __name__ == "__main__":

    pass