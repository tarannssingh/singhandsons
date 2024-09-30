from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/bottler",
    tags=["bottler"],
    dependencies=[Depends(auth.get_api_key)],
)

class PotionInventory(BaseModel):
    potion_type: list[int]
    quantity: int

@router.post("/deliver/{order_id}")
def post_deliver_bottles(potions_delivered: list[PotionInventory], order_id: int):
    """ """
    with db.engine.begin() as connection:
        print(f"potions delievered: {potions_delivered} order_id: {order_id}")
        # remove the amount of green to remove
        for potion in potions_delivered:
            # assume it is green 
            # update the amount of green ml available
            connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_ml = num_green_ml - {potion.quantity * 100}"))
            # update the amount of potions added 
            connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_green_potions = num_green_potions + :quantity"), {"quantity": potion.quantity })

    
    # add that amount to potions
    return "OK"

@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """

    # Each bottle has a quantity of what proportion of red, blue, and
    # green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.

    # Initial logic: bottle all barrels into red potions.
    with db.engine.begin() as connection:
        num_green_ml = connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory")).scalar()
        num_green_ml = 200
        if num_green_ml // 100 != 0:
            # remove that amount from my db
            # connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_ml = num_green_ml - {(num_green_ml // 100) * 100}"))
            return [
                    {
                        "potion_type": [0, 100, 0, 0],
                        "quantity": num_green_ml // 100,
                    }
                ]
        return []
                
            # return [
            #     {
            #         "potion_type": [100, 0, 0, 0],
            #         "quantity": 5,
            #     }
            #     ]   

# [
#   {
#     "potion_type": [r, g, b, d],
#     "quantity": "integer"
#   }
# ]

if __name__ == "__main__":
    print(get_bottle_plan())