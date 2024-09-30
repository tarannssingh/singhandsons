import sqlalchemy
from src import database as db

from fastapi import APIRouter

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """
    with db.engine.begin() as connection:
        # connection.execute is like fetch let response = await fetch({})
        # and .scalar or .fetchall are like await let jsonData = await response.json()
        result = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory;")).fetchall()
        num_green_price  = connection.execute(sqlalchemy.text("SELECT num_green_price FROM global_inventory;")).scalar()

        # if we don't have any in stock, we shouldn't even consdier displaying, chipotle example
        if result [0][0] == 0:
            return []

        return [
            {
                "sku": "GREEN_POTION_0",
                "name": "green potion",
                "quantity": result[0][0],
                "price": num_green_price,
                "potion_type": [0, 100, 0, 0],
            }
        ]

        # return [
        #         {
        #             "sku": "RED_POTION_0",
        #             "name": "red potion",
        #             "quantity": 1,
        #             "price": 50,
        #             "potion_type": [100, 0, 0, 0],
        #         }
        #     ]
