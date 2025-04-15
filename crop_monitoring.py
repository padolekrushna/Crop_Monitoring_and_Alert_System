import streamlit as st
import requests
import sqlite3
import pandas as pd
from twilio.rest import Client

class CropMonitoringSystem:
    def __init__(self):
        # Weather API settings
        self.api_key = "f766eb5e5eda8de7e9ad20f39d11521a"
        self.db_name = "crop_thresholds.db"

        # Twilio settings
        self.twilio_sid = "AC2d156a75e71a330fefb9cb64852b6db4"
        self.twilio_auth_token = "81ae2d911c47a1484d7f660bd7f7ff56"
        self.from_number = "+15025762436"

        # Initialize database
        self.setup_database()

    def setup_database(self):
        """Create and initialize the SQLite database with crop thresholds"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        # Create table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS crop_weather_thresholds (
                crop TEXT PRIMARY KEY,
                max_rain_mm INTEGER,
                min_temp_c INTEGER,
                max_temp_c INTEGER
            )
        """)

        # Initial crop data
        crop_data = [
            ("Tomato", 40, 15, 35),
            ("Wheat", 60, 10, 28),
            ("Rice", 80, 20, 38),
            ("Corn", 55, 15, 30),
            ("Cotton", 50, 18, 35),
            ("Potatoes", 45, 10, 28),
            ("Soybeans", 60, 15, 32)
        ]

        # Insert data
        cursor.executemany("""
            INSERT OR REPLACE INTO crop_weather_thresholds
            (crop, max_rain_mm, min_temp_c, max_temp_c) VALUES (?, ?, ?, ?)
        """, crop_data)

        conn.commit()
        conn.close()

    def get_all_crops(self):
        """Fetch all crops from the database"""
        conn = sqlite3.connect(self.db_name)
        df = pd.read_sql_query("SELECT * FROM crop_weather_thresholds", conn)
        conn.close()
        return df

    def get_crop_thresholds(self, crop_name):
        """Fetch thresholds for a specific crop"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM crop_weather_thresholds WHERE crop = ?", (crop_name,))
        result = cursor.fetchone()
        conn.close()

        if result:
            return {
                "crop": result[0],
                "max_rain_mm": result[1],
                "min_temp_c": result[2],
                "max_temp_c": result[3]
            }
        return None

    def add_or_update_crop(self, crop_name, max_rain, min_temp, max_temp):
        """Add or update a crop's thresholds"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO crop_weather_thresholds
            (crop, max_rain_mm, min_temp_c, max_temp_c) VALUES (?, ?, ?, ?)
        """, (crop_name, max_rain, min_temp, max_temp))

        conn.commit()
        conn.close()

    def fetch_weather(self, lat, lon):
        """Fetch weather data from OpenWeatherMap API"""
        url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={self.api_key}&units=metric"

        try:
            response = requests.get(url)
            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"Error fetching weather data: {response.status_code}")
                return None
        except Exception as e:
            st.error(f"Exception when fetching weather: {e}")
            return None

    def check_weather_against_thresholds(self, weather_data, crop_name):
        """Check if weather conditions are suitable for the crop"""
        if not weather_data:
            return []

        thresholds = self.get_crop_thresholds(crop_name)
        if not thresholds:
            return []

        alerts = []

        for entry in weather_data["list"]:
            temp = entry["main"]["temp"]
            rain = entry.get("rain", {}).get("3h", 0)
            dt_txt = entry["dt_txt"]

            issues = []
            if temp < thresholds["min_temp_c"]:
                issues.append(f"Temperature too low: {temp}°C (min: {thresholds['min_temp_c']}°C)")
            if temp > thresholds["max_temp_c"]:
                issues.append(f"Temperature too high: {temp}°C (max: {thresholds['max_temp_c']}°C)")
            if rain > thresholds["max_rain_mm"]:
                issues.append(f"Rainfall too high: {rain}mm (max: {thresholds['max_rain_mm']}mm)")

            if issues:
                alerts.append({
                    "timestamp": dt_txt,
                    "temperature": temp,
                    "rainfall": rain,
                    "issues": issues
                })

        return alerts

    def send_sms(self, to_number, message):
        """Send SMS alert using Twilio"""
        try:
            client = Client(self.twilio_sid, self.twilio_auth_token)
            message = client.messages.create(
                body=message,
                from_=self.from_number,
                to=to_number
            )
            return True
        except Exception as e:
            st.error(f"Failed to send SMS: {e}")
            return False
''')

print("Created crop_monitoring.py")

# Cell 4: Create the Streamlit application file
with open('app.py', 'w') as f:
  f.write('''
import streamlit as st
import sqlite3
import pandas as pd
import requests
import json
from datetime import datetime

# Initialize the crop monitoring system
from crop_monitoring import CropMonitoringSystem
cms = CropMonitoringSystem()

# Set page config
st.set_page_config(
    page_title="Crop Monitoring and Alert System",
    page_icon="🌱",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main {
        padding: 2rem;
    }
    .alert-box {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .alert-critical {
        background-color: #FFEBEE;
        border-left: 5px solid #F44336;
    }
    .alert-warning {
        background-color: #FFF8E1;
        border-left: 5px solid #FFC107;
    }
    .section-header {
        padding-top: 1rem;
        padding-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# App header
st.title("🌱 Crop Monitoring and Alert System")
st.markdown("Monitor weather conditions for your crops and receive alerts when conditions are unfavorable.")

# Sidebar
with st.sidebar:
    st.header("Configuration")

    # Location settings
    st.subheader("Location")
    col1, col2 = st.columns(2)
    with col1:
        lat = st.number_input("Latitude", value=19.7515, step=0.0001, format="%.4f")
    with col2:
        lon = st.number_input("Longitude", value=75.7139, step=0.0001, format="%.4f")

    # Crop selection
    st.subheader("Crop")
    crops_df = cms.get_all_crops()
    selected_crop = st.selectbox("Select crop to monitor", crops_df["crop"].tolist())

    # Show selected crop thresholds
    if selected_crop:
        thresholds = cms.get_crop_thresholds(selected_crop)
        if thresholds:
            st.info(f"""
            **{selected_crop} Thresholds**
            - Max Rainfall: {thresholds['max_rain_mm']} mm
            - Temperature Range: {thresholds['min_temp_c']}°C to {thresholds['max_temp_c']}°C
            """)

    # SMS notification settings
    st.subheader("SMS Notifications")
    enable_sms = st.checkbox("Enable SMS alerts", value=False)
    if enable_sms:
        phone_number = st.text_input("Phone number (with country code)", value="+91")

    # Fetch weather data button
    if st.button("Fetch Weather Data"):
        st.session_state.weather_data = cms.fetch_weather(lat, lon)
        if st.session_state.weather_data:
            st.session_state.alerts = cms.check_weather_against_thresholds(
                st.session_state.weather_data,
                selected_crop
            )
            if enable_sms and 'alerts' in st.session_state and st.session_state.alerts:
                alert_message = f"⚠️ ALERT: Unfavorable weather for {selected_crop}. Check app for details."
                cms.send_sms(phone_number, alert_message)
        st.success("Weather data updated!")

# Main content
tabs = st.tabs(["Weather Forecast", "Alerts", "Manage Crops"])

# Weather Forecast Tab
with tabs[0]:
    st.header("Weather Forecast")

    if 'weather_data' in st.session_state and st.session_state.weather_data:
        weather_data = st.session_state.weather_data

        # Current weather
        current = weather_data["list"][0]
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Temperature", f"{current['main']['temp']}°C")
        with col2:
            st.metric("Humidity", f"{current['main']['humidity']}%")
        with col3:
            st.metric("Wind", f"{current['wind']['speed']} m/s")

        # Forecast table
        st.subheader("5-Day Forecast")
        forecast_data = []

        for entry in weather_data["list"]:
            date = datetime.fromisoformat(entry["dt_txt"].replace(" ", "T"))
            forecast_data.append({
                "Date": date.strftime("%Y-%m-%d"),
                "Time": date.strftime("%H:%M"),
                "Temperature (°C)": entry["main"]["temp"],
                "Humidity (%)": entry["main"]["humidity"],
                "Conditions": entry["weather"][0]["description"],
                "Rainfall (mm)": entry.get("rain", {}).get("3h", 0)
            })

        forecast_df = pd.DataFrame(forecast_data)
        st.dataframe(forecast_df, use_container_width=True)
    else:
        st.info("Click 'Fetch Weather Data' to see the forecast")

# Alerts Tab
with tabs[1]:
    st.header("Weather Alerts")

    if 'alerts' in st.session_state and st.session_state.alerts:
        alerts = st.session_state.alerts

        st.warning(f"{len(alerts)} potential weather issues detected for {selected_crop}")

        for i, alert in enumerate(alerts):
            with st.expander(f"Alert for {alert['timestamp']}"):
                st.write(f"**Temperature:** {alert['temperature']}°C")
                st.write(f"**Rainfall:** {alert['rainfall']} mm")
                st.write("**Issues:**")
                for issue in alert['issues']:
                    st.markdown(f"- {issue}")
    else:
        st.info("No alerts to display. Click 'Fetch Weather Data' to check for potential issues.")

# Manage Crops Tab
with tabs[2]:
    st.header("Manage Crop Thresholds")

    # Display current crops
    st.subheader("Current Crops")
    crops_df = cms.get_all_crops()
    st.dataframe(crops_df, use_container_width=True)

    # Add or update crop
    st.subheader("Add or Update Crop")
    with st.form("crop_form"):
        crop_name = st.text_input("Crop Name")
        col1, col2, col3 = st.columns(3)
        with col1:
            max_rain = st.number_input("Max Rainfall (mm)", min_value=0, value=50)
        with col2:
            min_temp = st.number_input("Min Temperature (°C)", value=10)
        with col3:
            max_temp = st.number_input("Max Temperature (°C)", value=35)

        submit_button = st.form_submit_button("Save Crop")

        if submit_button and crop_name:
            cms.add_or_update_crop(crop_name, max_rain, min_temp, max_temp)
            st.success(f"Saved threshold values for {crop_name}")
            st.experimental_rerun()

# Add footer
st.markdown("---")
st.caption("Crop Monitoring and Alert System v1.0 | Created with Streamlit")