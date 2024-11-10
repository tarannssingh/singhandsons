from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db
import logging
logger = logging.getLogger("uvicorn")
from datetime import datetime

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.post("/reset")
def reset():
    """
    Reset the game state. Gold goes to 100, all potions are removed from
    inventory, and all barrels are removed from inventory. Carts are all reset.
    """
    with db.engine.begin() as connection:
        # reset gold
        logger.info("reset")
        
        # archive and reset tables
        time = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        '''
                           
        '''
        sql_to_execute = f'''
                            CREATE TABLE ztransactions_{time} as SELECT * FROM transactions;
                            CREATE TABLE zgold_ledger_entries_{time} as SELECT * FROM gold_ledger_entries;
                            CREATE TABLE zpotion_ledger_entries_{time} as SELECT * FROM potion_ledger_entries;
                            CREATE TABLE zml_ledger_entries_{time} as SELECT * FROM ml_ledger_entries;
                            CREATE TABLE zcart_{time} as SELECT * FROM cart;
                            TRUNCATE TABLE transactions;
                            TRUNCATE TABLE gold_ledger_entries;
                            TRUNCATE TABLE potion_ledger_entries;
                            TRUNCATE TABLE ml_ledger_entries;
                            TRUNCATE TABLE cart;
                         '''
        connection.execute(sqlalchemy.text(sql_to_execute))
        # make transaction
        sql_to_execute = "INSERT INTO transactions (description) VALUES ('Reset Shop: 100 Gold') RETURNING id"
        transaction_id = connection.execute(sqlalchemy.text(sql_to_execute)).scalar()
        # Insert base gold to ledger
        sql_to_execute = f'INSERT INTO gold_ledger_entries (transaction_id, change) VALUES ({transaction_id}, 100)'
        connection.execute(sqlalchemy.text(sql_to_execute))

        connection.execute(sqlalchemy.text("UPDATE global_inventory SET potion_capacity = 1, ml_capacity = 1"))
        
        # connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = 100, potion_capacity = 1, ml_capacity = 1, num_red_ml = 0, num_green_ml = 0, num_blue_ml = 0, num_dark_ml = 0"))
        # connection.execute(sqlalchemy.text("UPDATE potion_inventory SET num_potions = 0"))    
        
        
        # connection.execute(sqlalchemy.text("UPDATE cart SET num_of_green_potions = 0, num_of_red_potions = 0, num_of_blue_potions = 0"))
        #! Don't want to remove old data as it is good for analytics 
        return "OK"

