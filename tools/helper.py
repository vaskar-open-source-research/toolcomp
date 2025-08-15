import json

from tools.calculator import Calculator
from tools.date import Date
from tools.google_search import GoogleAPI
from tools.meteo_weather import CurrentWeather
from tools.meteo_weather import HistoricalWeather
from tools.wiki_search import WikiSearch
from tools.wolfram_alpha import WolframAlpha
from tools.stocks import TimeSeriesIntraday, TimeSeriesDaily, TickerSearch
from tools.python_interpreter import PythonInterpreter


def get_all_tools_mapping():

    mapping = {
        "calculator": Calculator(),
        "date": Date(),
        "google_search": GoogleAPI(),
        "wiki_search": WikiSearch(),
        "current_weather": CurrentWeather(),
        "historical_weather": HistoricalWeather(),
        "wolfram_alpha": WolframAlpha(),
        "time_series_intraday": TimeSeriesIntraday(),
        "time_series_daily": TimeSeriesDaily(),
        "ticker_search": TickerSearch(),
        "python_interpreter": PythonInterpreter(),
    }

    return mapping
