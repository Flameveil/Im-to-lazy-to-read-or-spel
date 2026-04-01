import requests

"""
AI Prompt:
using open-meteo api write a python app that will prompt the user for a city and state. Using the city and state,
the app will then print out the next ten days of forecast showing the minimum and maximum temperature in 
Fahrenheit and the daily rainfall in inches.
"""

def get_coordinates(city, state):
    """Converts City and State to Latitude/Longitude using Open-Meteo Geocoding API."""
    search_query = f"{city}, {state}"
    geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={search_query}&count=10&language=en&format=json"

    response = requests.get(geo_url)
    data = response.json()

    if "results" not in data:
        return None

    result = data["results"][0]
    return {
        "lat": result["latitude"],
        "lon": result["longitude"],
        "full_name": f"{result['name']}, {result.get('admin1', state)}"
    }


def get_weather(lat, lon):
    """Fetches 10-day forecast in Fahrenheit and inches."""
    weather_url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": ["temperature_2m_max", "temperature_2m_min", "precipitation_sum"],
        "temperature_unit": "fahrenheit",
        "precipitation_unit": "inch",
        "timezone": "auto",
        "forecast_days": 10
    }

    response = requests.get(weather_url, params=params)
    return response.json()


def main():
    print("--- 10-Day Weather Forecast ---")
    city = input("Enter City: ").strip()
    state = input("Enter State: ").strip()

    print(f"\nSearching for {city}...")
    location = get_coordinates(city, state)

    if not location:
        print("Could not find that location. Please check the spelling.")
        return

    weather = get_weather(location['lat'], location['lon'])
    daily = weather['daily']

    print(f"\n10-Day Forecast for {location['full_name']}:")
    print(f"{'Date':<12} | {'Max Temp':<10} | {'Min Temp':<10} | {'Rain (in)'}")
    print("-" * 55)

    for i in range(len(daily['time'])):
        date = daily['time'][i]
        t_max = daily['temperature_2m_max'][i]
        t_min = daily['temperature_2m_min'][i]
        rain = daily['precipitation_sum'][i]

        print(f"{date:<12} | {t_max:>5}°F    | {t_min:>5}°F    | {rain:.2f} in")


if __name__ == "__main__":
    main()