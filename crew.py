from crewai import Agent, Crew, Task
from crewai.project import CrewBase
from crewai_tools import MCPServerAdapter
from mcp import StdioServerParameters
from pathlib import Path
import os

@CrewBase
class WeatherForecastCrew():
    """Weather Forecast Crew"""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    def __init__(self):
        self.weather_tools = None

    def setup_mcp_tools(self):
        """Set up MCP server tools for weather forecasting"""
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
        
        self.weather_tools = MCPServerAdapter([server_params, file_server_params, fetch_server_params])
        return self.weather_tools

    def create_agent_with_tools(self, tools):
        """Create the meteorologist agent with the provided tools"""
        return Agent(
            config=self.agents_config["weather_forecast_agent"],
            tools=tools,
            verbose=True
        )

    def create_task_with_agent(self, agent, latitude: float, longitude: float, location_name: str = "the requested location"):
        """Create the weather forecast task with the provided agent"""
        # Format the task description with the provided parameters
        task_config = self.tasks_config["weather_forecast_task"].copy()
        task_config["description"] = task_config["description"].format(
            latitude=latitude,
            longitude=longitude,
            location_name=location_name
        )
        
        return Task(
            config=task_config,
            agent=agent,
            verbose=True
        )

    def run_forecast(self, latitude: float, longitude: float, location_name: str = "the requested location"):
        """Run the weather forecast crew and return the result"""
        print(f"Generating weather forecast for {location_name} ({latitude}, {longitude})")
        print("=" * 60)
        
        try:
            # Set up tools
            self.setup_mcp_tools()
            
            with self.weather_tools as tools:
                print(f"Available tools: {[tool.name for tool in tools] if hasattr(tools, '__iter__') else 'Loading...'}")
                
                # Create the agent with the tools
                meteorologist = self.create_agent_with_tools(tools)
                
                # Create the task with the agent
                forecast_task = self.create_task_with_agent(meteorologist, latitude, longitude, location_name)
                
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