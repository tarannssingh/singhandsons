from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db
import logging
logger = logging.getLogger("uvicorn")

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
        logger.info(f"potions delievered: {potions_delivered} order_id: {order_id}")
        # remove the amount of green to remove
        for potion in potions_delivered:
            # update the amount of green ml available
            # update the amount of potions added 
            red = potion.potion_type[0]
            green = potion.potion_type[1]
            blue = potion.potion_type[2]
            dark = potion.potion_type[3]

            # update the potion count
            connection.execute(sqlalchemy.text("UPDATE potion_inventory SET num_potions = num_potions + :quantity WHERE green = :green AND red = :red AND blue = :blue AND dark = :dark"), {"quantity": potion.quantity, "red": red, "green": green, "blue": blue, "dark": dark})
            # update the ml count
            connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_ml = num_red_ml - {red * potion.quantity}, num_green_ml = num_green_ml - {green * potion.quantity}, num_blue_ml = num_blue_ml - {blue * potion.quantity}, num_dark_ml = num_dark_ml - {dark * potion.quantity}"))
            # connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET ml = - {potion.potion_type[0] * potion.quantity}"))
            
            # [
            #     {
            #         "potion_type": [
            #         50, 50, 0, 0
            #         ],
            #         "quantity": 0
            #     }
            #  ]

            # use the array to pick

            
    
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
        # mls 
        red = connection.execute(sqlalchemy.text("SELECT num_red_ml FROM global_inventory")).scalar()
        green = connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory")).scalar()
        blue = connection.execute(sqlalchemy.text("SELECT num_blue_ml FROM global_inventory")).scalar()
        dark = connection.execute(sqlalchemy.text("SELECT num_dark_ml FROM global_inventory")).scalar()

        # potions
        to_bottle = {}
        potion_blueprint = {}
        potions = connection.execute(sqlalchemy.text("SELECT sku, red, green, blue, dark FROM potion_inventory WHERE to_sell = 1")).fetchall()
        for potion in potions:
            # deduct from global
            # see if any of global became negative
            # if not than add one more quantity 
            # potion_blueprint = []
            # for i in range(1,5):
            #     potion_blueprint.append(potion[i]) if potion[i] else potion_blueprint.append(0)
            potion_blueprint[potion[0]] = (int(potion[1]), int(potion[2]), int(potion[3]), int(potion[4]))
            to_bottle[potion[0]] = {
                        "potion_type": potion_blueprint[potion[0]],
                        "quantity": 0,
                    }
        continue_bottiling = True 
        while continue_bottiling:
            continue_bottiling = False
            for sku in potion_blueprint.keys():
                potion_vals = potion_blueprint[sku]
                if red - potion_vals[0] >= 49 and green - potion_vals[1] >= 0 and blue - potion_vals[2] >= 0 and dark - potion_vals[3] >= 0:
                    continue_bottiling = True 
                    to_bottle[sku]["quantity"] += 1
                    red -= potion_vals[0]
                    green -= potion_vals[1]
                    blue -= potion_vals[2]
                    dark -= potion_vals[3]    
            # while one of ml is zero contiunting adding to quanity  (remove from blue print if its not possible) (check if i have capacity (55 poitons vs 50))
            # loop on the blue print 
        for bottle in list(to_bottle.keys()):
            if to_bottle[bottle]["quantity"] == 0:
                del to_bottle[bottle]
        return list(to_bottle.values())
                
            # return [
            #     {
            #         "potion_type": [100, 0, 0, 0],
            #         "quantity": 5,
            #     }
            #     ]   
            
            # case [0,0,0,1]:
            #     pass
            # if potion[1]:
            #     green_ml = potion[1]
            # if potion[2]:
            #     red_ml = potion[2]
            # if potion[3]:
            #     blue_ml = potion[3]
            # if potion[4]:
            #     dark_ml = potion[4]

            # [
            #   {
            #     "potion_type": [r, g, b, d],
            #     "quantity": "integer"
            #   }
            # ]

if __name__ == "__main__":
    print(get_bottle_plan())