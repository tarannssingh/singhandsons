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
                case [0,0,0,1]:
                    connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_dark_ml = num_dark_ml + {barrels.ml_per_barrel * barrels.quantity}"))
                    connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold = gold - {barrels.price * barrels.quantity}"))
        return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    logger.info(wholesale_catalog)

    with db.engine.begin() as connection:
        num_of_ml = connection.execute(sqlalchemy.text("SELECT num_red_ml, num_green_ml, num_blue_ml, num_dark_ml FROM global_inventory")).first()
        net_worth = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory")).scalar()
        # potions = connection.execute(sqlalchemy.text("SELECT sku, red, green, blue, dark, num_potions FROM potion_inventory")).fetchall()

        # log what is being sold
        # [r, g, b, d]
        # available potions to buy

        barrel_colors = {}
        budget = {}
        left_over_coins = 0 
        colors = ["red", "green", "blue", "dark"]
        for color in colors:
            budget[color] = net_worth // 4 
            barrel_colors[color] = []

        for barrel in wholesale_catalog:
            # buy where the price is lowest and is necary budget each one (havea list) 
            # budget system and then append the barrels that fit critera starting form the biggest and going down from there
            # keep this as a second strategy to buy something if the first startegey above returns nothing to buy 
            if barrel.potion_type == [0, 1, 0, 0]:   # check if the wholesaler is selling the goods we need and if we have the funds to purchase
                barrel_colors["green"].append({"sku" : barrel.sku, "price" : barrel.price, "quantity": barrel.quantity})
            if barrel.potion_type == [1, 0, 0, 0]:   # check if the wholesaler is selling the goods we need and if we have the funds to purchase
                barrel_colors["red"].append({"sku" : barrel.sku, "price" : barrel.price, "quantity": barrel.quantity})
            if barrel.potion_type == [0, 0, 1, 0]:   # check if the wholesaler is selling the goods we need and if we have the funds to purchase
                barrel_colors["blue"].append({"sku" : barrel.sku, "price" : barrel.price, "quantity": barrel.quantity})
            if barrel.potion_type == [0, 0, 0, 1]:
                barrel_colors["dark"].append({"sku" : barrel.sku, "price" : barrel.price, "quantity": barrel.quantity})
        
        # Now buy what we have capacity to buy
        for color in colors:
            barrel_colors[color] = sorted(barrel_colors[color], key = lambda b: b["price"])

        toBuy = []
        continueAdding = 0
        while True:
            for color in colors:
                if len(barrel_colors[color]) != 0: # if we need to buy and the seller is selling                        
                    for index, barrel in enumerate(barrel_colors[color]):
                        if barrel["quantity"] != 0 and budget[color] >= barrel["price"]:
                            toBuy.append({"sku" : barrel.sku, "price" : barrel.price})
                            barrel_colors[color][index]["quantity"] -= 1
                            budget[color] -= barrel["price"]
                            continueAdding += 1
            if not continueAdding:  # this is a flag to make sure we actually have the funds to add any 
                break
            continueAdding = 0
            
        for color in colors:
            left_over_coins += budget[color]
        # This is just bootstrap code, so ill buy certain ml if I don't have any, to just make custom potions
        if num_of_ml[2] < 100 and len(barrel_colors["blue"]) and barrel_colors["blue"][0]["quantity"] != 0 and  barrel_colors["blue"][0]["price"] <= left_over_coins: # dark
            toBuy.append(barrel_colors["blue"][0])
            barrel_colors["blue"][0]["quantity"] -= 1
            left_over_coins -= barrel_colors["blue"][0]["price"]
        if num_of_ml[3] < 100 and len(barrel_colors["dark"]) and barrel_colors["dark"][0]["quantity"] != 0 and barrel_colors["dark"][0]["price"] <= left_over_coins: # dark
            toBuy.append(barrel_colors["dark"][0])
            barrel_colors["dark"][0]["quantity"] -= 1
            left_over_coins -= barrel_colors["dark"][0]["price"]

        logger.info(f"{left_over_coins}")
        logger.info(f"{barrel_colors}")
        # it will return nothing if there is nothing to return, else it will return what we marked to buy
        return toBuy
    

        # return [
        #     {
        #         "sku": "SMALL_RED_BARREL",
        #         "quantity": 1,
        #     }
        # ]

