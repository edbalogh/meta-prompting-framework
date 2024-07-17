from fastapi import FastAPI
from langserve import add_routes

from api.endpoints import conversations
from agent.graph import agent

app = FastAPI()

# Mount all endpoint routers
app.include_router(conversations.router)

# add langserve routes
add_routes(
    app=app,
    runnable=agent.with_types(input_type=dict, output_type=dict),
    path='/agents/helloworld'
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=3000, log_level="debug", reload=True)  # Adjust host and port as needed