from fastapi import APIRouter

router = APIRouter(prefix="/api/conversations")

@router.get('/')
async def get_all_customer_nodes():
    return []
