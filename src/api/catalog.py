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
        sql_to_execute = "SELECT num_green_potions, gold FROM global_inventory"
        result = connection.execute(sqlalchemy.text(sql_to_execute))

        print(result)
        return [
             {
                "sku": "GREEN_POTION_0",
                "name": "green potion",
                "quantity": result,
                "price": result,
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
