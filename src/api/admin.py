from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db
import logging
logger = logging.getLogger("uvicorn")

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
        logger.info("reset")
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = 100, potion_capacity = 1, ml_capacity = 1, num_red_ml = 0, num_green_ml = 0, num_blue_ml = 0, num_dark_ml = 0"))
        connection.execute(sqlalchemy.text("UPDATE potion_inventory SET num_potions = 0"))    
        # connection.execute(sqlalchemy.text("UPDATE cart SET num_of_green_potions = 0, num_of_red_potions = 0, num_of_blue_potions = 0"))
        #! Don't want to remove old data as it is good for analytics 
        return "OK"

