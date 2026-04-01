# first install requests -> pip install requests

import requests  # input requests library

import requests
import json

req = {
    "latitude": 40.71,
    "longitude": -74.00,
    "daily": ["temperature_2m_max", "temperature_2m_min"], # Request daily variables
    "temperature_unit": "fahrenheit",
    "timezone": "auto" # Best practice: adjusts 'today' and 'tomorrow' to local time
}

url = "https://api.open-meteo.com/v1/forecast"
response = requests.get(url, params=req)
print(response.url)
print(response.status_code)

if response: # possible because the .__bool__() is overloaded
    print("Success!")
    print('data returned: ', response.text)
    print('headers: ', response.headers)
    print(json.dumps(response.json(), indent=4))
    data = response.json()
    date_tomorrow = data['daily']['time'][1]
    temp_max = data['daily']['temperature_2m_max'][1]
    temp_min = data['daily']['temperature_2m_min'][1]
    print(f"Forecast for {date_tomorrow}:")
    print(f"High: {temp_max}°F")
    print(f"Low: {temp_min}°F")
else:
    raise Exception(f"Non-success status code: {response.status_code}")
