#!/usr/bin/env python3
"""
Weather Forecast CrewAI Integration using MCP Server

This script creates a meteorologist agent that uses our FastMCP weather server
to generate weather forecast summaries with emphasis on hazardous conditions.
"""

import sys
import os
from pathlib import Path
from mcp import StdioServerParameters
from crewai import Agent, Task, Crew
from crewai_tools import MCPServerAdapter

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
        # Set up the MCP Server Adapter for our weather server
        weather_server_path = Path(__file__).parent / "weather_mcp_server.py"
        
        if not weather_server_path.exists():
            raise FileNotFoundError(f"Weather server not found at {weather_server_path}")
        
        server_params = StdioServerParameters(
            command="python",
            args=[str(weather_server_path)],
        )

        file_server_params = StdioServerParameters(
            command="npx",
            args=[
                "-y",
                "@modelcontextprotocol/server-filesystem",
                os.getcwd(),
            ]
        )

        fetch_server_params = StdioServerParameters(
            command="python",
            args=[
                "-m",
                "mcp_server_fetch"
            ]
        )
        
        # Create the MCP Server Adapter
        with MCPServerAdapter([server_params, file_server_params, fetch_server_params]) as weather_tools:
            print(f"Available tools: {[tool.name for tool in weather_tools] if hasattr(weather_tools, '__iter__') else 'Loading...'}")
            
            # Create the meteorologist agent
            meteorologist = Agent(
                role="Meteorologist",
                goal="Write clear, accurate weather summaries for a well-informed audience with emphasis on hazardous conditions",
                backstory="""You are an AI meteorologist tool that specializes in fetching, processing, 
                and analyzing weather forecast data. You have access to detailed hourly weather forecasts 
                from the National Weather Service and can identify potentially hazardous weather conditions. 
                Your expertise lies in translating complex meteorological data into clear information that another educated 
                professional (who is often not a meteorologist) can understand.""",
                tools=weather_tools,
                verbose=True,
                allow_delegation=False
            )
            
            # Create the forecast task
            forecast_task = Task(
                description=f"""
                Generate a comprehensive weather forecast summary for {location_name} (coordinates: {latitude}, {longitude}).
                
                Your task is to:
                1. Fetch the hourly weather forecast data for the next several days using the get_hourly_weather_forecast tool
                2. Analyze the data for hazardous weather conditions including:
                    - Thunderstorms or severe weather
                    - Sustained winds over 20 mph
                    - Wind gusts over 25 mph  
                    - Heavy rainfall (significant precipitation)
                    - Fog or low visibility conditions
                    - Sudden, or rapid changes, in day-to-day weather.
                3. Express the certainty of hazardous weather conditions. Do not use explicit probability values,
                but feel free to descriptive language to determine the risk or confidence of the hazardous weather if there
                is any.
                4. Write a 1-2 paragraph forecast summary that:
                    - Emphasizes any hazardous conditions found
                    - Provides timing and intensity details for hazardous weather
                    - If no hazardous conditions exist, gives a brief summary of general weather patterns
                    - Uses clear, accessible language that other professionals can understand
                    - Does not include any fabricated or speculative information
                    - Prefers days of the week over dates when communicating the timing of hazardous weather
                    - Prefers temperature ranges (e.g. mid 70s, around 70, mid to upper 70s) over specific temperatures (e.g. 70, 71, 72)
                
                Use the coordinates: latitude={latitude}, longitude={longitude}
                
                Base your analysis ONLY on the actual weather data retrieved. Do not make assumptions 
                or add information not present in the forecast data.
                """,
                agent=meteorologist,
                expected_output="""A weather forecast summary, properly formatted in markdown, with the following sections:
                - A clear headline about the overall weather pattern
                - 1-2 paragraphs describing conditions with emphasis on any hazardous weather
                - Specific timing and intensity details for significant weather events
                - Practical implications for daily activities if hazardous conditions are present
                - Save the forecast summary in this folder folder with the filename: weather_forecast.md; give me the full path to the file after it is saved
                
                Example format:
                # Weather Forecast for [Location]
                
                **Hazardous Weather Alert:** [If applicable]
                
                [1-2 paragraph summary based on actual forecast data]
                """
            )
            
            # Create the crew
            crew = Crew(
                agents=[meteorologist],
                tasks=[forecast_task],
                verbose=True
            )
            
            print("Starting crew execution...")
            result = crew.kickoff()
            
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
        
        # Save to file
        #save_forecast_to_file(str(forecast))
        
        print("\nForecast generation complete!")
    else:
        print("Failed to generate weather forecast.")
        
    print("\nOther examples you can try:")
    print("- example_nyc_forecast()")
    print("- example_denver_forecast()")
    print("- run_weather_forecast(your_lat, your_lon, 'Your Location')")