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
    with db.engine.begin() as connection:
        print(f"barrels delievered: {barrels_delivered} order_id: {order_id}")
        # Update the barrels delievered assuming just green
        for barrels in barrels_delivered:
            # match barrels.potion_type:
                # case [0,1,0,0]:
                    # query to get my current amount of green ml
                    num_green_ml = connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory")).scalar()
                    # query to update my inventory
                    connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_ml={num_green_ml + barrels.ml_per_barrel * barrels.quantity}"))
                    connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold = gold - {barrels.price * barrels.quantity}"))
                # case [0,0,0,1]:
                #     pass
                # case [0,0,0,1]:
                #     pass
                # case [0,0,0,1]:
                #     pass
        return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)

    with db.engine.begin() as connection:
        num_of_green_potions = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory")).scalar()
        net_worth = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory")).scalar()

        # so iterate through catalog and find the potion_type of just green for right now
        green_sku = ""
        for barrel in wholesale_catalog:
            if barrel.potion_type == [0, 1, 0, 0] and net_worth >= barrel.price:   # check if the wholesaler is selling the goods we need and if we have the funds to purchase
                green_sku = barrel.sku
                
        if num_of_green_potions < 10 and green_sku != "": # if we need to buy and the seller is selling
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

