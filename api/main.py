from fastapi import FastAPI
from langserve import add_routes
from endpoints import conversations
from agent.chat_agent import build_agent
from agent.utils.llm_setup import get_llm
import asyncio

app = FastAPI()

# Mount all endpoint routers
app.include_router(conversations.router)

async def setup_agent():
    return await build_agent(get_llm("openai", "gpt-4o-mini"))

agent = asyncio.run(setup_agent())

# add langserve routes
add_routes(
    app=app,
    runnable=agent.with_types(input_type=dict, output_type=dict),
    path='/agents/meta-prompter'
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=3000, log_level="debug", reload=True)
