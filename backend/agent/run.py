import os
import logging
from langchain_core.messages import HumanMessage
from langchain_core.tools import Tool
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_community.utilities.wolfram_alpha import WolframAlphaAPIWrapper
from langchain_community.tools.wolfram_alpha import WolframAlphaQueryRun
from langchain_community.utilities.wikipedia import WikipediaAPIWrapper
from utils.llm_setup import get_llm
from utils.meta_prompting_agent import create_meta_prompting_agent

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

model = get_llm(provider="openai", model_name="gpt-4o")
# model = get_llm(provider="claude", model_name="claude-3-5-sonnet-20240620")

# Create instances of the tools
tools = [
    TavilySearchResults(max_results=3),
]

# Try to add Wolfram Alpha tool if available
wolfram_alpha_appid = os.getenv("WOLFRAM_ALPHA_APPID")

if wolfram_alpha_appid:
    try:
        wolfram = WolframAlphaAPIWrapper()
        tools.append(WolframAlphaQueryRun(api_wrapper=wolfram))
        logger.info("Wolfram Alpha tool added successfully.")
    except Exception as e:
        logger.warning(f"Failed to initialize Wolfram Alpha tool: {str(e)}")
else:
    logger.warning("WOLFRAM_ALPHA_APPID not set. Skipping Wolfram Alpha tool.")

# Try to add Wikipedia tool if available
try:
    wikipedia = WikipediaAPIWrapper()
    tools.append(Tool(
        name="Wikipedia",
        func=wikipedia.run,
        description="Useful for querying Wikipedia to get information on a wide range of topics."
    ))
    logger.info("Wikipedia tool added successfully.")
except ImportError:
    logger.warning("Wikipedia package not found. Proceeding without Wikipedia tool.")

agent = create_meta_prompting_agent(model, tools)

# Use streaming with improved output formatting
try:
    complex_query = """
    Compare the economic impact of renewable energy adoption in Germany and China over the last decade. 
    Include data on their current energy mix, major renewable projects, and how this shift has affected 
    their carbon emissions and job markets. Also, provide a brief forecast of their renewable energy goals 
    for the next 5 years.
    """
    for chunk in agent.stream({"messages": [HumanMessage(content=complex_query)], "error_log": [], "turn_count": 0}):
        for key, value in chunk.items():
            if 'messages' in value:
                for message in value['messages']:
                    print(f"\n{'=' * 40}")
                    print(f"{message.type.capitalize()}:")
                    print(f"{'=' * 40}")
                    print(message.content)
            elif key == 'error_log':
                print(f"\n{'=' * 40}")
                print("Error Log:")
                print(f"{'=' * 40}")
                for error in value:
                    print(error)
            else:
                print(f"\n{'=' * 40}")
                print(f"{key.capitalize()}:")
                print(f"{'=' * 40}")
                for sub_key, sub_value in value.items():
                    print(f"{sub_key}: {sub_value}")
        print("\n" + "-" * 80 + "\n")
except Exception as e:
    logger.exception("An error occurred during execution")
    raise