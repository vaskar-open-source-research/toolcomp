import json
import requests
from tools.tool_base_class import ToolBaseClass
import os
import datetime


class StocksToolBaseClass(ToolBaseClass):
    """
    Alpha Vantage Stocks API
    """

    def __init__(self):
        self.base_url = "https://www.alphavantage.co/query"
        self.api_key = os.getenv("ALPHA_VANTAGE_API_KEY")

    def _format_url(self, args):
        args_str = "&".join([f"{k}={v}" for k, v in args.items()])
        return f"{self.base_url}?{args_str}"

    def _call(self, url):
        response = requests.get(url)
        return response.json()
    
    def format_time_series_results(self, data, historical_date=None,number_of_days=None):
        """
        Format the time series results to be displayed in the frontend
        """
        if "Time Series (5min)" in data:
            raw_data = data["Time Series (5min)"]
        elif "Time Series (60min)" in data:
            raw_data = data["Time Series (60min)"]
        elif "Time Series (1min)" in data:
            raw_data =  data["Time Series (1min)"]
        elif "Time Series (15min)" in data:
            raw_data =  data["Time Series (15min)"]
        elif "Time Series (30min)" in data:
            raw_data =  data["Time Series (30min)"]
        elif "Time Series (Daily)" in data:
            raw_data = data["Time Series (Daily)"]
        
        formatted_data = [
            {
                "timestamp": key,
                "open_market_value": value["1. open"],
                "high_market_value": value["2. high"],
                "low_market_value": value["3. low"],
                "close_market_value": value["4. close"],
                "volume": value["5. volume"],
            } for key, value in raw_data.items()
        ]
        if historical_date:
            for c, d in enumerate(formatted_data):
                if historical_date in d['timestamp']:
                    break
            formatted_data = formatted_data[c:]


        if number_of_days:
            formatted_data = formatted_data[:number_of_days]
        return formatted_data
    

    def format_search_results(self, data):

        if "bestMatches" in data:
            raw_data = data["bestMatches"]
            formatted_data = [
                {
                    "symbol": entry["1. symbol"],
                    "name": entry["2. name"],
                    "type": entry["3. type"],
                    "region": entry["4. region"],
                    "market_open": entry["5. marketOpen"],
                    "market_close": entry["6. marketClose"],
                    "timezone": entry["7. timezone"],
                    "currency": entry["8. currency"],
                    "match_score": entry["9. matchScore"],
                } for entry in raw_data
            ]
            return formatted_data
        return data
    

class TimeSeriesIntraday(StocksToolBaseClass):

    def __init__(self):
        super().__init__()
        self.tool_name = "time_series_intraday"

    def get_firefunction_spec(self):
        desc = {
        "name": "time_series_intraday",
        "description": "Time Series Intraday tool. Returns intraday time series of the equity specified. To get historical info use the month parameter to specify the month in history you want to query.",
        "parameters": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "The name of the equity of your choice.",
                },
                "interval": {
                    "type": "string",
                    "description": "Time interval between two consecutive data points in the time series. The following values are supported: 1min, 5min, 15min, 30min, 60min",
                },
                "month": {
                    "type": "string",
                    "description": "You can use the month parameter (in YYYY-MM format) to query a specific month in history. For example, month=2009-01.",
                },
                },
            "required": ["symbol", "interval"],


            },
        }
        return desc
    
    def validate(self, args={}):
        if "symbol" not in args or not isinstance(args["symbol"], str):
            return False
        if "interval" not in args or not isinstance(args["interval"], str):
            return False
        return True
    def _find_previous_date(self, data, date):
        current_date=False
        previous_date=None
        for d in data:

            if date in d['timestamp']:
                current_date=True
            if current_date:
                if date not in d['timestamp']:
                    previous_date=d['timestamp'].split(' ')[0]
                    break
        return previous_date
    
    def call(self, args={}):

        try:
            symbol = args["symbol"]
        except:
            return {"error": "Required field \"symbol\" not provided.", "result": ""}

        try:
            interval = args["interval"]
        except:
            return {"error": "Required field \"interval\" not provided.", "result": ""}
        month = args.get("month", "")
        historical_date = args.get("historical_date", "")
        args = {"function": "TIME_SERIES_INTRADAY", "symbol": symbol, "interval": interval, "apikey": self.api_key}
        if month:
            args["month"] = month
        if (historical_date) and (not month):
            date_string = historical_date
            start_date_obj = datetime.datetime.strptime(date_string, "%m/%d/%Y")
            args['outputsize'] = 'full'
            args["month"] = start_date_obj.strftime("%Y-%m")
        url = self._format_url(args)
        try:
            result = self._call(url)
            data = self.format_time_series_results(result)
        except Exception as e:
            return {"error": str(e), "result": ""}
        if (historical_date) and (not month):
            _date=start_date_obj.strftime("%Y-%m-%d")
            previous_date=self._find_previous_date(data, _date)
            if previous_date is None:

                start_date_obj-=datetime.timedelta(days=9)
                args["month"] = start_date_obj.strftime("%Y-%m")
                url = self._format_url(args)
                result = self._call(url)
                new_data = self.format_time_series_results(result)
                data += new_data
                previous_date=self._find_previous_date(data, _date)
            mod_data=[]
            for d in data:
                if previous_date in d['timestamp']:
                    mod_data.append(d)
            mod_data=mod_data[:100]
            return {"error": "", "result": mod_data}

        return {"error": "", "result": data}

class TimeSeriesDaily(StocksToolBaseClass):

    def __init__(self):
        super().__init__()
        self.tool_name = "time_series_daily"

    def get_firefunction_spec(self):
        desc = {
            "name": "time_series_daily",
            "description": "Time Series Daily tool. Returns daily time series of the equity specified for the last number_of_days days from the current date.",
            "parameters": {
                "type": "object",
                "properties":{
                    "symbol": {
                        "type": "string",
                        "description": "The name of the equity of your choice.",
                    },
                    "number_of_days": {
                        "type": "integer",
                        "description": "The number of days before today to return data for.",
                    },
                },
                "required": ["symbol", "number_of_days"],
            }
        }
        return desc
    
    def validate(self, args={}):
        if "symbol" not in args or not isinstance(args["symbol"], str):
            return False
        if "number_of_days" not in args or not isinstance(args["number_of_days"], int):
            return False
        return True
    
    def call(self, args={}):
        try:
            symbol = args["symbol"]
        except:
            return {"error": "Required field \"symbol\" not provided.", "result": ""}
        outputsize = "compact"
        month = args.get("month", "")
        try:
            number_of_days = args["number_of_days"]
        except:
            return {"error": "Required field \"number_of_days\" not provided.", "result": ""}
        historical_date = args.get("historical_date", "")

        if type(number_of_days) == str:
            if number_of_days.isdigit():
                number_of_days = int(number_of_days)
            else:
                return {"error": "Invalid number of days. Please provide an integer.", "result": ""}

        url = self._format_url({"function": "TIME_SERIES_DAILY", "symbol": symbol, "outputsize": outputsize, "apikey": self.api_key, "month": month})
        try:
            if historical_date:
                start_date_obj = datetime.datetime.strptime(historical_date, "%m/%d/%Y")
                _date=start_date_obj.strftime("%Y-%m-%d")
                url = self._format_url({"function": "TIME_SERIES_DAILY", "symbol": symbol, "outputsize": "full", "apikey": self.api_key, "month": month})
                data = self.format_time_series_results(self._call(url),historical_date=_date, number_of_days=number_of_days)
            else:
                data = self.format_time_series_results(self._call(url), number_of_days=number_of_days)
        except Exception as e:
            return {"error": str(e), "result": ""}
        return {"error": "", "result": data}

class TickerSearch(StocksToolBaseClass):

    def __init__(self):
        super().__init__()
        self.tool_name = "ticker_search"
    
    def get_firefunction_spec(self):
        desc = {
            "name": "ticker_search",
            "description": "Ticker Search tool. Returns the ticker symbol given a text string to search for. This can be company name or key words.",
            "parameters": {
                "type": "object",
                "properties": {
                    "keywords": {
                        "type": "string",
                        "description": "A text string to search for.",
                    },
                },
                "required": ["keywords"],
            }
        }
        return desc

    def validate(self, args={}):
        if "keywords" not in args or not isinstance(args["keywords"], str):
            return False
        return True
    
    def call(self, args={}):
        try:
            keywords = args["keywords"]
        except:
            return {"error": "Required field \"keywords\" not provided.", "result": ""}
        url = self._format_url({"function": "SYMBOL_SEARCH", "keywords": keywords, "apikey": self.api_key})
        try:
            data = self.format_search_results(self._call(url))
        except Exception as e:
            return {"error": str(e), "result": ""}
        return {"error": "", "result": data}
