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

class Barrel(BaseModel):
    sku: str

    ml_per_barrel: int
    potion_type: list[int]
    price: int

    quantity: int

@router.post("/deliver/{order_id}")
def post_deliver_barrels(barrels_delivered: list[Barrel], order_id: int):
    """ """
    print(f"barrels delievered: {barrels_delivered} order_id: {order_id}")
    # Update the barrels delievered
    

    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory")).scalar()
        print(wholesale_catalog)
        

        # so iterate through catalog and find the potion_type of just green for right now
        green_sku = ""
        for barrel in wholesale_catalog:
            if barrel.potion_type[1] == 1:
                green_sku = barrel.sku
        
        if result < 10 and green_sku != "": # if we need to buy and the seller is selling
            return [
                {
                    "sku": green_sku,
                    "quantity": 1,
                }
            ]
        return [] # else buy nothing
    

        # return [
        #     {
        #         "sku": "SMALL_RED_BARREL",
        #         "quantity": 1,
        #     }
        # ]

