from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import math
import sqlalchemy
from src import database as db


router = APIRouter(
    prefix="/inventory",
    tags=["inventory"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.get("/audit")
def get_inventory():
    """ """
    with db.engine.begin() as connection:
        gold = connection.execute(sqlalchemy.text(f"SELECT CAST(COALESCE(SUM(change), 0) AS INT) FROM gold_ledger_entries")).scalar()
        ml = connection.execute(sqlalchemy.text(f"SELECT CAST(COALESCE(SUM(change), 0) AS INT) FROM ml_ledger_entries")).scalar()
        potions = connection.execute(sqlalchemy.text(f"SELECT CAST(COALESCE(SUM(change), 0) AS INT) FROM potion_ledger_entries")).scalar()
        return {"number_of_potions": potions, "ml_in_barrels": ml, "gold": gold}

# Gets called once a day
@router.post("/plan")
def get_capacity_plan():
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """
    with db.engine.begin() as connection:
        # potion_capacity = 50 
        # potion_capacity_multiplier = connection.execute(sqlalchemy.text(f"SELECT potion_capacity FROM global_inventory")).scalar()
        # ml_capacity = 10000 
        # potion_capacity_multiplier = connection.execute(sqlalchemy.text(f"SELECT ml_capacity FROM global_inventory")).scalar()

        # return {
        #     "potion_capacity": potion_capacity_multiplier,
        #     "ml_capacity": potion_capacity_multiplier
        # }

        gold = connection.execute(sqlalchemy.text(f"SELECT CAST(COALESCE(SUM(change), 0) AS INT) FROM gold_ledger_entries")).scalar()
        ml = connection.execute(sqlalchemy.text(f"SELECT CAST(COALESCE(SUM(change), 0) AS INT) FROM ml_ledger_entries")).scalar()
        potion_capacity = connection.execute(sqlalchemy.text(f"SELECT ml_capacity FROM global_inventory")).scalar()
        ml_capacity = connection.execute(sqlalchemy.text(f"SELECT potion_capacity FROM global_inventory")).scalar()
        if gold > 1200: 
            if potion_capacity <= 3 * ml_capacity: 
                return {
                    "potion_capacity": 1,
                    "ml_capacity": 0
                }
            else:
                return {
                    "potion_capacity": 0,
                    "ml_capacity": 1
                }
        return {
            "potion_capacity": 0,
            "ml_capacity": 0
        }
#         {
#   "potion_capacity": "number",
#   "ml_capacity": "number"
# }


class CapacityPurchase(BaseModel):
    potion_capacity: int
    ml_capacity: int

# Gets called once a day
@router.post("/deliver/{order_id}")
def deliver_capacity_plan(capacity_purchase : CapacityPurchase, order_id: int):
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """
    with db.engine.begin() as connection:
        if capacity_purchase.potion_capacity != 0 or capacity_purchase.ml_capacity != 0:
            # insert the transaction and get the corresponding id
            description = f"Capacity: Buy {capacity_purchase.potion_capacity} potion capacity and {capacity_purchase.ml_capacity} ml capacity"
            sql_to_execute = "INSERT INTO transactions (description) VALUES (:description) RETURNING id"
            values = {"description": description}
            transaction_id = connection.execute(sqlalchemy.text(sql_to_execute), values).scalar()
            connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET potion_capacity = potion_capacity + {capacity_purchase.potion_capacity}, ml_capacity = ml_capacity + {capacity_purchase.ml_capacity}"))
            # update gold
            values = {"transaction_id": transaction_id, "change": -1 * (capacity_purchase.potion_capacity * 1000 + capacity_purchase.ml_capacity * 1000)}
            sql_to_execute = "INSERT INTO gold_ledger_entries (transaction_id, change) VALUES (:transaction_id, :change)"
            connection.execute(sqlalchemy.text(sql_to_execute), values)
        
    return "OK"
