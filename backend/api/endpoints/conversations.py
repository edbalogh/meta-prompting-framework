from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
import os
from langchain_community.graphs import Neo4jGraph

NEO4J_CUSTOMERS_URI = os.environ.get("NEO4J_CUSTOMERS_URI")
NEO4J_USERNAME = os.environ.get("NEO4J_USERNAME")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD")

router = APIRouter(prefix="/api/conversations")

@router.get('/')
async def get_all_customer_nodes():
    return []
