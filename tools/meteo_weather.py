import openmeteo_requests
import requests
import requests_cache
import pandas as pd
from retry_requests import retry
import os
import datetime
from utils.keystore import auth_tools
from tools.tool_base_class import ToolBaseClass


class WeatherBase(ToolBaseClass):
    """
    A base class for weather tools.
    """

    def __init__(self):
        self.api_key = os.getenv("OPENWEATHER_API_KEY")
        self.geodecoder_api_url = "http://api.openweathermap.org/geo/1.0/direct?q={city_name},{country_code}&limit=5&appid={api_key}"
        self.openmeteo = openmeteo_requests.Client()

    def get_lat_and_lon(self, city_name, country_code):
        geodecoder_request_url = self.geodecoder_api_url.format(
            city_name=city_name, country_code=country_code, api_key=self.api_key
        )
        error, response_body = self.get_request(geodecoder_request_url)

        if error:
            return error, None, None

        try:
            lat = response_body[0]["lat"]
            lon = response_body[0]["lon"]
        except Exception as e:
            return "Could not find latitude and longitude for the city. Please double check the city_name and the country_code.", None, None

        return None, lat, lon

    def get_open_meteo_response(self, url, params):
        try:
            response = self.openmeteo.weather_api(url, params=params)
        except Exception as e:
            return e, None

        return None, response
    
    def get_request(self, url):
        try:
            x = requests.get(url)
        except Exception as e:
            return e, None

        response_body = x.json()

        if type(response_body) == dict and "message" in response_body:
            return response_body["message"], None

        return None, response_body

    def get_hourly_data_df(self, response):
        hourly = response.Hourly()
        hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
        hourly_rain = hourly.Variables(1).ValuesAsNumpy()
        hourly_snowfall = hourly.Variables(2).ValuesAsNumpy()

        hourly_data = {"date": pd.date_range(
            start = pd.to_datetime(hourly.Time(), unit = "s", utc = True),
            end = pd.to_datetime(hourly.TimeEnd(), unit = "s", utc = True),
            freq = pd.Timedelta(seconds = hourly.Interval()),
            inclusive = "left"
        )}
        hourly_data["temperature (F)"] = hourly_temperature_2m
        hourly_data["rain"] = hourly_rain
        hourly_data["snowfall"] = hourly_snowfall
        hourly_dataframe = pd.DataFrame(data = hourly_data)
        return hourly_dataframe

    def get_daily_data_dict(self, response):
        # ["temperature_2m_mean", "rain_sum", "snowfall_sum", "precipitation_hours"]
        daily = response.Daily()
        daily_temperature_mean = daily.Variables(0).ValuesAsNumpy()
        daily_rain = daily.Variables(1).ValuesAsNumpy()
        daily_snowfall = daily.Variables(2).ValuesAsNumpy()
        daily_precipitation_hours = daily.Variables(3).ValuesAsNumpy()

        daily_data = {"date": pd.date_range(
            start = pd.to_datetime(daily.Time(), unit = "s", utc = True),
            end = pd.to_datetime(daily.TimeEnd(), unit = "s", utc = True),
            freq = pd.Timedelta(seconds = daily.Interval()),
            inclusive = "left"
        )}

        daily_data["temperature (°F)"] = daily_temperature_mean
        daily_data["total rain (mm)"] = daily_rain
        daily_data["total snowfall (mm)"] = daily_snowfall
        daily_data["precipitation hours (hours)"] = daily_precipitation_hours

        daily_data_dict = [{
            "date": date_data.strftime("%Y-%m-%d %H:%M:%S"),
            "temperature (°F)": str(temperature),
            "total rain (mm)": str(rain),
            "total snowfall (mm)": str(snowfall),
            "precipitation hours (hours)": str(precipitation_hours)
        } for date_data, temperature, rain, snowfall, precipitation_hours in zip(daily_data["date"], daily_data["temperature (°F)"], daily_data["total rain (mm)"], daily_data["total snowfall (mm)"], daily_data["precipitation hours (hours)"])]
        
        return daily_data_dict
        

class CurrentWeather(WeatherBase):
    """
    current_weather - gets real time weather for a city given a city name and country code.

    args:
        city_name: A string, the name of the city.
        country_code: A string, the country code of the city. Please use ISO 3166 country codes.

    output:
        error: A string, an error message if an error occurred
        result: The response object of the weather API

    """

    def __init__(self):
        super().__init__()
        self.tool_name = "current_weather"
        self.current_weather_api_url = "https://api.open-meteo.com/v1/forecast"

    def get_description(self):
        desc = """current_weather: Retrieves current daily average for temperature and daily sums of rainfall, snowfall, and hours of precipitation for a city given a city_name and a country_code. It does not return historical information about weather.
        Your input should be a json (args json schema): {{"city_name" : string,  country_code: string }} The Action to trigger this API should be calculator and the input parameters should be a json dict string. 
        Here is a description of each of the parameters:

        city_name: A string, the name of the city.
        country_code: A string, the country code of the city. Please use ISO 3166 country codes.
        
        Here are some example Action Input to this tool:

        {"city_name" : "London", "country_code": "GB"}
        {"city_name" : "Calgary", "country_code": "CA"}
        """
        return desc
    
    def get_firefunction_spec(self):

        desc = {
            "name": "current_weather",
            "description": "Retrieves current daily average for temperature and daily sums of rainfall, snowfall, and hours of precipitation for a city given a city_name and a country_code. It does not return historical information about weather.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city_name": {
                        "type": "string",
                        "description": "The name of the city.",
                    },
                    "country_code": {
                        "type": "string",
                        "description": "The country code of the city. Please use ISO 3166 country codes.",
                    },
                },
                "required": ["city_name", "country_code"],
            },
        }
        return desc

    def validate(self, args={}):
        # TODO: add validation for country code being a valid ISO 3166 country code
        if (
            "city_name" not in args
            or "country_code" not in args
            or not isinstance(args["input_query"], str)
        ):
            return False
        return True

    def call(self, args={}):

        try:
            city_name = args["city_name"]
        except:
            return {"error": "Required field \"city_name\" not provided.", "result": ""}

        try:
            country_code = args["country_code"]
        except:
            return {"error": "Required field \"country_code\" not provided.", "result": ""}
        historical_date = args.get("historical_date", "")
        if historical_date:
            date_string = historical_date
            start_date_obj = datetime.datetime.strptime(date_string, "%m/%d/%Y") #- datetime.timedelta(days=7)
            end_date_obj = start_date_obj + datetime.timedelta(days=6)
            end_date_obj = min(end_date_obj, datetime.datetime.now())



            # Format the datetime object to the desired output format
            start_formatted_date = start_date_obj.strftime("%Y-%m-%d")
            end_formatted_date = end_date_obj.strftime("%Y-%m-%d")


            historical_tool = HistoricalWeather()
            hist_out=historical_tool.call(
            {
                "city_name": city_name,
                "country_code": country_code,
                "start_date": str(start_formatted_date),
                "end_date": str(end_formatted_date),
            })
            return {"error": hist_out['error'], "result": hist_out['result']}


    
        error, lat, lon = self.get_lat_and_lon(city_name, country_code)

        if error:
            return {"error": error, "result": ""}

        params = {"latitude": lat, "longitude": lon, "daily": ["temperature_2m_mean", "rain_sum", "snowfall_sum", "precipitation_hours"], "temperature_unit": "fahrenheit"}
        error, responses = self.get_open_meteo_response(self.current_weather_api_url, params)

        daily_data_dict = self.get_daily_data_dict(responses[0])

        if error:
            return {"error": error, "result": ""}

        return {"error": "", "result": daily_data_dict}


class HistoricalWeather(WeatherBase):
    """
    historical_weather - gets historical weather for a city given city name, country code, start time and end time. The historical records date back to 1940s but there is a 5-day delay in the data, meaning you cannot get current weather data for the last 5 days.

    args:
        city_name: A string, the name of the city.
        country_code: A string, the country code of the city. Please use ISO 3166 country codes.
        start_date: Start time in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format

    output:
        error: A string, an error message if an error occurred
        result: The response object of the weather API

    """

    def __init__(self):
        super().__init__()
        self.tool_name = "historical_weather"
        self.historical_weather_api_url = "https://archive-api.open-meteo.com/v1/archive"

    def get_description(self):
        desc = """historical_weather: Retrieves historical weather for a city given city name, country code, start time and end time. The historical records date back to 1940s but there is a 5-day delay in the data, meaning you cannot get current weather data for the last 5 days.
        Your input should be a json (args json schema): {{"city_name" : string,  country_code: string, start_date: date, end_date: date }} The Action to trigger this API should be calculator and the input parameters should be a json dict string. 
        Here is a description of each of the parameters:

        city_name: A string, the name of the city.
        country_code: A string, the country code of the city. Please use ISO 3166 country codes.
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format

        Here are some example Action Input to this tool:

       {"city_name": "London","country_code": "GB", "start_date": "2024-03-09", "end_date": "2024-03-23"}    
       """
        return desc
    
    def get_firefunction_spec(self):
        desc = {
            "name": "historical_weather",
            "description": "Retrieves daily averages for temperature and daily sums of rainfall, snowfall, and hours of precipitation for a city given city name, country code, start time and end time. The historical records date back to 1940s but there is a 5-day delay in the data, meaning you cannot get current weather data for the last 5 days.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city_name": {
                        "type": "string",
                        "description": "The name of the city.",
                    },
                    "country_code": {
                        "type": "string",
                        "description": "The country code of the city. Please use ISO 3166 country codes.",
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Start date in YYYY-MM-DD format.",
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date in YYYY-MM-DD format.",
                    },
                },
                "required": ["city_name", "country_code", "start_date", "end_date"],
            },
        }

        return desc

    def validate(self, args={}):
        # TODO: add validation for country code being a valid ISO 3166 country code
        if (
            "city_name" not in args
            or "country_code" not in args
            or not isinstance(args["input_query"], str)
        ):
            return False
        return True

    def call(self, args={}):

        try:
            city_name = args["city_name"]
        except:
            return {"error": "Required field \"city_name\" not provided.", "result": ""}
        try:
            country_code = args["country_code"]
        except:
            return {"error": "Required field \"country_code\" not provided.", "result": ""}
        try:
            start_date = args["start_date"]
        except:
            return {"error": "Required field \"start_date\" not provided.", "result": ""}
        try:
            end_date = args["end_date"]
        except:
            return {"error": "Required field \"end_date\" not provided.", "result": ""}
        error, lat, lon = self.get_lat_and_lon(city_name, country_code)

        if error:
            return {"error": error, "result": ""}

        params = {"latitude": lat, "longitude": lon, "start_date": start_date, "end_date": end_date,  "daily": ["temperature_2m_mean", "rain_sum", "snowfall_sum", "precipitation_hours"], "temperature_unit": "fahrenheit"}
        error, responses = self.get_open_meteo_response(self.historical_weather_api_url, params)

        if not responses:
            return {"error": "Meteo Weather API didn't return anything", "result": ""}
        daily_data_dict = self.get_daily_data_dict(responses[0])

        if error:
            return {"error": error, "result": ""}

        return {"error": "", "result": daily_data_dict}
