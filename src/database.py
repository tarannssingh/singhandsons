import os
import dotenv
from sqlalchemy import create_engine
import sqlalchemy

def database_connection_url():
    dotenv.load_dotenv()
    return os.environ.get("POSTGRES_URI")

engine = create_engine(database_connection_url(), pool_pre_ping=True)
metadata_obj = sqlalchemy.MetaData()
customers = sqlalchemy.Table("customers", metadata_obj, autoload_with=engine)
potion_inventory = sqlalchemy.Table("potion_inventory", metadata_obj, autoload_with=engine)
cart_item = sqlalchemy.Table("cart_item", metadata_obj, autoload_with=engine)
cart = sqlalchemy.Table("cart", metadata_obj, autoload_with=engine)