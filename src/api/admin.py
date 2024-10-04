from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.post("/reset")
def reset():
    """
    Reset the game state. Gold goes to 100, all potions are removed from
    inventory, and all barrels are removed from inventory. Carts are all reset.
    """
    with db.engine.begin() as connection:
        # reset gold
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = 100, potion_capacity = 1, ml_capacity = 1"))
        connection.execute(sqlalchemy.text("UPDATE potion_inventory SET num_ml = 0, num_potions = 0, num_price = 50"))    
        
        return "OK"

