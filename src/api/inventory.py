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
        gold = connection.execute(sqlalchemy.text(f"SELECT gold FROM global_inventory")).scalar()
        pre_ml = connection.execute(sqlalchemy.text(f"SELECT num_red_ml, num_green_ml, num_blue_ml FROM global_inventory")).fetchall()
        ml = pre_ml[0][0] + pre_ml[0][1] + pre_ml[0][2]
        potions = connection.execute(sqlalchemy.text(f"SELECT SUM(num_potions) FROM potion_inventory")).scalar()
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

        gold = connection.execute(sqlalchemy.text(f"SELECT gold FROM global_inventory")).scalar()
        if gold > 4000: 
            return {
                "potion_capacity": 1,
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
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET potion_capacity = potion_capacity + {capacity_purchase.potion_capacity}, ml_capacity = ml_capacity + {capacity_purchase.ml_capacity}"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold = gold - {1000 * capacity_purchase.potion_capacity + 1000 * capacity_purchase.ml_capacity}"))

    return "OK"
