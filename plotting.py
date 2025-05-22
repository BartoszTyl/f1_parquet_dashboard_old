import matplotlib.pyplot as plt
from matplotlib import colormaps
# from matplotlib.patches import Patch
from matplotlib.collections import LineCollection
import matplotlib as mpl

import seaborn as sns
import plotly
import pandas as pd
import numpy as np 
import re
from typing import Dict

import matplotlib.patches as mpatches
# from adjustText import adjust_text

plt.style.use('dark_background')

master_dir = "/Users/bartosz/f1_data"

def add_watermark(
        fig,
        watermark_text: str = "FORMULA STATS",
        alpha: int = 0.35,
        fontsize: int = 90,
        rotation: int = 30,
        y_position: float = 0.5
    ) -> plt.Figure:

    fig.text(
        0.5, y_position,
        watermark_text,
        fontsize=fontsize,
        color='gray',
        alpha=alpha,
        ha='center',
        va='center',
        weight='bold',
        rotation=rotation,
        transform=fig.transFigure
    )
    return fig



def get_teams_order(
        dir: str,
        year: int,
        event: str,
        session: str,
        fastest_first: bool = True) -> pd.Index:
    
    df_schedule = pd.read_parquet(f"{dir}/{year}/schedule.parquet", columns=["EventName", "EventDate", "DirName"])
    dir_name = df_schedule[df_schedule["EventName"] == event]["DirName"].iloc[0]
    
    df_laps = pd.read_parquet(
        f"{dir}/{year}/{dir_name}/{session}/laps.parquet",
        columns=["LapTime", "Team"]
    )

    df_laps["Lap Time (s)"] = df_laps["LapTime"].dt.total_seconds()

    teams_order = df_laps.groupby("Team").median()["Lap Time (s)"].sort_values(ascending=fastest_first).index

    return teams_order



def get_drivers_order(
        dir: str,
        year: int,
        event: str,
        session: str,
        fastest_first: bool = True) -> pd.Index:
    
    df_schedule = pd.read_parquet(f"{dir}/{year}/schedule.parquet", columns=["EventName", "EventDate", "DirName"])
    dir_name = df_schedule[df_schedule["EventName"] == event]["DirName"].iloc[0]
    
    df_laps = pd.read_parquet(
        f"{dir}/{year}/{dir_name}/{session}/laps.parquet",
        columns=["LapTime", "Driver"]
    )

    df_laps["Lap Time (s)"] = df_laps["LapTime"].dt.total_seconds()

    drivers_order = df_laps.groupby("Driver").median()["Lap Time (s)"].sort_values(ascending=fastest_first).index

    return drivers_order



def get_teams_colors(
        dir: str = "/Users/bartosz/f1_data",
        year: int = None,
        event: str = None,
        session: str = None,
        color_map: str = "fastf1") -> Dict[str, str]:
    
    df_schedule = pd.read_parquet(f"{dir}/{year}/schedule.parquet", columns=["EventName", "EventDate", "DirName"])
    dir_name = df_schedule[df_schedule["EventName"] == event]["DirName"].iloc[0]

    color_column = "TeamColorOfficial" if color_map == "official" else "TeamColorFastf1"

    df_results = pd.read_parquet(
        f"{dir}/{year}/{dir_name}/{session}/results.parquet",
        columns=["TeamName", color_column]
    ).dropna(subset=["TeamName", color_column])

    # Ensure colors are properly formatted, fallback to white
    teams_colors = {
        team: (f"#{color}" if not str(color).startswith("#") else str(color))
        for team, color in zip(df_results["TeamName"], df_results[color_column])
    }

    return teams_colors



def format_lap_time(seconds: float) -> str:
    # Ensure that seconds is a float
    if isinstance(seconds, pd.Timedelta):
        seconds = seconds.total_seconds()
    elif not isinstance(seconds, (int, float)):
        raise ValueError("Expected seconds to be a number or Timedelta")

    minutes = int(seconds // 60)
    seconds = seconds % 60
    milliseconds = int((seconds % 1) * 1000)
    return f"{minutes:01}:{int(seconds):02}.{milliseconds:03}"



def plot_team_lap_time_dist(
        laps: pd.DataFrame,
        year: int,
        event: str,
        session: str,
        teams_colors: Dict,
        remove_outliers: str = "Yes",
        watermark: bool = True) -> plt.Figure:


    if remove_outliers == "Yes":
        Q1 = laps['Lap Time (s)'].quantile(0.25)
        Q3 = laps['Lap Time (s)'].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        laps = laps[(laps['Lap Time (s)'] >= lower_bound) & (laps['Lap Time (s)'] <= upper_bound)]

    teams_order = laps.groupby("Team")["Lap Time (s)"].median().sort_values().index

    fig, ax = plt.subplots(figsize=(15, 8))

    sns.boxplot(
        data=laps,
        x="Team",
        y="Lap Time (s)",
        hue="Team",
        order=teams_order,
        palette=teams_colors,
        whiskerprops=dict(color="white"),
        boxprops=dict(edgecolor="white"),
        medianprops=dict(color="grey"),
        capprops=dict(color="white"),
        flierprops=dict(marker='o', markerfacecolor='lightgrey', markersize=5, linestyle='none'),
        width=0.6,
        dodge=False
    )

    avg_lap_times = laps.groupby('Team')['Lap Time (s)'].median().reindex(teams_order).dropna()
    tick_labels = [f"{team} \n {format_lap_time(avg_lap_time)}" for team, avg_lap_time in zip(avg_lap_times.index, avg_lap_times)]

    plt.xticks(ticks=np.arange(len(tick_labels)), labels=tick_labels, rotation=45)
    
    
    # Main title
    ax.set_title("Team Lap Time Distribution", fontsize=18, color='white', fontweight='bold', y=1.05)

    # Subtitle positioned below the main title
    ax.text(0.5, 1.02, f"{year} | {event} | {session.replace('_', ' ').title()}", ha='center', fontsize=13, color='white', transform=ax.transAxes)


    plt.grid(visible=False)
    ax.set(xlabel=None)

    return add_watermark(fig) if watermark else fig



def plot_violin_dist_point_socrers(
        laps: pd.DataFrame,
        results: pd.DataFrame,
        year: int,
        event: str,
        session: str,
        teams_colors: Dict,
        remove_outliers: str = "Yes",
        show_tyre_compounds: str = "Yes",
        watermark: bool = True) -> plt.Figure:

    finishing_order = results[:10]["Abbreviation"]

    palette = {
        driver: teams_colors.get(team_name, "#FFFFFF")
        for driver, team_name in zip(results["Abbreviation"], results["TeamName"])
        }


    if remove_outliers == "Yes":
        Q1 = laps['Lap Time (s)'].quantile(0.25)
        Q3 = laps['Lap Time (s)'].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        laps = laps[(laps['Lap Time (s)'] >= lower_bound) & (laps['Lap Time (s)'] <= upper_bound)]

    fig, ax = plt.subplots(figsize=(15, 8))

    # Driver laps violin plot
    sns.violinplot(data=laps,
                    x="Driver",
                    y="Lap Time (s)",
                    hue="Driver",
                    inner=None,
                    scale="width",
                    density_norm="area",
                    order=finishing_order,
                    dodge=False,
                    palette=palette,
                    ax=ax
                    )

    if show_tyre_compounds == "Yes":
        compound_palette = dict(zip(laps["Compound"].unique(), laps.drop_duplicates(subset=["Compound"])["CompoundColor"]))
        # Tyre compounds plot
        sns.swarmplot(data=laps,
                    x="Driver",
                    y="Lap Time (s)",
                    order=finishing_order,
                    hue="Compound",
                    palette=compound_palette,
                    hue_order=list(compound_palette.keys()),
                    dodge=False,
                    linewidth=1,
                    edgecolor='black',
                    size=5,
                    ax=ax
                    )
        
        ax.legend(fontsize=12, title="Tyre Compound", title_fontsize=12, markerscale=2.5)

    ax.set_xlabel("Driver")
    ax.set_ylabel("Lap Time (s)")


    # Main title
    ax.set_title("Point Scorers Lap Time Distribution", fontsize=18, color='white', fontweight='bold', y=1.05)

    # Subtitle positioned below the main title
    ax.text(0.5, 1.02, f"{year} | {event} | {session.replace('_', ' ').title()}", ha='center', fontsize=13, color='white', transform=ax.transAxes)

    return add_watermark(fig) if watermark else fig



def plot_drivers_lap_time_dist(
        laps: pd.DataFrame,
        results: pd.DataFrame,
        year: int,
        event: str,
        session: str,
        teams_colors: Dict,
        remove_outliers: str = "Yes",
        watermark: bool = True) -> plt.Figure:
    
    # Create a palette mapping driver to team color
    palette = {
        driver: teams_colors.get(team_name, "#FFFFFF")
        for driver, team_name in zip(results["Abbreviation"], results["TeamName"])
    }

    if remove_outliers == "Yes":
        Q1 = laps['Lap Time (s)'].quantile(0.25)
        Q3 = laps['Lap Time (s)'].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        laps = laps[(laps['Lap Time (s)'] >= lower_bound) & (laps['Lap Time (s)'] <= upper_bound)]

    fig, ax = plt.subplots(figsize=(15, 8))

    # Order drivers by median lap time
    drivers_order = laps.groupby("Driver")["Lap Time (s)"].median().sort_values().index

    avg_lap_times = laps.groupby('Driver')['Lap Time (s)'].median().reindex(drivers_order)

    tick_labels = [
        f"{driver} \n {format_lap_time(avg_lap_time) if not pd.isna(avg_lap_time) else 'No Data'}"
        for driver, avg_lap_time in zip(avg_lap_times.index, avg_lap_times)
    ]

    sns.boxplot(data=laps,
                x="Driver",
                y="Lap Time (s)",
                hue="Driver",
                order=drivers_order,
                palette=palette,
                whiskerprops=dict(color="white"),
                boxprops=dict(edgecolor="white"),
                medianprops=dict(color="grey"),
                capprops=dict(color="white"),
                flierprops=dict(marker='o', markerfacecolor='lightgrey', markersize=5, linestyle='none'),
                width=0.5,
                dodge=False
                )
    
    # Set custom x-ticks with rotation and labels
    plt.xticks(
        ticks=np.arange(len(tick_labels)),
        labels=tick_labels,
        ha='center',
        rotation=45,
    )

    # Main title
    ax.set_title("Drivers Lap Time Distribution", fontsize=18, color='white', fontweight='bold', y=1.05)

    # Subtitle positioned below the main title
    ax.text(0.5, 1.02, f"{year} | {event} | {session.replace('_', ' ').title()}", ha='center', fontsize=13, color='white', transform=ax.transAxes)

    # Create a team-based legend
    unique_teams = results[['TeamName']].drop_duplicates().sort_values(by="TeamName")
    team_legend = [
        mpatches.Patch(facecolor=teams_colors.get(team, "#FFFFFF"), label=team)
        for team in unique_teams["TeamName"]
    ]

    ax.legend(handles=team_legend, title="Teams", loc='upper left', bbox_to_anchor=(1, 1))

    return add_watermark(fig) if watermark else fig



def plot_weather_data(
        weather: pd.DataFrame,
        year: int,
        event: str,
        session: str,
        elements_to_plot: list = None,
        watermark: bool = True) -> plt.Figure:
    
    # Set default value for elements_to_plot if None (i.e., plot everything)
    if elements_to_plot is None or len(elements_to_plot) == 0:
        elements_to_plot = ["Air Temp", "Track Temp", "Rainfall", "Wind Speed", "Wind Direction", "Air Pressure", "Relative Humidity"]
    
    # Load the schedule and weather data
    # df_schedule = pd.read_parquet(f"{dir}/{year}/schedule.parquet", columns=["EventName", "EventDate", "DirName"])
    # dir_name = df_schedule[df_schedule["EventName"] == event]["DirName"].iloc[0]
    # df_weather = pd.read_parquet(f"{dir}/{year}/{dir_name}/{session}/weather.parquet")
    
    # Convert Time to minutes
    weather["Time (m)"] = weather["Time"].dt.total_seconds() // 60
    
    # Define the available plots for each weather element
    plot_data = {
        "Air Temp": {"data": weather["AirTemp"], "ylabel": "Air Temp (°C)", "title": "Air Temperature", "color": 'r'},
        "Track Temp": {"data": weather["TrackTemp"], "ylabel": "Track Temp (°C)", "title": "Track Temperature", "color": 'm'},
        "Rainfall": {"data": weather["Rainfall"], "ylabel": "Rainfall", "title": "Rainfall", "color": 'c', "yticks": [0, 1], "yticklabels": ["No", "Yes"]},
        "Wind Direction": {"data": weather["WindDirection"], "ylabel": "Wind Direction (°)", "title": "Wind Direction", "color": 'y'},
        "Wind Speed": {"data": weather["WindSpeed"], "ylabel": "Wind Speed (m/s)", "title": "Wind Speed", "color": 'orange'},
        "Air Pressure": {"data": weather["Pressure"], "ylabel": "Air Press (mbar)", "title": "Air Pressure", "color": 'g'},
        "Relative Humidity": {"data": weather["Humidity"], "ylabel": "Rel Humid (%)", "title": "Humidity", "color": 'b'}
    }

    # Prepare the grid ratio based on selected elements
    num_plots = len(elements_to_plot)
    if num_plots > 2:
        height_ratios = [
            1.5 if elem in ["Air Temp", "Track Temp", "Wind Speed"] else 
            0.5 if elem in ["Rainfall", "Relative Humidity"] else
            1 if elem in ["Air Pressure"] else
            1 for elem in elements_to_plot
        ]
    else:
        height_ratios = [
            1.5 for elem in elements_to_plot
        ]

    # Adjust number of rows based on selected elements
    fig, ax = plt.subplots(num_plots, gridspec_kw={'height_ratios': height_ratios}, constrained_layout=True, figsize=(12, 2 * num_plots))

    # Ensure ax is always an array, even for one plot
    if num_plots == 1:
        ax = [ax]
    
    # Plot the selected elements in the order they were chosen
    for i, element in enumerate(elements_to_plot):
        data = plot_data[element]
        ax[i].plot(weather["Time (m)"], data["data"], color=data["color"], linewidth=2)
        ax[i].set_ylabel(data["ylabel"], color='white', fontsize=12)
        
        # Custom ticks for Rainfall
        if element == "Rainfall":
            ax[i].set_yticks(data["yticks"])
            ax[i].set_yticklabels(data["yticklabels"], fontsize=12)
        
        ax[i].grid(True, linestyle='--', alpha=0.6)
        ax[i].tick_params(axis='both', labelsize=10)
    
    # Main title
    ax[0].set_title("Weather Data", fontsize=18, color='white', fontweight='bold', y=1.18, x=0.47)

    # Subtitle positioned below the main title
    ax[0].text(0.47, 1.08, f"{year} | {event} | {session.replace('_', ' ').title()}", ha='center', fontsize=13, color='white', transform=ax[0].transAxes)

    # Adjust watermark size and rotation based on number of plots
    if watermark:
        # Font size should increase with more plots
        watermark_font_size = min(50 + num_plots * 10, 120)  # Max font size of 150
        watermark_rotation = min(0 + (num_plots - 1) * 10, 55)  # Max rotation of 60 degrees
        
        # Add watermark with adjusted parameters
        add_watermark(fig, fontsize=watermark_font_size, rotation=watermark_rotation)

    return fig



def plot_telemetry():
    pass



def plot_team_pace_comparison(
        laps: pd.DataFrame,
        results: pd.DataFrame,
        year: int,
        event: str,
        session: str,
        teams_colors: Dict,
        lap: str = "Average",
        lap_number: int = None,
        remove_outliers: str = "Yes",
        watermark: bool = True) -> plt.Figure:

    if remove_outliers == "Yes":
        Q1 = laps['Lap Time (s)'].quantile(0.25)
        Q3 = laps['Lap Time (s)'].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        laps = laps[(laps['Lap Time (s)'] >= lower_bound) & (laps['Lap Time (s)'] <= upper_bound)]

    fig, ax = plt.subplots(figsize=(15, 8))

    laps = laps.sort_values("LapTime")

    

    # Process data according to lap and lap_number
    if lap == "Average":
        team_lap = laps.groupby("Team")["Lap Time (s)"].median()
        results[f"Team{lap}Lap"] = results["TeamName"].map(team_lap)
        results[f"PercentageDiff{lap}Lap"] = (((results[f"Team{lap}Lap"] - results[f"Team{lap}Lap"].min()) / results[f"Team{lap}Lap"].min()) * 100).round(2)
    
    elif lap == "Fastest":
        team_lap = laps.groupby("Team")["Lap Time (s)"].min()
        results[f"Team{lap}Lap"] = results["TeamName"].map(team_lap)
        results[f"PercentageDiff{lap}Lap"] = (((results[f"Team{lap}Lap"] - results[f"Team{lap}Lap"].min()) / results[f"Team{lap}Lap"].min()) * 100).round(2)

    elif lap == "Specific":
        team_lap = laps[laps["LapNumber"] == lap_number].groupby("Team")["Lap Time (s)"].first()
        results[f"Team{lap}Lap"] = results["TeamName"].map(team_lap)
        results[f"PercentageDiff{lap}Lap"] = (((results[f"Team{lap}Lap"] - results[f"Team{lap}Lap"].min()) / results[f"Team{lap}Lap"].min()) * 100).round(2)    

    results = results.groupby("TeamName").agg({
                f'PercentageDiff{lap}Lap': 'first',
                'TeamColorFastf1': 'first',
                f"Team{lap}Lap": 'first'
            }).reset_index()
    
    results = results.sort_values(by=f"PercentageDiff{lap}Lap")

    ax.bar(results["TeamName"], results[f"PercentageDiff{lap}Lap"], color=results['TeamColorFastf1'])

    ax.set_ylabel('Percentage Difference (%)')
    ax.set_xlabel('Team & Time (s)')
    ax.set_title('Avg Lap Team Pace Comparison')

    tick_labels = [
        f"{team}\n{format_lap_time(lap_time)}"
            for team, lap_time in zip(
            results["TeamName"],
            results[f"Team{lap}Lap"]
            )
        ]
    
    for index, value in enumerate(results[f"PercentageDiff{lap}Lap"]):
        ax.text(index, value + 0.1, f"+{value:.2f}%", ha='center', va='top')
    
    ax.set_xticks(np.arange(len(results["TeamName"])))
    ax.set_xticklabels(tick_labels, rotation=45)

    ax.set_ylim(results[f"PercentageDiff{lap}Lap"].max() + 1, 0)

    # Main title
    ax.set_title("Team Pace Comparison", fontsize=18, color='white', fontweight='bold', y=1.05)

    # Subtitle positioned below the main title
    ax.text(0.5, 1.02, f"{year} | {event} | {session.replace('_', ' ').title()} | Lap: {lap if lap in ['Average', 'Fastest'] else lap_number}", ha='center', fontsize=13, color='white', transform=ax.transAxes)

    return add_watermark(fig) if watermark else fig



def plot_gear_shifts_on_circuit(
        telemetry: pd.DataFrame,
        laps: pd.DataFrame,
        year: int,
        event: str,
        session: str,
        lap: int,
        driver: str,
        watermark: bool = True,
        rotation_angle: int = 0
        ) -> plt.Figure:
    
    telemetry = telemetry[(telemetry["driver"] == driver) & (telemetry["lap"] == lap)]

    x = np.array(telemetry['X'].values)
    y = np.array(telemetry['Y'].values)

    points = np.array([x, y]).T.reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)
    gear = telemetry['nGear'].to_numpy().astype(float)

    # Rotation matrix for counter-clockwise rotation
    angle_rad = np.deg2rad(rotation_angle)
    rotation_matrix = np.array([[np.cos(angle_rad), -np.sin(angle_rad)], 
                                [np.sin(angle_rad), np.cos(angle_rad)]])

    # Apply the rotation to the points in the track
    rotated_segments = []
    for segment in segments:
        rotated_segment = np.dot(segment.reshape(-1, 2), rotation_matrix)
        rotated_segments.append(rotated_segment)
    rotated_segments = np.array(rotated_segments)

    cmap = colormaps['Paired']
    lc_comp = LineCollection(rotated_segments, norm=plt.Normalize(1, cmap.N+1), cmap=cmap)
    lc_comp.set_array(gear)
    lc_comp.set_linewidth(4)
    
    fig, ax = plt.subplots(figsize=(10, 8))

    plt.gca().add_collection(lc_comp)
    plt.axis('equal')
    plt.tick_params(labelleft=False, left=False, labelbottom=False, bottom=False)

    cbar = plt.colorbar(mappable=lc_comp, label="Gear",
                    boundaries=np.arange(1, 10))
    cbar.set_ticks(np.arange(1.5, 9.5))
    cbar.set_ticklabels(np.arange(1, 9))
    
    # Main title
    ax.set_title("Gear Shifts Per Lap", fontsize=18, color='white', fontweight='bold', y=1.04)

    lap_time = laps[(laps["LapNumber"] == lap) & (laps["Driver"] == driver)]["LapTime"].iloc[0]

    # Subtitle positioned below the main title
    ax.text(0.5, 1.02, f"{year} | {event} | {session.replace('_', ' ').title()} | Driver: {driver} | Lap: {lap} ({format_lap_time(lap_time)})", ha='center', fontsize=10, color='white', transform=ax.transAxes)

    return add_watermark(fig, fontsize=60) if watermark else fig



def plot_speed_over_lap(
        telemetry: pd.DataFrame,
        laps: pd.DataFrame,
        year: int,
        event: str,
        session: str,
        lap: int,
        driver: str,
        watermark: bool = True,
        rotation_angle: float = 0
        ) -> plt.Figure:
    
    telemetry = telemetry[(telemetry["driver"] == driver) & (telemetry["lap"] == lap)]

    x = telemetry['X'].to_numpy()
    y = telemetry['Y'].to_numpy()
    
    points = np.array([x, y]).T.reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)
    speed = telemetry['Speed'].to_numpy().astype(float)

    # Rotation matrix for counter-clockwise rotation
    angle_rad = np.deg2rad(rotation_angle)
    rotation_matrix = np.array([[np.cos(angle_rad), -np.sin(angle_rad)], 
                                [np.sin(angle_rad), np.cos(angle_rad)]])

    # Apply the rotation to the points in the track
    rotated_segments = []
    for segment in segments:
        rotated_segment = np.dot(segment.reshape(-1, 2), rotation_matrix)
        rotated_segments.append(rotated_segment)
    rotated_segments = np.array(rotated_segments)

    cmap = mpl.cm.plasma
    norm = plt.Normalize(vmin=50, vmax=350)  # Set fixed range for speed
    lc_comp = LineCollection(rotated_segments, norm=norm, cmap=cmap, linewidth=4)
    lc_comp.set_array(speed)

    fig, ax = plt.subplots(figsize=(10, 8))
    
    plt.gca().add_collection(lc_comp)
    plt.axis('equal')
    plt.tick_params(labelleft=False, left=False, labelbottom=False, bottom=False)

    cbar = plt.colorbar(mappable=lc_comp, label="Speed (km/h)")
    cbar.set_ticks(np.linspace(50, 350, num=6))
    cbar.set_ticklabels([f"{s:.0f}" for s in np.linspace(50, 350, num=6)])

    lap_time = laps[(laps["LapNumber"] == lap) & (laps["Driver"] == driver)]["LapTime"].iloc[0]

    ax.set_title("Speed Over Lap", fontsize=18, color='white', fontweight='bold', y=1.04)
    ax.text(0.5, 1.02, f"{year} | {event} | {session.replace('_', ' ').title()} | Driver: {driver} | Lap: {lap} ({format_lap_time(lap_time)})", 
            ha='center', fontsize=10, color='white', transform=ax.transAxes)

    return add_watermark(fig, fontsize=60) if watermark else fig



def plot_setup_performance():
    pass


def plot_mean_vs_max_speed():
    pass







# Testing debugging

if __name__ == "__main__":
    
    # print(get_teams_order(master_dir, 2025, "Australian Grand Prix", "Race"))
    # print(get_drivers_order(master_dir, 2025, "Australian Grand Prix", "Race"))
    # print(get_teams_colors(master_dir, 2025, "Australian Grand Prix", "Race"))


    # results = pd.read_parquet(
    #         f"/Users/bartosz/f1_data/2025/2025-03-16_australian_grand_prix/race/results.parquet",
    #         columns=["Abbreviation", "TeamColorFastf1", "TeamName"]
    #     )


    # teams_colors = get_teams_colors(master_dir, 2025, "Australian Grand Prix", "Race")

    # # Map driver to team color with a fallback
    # driver_colors = {
    # driver: teams_colors.get(team_name, "#FFFFFF")
    # for driver, team_name in zip(results["Abbreviation"], results["TeamName"])
    # }

    # print(len(driver_colors))
    pass