from django.shortcuts import render
import requests
from datetime import datetime, timedelta
from .models import WeatherData
from django.core.mail import send_mail
from django.conf import settings

# Function to handle weather search and display weather info
def weather(request):
    weather_data = None  # Initialize weather_data as None

    if request.method == 'POST':  # If the request is a POST (form submission)
        city = request.POST.get('city', '').strip()  # Get city from form input and strip whitespace
        api_key = 'b6d6b910138522e1ca243a92ba3bec4f'  # OpenWeather API key
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&units=metric&appid={api_key}"

        response = requests.get(url)
        if response.status_code == 200:  # Check for a successful response
            data = response.json()

            # Extract and organize the necessary data
            weather_data = {
                'city': city,
                'temperature': data['main']['temp'],
                'humidity': data['main']['humidity'],
                'wind_speed': data['wind']['speed'],
                'clouds': data['clouds']['all'],
                'description': data['weather'][0]['description'],
                'icon': data['weather'][0]['icon'],
            }
        else:
            weather_data = {'error': 'City not found or API error'}

    return render(request, 'weatherapp/weather.html', {'weather_data': weather_data})

# Function to retrieve hourly temperatures for a given city
def get_hourly_temperatures(city):
    API_KEY = 'b6d6b910138522e1ca243a92ba3bec4f'  # OpenWeather API key
    BASE_URL = f"http://api.openweathermap.org/data/2.5/onecall?lat={{lat}}&lon={{lon}}&exclude=current,minutely,daily,alerts&appid={API_KEY}&units=metric"

    # Get the location coordinates (latitude and longitude) based on the city
    location_url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}"
    response = requests.get(location_url)

    if response.status_code == 200:
        location_data = response.json()
        lat = location_data['coord']['lat']
        lon = location_data['coord']['lon']

        hourly_response = requests.get(BASE_URL.format(lat=lat, lon=lon))

        if hourly_response.status_code == 200:
            hourly_data = hourly_response.json()
            hourly_temperatures = {}

            # Collect temperatures for every 2 hours
            for i in range(0, 24, 2):
                hour_data = hourly_data['hourly'][i]
                time = convert_time(hour_data['dt'])
                temp = hour_data['temp']
                hourly_temperatures[time] = temp

            return hourly_temperatures
    return None  # Return None if there is an error

# Function to get air quality index for a given city
def get_air_quality(city):
    API_KEY = 'b6d6b910138522e1ca243a92ba3bec4f'
    location_url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}"
    response = requests.get(location_url)

    if response.status_code == 200:
        location_data = response.json()
        lat = location_data['coord']['lat']
        lon = location_data['coord']['lon']

        air_quality_url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={API_KEY}"
        air_quality_response = requests.get(air_quality_url)

        if air_quality_response.status_code == 200:
            air_quality_data = air_quality_response.json()
            aqi = air_quality_data['list'][0]['main']['aqi']  # Air Quality Index (AQI: 1 to 5)
            return aqi
    return None  # Return None if there is an error

# Function to retrieve yesterday's temperature from the database
def get_yesterday_temperature(city):
    yesterday = datetime.now() - timedelta(days=1)
    yesterday_data = WeatherData.objects.filter(city=city, timestamp__date=yesterday.date()).first()

    if yesterday_data:
        return yesterday_data.temperature  # Adjust this according to your model's field
    return None  # Return None if no data is found

# Helper function to convert timestamps into readable time
def convert_time(timestamp):
    return datetime.fromtimestamp(timestamp).strftime('%H:%M')

# Fetch all weather data including current, hourly, and additional metrics
def fetch_weather_data(city):
    API_KEY = 'b6d6b910138522e1ca243a92ba3bec4f'
    BASE_URL = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"

    response = requests.get(BASE_URL)
    if response.status_code == 200:
        data = response.json()

        current_temp = data['main']['temp']
        hourly_temps = get_hourly_temperatures(city)

        precipitation_expected = 'rain' in data or 'snow' in data
        precipitation_probability = data.get('rain', {}).get('1h', 0)
        precipitation_probability = (precipitation_probability * 100) if precipitation_probability else 0  # Convert to percentage

        wind_speed = data['wind']['speed']
        humidity = data['main']['humidity']
        air_quality = get_air_quality(city)
        sunrise_time = convert_time(data['sys']['sunrise'])
        sunset_time = convert_time(data['sys']['sunset'])

        yesterday_temp = get_yesterday_temperature(city)

        return {
            'city_name': city,
            'current_temp': current_temp,
            'hourly_temps': hourly_temps,
            'precipitation_expected': precipitation_expected,
            'precipitation_probability': precipitation_probability,  # Add this line
            'wind_speed': wind_speed,
            'yesterday_temp': yesterday_temp,
            'humidity': humidity,
            'air_quality': air_quality,
            'sunrise_time': sunrise_time,
            'sunset_time': sunset_time,
        }
    else:
        return None  # Handle error scenario

# Function for comparing current temperature to a baseline or previous value
def calculate_temperature_comparison(current_temp):
    # Example logic to compare temperature (you can adjust this as needed)
    return current_temp - 15  # Example: comparison with 15°C baseline

# View function to display detailed weather information
def details_view(request):
    city_name = request.GET.get('city', '').strip()  # Get the city from the URL query

    weather_data = fetch_weather_data(city_name)
    if weather_data is None:
        return render(request, 'weatherapp/details.html', {'error': 'Weather data not found'})

    current_temp = weather_data['current_temp']
    hourly_temps = weather_data['hourly_temps']
    wind_speed = weather_data['wind_speed']
    humidity = weather_data['humidity']
    air_quality = weather_data['air_quality']
    sunrise_time = weather_data['sunrise_time']
    sunset_time = weather_data['sunset_time']

    precipitation_expected = weather_data['precipitation_expected']
    precipitation_probability = weather_data['precipitation_probability']

    comparison = calculate_temperature_comparison(current_temp)

    context = {
        'city_name': city_name,
        'current_temp': current_temp,
        'hourly_temps': hourly_temps,
        'wind_speed': wind_speed,
        'humidity': humidity,
        'air_quality': air_quality,
        'sunrise_time': sunrise_time,
        'sunset_time': sunset_time,
        'precipitation_expected': precipitation_expected,
        'precipitation_probability': precipitation_probability,
        'comparison': comparison,
    }

    return render(request, 'weatherapp/details.html', context)

def dashboard(request):
    # Add your dashboard logic here (if needed)
    return render(request, 'weatherapp/dashboard.html')

def about(request):
    # Add your about page logic here (if needed)
    return render(request, 'weatherapp/about.html')
    
def globe(request):
    # Add your about page logic here (if needed)
    return render(request, 'weatherapp/globe.html')

import requests

import requests

def travel_view(request):
    travel_data = None  # Initialize as None
    error = None

    if request.method == 'POST':
        city = request.POST.get('city', '').strip()
        email = request.POST.get('email', '').strip()  # Get the email from the form

        # Step 1: Fetch geocoding info (latitude and longitude) using OpenCage API
        open_cage_api_key = '9eaac027b18e446ebf2386de3dc0cd29'
        geocode_url = f"https://api.opencagedata.com/geocode/v1/json?q={city}&key={open_cage_api_key}"
        geocode_response = requests.get(geocode_url)

        if geocode_response.status_code == 200:
            geocode_data = geocode_response.json()
            if geocode_data['results']:
                lat = geocode_data['results'][0]['geometry']['lat']
                lon = geocode_data['results'][0]['geometry']['lng']

                # Step 2: Fetch weather data using OpenWeather API
                open_weather_api_key = 'b6d6b910138522e1ca243a92ba3bec4f'
                weather_url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units=metric&appid={open_weather_api_key}"
                weather_response = requests.get(weather_url)

                if weather_response.status_code == 200:
                    weather_data = weather_response.json()

                    # Step 3: Fetch points of interest using Foursquare API
                    foursquare_api_key = 'fsq3h8wwlUXZhdBV4PLgj5k6RToDOTtxsP3BFNmAPvPz7WY='
                    poi_url = f"https://api.foursquare.com/v3/places/search?ll={lat},{lon}&radius=2000&limit=10"
                    headers = {
                        "Authorization": foursquare_api_key
                    }
                    poi_response = requests.get(poi_url, headers=headers)

                    if poi_response.status_code == 200:
                        poi_data = poi_response.json()
                        poi_list = poi_data.get('results', [])

                        # Step 4: Fetch images for each POI using Foursquare Photos API
                        for poi in poi_list:
                            poi_id = poi['fsq_id']
                            image_url = f"https://api.foursquare.com/v3/places/{poi_id}/photos"
                            image_response = requests.get(image_url, headers=headers)

                            if image_response.status_code == 200:
                                image_data = image_response.json()
                                if image_data:
                                    image = image_data[0]
                                    poi['image_url'] = f"{image['prefix']}original{image['suffix']}"
                                else:
                                    poi['image_url'] = None
                            else:
                                poi['image_url'] = None

                        # Step 5: Aggregate the data for display on the travel page
                        travel_data = {
                            'city': city,
                            'latitude': lat,
                            'longitude': lon,
                            'temperature': weather_data['main']['temp'],
                            'weather_description': weather_data['weather'][0]['description'],
                            'points_of_interest': poi_list,
                        }

                        # Step 6: Send email if an email address is provided
                        if email:
                            subject = f"Points of Interest in {city}"
                            poi_details = "\n".join(
                                [f"{poi['name']} - {poi['location']['address']}" for poi in poi_list]
                            )
                            message = f"Here are some interesting places to visit in {city}:\n\n{poi_details}"
                            try:
                                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])
                                travel_data['email_sent'] = True
                                travel_data['email'] = email
                            except Exception as e:
                                error = f"Failed to send email: {str(e)}"
                    else:
                        error = f"Error fetching points of interest: {poi_response.status_code} {poi_response.text}"
                else:
                    error = f"Error fetching weather data: {weather_response.status_code} {weather_response.text}"
            else:
                error = "Location not found in OpenCage."
        else:
            error = f"Error fetching geocoding information: {geocode_response.status_code} {geocode_response.text}"

    return render(request, 'weatherapp/travel.html', {'travel_data': travel_data, 'error': error})