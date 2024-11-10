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
        # for each potion update the potion ledger
        for potion in potions_delivered:
            red = potion.potion_type[0]
            green = potion.potion_type[1]
            blue = potion.potion_type[2]
            dark = potion.potion_type[3]

            # insert the transaction and get the corresponding id
            description = f"Bottle: {potion.quantity} of [{red}, {green}, {blue}, {dark}]"
            sql_to_execute = "INSERT INTO transactions (description) VALUES (:description) RETURNING id"
            values = {"description": description}
            transaction_id = connection.execute(sqlalchemy.text(sql_to_execute), values).scalar()

            # update the ml used to bottle said potion       
            values = {
                "transaction_id": transaction_id,
                "red_quantity": -red * potion.quantity,
                "green_quantity": -green * potion.quantity,
                "blue_quantity": -blue * potion.quantity,
                "dark_quantity": -dark * potion.quantity
            }
            sql_to_execute = '''
                                INSERT INTO ml_ledger_entries (transaction_id, ml_id, change) VALUES (:transaction_id, 1, :red_quantity);
                                INSERT INTO ml_ledger_entries (transaction_id, ml_id, change) VALUES (:transaction_id, 2, :green_quantity);
                                INSERT INTO ml_ledger_entries (transaction_id, ml_id, change) VALUES (:transaction_id, 3, :blue_quantity);
                                INSERT INTO ml_ledger_entries (transaction_id, ml_id, change) VALUES (:transaction_id, 4, :dark_quantity);
                            '''
            connection.execute(sqlalchemy.text(sql_to_execute), values)

            # update the potion count 
            sql_to_execute = "SELECT id FROM potion_inventory WHERE red = :red AND green = :green AND blue = :blue AND dark = :dark"
            values = {
                "red" : red,
                "green" : green,
                "blue": blue,
                "dark": dark
            }
            
            potion_id = connection.execute(sqlalchemy.text(sql_to_execute), values).scalar()
            values = {
                "transaction_id": transaction_id,
                "potion_id": potion_id,
                "quantity": potion.quantity 
            }

            sql_to_execute = '''
                                INSERT INTO potion_ledger_entries (transaction_id, potion_id, change) VALUES (:transaction_id, :potion_id, :quantity);
                             '''
            connection.execute(sqlalchemy.text(sql_to_execute), values)
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
        current_potions_count = connection.execute(sqlalchemy.text(f"SELECT CAST(COALESCE(SUM(change), 0) AS INT) FROM potion_ledger_entries")).scalar()
        potion_capacity = connection.execute(sqlalchemy.text(f"SELECT ml_capacity FROM global_inventory")).scalar()
        allowance = potion_capacity * 50 - current_potions_count
        # mls        
        # get the mls
        sql_to_execute = '''
                                    SELECT ml_catalog.name, CAST(COALESCE(SUM(change), 0) AS INT) as ml FROM ml_catalog 
                                    LEFT JOIN ml_ledger_entries 
                                    ON ml_ledger_entries.ml_id = ml_catalog.id
                                    GROUP BY ml_catalog.name
                         '''
        red = 0 
        green = 0
        blue = 0
        dark = 0
        ml_query = list(connection.execute(sqlalchemy.text(sql_to_execute)))
        for ml in ml_query:
            if ml[0] == "RED":
                red = ml[1]
            if ml[0] == "GREEN":
                green = ml[1]
            if ml[0] == "BLUE":
                blue = ml[1]
            if ml[0] == "DARK":
                dark = ml[1]


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
                if allowance <= 0: # if we don't have the capacity to make more, than stop going through potions
                    break
                potion_vals = potion_blueprint[sku]
                if red - potion_vals[0] >= 0 and green - potion_vals[1] >= 0 and blue - potion_vals[2] >= 0 and dark - potion_vals[3] >= 0:
                    continue_bottiling = True 
                    to_bottle[sku]["quantity"] += 1
                    allowance -= 1
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
        # Logic to prune any bottles we don't have capacity for
        # allowed_amount = 50 * potion_capacity - current_potions_count
        # while allowed_amount = 0 
        # for bottle in to_buy:
        # # remove any potions that we are not allowed to buy because of spacing limits
        # to_buy = list(to_bottle.values())




        # return to_buy
    
# 



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