from flask import Flask, request, jsonify,render_template
from flask_cors import CORS
import requests
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# === App Initialization ===
app = Flask(__name__, static_folder='frontend', template_folder='frontend')
CORS(app)
load_dotenv()

# === API Keys ===
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

# === Crop Data ===
crop_data = [
    {"name": "wheat", "temp": (15, 25), "rainfall": (20, 30), "soil": "loamy"},
    {"name": "rice", "temp": (20, 35), "rainfall": (100, 200), "soil": "clay"},
    {"name": "millet", "temp": (25, 35), "rainfall": (20, 50), "soil": "sandy"},
    {"name": "barley", "temp": (12, 25), "rainfall": (30, 60), "soil": "loamy"},
    {"name": "maize", "temp": (18, 27), "rainfall": (50, 80), "soil": "clay"},
    {"name": "sorghum", "temp": (20, 35), "rainfall": (100, 300), "soil": "sandy"},
    {"name": "cotton", "temp": (20, 40), "rainfall": (150, 300), "soil": "loamy"},
    {"name": "tomato", "temp": (18, 30), "rainfall": (50, 100), "soil": "loamy"},
    {"name": "beans", "temp": (15, 25), "rainfall": (100, 200), "soil": "loamy"},
    {"name": "groundnut", "temp": (25, 35), "rainfall": (50, 150), "soil": "sandy"},
    {"name": "chickpea", "temp": (15, 30), "rainfall": (200, 300), "soil": "loamy"},
    {"name": "sweet potato", "temp": (18, 28), "rainfall": (60, 150), "soil": "loamy"},
    {"name": "cassava", "temp": (25, 35), "rainfall": (500, 1500), "soil": "clay"}
]

# === Helper Functions ===
def get_weather(city):
    """Fetch current weather data from OpenWeatherMap."""
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric"
    print(f"Requesting weather data from URL: {url}")  # Log the URL for debugging

    response = requests.get(url)

    # Log the response status code and content for debugging
    print(f"Response status code: {response.status_code}")
    print(f"Response content: {response.text}")

    if response.status_code == 200:
        data = response.json()
        temp = data['main']['temp']
        humidity = data['main']['humidity']
        rainfall = data.get('rain', {}).get('1h', 0)
        return temp, humidity, rainfall
    elif response.status_code == 401:
        print("❌ Invalid API key.")
    elif response.status_code == 404:
        print(f"❌ City '{city}' not found.")
    else:
        print(f"❌ Unexpected error: {response.status_code}")
    return None, None, None



def get_city_coordinates(city):
    """Get latitude and longitude for a city."""
    geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={city}&appid={OPENWEATHER_API_KEY}"
    response = requests.get(geo_url).json()

    if response and len(response) > 0:
        lat, lon = response[0]['lat'], response[0]['lon']
        return lat, lon
    else:
        return None, None


def get_rainfall_from_nasa(lat, lon):
    """Fetch average rainfall from NASA POWER API."""
    today = datetime.today().strftime('%Y%m%d')
    past_six_months = (datetime.today() - timedelta(days=180)).strftime('%Y%m%d')

    nasa_url = f"https://power.larc.nasa.gov/api/temporal/daily/point?parameters=PRECTOTCORR&latitude={lat}&longitude={lon}&start={past_six_months}&end={today}&community=re&format=json"
    
    response = requests.get(nasa_url).json()

    try:
        rainfall_values = list(response['properties']['parameter']['PRECTOTCORR'].values())
        filtered_values = [value for value in rainfall_values if value != -999]
        avg_rainfall = (sum(filtered_values) / len(filtered_values)) * 25.4  # Convert to mm
        return round(avg_rainfall, 2)
    except KeyError:
        print("❌ No rainfall data found.")
        return 0


def recommend_crops(soil, temp, avg_rainfall):
    """Recommend suitable crops based on soil, temperature, and rainfall."""
    recommended = []
    alternative = []

    for crop in crop_data:
        strict_temp = crop["temp"][0] <= temp <= crop["temp"][1]
        strict_rainfall = crop["rainfall"][0] <= avg_rainfall <= crop["rainfall"][1]
        soil_match = crop["soil"] == soil

        relaxed_temp = crop["temp"][0] - 5 <= temp <= crop["temp"][1] + 5
        relaxed_rainfall = crop["rainfall"][0] - 40 <= avg_rainfall <= crop["rainfall"][1] + 40

        if strict_temp and strict_rainfall and soil_match:
            recommended.append(crop["name"])
        elif relaxed_temp and relaxed_rainfall and soil_match:
            alternative.append(crop["name"])

    return recommended, alternative


def water_efficiency_tip():
    """Return water-saving farming tip."""
    return "💡 Use drip irrigation or mulching techniques to conserve water."


def climate_adaptation_tip(rainfall, temp):
    """Provide climate adaptation tips."""
    if rainfall < 50:
        return "🌾 Low rainfall detected. Plant drought-resistant crops like millet or sorghum."
    elif temp > 30:
        return "☀️ High temperature detected. Grow heat-tolerant crops like maize or millet."
    else:
        return "✅ Optimal climate for multiple crops. Focus on soil health and efficient irrigation."


# === Flask Route ===
# === Flask Route ===
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/recommend', methods=['POST'])
def recommend():
    """API endpoint for crop recommendation."""
    data = request.json
    city = data.get('city')
    soil = data.get('soil')

    # Validate inputs
    if not city or not soil:
        return jsonify({"error": "City and soil type are required."}), 400

    # Get weather data
    temp, humidity, rainfall = get_weather(city)
    
    if temp is None:
        return jsonify({"error": "Failed to fetch weather data."}), 500

    # Get coordinates and NASA rainfall data
    lat, lon = get_city_coordinates(city)
    if lat is None or lon is None:
        return jsonify({"error": "Invalid city name."}), 400

    avg_rainfall = get_rainfall_from_nasa(lat, lon)

    # Recommend crops
    recommended, alternative = recommend_crops(soil, temp, avg_rainfall)

    # Prepare the response
    response = {
        "city": city,
        "temp": temp,
        "humidity": humidity,
        "rainfall": rainfall,
        "avg_rainfall": avg_rainfall,
        "recommended": recommended,
        "alternative": alternative,
        "water_tip": water_efficiency_tip(),
        "climate_tip": climate_adaptation_tip(rainfall, temp)
    }

    return jsonify(response)


# === Run Server ===
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

