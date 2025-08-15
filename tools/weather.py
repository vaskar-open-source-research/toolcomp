import requests
from tools.tool_base_class import ToolBaseClass
import os


class WeatherBase(ToolBaseClass):
    """
    A base class for weather tools.
    """

    def __init__(self):
        self.tool_name = "weather"
        self.api_key = os.getenv("OPENWEATHER_API_KEY")
        self.geodecoder_api_url = "http://api.openweathermap.org/geo/1.0/direct?q={city_name},{country_code}&limit=5&appid={api_key}"

    def get_lat_and_lon(self, city_name, country_code):
        geodecoder_request_url = self.geodecoder_api_url.format(
            city_name=city_name, country_code=country_code, api_key=self.api_key
        )
        error, response_body = self.get_request(geodecoder_request_url)

        if error:
            return error, None, None

        lat = response_body[0]["lat"]
        lon = response_body[0]["lon"]

        return None, lat, lon

    def get_request(self, url):
        try:
            x = requests.get(url)
        except Exception as e:
            return e, None

        response_body = x.json()

        if type(response_body) == dict and "message" in response_body:
            return response_body["message"], None

        return None, response_body


class CurrentWeather(WeatherBase):
    """
    Current Weather - gets real time weather for a city given a city name and country code.

    args:
        city_name: A string, the name of the city.
        country_code: A string, the country code of the city. Please use ISO 3166 country codes.

    output:
        error: A string, an error message if an error occurred
        result: The response object of the weather API

    """

    def __init__(self):
        super().__init__()
        self.current_weather_api_url = "https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}"

    def get_description(self):
        desc = """current_weather: Retrieves real time weather for a city given a city_name and a country_code. It does not return historical information about weather.
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
            "description": "Retrieves real time weather for a city given a city_name and a country_code. It does not return historical information about weather.",
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
        error, lat, lon = self.get_lat_and_lon(city_name, country_code)

        if error:
            return {"error": error, "result": ""}

        current_weather_request_url = self.current_weather_api_url.format(
            lat=lat, lon=lon, api_key=self.api_key
        )

        error, response_body = self.get_request(current_weather_request_url)

        if error:
            return {"error": error, "result": ""}

        return {"error": "", "result": response_body}


class HistoricalWeather(WeatherBase):
    """
    Weather - gets historical weather for a city given city name, country code, start time and end time.

    args:
        city_name: A string, the name of the city.
        country_code: A string, the country code of the city. Please use ISO 3166 country codes.
        start_time: Start time (unix time, UTC time zone), e.g. start=1369728000
        end_time: End time (unix time, UTC time zone), e.g. end=1369789200

    output:
        error: A string, an error message if an error occurred
        result: The response object of the weather API

    """

    def __init__(self):
        super().__init__()
        self.historical_weather_api_url = "https://history.openweathermap.org/data/2.5/history/city?lat={lat}&lon={lon}&type=hour&start={start}&end={end}&appid={api_key}"

    def get_description(self):
        desc = """historical_weather: Retrieves historical weather for a city given city name, country code, start time and end time. 
        Your input should be a json (args json schema): {{"city_name" : string,  country_code: string, start: string, end: string }} The Action to trigger this API should be calculator and the input parameters should be a json dict string. 
        Here is a description of each of the parameters:

        city_name: A string, the name of the city.
        country_code: A string, the country code of the city. Please use ISO 3166 country codes.
        start_time: Start time (unix time, UTC time zone), e.g. start=1369728000
        end_time: End time (unix time, UTC time zone), e.g. end=1369789200

        Here are some example Action Input to this tool:

        {"city_name" : "London", "country_code": "GB", start_time: "1369728000", end_time: "1369789200"}
        """
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
        city_name = args["city_name"]
        country_code = args["country_code"]
        start_time = args["start_time"]
        end_time = args["end_time"]
        error, lat, lon = self.get_lat_and_lon(city_name, country_code)

        if error:
            return {"error": error, "result": ""}

        current_weather_request_url = self.historical_weather_api_url.format(
            lat=lat, lon=lon, start=start_time, end=end_time, api_key=self.api_key
        )

        error, response_body = self.get_request(current_weather_request_url)

        if error:
            return {"error": error, "result": ""}

        return {"error": "", "result": response_body}
