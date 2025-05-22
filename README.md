# 🏎️ F1 Parquet Dashboard

**F1 Parquet Dashboard** is a Streamlit-based interactive dashboard designed to explore, visualise, and analyse Formula 1 data from 2018 onwards. Whether you’re a casual fan or a strategy enthusiast, this tool simplifies F1 data analytics by using preloaded datasets and dynamic plotting features. All data originates from **FastF1** and is converted to Parquet files for faster reading and reduced storage requirements.



## 🚀 Features

- **Interactive Visuals**: Explore lap time distributions, team pace comparisons, full race data, telemetry, and weather stats.
- **Dynamic Sidebar**: Select a year, event, and session. Options update based on your selections.
- **Tabs Interface**:
  - **Visuals** – Interactive charts with downloadable graphics.
  - **Schedule** – Event overview by season.
  - **Drivers List** – Driver profiles from Wikipedia (F1, F2, F3, F1 Academy).
  - **Circuits** - Circuit based visuals (speed/gear changes over a lap).
  - **Standings, Records, Guide, About** – (placeholders for expansion).


## 📦 Project Structure

```
├── dashboard_app.py           # Main Streamlit app
├── plotting.py                # Plotting functions
├── scrape.py                  # Scraping functions (Wikipedia)
├── /f1_data                   # Cached parquet files (schedule, telemetry, laps, results, weather)
│   └── YYYY
│       └── event/session/
│           ├── laps.parquet
│           ├── telemetry_data.parquet
│           ├── results.parquet
│           ├── weather.parquet
│       └── schedule.parquet
└── README.md
```



## 🧰 Dependencies

Install required packages with:

```bash
pip install streamlit pandas matplotlib rapidfuzz unidecode
```

Parquet support requires:

```bash
pip install pyarrow
```



## ▶️ Running the App

```bash
streamlit run dashboard_app.py
```

Make sure to set `dir = "/path/to/your/f1_data"` inside the script to point to your cached data location.



## 📁 Data Requirements

This app expects a local `/f1_data` directory structured by year, event, and session, containing pre-saved `.parquet` files including:

- `laps.parquet`
- `telemetry_data.parquet`
- `results.parquet`
- `weather.parquet`
- `schedule.parquet`
- `race_control_messages.parquet`
- `session_status.parquet`

You must also generate or scrape `f1_drivers_wiki_YYYY-MM-DD.parquet` for driver info (via the provided `scrape_drivers_wiki()` function).



## 📸 Sample Visuals

- Team Lap Time Distributions (with outlier control) ![Team Lap Times](examples/images/Team%20Lap%20Time%20Dist%202025%20Chinese%20Grand%20Prix.png)
- Violin plots of point scorers' pace ![Team Lap Times](examples/images/Violin%20Point%20Scorers%202025%20Chinese%20Grand%20Prix%20Race.png)
- Multi-element weather plots ![Team Lap Times](examples/images/Weather%20Data%202025%20Chinese%20Grand%20Prix.png)
- Circuit based plots of speed and gear changes
<p float="centre">
  <img src="examples/images/Gear%20Shifts%20Per%20Lap%202025%20Chinese%20Grand%20Prix.png" width="45%" />
  <img src="examples/images/Speed%20Per%20Lap%202025%20Chinese%20Grand%20Prix.png" width="45%" />
</p>



## ✍🏻 Acknowledgements ##

This project uses data provided by the FastF1 library, created and maintained by Theo Ehrlich. Huge thanks to the FastF1 community for making detailed F1 data accessible for analysis and visualization.



## 👨‍💻 Author

Bartosz Tylczynski – UoL Computer Science student & Formula 1 strategy enthusiast  
📍 Built for educational and analytical purposes.



## 📄 License

MIT License – feel free to use, adapt, and expand this project.



## 🏁 Notes
This project is not longer maintained and will be soon replaced with a new version. Formula Stats (Django-based web app) is currently in development, open alpha version will be released soon!


## ‼️ Disclaimer
F1 Parquet Dashboard is an independent platform and is not affiliated with, endorsed by, or in any way officially connected to Formula 1, F1, the FIA (Fédération Internationale de l'Automobile), or any other Formula 1-related entities.
All trademarks, logos, team names, driver names are the property of their respective owners.
Formula Stats provides data and analysis based on publicly available information and does not represent any official Formula 1 organization.
