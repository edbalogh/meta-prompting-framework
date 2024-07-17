# Set up the tool
from langchain_anthropic import ChatAnthropic
from tools.demo_tools import get_weather
from psycopg_pool import ConnectionPool
import os

from utils.postgres_saver import PostgresSaver

# setup tools
tools = [get_weather]

# setup the model
model = ChatAnthropic(model="claude-3-5-sonnet-20240620")
model = model.bind_tools(tools)

pg_user = os.environ['POSTGRES_USER']
pg_password = os.environ['POSTGRES_PASSWORD']
pg_db = os.environ['POSTGRES_DB']
DB_URI = f"postgresql://{pg_user}:{pg_password}@localhost:5432/{pg_db}?sslmode=disable"

pool = ConnectionPool(
    # Example configuration
    conninfo=DB_URI,
    max_size=20,
)

checkpointer = PostgresSaver(sync_connection=pool)
checkpointer.create_tables(pool)

from langgraph.prebuilt import create_react_agent

agent = create_react_agent(model, tools=tools, checkpointer=checkpointer)
