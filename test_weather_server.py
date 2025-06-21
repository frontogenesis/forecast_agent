#!/usr/bin/env python3
"""
Test script for the Weather DWML MCP Server
"""

import asyncio
import json
import subprocess
import sys
from pathlib import Path

async def test_weather_server():
    """Test the weather MCP server directly."""
    # Import the server components
    sys.path.append(str(Path(__file__).parent))
    
    try:
        from weather_mcp_server import WeatherDWMLParser
        import httpx
        
        print("Testing DWML parser directly...")
        
        # Test coordinates (Houston, TX area)
        lat, lon = 29.752, -93.867
        url = f"https://forecast.weather.gov/MapClick.php?lat={lat}&lon={lon}&FcstType=digitalDWML"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            print(f"Fetching data from: {url}")
            response = await client.get(url)
            response.raise_for_status()
            
            print(f"Response status: {response.status_code}")
            print(f"Content type: {response.headers.get('content-type', 'unknown')}")
            print(f"Content length: {len(response.text)} characters")
            
            # Parse the data
            parser = WeatherDWMLParser(response.text)
            forecasts = parser.parse_hourly_forecast()
            
            print(f"\nParsed {len(forecasts)} hourly forecasts")
            
            if forecasts:
                print("\nFirst 3 forecast entries:")
                for i, forecast in enumerate(forecasts[:3]):
                    print(f"\n--- Hour {i+1} ---")
                    print(json.dumps(forecast, indent=2))
                
                print(f"\nSample keys from first forecast:")
                print(list(forecasts[0].keys()))
            else:
                print("No forecasts were parsed. Raw XML sample:")
                print(response.text[:1000] + "..." if len(response.text) > 1000 else response.text)
                
    except ImportError as e:
        print(f"Import error: {e}")
        print("Make sure you have the required dependencies installed:")
        print("pip install fastmcp httpx")
    except Exception as e:
        print(f"Error: {e}")

def test_mcp_server_cli():
    """Test the MCP server via CLI interface."""
    print("\n" + "="*50)
    print("Testing MCP Server CLI Interface")
    print("="*50)
    
    try:
        # Create a test input for the MCP server
        test_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "get_hourly_weather_forecast",
                "arguments": {
                    "latitude": 29.752,
                    "longitude": -93.867,
                    "hours": 6
                }
            }
        }
        
        print("Test request:")
        print(json.dumps(test_request, indent=2))
        print("\nTo test the MCP server manually, save the above JSON to a file")
        print("and pipe it to the server:")
        print("echo '{}' | python weather_mcp_server.py".format(json.dumps(test_request)))
        
    except Exception as e:
        print(f"Error preparing CLI test: {e}")

if __name__ == "__main__":
    print("Weather DWML MCP Server Test")
    print("="*40)
    
    # Test the parser directly
    asyncio.run(test_weather_server())
    
    # Show CLI test instructions
    test_mcp_server_cli()