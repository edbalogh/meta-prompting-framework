import os, logging
from langchain_core.tools import Tool
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_community.utilities.wolfram_alpha import WolframAlphaAPIWrapper
from langchain_community.tools.wolfram_alpha import WolframAlphaQueryRun
from langchain_community.utilities.wikipedia import WikipediaAPIWrapper
from agent.utils.meta_prompting_agent import create_meta_prompting_agent
from psycopg_pool import AsyncConnectionPool
from agent.utils.postgres_saver import PostgresSaver

DB_NAME=os.environ['POSTGRES_DB']
DB_USER=os.environ['POSTGRES_USER']
DB_PWD=os.environ['POSTGRES_PASSWORD']

DB_URI = f"postgresql://{DB_USER}:{DB_PWD}@db/{DB_NAME}"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def build_agent(model):
    
    pool = AsyncConnectionPool(
        # Example configuration
        conninfo=DB_URI,
        max_size=20,
    )

    checkpointer = PostgresSaver(async_connection=pool)
    await checkpointer.acreate_tables(pool)

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

    return create_meta_prompting_agent(model, tools)