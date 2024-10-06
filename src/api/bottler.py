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
            connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_ml = num_red_ml - {red}, num_green_ml = num_green_ml - {green}, num_blue_ml = num_blue_ml - {blue}, num_dark_ml = num_dark_ml - {dark}"))
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
        result = connection.execute(sqlalchemy.text("SELECT sku, red, green, blue, dark FROM potion_inventory")).fetchall()
        
        green = connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory")).scalar()
        red = connection.execute(sqlalchemy.text("SELECT num_red_ml FROM global_inventory")).scalar()
        blue = connection.execute(sqlalchemy.text("SELECT num_blue_ml FROM global_inventory")).scalar()
        dark = connection.execute(sqlalchemy.text("SELECT num_dark_ml FROM global_inventory")).scalar()

        toBottle = []

        for potion in result:
            # deduct from global
            # see if any of global became negative
            # if not than add one more quantity 
            potion_blueprint = []
            for i in range(1,5):
                potion_blueprint.append(potion[i]) if potion[i] else potion_blueprint.append(0)
            match potion_blueprint:
                case [0,100,0,0]: # green
                    # query to get my current amount of green ml
                    # query to update my inventory
                    if green // 100 != 0:
                        logger.info(f"number of {potion[1]} I want to bottle: {green//100} ml")
                        toBottle.append(
                            {
                                "potion_type": potion_blueprint,
                                "quantity": green // 100,
                            }
                        )
                case [100,0,0,0]: # red
                     if red // 100 != 0:
                        logger.info(f"number of {potion[1]} I want to bottle: {red//100} ml")
                        toBottle.append(
                            {
                                "potion_type": potion_blueprint,
                                "quantity": red // 100,
                            }
                        )
                case [0,0,100,0]: # blue
                    if blue // 100 != 0:
                        logger.info(f"number of {potion[1]} I want to bottle: {blue//100} ml")
                        toBottle.append(
                            {
                                "potion_type": potion_blueprint,
                                "quantity": blue // 100,
                            }
                        )
        return toBottle
                
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