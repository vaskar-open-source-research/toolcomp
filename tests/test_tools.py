#!/usr/bin/env python3
"""
Unit Tests for ToolComp Tools

This script provides a proper unit test framework for testing the toolcomp tools.
"""

import unittest

# Import helpers for tool management
from tools.helper import get_all_tools_mapping
from utils.keystore import auth_tools

class ToolsTestCase(unittest.TestCase):
    """Base test case with common setup and helper methods."""
    
    def setUp(self):
        """Set up test environment."""
        
        # auth tools
        auth_tools()
        
        # Get mapping of all tools
        self.tools = get_all_tools_mapping()
    
    def assertToolResult(self, result, has_error=False):
        """Helper method to assert tool result structure."""
        self.assertIsInstance(result, dict)
        self.assertIn("error", result)
        self.assertIn("result", result)
        
        if has_error:
            self.assertNotEqual(result["error"], "")
        else:
            self.assertEqual(result["error"], "")
            self.assertNotEqual(result["result"], "")


class CalculatorToolTests(ToolsTestCase):
    """Tests for the Calculator tool."""
    
    def test_calculator_exists(self):
        """Test that the calculator tool is available."""
        self.assertIn("calculator", self.tools)
    
    def test_calculator_valid_expression(self):
        """Test calculator with a valid expression."""
        if "calculator" not in self.tools:
            self.skipTest("Calculator tool not available")
        
        calculator = self.tools["calculator"]
        result = calculator.call({"operation": "2 * (3 + 4) / 2"})
        
        self.assertToolResult(result)
        self.assertEqual(result["result"], "7.0")
    
    def test_calculator_invalid_expression(self):
        """Test calculator with an invalid expression."""
        if "calculator" not in self.tools:
            self.skipTest("Calculator tool not available")
        
        calculator = self.tools["calculator"]
        result = calculator.call({"operation": "2 * (3 + 4 / 2"})  # Missing closing parenthesis
        
        self.assertToolResult(result, has_error=True)


class DateToolTests(ToolsTestCase):
    """Tests for the Date tool."""
    
    def test_date_exists(self):
        """Test that the date tool is available."""
        self.assertIn("date", self.tools)
    
    def test_date_current(self):
        """Test getting current date."""
        if "date" not in self.tools:
            self.skipTest("Date tool not available")
        
        date_tool = self.tools["date"]
        result = date_tool.call({})
        
        self.assertToolResult(result)
        self.assertIn("Today is", result["result"])
    
    def test_date_historical(self):
        """Test getting a historical date."""
        if "date" not in self.tools:
            self.skipTest("Date tool not available")
        
        date_tool = self.tools["date"]
        result = date_tool.call({"historical_date": "02/15/2024"})
        
        self.assertToolResult(result)
        self.assertIn("Today is", result["result"])
        self.assertIn("February 15, 2024", result["result"])


class WolframAlphaToolTests(ToolsTestCase):
    """Tests for the Wolfram Alpha tool."""
    
    def test_wolfram_exists(self):
        """Test that the Wolfram Alpha tool is available."""
        self.assertIn("wolfram_alpha", self.tools)
    
    def test_wolfram_valid_query(self):
        """Test Wolfram Alpha with a valid query."""
        if "wolfram_alpha" not in self.tools:
            self.skipTest("Wolfram Alpha tool not available")
        
        wolfram = self.tools["wolfram_alpha"]
        result = wolfram.call({"query": "What is 4 + 5?"})
        
        self.assertToolResult(result)
        self.assertEqual(result["result"], "9")


class WikiSearchToolTests(ToolsTestCase):
    """Tests for the Wikipedia Search tool."""
    
    def test_wiki_exists(self):
        """Test that the Wikipedia Search tool is available."""
        self.assertIn("wiki_search", self.tools)
    

    def test_wiki_search_valid_query(self):
        """Test Wikipedia Search with a valid query."""
        if "wiki_search" not in self.tools:
            self.skipTest("Wiki Search tool not available")
        
        wiki = self.tools["wiki_search"]
        result = wiki.call({"query": "Python programming language", "num_results": 1})
        
        self.assertToolResult(result)
        self.assertIsInstance(result["result"], list)
        self.assertEqual(len(result["result"]), 1)


class GoogleSearchToolTests(ToolsTestCase):
    """Tests for the Google Search tool."""
    
    def test_google_search_exists(self):
        """Test that the Google Search tool is available."""
        self.assertIn("google_search", self.tools)
    
    def test_google_search_valid_query(self):
        """Test Google Search with a valid query."""
        if "google_search" not in self.tools:
            self.skipTest("Google Search tool not available")
        
        google_search = self.tools["google_search"]
        result = google_search.call({"query": "Python programming language"})
        
        self.assertToolResult(result)
        self.assertIsInstance(result["result"], list)
        self.assertGreater(len(result["result"]), 0)


class CurrentWeatherToolTests(ToolsTestCase):
    """Tests for the Current Weather tool."""
    
    def test_current_weather_exists(self):
        """Test that the Current Weather tool is available."""
        self.assertIn("current_weather", self.tools)
    
    def test_current_weather_valid_location(self):
        """Test Current Weather with a valid location."""
        if "current_weather" not in self.tools:
            self.skipTest("Current Weather tool not available")
        
        current_weather = self.tools["current_weather"]
        result = current_weather.call({"city_name": "New York", "country_code": "US"})
        
        self.assertToolResult(result)
        # Verify result has typical weather information
        weather_data = result["result"]
        self.assertIsInstance(weather_data, list)
        self.assertIn("temperature (°F)", weather_data[0])
        self.assertIn("total snowfall (mm)", weather_data[0])
        self.assertIn("precipitation hours (hours)", weather_data[0])


class HistoricalWeatherToolTests(ToolsTestCase):
    """Tests for the Historical Weather tool."""
    
    def test_historical_weather_exists(self):
        """Test that the Historical Weather tool is available."""
        self.assertIn("historical_weather", self.tools)
    
    def test_historical_weather_valid_params(self):
        """Test Historical Weather with valid parameters."""
        if "historical_weather" not in self.tools:
            self.skipTest("Historical Weather tool not available")
        
        historical_weather = self.tools["historical_weather"]
        result = historical_weather.call({
            "city_name": "New York",
            "country_code": "US",
            "start_date": "2023-01-01",
            "end_date": "2023-01-05"
        })
        
        self.assertToolResult(result)
        # Verify result has typical weather information
        weather_data = result["result"]
        self.assertIsInstance(weather_data, list)
        self.assertIn("temperature (°F)", weather_data[0])
        self.assertIn("total snowfall (mm)", weather_data[0])
        self.assertIn("precipitation hours (hours)", weather_data[0])


class TimeSeriesIntradayToolTests(ToolsTestCase):
    """Tests for the Time Series Intraday tool."""
    
    def test_time_series_intraday_exists(self):
        """Test that the Time Series Intraday tool is available."""
        self.assertIn("time_series_intraday", self.tools)
    
    def test_time_series_intraday_valid_params(self):
        """Test Time Series Intraday with valid parameters."""
        if "time_series_intraday" not in self.tools:
            self.skipTest("Time Series Intraday tool not available")
        
        time_series_intraday = self.tools["time_series_intraday"]
        result = time_series_intraday.call({
            "symbol": "AAPL",
            "interval": "60min",
            "outputsize": "compact"
        })
        
        self.assertToolResult(result)
        # Verify result has expected stock data structure
        self.assertIsInstance(result["result"], list)


class TimeSeriesDailyToolTests(ToolsTestCase):
    """Tests for the Time Series Daily tool."""
    
    def test_time_series_daily_exists(self):
        """Test that the Time Series Daily tool is available."""
        self.assertIn("time_series_daily", self.tools)
    
    def test_time_series_daily_valid_params(self):
        """Test Time Series Daily with valid parameters."""
        if "time_series_daily" not in self.tools:
            self.skipTest("Time Series Daily tool not available")
        
        time_series_daily = self.tools["time_series_daily"]
        result = time_series_daily.call({
            "symbol": "AAPL",
            "outputsize": "compact",
            "number_of_days": 5
        })
        
        self.assertToolResult(result)
        # Verify result has expected stock data structure
        self.assertIsInstance(result["result"], list)
        self.assertIn("timestamp", result["result"][0])
        self.assertIn("open_market_value", result["result"][0])
        self.assertIn("high_market_value", result["result"][0])
        self.assertIn("close_market_value", result["result"][0])
        self.assertIn("volume", result["result"][0])


class TickerSearchToolTests(ToolsTestCase):
    """Tests for the Ticker Search tool."""
    
    def test_ticker_search_exists(self):
        """Test that the Ticker Search tool is available."""
        self.assertIn("ticker_search", self.tools)
    
    def test_ticker_search_valid_query(self):
        """Test Ticker Search with a valid query."""
        if "ticker_search" not in self.tools:
            self.skipTest("Ticker Search tool not available")
        
        ticker_search = self.tools["ticker_search"]
        result = ticker_search.call({
            "keywords": "Apple"
        })
        
        self.assertToolResult(result)
        # Verify result has expected ticker data structure
        self.assertIsInstance(result["result"], list)
        if result["result"]:  # If any results returned
            first_result = result["result"][0]
            self.assertIn("symbol", first_result)
            self.assertIn("name", first_result)


class PythonInterpreterToolTests(ToolsTestCase):
    """Tests for the Python Interpreter tool."""
    
    def test_python_interpreter_exists(self):
        """Test that the Python Interpreter tool is available."""
        self.assertIn("python_interpreter", self.tools)
    
    def test_python_interpreter_valid_code(self):
        """Test Python Interpreter with a valid code."""
        if "python_interpreter" not in self.tools:
            self.skipTest("Python Interpreter tool not available")
        
        python = self.tools["python_interpreter"]
        result = python.call({"code": "print('Hello, World!')"})
        
        self.assertToolResult(result)
        self.assertEqual(result["result"].strip(), "Hello, World!")


class WeatherToolTests(ToolsTestCase):
    """Tests for the Weather tool."""
    
    def test_weather_exists(self):
        """Test that the Weather tool is available."""
        self.assertIn("current_weather", self.tools)
        self.assertIn("historical_weather", self.tools)


    def test_current_weather_valid_location(self):
        """Test Current Weather with a valid location."""
        if "current_weather" not in self.tools:
            self.skipTest("Current Weather tool not available")
        
        weather = self.tools["current_weather"]
        result = weather.call({"city_name": "New York", "country_code": "US"})

        self.assertToolResult(result)
        self.assertIn("temperature (°F)", result["result"][0])
        self.assertIn("total snowfall (mm)", result["result"][0])
        self.assertIn("precipitation hours (hours)", result["result"][0])


    def test_historical_weather_valid_location(self):
        """Test Historical Weather with a valid location."""
        if "historical_weather" not in self.tools:
            self.skipTest("Historical Weather tool not available")
        
        historical_weather = self.tools["historical_weather"]
        result = historical_weather.call({
            "city_name": "New York",
            "country_code": "US",
            "start_date": "2023-01-01",
            "end_date": "2023-01-05"
        })  
        
        self.assertToolResult(result)
        self.assertIn("temperature (°F)", result["result"][0])
        self.assertIn("total snowfall (mm)", result["result"][0])
        self.assertIn("precipitation hours (hours)", result["result"][0])



def run_tests():
    """Run the unit tests."""
    unittest.main()


if __name__ == "__main__":
    run_tests()