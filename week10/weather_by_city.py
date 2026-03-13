# first install requests -> pip install requests
import requests

def get_weather_by_city(city, state):
    # 1. Geocoding API: Convert City/State to Coordinates
    # We combine city and state in the 'name' parameter for better accuracy

    geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&admin1={state}&count=1&language=en&format=json"
    print(geo_url)

    geo_response = requests.get(geo_url)
    geo_data = geo_response.json()


    if "results" not in geo_data:
        print(f"Error: Could not find location '{city} {state}'")
        return

    # Extract coordinates and location details
    result = geo_data["results"][0]
    lat = result["latitude"]
    lon = result["longitude"]
    get_forcast(city_name, state_name, lat, lon)

def get_forcast(city, state, lat, lon):
    req = {
        "latitude": lat,
        "longitude": lon,
        "daily": ["temperature_2m_max", "temperature_2m_min"], # Request daily variables
        "temperature_unit": "fahrenheit",
        "timezone": "auto" # Best practice: adjusts 'today' and 'tomorrow' to local time
    }

    url = "https://api.open-meteo.com/v1/forecast"
    response = requests.get(url, params=req)
    print(response.url)
    print(response.status_code)

    if response: # possible because the .__bool__() is overloaded
        data = response.json()
        date_tomorrow = data['daily']['time'][1]
        temp_max = data['daily']['temperature_2m_max'][1]
        temp_min = data['daily']['temperature_2m_min'][1]
        print(f"Forecast for {date_tomorrow} at {city}, {state}:")
        print(f"High: {temp_max}°F")
        print(f"Low: {temp_min}°F")
    else:
        raise Exception(f"Non-success status code: {response.status_code}")

if __name__ == "__main__":
    try:
        city_name = input("Enter city name: ")
        state_name = input("Enter state name: ")
        get_weather_by_city(city_name, state_name)
    except Exception as e:
        print(e)
