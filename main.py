#!/usr/bin/env python3
"""
Weather Forecast CrewAI Integration using MCP Server

This script creates a meteorologist agent that uses the FastMCP weather server
to generate weather forecast summaries with emphasis on hazardous conditions.
"""

import sys

from dotenv import load_dotenv
from crew import WeatherForecastCrew

load_dotenv()

def run_weather_forecast(latitude: float, longitude: float, location_name: str = "the requested location"):
    """
    Run the weather forecast crew and return the result.
    
    Args:
        latitude: Latitude for weather forecast
        longitude: Longitude for weather forecast
        location_name: Human-readable location name
        
    Returns:
        str: The weather forecast summary in markdown format
    """
    print(f"Generating weather forecast for {location_name} ({latitude}, {longitude})")
    print("=" * 60)
    
    try:
        # Create the weather forecast crew
        weather_crew = WeatherForecastCrew()
        
        # Run the forecast
        result = weather_crew.run_forecast(latitude, longitude, location_name)
        
        return result
                
    except Exception as e:
        print(f"Error generating weather forecast: {e}")
        import traceback
        traceback.print_exc()
        return None

# Example usage and test functions
def example_houston_forecast():
    """Example: Generate forecast for Houston, TX area."""
    return run_weather_forecast(
        latitude=29.7601,
        longitude=-95.3701,
        location_name="Houston, Texas"
    )

def example_nyc_forecast():
    """Example: Generate forecast for New York City."""
    return run_weather_forecast(
        latitude=40.7128,
        longitude=-74.0060,
        location_name="New York City, New York"
    )

def example_denver_forecast():
    """Example: Generate forecast for Denver, CO."""
    return run_weather_forecast(
        latitude=39.7392,
        longitude=-104.9903,
        location_name="Denver, Colorado"
    )

if __name__ == "__main__":
    print("Weather Forecast using CrewAI")
    print("=" * 40)
    
    # Check if coordinates were provided as command line arguments
    if len(sys.argv) >= 3:
        try:
            lat = float(sys.argv[1])
            lon = float(sys.argv[2])
            location = sys.argv[3] if len(sys.argv) > 3 else f"Location at {lat}, {lon}"
            
            print(f"Using provided coordinates: {lat}, {lon}")
            forecast = run_weather_forecast(lat, lon, location)
            
        except ValueError:
            print("Error: Invalid coordinates provided")
            print("Usage: python weather_forecast_crew.py <latitude> <longitude> [location_name]")
            sys.exit(1)
    else:
        # Run Houston example by default
        print("No coordinates provided, running Houston area example...")
        forecast = example_houston_forecast()
    
    if forecast:
        print("\n" + "=" * 60)
        print("WEATHER FORECAST RESULT:")
        print("=" * 60)
        print(forecast)
        print("\n" + "=" * 60)
        
        print("\nForecast generation complete!")
    else:
        print("Failed to generate weather forecast.")
        
    print("\nOther examples you can try:")
    print("- example_nyc_forecast()")
    print("- example_denver_forecast()")
    print("- run_weather_forecast(your_lat, your_lon, 'Your Location')")