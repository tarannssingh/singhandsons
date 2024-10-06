from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)

import logging
logger = logging.getLogger("uvicorn")

class Barrel(BaseModel):
    sku: str

    ml_per_barrel: int
    potion_type: list[int]
    price: int

    quantity: int

@router.post("/deliver/{order_id}")
def post_deliver_barrels(barrels_delivered: list[Barrel], order_id: int):
    """ """
    with db.engine.begin() as connection:
        logger.info(f"barrels delievered: {barrels_delivered} order_id: {order_id}")
        # Update the barrels delievered assuming just green
        for barrels in barrels_delivered:
            # if the 3 possiblities and update the gold and inventory accordingly
            match barrels.potion_type:
                case [0,1,0,0]: # green
                    # query to get my current amount of green ml
                    # query to update my inventory
                    connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_ml = num_green_ml + {barrels.ml_per_barrel * barrels.quantity}"))
                    connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold = gold - {barrels.price * barrels.quantity}"))
                case [1,0,0,0]: # red
                    connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_ml = num_red_ml + {barrels.ml_per_barrel * barrels.quantity}"))
                    connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold = gold - {barrels.price * barrels.quantity}"))
                case [0,0,1,0]: # blue
                    connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_blue_ml = num_blue_ml + {barrels.ml_per_barrel * barrels.quantity}"))
                    connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold = gold - {barrels.price * barrels.quantity}"))
                # case [0,0,0,1]:
                #     pass
        return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    logger.info(wholesale_catalog)

    with db.engine.begin() as connection:
        num_of_green_potions = connection.execute(sqlalchemy.text("SELECT num_potions FROM potion_inventory WHERE sku = 'GREEN'")).scalar()
        num_of_red_potions = connection.execute(sqlalchemy.text("SELECT num_potions FROM potion_inventory WHERE sku = 'RED'")).scalar()
        num_of_blue_potions = connection.execute(sqlalchemy.text("SELECT num_potions FROM potion_inventory WHERE sku = 'BLUE'")).scalar()

        # potions = connection.execute(sqlalchemy.text("SELECT sku, red, green, blue, dark, num_potions FROM potion_inventory")).fetchall()

        # log what is being sold
        # [r, g, b, d]
        green = {"sku" : "", "price" : 0}
        red = {"sku" : "", "price" : 0}
        blue = {"sku" : "", "price" : 0}
        for barrel in wholesale_catalog:
            if barrel.potion_type == [0, 1, 0, 0] and barrel.sku == "SMALL_GREEN_BARREL":   # check if the wholesaler is selling the goods we need and if we have the funds to purchase
                green["sku"] = barrel.sku
                green["price"] = barrel.price
            if barrel.potion_type == [1, 0, 0, 0] and barrel.sku == "SMALL_RED_BARREL":   # check if the wholesaler is selling the goods we need and if we have the funds to purchase
                red["sku"] = barrel.sku
                red["price"] = barrel.price
            if barrel.potion_type == [0, 0, 1, 0] and barrel.sku == "SMALL_BLUE_BARREL":   # check if the wholesaler is selling the goods we need and if we have the funds to purchase
                blue["sku"] = barrel.sku
                blue["price"] = barrel.price
        
        # Now buy what we have capacity to buyt 
        toBuy = []
        net_worth = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory")).scalar()

        
        if num_of_red_potions < 5 and red["sku"] != "" and net_worth >= red["price"]: # if we need to buy and the seller is selling
            toBuy.append(
                {
                    "sku": red["sku"],
                    "quantity": 1,
                }
            )
            net_worth -= red["price"]
        if num_of_blue_potions < 5 and blue["sku"] != "" and net_worth >= blue["price"]: # if we need to buy and the seller is selling
            toBuy.append(
                {
                    "sku": blue["sku"],
                    "quantity": 1,
                }
            )
            net_worth -= blue["price"]   
        if num_of_green_potions < 5 and green["sku"] != "" and net_worth >= green["price"]: # if we need to buy and the seller is selling
            toBuy.append(
                {
                    "sku": green["sku"],
                    "quantity": 1,
                }
            )
            net_worth -= green["price"]

        # it will return nothing if there is nothing to return, else it will return what we marked to buy
        return toBuy
    

        # return [
        #     {
        #         "sku": "SMALL_RED_BARREL",
        #         "quantity": 1,
        #     }
        # ]

