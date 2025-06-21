#!/usr/bin/env python3
"""
Weather DWML MCP Server using FastMCP

An MCP server that fetches DWML weather data from the National Weather Service
and returns hourly forecasts as structured data.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List
from xml.etree import ElementTree as ET

import httpx
from fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("weather-mcp-server")

# Create the FastMCP server
mcp = FastMCP("Weather DWML Server")

class WeatherDWMLParser:
    """Parser for DWML weather data from NWS."""
    
    def __init__(self, xml_content: str):
        self.root = ET.fromstring(xml_content)
        self.namespace = {'dwml': 'http://www.nws.noaa.gov/forecasts/xml/DWMLgen/schema/DWML.xsd'}
    
    def parse_hourly_forecast(self) -> List[Dict[str, Any]]:
        """Parse DWML XML and return hourly forecast data."""
        try:
            # Find the time layout for hourly data
            time_layouts = self.root.findall('.//time-layout', self.namespace)
            hourly_times = None
            hourly_layout_key = None
            
            # Look for hourly time layout (usually has many time entries)
            for layout in time_layouts:
                layout_key = layout.find('layout-key', self.namespace)
                if layout_key is not None:
                    start_times = layout.findall('start-valid-time', self.namespace)
                    if len(start_times) > 24:  # Likely hourly data
                        hourly_times = [time.text for time in start_times]
                        hourly_layout_key = layout_key.text
                        break
            
            if not hourly_times or not hourly_layout_key:
                logger.warning("Could not find hourly time layout")
                return []
            
            # Initialize forecast list
            forecasts = []
            for time_str in hourly_times:
                # Parse the time string
                try:
                    # Handle different time formats - DWML uses local time with timezone offset
                    # Format is typically: 2025-05-28T18:00:00-05:00
                    dt = datetime.fromisoformat(time_str)
                    
                    # Keep the original timezone-aware datetime for valid_time
                    valid_time = dt.isoformat()
                    
                    # Create readable format in local time (12-hour format with AM/PM)
                    readable_time = dt.strftime('%Y-%m-%d %I:%M:%S %p')
                    
                    forecast = {
                        'valid_time': valid_time,
                        'datetime_readable': readable_time
                    }
                    forecasts.append(forecast)
                except ValueError as e:
                    logger.warning(f"Could not parse time {time_str}: {e}")
                    continue
            
            # Parse weather parameters
            parameters = self.root.find('.//parameters', self.namespace)
            if parameters is None:
                logger.warning("No parameters found in DWML")
                return forecasts
            
            # Temperature
            self._parse_temperature_data(parameters, hourly_layout_key, forecasts)
            
            # Humidity
            self._parse_humidity_data(parameters, hourly_layout_key, forecasts)
            
            # Wind Speed and Direction
            self._parse_wind_data(parameters, hourly_layout_key, forecasts)
            
            # Weather conditions
            self._parse_weather_conditions(parameters, hourly_layout_key, forecasts)
            
            # Precipitation probability
            self._parse_precipitation_data(parameters, hourly_layout_key, forecasts)
            
            # Cloud cover
            self._parse_cloud_cover(parameters, hourly_layout_key, forecasts)
            
            return forecasts
            
        except ET.ParseError as e:
            logger.error(f"XML parsing error: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error parsing DWML: {e}")
            return []
    
    def _parse_temperature_data(self, parameters, layout_key: str, forecasts: List[Dict]):
        """Parse temperature data from parameters."""
        temps = parameters.findall('.//temperature', self.namespace)
        for temp in temps:
            time_layout = temp.get('time-layout')
            temp_type = temp.get('type', 'unknown')
            units = temp.get('units', 'Fahrenheit')
            
            if time_layout == layout_key:
                values = temp.findall('value', self.namespace)
                for i, value in enumerate(values):
                    if i < len(forecasts) and value.text:
                        key = f'temperature_{temp_type.lower()}'
                        forecasts[i][key] = {
                            'value': float(value.text),
                            'units': units
                        }
    
    def _parse_humidity_data(self, parameters, layout_key: str, forecasts: List[Dict]):
        """Parse humidity data from parameters."""
        humidity_elem = parameters.find('.//humidity[@time-layout="{}"]'.format(layout_key), self.namespace)
        if humidity_elem is not None:
            values = humidity_elem.findall('value', self.namespace)
            for i, value in enumerate(values):
                if i < len(forecasts) and value.text:
                    forecasts[i]['humidity'] = {
                        'value': float(value.text),
                        'units': humidity_elem.get('units', 'percent')
                    }
    
    def _parse_wind_data(self, parameters, layout_key: str, forecasts: List[Dict]):
        """Parse wind speed and direction data."""
        # Wind speed
        wind_speed = parameters.find('.//wind-speed[@time-layout="{}"]'.format(layout_key), self.namespace)
        if wind_speed is not None:
            values = wind_speed.findall('value', self.namespace)
            for i, value in enumerate(values):
                if i < len(forecasts) and value.text:
                    if 'wind' not in forecasts[i]:
                        forecasts[i]['wind'] = {}
                    forecasts[i]['wind']['speed'] = {
                        'value': float(value.text),
                        'units': wind_speed.get('units', 'knots')
                    }
        
        # Wind direction
        wind_dir = parameters.find('.//direction[@time-layout="{}"]'.format(layout_key), self.namespace)
        if wind_dir is not None:
            values = wind_dir.findall('value', self.namespace)
            for i, value in enumerate(values):
                if i < len(forecasts) and value.text:
                    if 'wind' not in forecasts[i]:
                        forecasts[i]['wind'] = {}
                    forecasts[i]['wind']['direction'] = {
                        'value': float(value.text) if value.text.isdigit() else value.text,
                        'units': wind_dir.get('units', 'degrees')
                    }
    
    def _parse_weather_conditions(self, parameters, layout_key: str, forecasts: List[Dict]):
        """Parse weather conditions."""
        weather = parameters.find('.//weather[@time-layout="{}"]'.format(layout_key), self.namespace)
        if weather is not None:
            weather_conditions = weather.findall('weather-conditions', self.namespace)
            for i, condition in enumerate(weather_conditions):
                if i < len(forecasts):
                    weather_summary = condition.get('weather-summary', 'No description')
                    forecasts[i]['weather_conditions'] = weather_summary
    
    def _parse_precipitation_data(self, parameters, layout_key: str, forecasts: List[Dict]):
        """Parse precipitation probability."""
        precip = parameters.find('.//probability-of-precipitation[@time-layout="{}"]'.format(layout_key), self.namespace)
        if precip is not None:
            values = precip.findall('value', self.namespace)
            for i, value in enumerate(values):
                if i < len(forecasts) and value.text:
                    forecasts[i]['precipitation_probability'] = {
                        'value': float(value.text),
                        'units': precip.get('units', 'percent')
                    }
    
    def _parse_cloud_cover(self, parameters, layout_key: str, forecasts: List[Dict]):
        """Parse cloud cover data."""
        cloud_cover = parameters.find('.//cloud-amount[@time-layout="{}"]'.format(layout_key), self.namespace)
        if cloud_cover is not None:
            values = cloud_cover.findall('value', self.namespace)
            for i, value in enumerate(values):
                if i < len(forecasts) and value.text:
                    forecasts[i]['cloud_cover'] = {
                        'value': float(value.text),
                        'units': cloud_cover.get('units', 'percent')
                    }


@mcp.tool()
async def get_hourly_weather_forecast(
    latitude: float,
    longitude: float,
    hours: int = 24
) -> str:
    """
    Get hourly weather forecast for specified coordinates using NWS DWML data.
    
    Args:
        latitude: Latitude coordinate (-90 to 90)
        longitude: Longitude coordinate (-180 to 180)  
        hours: Number of hours to return (default: 24, max: 168)
    
    Returns:
        JSON string with hourly weather forecast data
    """
    # Validate coordinates
    if not (-90 <= latitude <= 90):
        raise ValueError("Latitude must be between -90 and 90")
    if not (-180 <= longitude <= 180):
        raise ValueError("Longitude must be between -180 and 180")
    if not (1 <= hours <= 168):
        raise ValueError("Hours must be between 1 and 168")
    
    try:
        # Build the NWS DWML URL
        url = f"https://forecast.weather.gov/MapClick.php?lat={latitude}&lon={longitude}&FcstType=digitalDWML"
        
        # Fetch the DWML data
        async with httpx.AsyncClient(timeout=30.0) as client:
            logger.info(f"Fetching weather data from: {url}")
            response = await client.get(url)
            response.raise_for_status()
            
            # Parse the DWML
            parser = WeatherDWMLParser(response.text)
            forecasts = parser.parse_hourly_forecast()
            
            # Limit to requested number of hours
            if forecasts:
                forecasts = forecasts[:hours]
            
            # Format the response
            result = {
                "location": {
                    "latitude": latitude,
                    "longitude": longitude
                },
                "forecast_hours": len(forecasts),
                "requested_hours": hours,
                "hourly_forecasts": forecasts,
                "source": "National Weather Service DWML",
                "generated_at": datetime.utcnow().isoformat()
            }
            
            return json.dumps(result, indent=2)
            
    except httpx.TimeoutException:
        raise ValueError("Weather service request timed out")
    except httpx.HTTPStatusError as e:
        raise ValueError(f"Weather service returned error: {e.response.status_code}")
    except Exception as e:
        logger.error(f"Error fetching weather data: {e}")
        raise ValueError(f"Failed to fetch weather data: {str(e)}")


if __name__ == "__main__":
    mcp.run()