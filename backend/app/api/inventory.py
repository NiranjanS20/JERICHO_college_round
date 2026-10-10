from fastapi import APIRouter
from app.inventory import COMPONENT_INVENTORY

router = APIRouter(prefix="/api/inventory", tags=["inventory"])

@router.get("")
async def list_inventory():
    return [comp.__dict__ for comp in COMPONENT_INVENTORY]
