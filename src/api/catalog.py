import sqlalchemy
from src import database as db

import logging
logger = logging.getLogger("uvicorn")

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

        # result = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory;")).fetchall()
        # num_green_price  = connection.execute(sqlalchemy.text("SELECT num_green_price FROM global_inventory;")).scalar()

        potions = connection.execute(sqlalchemy.text("SELECT sku, red, green, blue, dark, name, num_potions, num_price FROM potion_catalog WHERE num_potions != 0;")).fetchall()
        
        logging.info("someone opened the catalog")
        # if we don't have any in stock, we shouldn't even consdier displaying, chipotle example
        catalog = []
        for potion in potions:
            catalog.append(
                 {
                    "sku": potion[0],
                    "name": potion[5],
                    "quantity": potion[6],
                    "price": potion[7],
                    "potion_type": [potion[1], potion[2], potion[3], potion[4]],
                }
            )
        logging.info(f"{catalog}")
        return catalog

        # return [
        #         {
        #             "sku": "RED_POTION_0",
        #             "name": "red potion",
        #             "quantity": 1,
        #             "price": 50,
        #             "potion_type": [100, 0, 0, 0],
        #         }
        #     ]
