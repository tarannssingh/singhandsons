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
            ml_id = None
            color = None
            match barrels.potion_type:
                case [0,1,0,0]: # green
                    ml_id = 2
                    color = 'GREEN'
                case [1,0,0,0]: # red
                    ml_id = 1
                    color = 'RED'
                case [0,0,1,0]: # blue
                    ml_id = 3
                    color = 'BLUE'
                case [0,0,0,1]:
                    ml_id = 4
                    color = 'DARK'
            if ml_id and color:
                # transaction
                sql_to_execute = "INSERT INTO transactions (description) VALUES (:description) RETURNING id"
                description = f'Purchase Barrel: {barrels.quantity} {color} at {barrels.ml_per_barrel} ml'
                values = {"description": description}
                transaction_id = connection.execute(sqlalchemy.text(sql_to_execute), values).scalar()
                
                # add new barrels
                sql_to_execute = "INSERT INTO ml_ledger_entries (transaction_id, ml_id, change) VALUES (:transaction_id, :ml_id, :change)"
                values = {"transaction_id": transaction_id, "ml_id": ml_id, "change": barrels.ml_per_barrel * barrels.quantity, "cost": -barrels.price * barrels.quantity}
                connection.execute(sqlalchemy.text(sql_to_execute), values)
                # remove gold
                sql_to_execute = "INSERT INTO gold_ledger_entries (transaction_id, change) VALUES (:transaction_id, :cost)"
                connection.execute(sqlalchemy.text(sql_to_execute), values)
        return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    logger.info(wholesale_catalog)

    with db.engine.begin() as connection:
        # num_of_ml = connection.execute(sqlalchemy.text("SELECT num_red_ml, num_green_ml, num_blue_ml, num_dark_ml FROM global_inventory")).first()
        # net_worth = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory")).scalar()
        ml_current = connection.execute(sqlalchemy.text(f"SELECT CAST(COALESCE(SUM(change), 0) AS INT) FROM ml_ledger_entries")).scalar()
        ml_capacity = connection.execute(sqlalchemy.text(f"SELECT ml_capacity FROM global_inventory")).scalar()
        allowance = ml_capacity * 10000 - ml_current
        logger.info(f"allowance left: {allowance}")

        sql_to_execute = '''
                            SELECT ml_catalog.name, CAST(COALESCE(SUM(change), 0) AS INT) as ml FROM ml_catalog 
                            LEFT JOIN ml_ledger_entries 
                            ON ml_ledger_entries.ml_id = ml_catalog.id
                            GROUP BY ml_catalog.name
                        '''
        num_of_ml = [0] * 4
        ml_query = list(connection.execute(sqlalchemy.text(sql_to_execute)))
        for ml in ml_query:
            if ml[0] == "RED":
                num_of_ml[0] = ml[1]
            if ml[0] == "GREEN":
                num_of_ml[1] = ml[1]
            if ml[0] == "BLUE":
                num_of_ml[2] = ml[1]
            if ml[0] == "DARK":
                num_of_ml[3] = ml[1]
        net_worth = connection.execute(sqlalchemy.text("SELECT CAST(SUM(change) AS INT) FROM gold_ledger_entries")).scalar()
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

        
        # converted_wholesale_catalog = [Barrel(**barrel) if not isinstance(barrel, Barrel) else barrel for barrel in wholesale_catalog]
        for barrel in wholesale_catalog:
            # buy where the price is lowest and is necary budget each one (havea list) 
            # budget system and then append the barrels that fit critera starting form the biggest and going down from there
            # keep this as a second strategy to buy something if the first startegey above returns nothing to buy 
            if barrel.potion_type == [0, 1, 0, 0]:   # check if the wholesaler is selling the goods we need and if we have the funds to purchase
                barrel_colors["green"].append(barrel)
            if barrel.potion_type == [1, 0, 0, 0]:   # check if the wholesaler is selling the goods we need and if we have the funds to purchase
                barrel_colors["red"].append(barrel)
            if barrel.potion_type == [0, 0, 1, 0]:   # check if the wholesaler is selling the goods we need and if we have the funds to purchase
                barrel_colors["blue"].append(barrel)
            if barrel.potion_type == [0, 0, 0, 1]:
                barrel_colors["dark"].append(barrel)
        # {"sku" : barrel.sku, "price" : barrel.price, "quantity": 0, "for_sale": barrel.quantity}
        # Now buy what we have capacity to buy
        for color in colors:
            barrel_colors[color] = sorted(barrel_colors[color], key = lambda b: b.price)

        toBuy = {}
        continueAdding = 0
        while True:
            for color in colors:
                if len(barrel_colors[color]) != 0: # if we need to buy and the seller is selling                        
                    for index, barrel in enumerate(barrel_colors[color]):
                        if barrel.quantity != 0 and budget[color] >= barrel.price:
                            allowance -= barrel.ml_per_barrel
                            if allowance < 0:
                                allowance += barrel.ml_per_barrel
                                break
                            if barrel.sku not in toBuy:
                                toBuy[barrel.sku] = {"sku" : barrel.sku, "quantity": 0}
                            toBuy[barrel.sku]["quantity"] += 1 
                            barrel.quantity -= 1 
                            # barrel_colors[color][index]["quantity"] -= 1
                            budget[color] -= barrel.price
                            continueAdding += 1
            if not continueAdding:  # this is a flag to make sure we actually have the funds to add any 
                break
            continueAdding = 0
            
        for color in colors:
            left_over_coins += budget[color]
        # This is just bootstrap code, so ill buy certain ml if I don't have any, to just make custom potions
        if num_of_ml[1] < 100 and len(barrel_colors["green"]) and barrel_colors["green"][0].quantity != 0 and  barrel_colors["green"][0].price <= left_over_coins and allowance - barrel_colors["green"][0].ml_per_barrel >= 0 : # dark
            sku = barrel_colors["green"][0].sku
            toBuy[sku] = {"sku" : sku, "quantity": 1}
            barrel_colors["green"][0].quantity -= 1
            left_over_coins -= barrel_colors["green"][0].price
            allowance -= barrel_colors["green"][0].ml_per_barrel 
        if num_of_ml[3] < 100 and len(barrel_colors["dark"]) and barrel_colors["dark"][0].quantity != 0 and barrel_colors["dark"][0].price <= left_over_coins and allowance - barrel_colors["dark"][0].ml_per_barrel >= 0 : # dark
            sku = barrel_colors["dark"][0].sku
            toBuy[sku] = {"sku" : sku, "quantity": 1}
            barrel_colors["dark"][0].quantity -= 1
            left_over_coins -= barrel_colors["dark"][0].price
            allowance -= barrel_colors["dark"][0].ml_per_barrel

        logger.info(f"{left_over_coins}")
        logger.info(f"{barrel_colors}")
        # it will return nothing if there is nothing to return, else it will return what we marked to buy
        # return toBuy
        # toBuy = filter(lambda b: b["quantity"] != 0, toBuy)
        # for barrel in toBuy:
        #     if "price" in barrel:
        #         del barrel["price"]

        logger.info(f"allowance left: {allowance}")
        return list(toBuy.values())
    
        # return [
        #     {
        #         "sku": "SMALL_RED_BARREL",
        #         "quantity": 1,
        #     }
        # ]

