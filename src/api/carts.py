from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
from enum import Enum
import sqlalchemy
from src import database as db
import logging
logger = logging.getLogger("uvicorn")

router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)

class search_sort_options(str, Enum):
    customer_name = "customer_name"
    item_sku = "item_sku"
    line_item_total = "line_item_total"
    timestamp = "timestamp"

class search_sort_order(str, Enum):
    asc = "asc"
    desc = "desc"   

@router.get("/search/", tags=["search"])
def search_orders(
    customer_name: str = "",
    potion_sku: str = "",
    search_page: str = "",
    sort_col: search_sort_options = search_sort_options.timestamp,
    sort_order: search_sort_order = search_sort_order.desc,
):
    """
    Search for cart line items by customer name and/or potion sku.

    Customer name and potion sku filter to orders that contain the 
    string (case insensitive). If the filters aren't provided, no
    filtering occurs on the respective search term.

    Search page is a cursor for pagination. The response to this
    search endpoint will return previous or next if there is a
    previous or next page of results available. The token passed
    in that search response can be passed in the next search request
    as search page to get that page of results.

    Sort col is which column to sort by and sort order is the direction
    of the search. They default to searching by timestamp of the order
    in descending order.

    The response itself contains a previous and next page token (if
    such pages exist) and the results as an array of line items. Each
    line item contains the line item id (must be unique), item sku, 
    customer name, line item total (in gold), and timestamp of the order.
    Your results must be paginated, the max results you can return at any
    time is 5 total line items.
    """

    return {
        "previous": "",
        "next": "",
        "results": [
            {
                "line_item_id": 1,
                "item_sku": "1 oblivion potion",
                "customer_name": "Scaramouche",
                "line_item_total": 50,
                "timestamp": "2021-01-01T00:00:00Z",
            }
        ],
    }


class Customer(BaseModel):
    customer_name: str
    character_class: str
    level: int

@router.post("/visits/{visit_id}")
def post_visits(visit_id: int, customers: list[Customer]):
    """
    Which customers visited the shop today?
    """

    logger.info(customers)

    return "OK"


@router.post("/")
def create_cart(new_cart: Customer):
    """ """
    with db.engine.begin() as connection:
        # create cart
        num_green_price = connection.execute(sqlalchemy.text("INSERT INTO cart (num_of_green_potions) VALUES (0)"))
        cart_id  = connection.execute(sqlalchemy.text("SELECT id FROM cart ORDER BY id DESC")).scalar()
        logger.info(f"new cart {cart_id}")
        return {"cart_id": cart_id} 
    
    return {"cart_id": 1} # default 


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(f"UPDATE cart SET num_of_green_potions = {cart_item.quantity} WHERE id = {cart_id}"))
        logger.info(f"cart {cart_id} added {cart_item.quantity} green potions")
        return "OK"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """
    # Make specfic logic for the cart
    logger.info(f"{CartCheckout.payment}")
    with db.engine.begin() as connection:
        # fetch the price of green potions
        num_green_price = connection.execute(sqlalchemy.text("SELECT num_green_price FROM global_inventory")).scalar()
        # get the quantity of the green potions this person wants to buy
        quantity  = connection.execute(sqlalchemy.text(f"SELECT num_of_green_potions FROM cart WHERE id = {cart_id}")).scalar()
        # add the amount of gold recieved to my global inventory
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold = gold + {num_green_price * quantity}"))
        logger.info(f"total_potions_bought: {quantity}, total_gold_paid: {num_green_price * quantity}")
        return {"total_potions_bought": quantity, "total_gold_paid": num_green_price * quantity}
    