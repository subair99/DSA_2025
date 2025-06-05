import os
import requests
from dotenv import load_dotenv
from langchain.tools import tool
import warnings

warnings.filterwarnings("ignore")

load_dotenv()

# Import LLM from model
try:
    from model import llm
    if llm is None:
        raise ValueError("LLM initialization failed in model.py")
    print("✅ Successfully imported LLM from model")
except Exception as e:
    print(f"❌ Error importing LLM: {e}")
    exit(1)


# Define tools
@tool
def calculate(expression: str) -> str:
    """Safely evaluate mathematical expressions."""
    try:
        # Simple calculator - be careful with eval in production
        allowed_chars = set('0123456789+-*/.() ')
        if not set(expression).issubset(allowed_chars):
            return "Invalid characters in expression"
        result = eval(expression)
        return f"{result}" # Only return the result
    except Exception as e:
        return f"Calculation error: {str(e)}"

@tool
def get_weather(city: str) -> str:
    """Get current weather for a city."""
    try:
        url = f"https://wttr.in/{city}?format=j1"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            current = data['current_condition'][0]
            temp = current['temp_C']
            desc = current['weatherDesc'][0]['value']
            # Directly format the desired output string
            return f"The weather in {city} is a {desc.lower()} with a temperature of {temp}°C."
        return f"Could not get weather for {city}"
    except Exception as e:
        return f"Weather error: {str(e)}"


# Create tools list
tools = [calculate, get_weather]


# Try different agent approaches
def create_agent_with_fallback():
    """Try different agent creation methods"""
    
    # Method 1: Tool calling agent (preferred)
    try:
        from langchain.agents import AgentExecutor, create_tool_calling_agent
        from langchain_core.prompts import ChatPromptTemplate
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful assistant. Use the available tools to answer questions."),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ])
        
        agent = create_tool_calling_agent(llm, tools, prompt)
        
        # Set verbose=False to suppress detailed agent execution logs
        agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=False) 
        
        print("✅ Tool calling agent created successfully!")
        return agent_executor
        
    except Exception as e:
        print(f"⚠️ Tool calling agent failed: {e}")
    

    # Method 2: React agent (fallback)
    try:
        from langchain.agents import create_react_agent, AgentExecutor
        from langchain import hub
        
        # Get react prompt
        prompt = hub.pull("hwchase17/react")
        agent = create_react_agent(llm, tools, prompt)
        
        # Set verbose=False
        agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=False)
        
        print("✅ React agent created successfully!")
        return agent_executor
        
    except Exception as e:
        print(f"⚠️  React agent failed: {e}")
    

    # Method 3: Legacy agent (last resort)
    try:
        from langchain.agents import initialize_agent, AgentType
        
        # Set verbose=False
        agent_executor = initialize_agent(
            tools=tools,
            llm=llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=False,
            handle_parsing_errors=True
        )
        
        print("✅ Legacy agent created successfully!")
        return agent_executor
        
    except Exception as e:
        print(f"❌ Legacy agent failed: {e}")
        return None


# --- Example Usage ---
if __name__ == "__main__":
    # Create agent
    agent_executor = create_agent_with_fallback()

    query = "What's the weather in Lagos?"
    
    if agent_executor:
        try:
            # Test the agent with calculation first
            result_calc = agent_executor.invoke({"input": "Calculate 15 * 7 + 23"})
            print(f"\nCalculation: {result_calc['output']}")
            
            
            # Then test with weather query
            result_weather = agent_executor.invoke({"input": query})
            print(f"\nWeather: {result_weather['output']}")
            
        except Exception as e:
            print(f"❌ Error running agent: {str(e)}")
            print(f"Error type: {type(e).__name__}")
            

            # Fallback to direct tool usage
            print("\n🔄 Falling back to direct tool usage:")
            
            calc_result_direct = calculate("15 * 7 + 23")
            print(f"Direct Calculation: {calc_result_direct}")
            
            weather_result_direct = get_weather("London")
            print(f"Direct Weather: {weather_result_direct}")

    else:
        print("❌ Failed to create any agent. Using tools directly:")