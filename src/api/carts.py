from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
from enum import Enum
import sqlalchemy
from sqlalchemy.orm import aliased
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
    metadata_obj = db.metadata_obj
    customers = db.customers
    potion_inventory = db.potion_inventory
    cart_item = db.cart_item
    cart = db.cart

    with db.engine.begin() as connection:
        limit = 5
        if search_page == "":
            offset = 0
        else:
            offset = int(search_page) * limit

        # metrics to sort by 
        if sort_col is search_sort_options.customer_name:
            order_by = customers.c.customer
        elif sort_col is search_sort_options.item_sku:
            order_by = potion_inventory.c.sku
        elif sort_col is search_sort_options.line_item_total:
            order_by = cart_item.c.quantity * potion_inventory.c.num_price
        elif sort_col is search_sort_options.timestamp:
            order_by = cart_item.c.created_at
        else:
            assert False
        if (sort_order == search_sort_order.asc):
            order_by = order_by.asc()
        else: 
            order_by = order_by.desc()

            # SELECT cart_item.cart_id, cart_item.created_at, customers.customer, potion_inventory.name, potion_inventory.num_price, cart_item.quantity FROM cart_item                                       
            # JOIN cart ON cart.id = cart_item.cart_id 
            # JOIN customers ON cart.customer_id = customers.id  
            # JOIN potion_inventory ON cart_item.bottle_id = potion_inventory.id
            # WHERE cart.is_checkout = 1
            # LIMIT 5
            # OFFSET 0

        stmt = (
            sqlalchemy.select (
                cart_item.c.cart_id.label("cart_id"),
                cart_item.c.id.label("line_item_id"),
                cart_item.c.created_at.label("timestamp"),
                customers.c.customer.label("customer_name"),
                potion_inventory.c.sku.label("potion_sku"),
                potion_inventory.c.name.label("potion_name"),
                potion_inventory.c.num_price.label("potion_price"),
                cart_item.c.quantity.label("quantity")
            )
            .select_from(cart_item)
            .join(cart, cart.c.id == cart_item.c.cart_id)
            .join(customers, customers.c.id == cart.c.customer_id)
            .join(potion_inventory, potion_inventory.c.id == cart_item.c.bottle_id)
            .where(cart.c.is_checkout == 1)
            .limit(limit)
            .offset(offset)
            .order_by(order_by)
        )            

            

        
        if customer_name != "":
            stmt = stmt.where(customers.c.customer.ilike(f"%{customer_name}%"))
        if potion_sku != "":
            stmt = stmt.where(potion_inventory.c.sku.ilike(f"%{potion_sku}%"))
    
        result = connection.execute(stmt)
        json = []
        for row in result:
            json.append (
                {
                    "line_item_id": row.line_item_id,
                    "item_sku": f"{row.quantity} {row.potion_name}",
                    "customer_name": f"{row.customer_name}",
                    "line_item_total": int(row.quantity) * int(row.potion_price),
                    "timestamp": f"{row.timestamp}"
                }
            )

        if search_page != "":
            p = int(search_page) - 1
            if p < 0:
                p = ""
        else: 
            p = ""
        if len(json) < 5:
            n = ""
        else: 
            n = 1
            if search_page != "":
                n = int(search_page) + 1
        return {
            "previous": f"{p}",
            "next": f"{n}",
            "results": json,
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
    with db.engine.begin() as connection:
        for customer in customers:
            values = {"customer": customer.customer_name, "character_class": customer.character_class, "level": customer.level}
            sql_to_execute = "INSERT INTO customers (customer, character_class, level) VALUES (:customer, :character_class, :level) ON CONFLICT DO NOTHING"
            connection.execute(sqlalchemy.text(sql_to_execute), values)
        logger.info(customers)
    return "OK"

@router.post("/")
def create_cart(new_cart: Customer):
    """ """
    with db.engine.begin() as connection:
        # get customer id
        values = {"customer": new_cart.customer_name, "character_class": new_cart.character_class, "level": new_cart.level}
        sql_to_execute = "INSERT INTO customers (customer, character_class, level) VALUES (:customer, :character_class, :level) ON CONFLICT DO NOTHING"
        connection.execute(sqlalchemy.text(sql_to_execute), values)
        sql_to_execute = "SELECT id FROM customers WHERE customer = :customer AND character_class = :character_class AND level = ':level'"
        customer_id = connection.execute(sqlalchemy.text(sql_to_execute), values).scalar()

        # create cart
        values = {"customer_id": customer_id}
        cart_id = connection.execute(sqlalchemy.text("INSERT INTO cart (customer_id) VALUES (:customer_id) RETURNING id"), values).scalar()
        # connection.execute(sqlalchemy.text("SELECT id FROM cart ORDER BY id DESC")).scalar()
        logger.info(f"new cart {cart_id} for customer {customer_id}")
        return {"cart_id": cart_id} 
    
    # return {"cart_id": 1} # default 


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """
    with db.engine.begin() as connection:
        # here I am going to see create a new entry 
        # get the the id of the sku
        logger.info(f"cart {cart_id} added {cart_item.quantity} {item_sku} potions")
        potion_id = connection.execute(sqlalchemy.text(f"SELECT id FROM potion_inventory WHERE sku = :item_sku"), {"item_sku": item_sku}).scalar()
        connection.execute(sqlalchemy.text(f'''
                                           INSERT INTO cart_item (cart_id, bottle_id, quantity) 
                                           VALUES (:cart_id, :potion_id, :cart_item_quantity) 
                                           ON CONFLICT (cart_id, bottle_id) DO UPDATE SET quantity = :cart_item_quantity;
                                           '''), {"cart_id" : cart_id, "potion_id" : potion_id, "cart_item_quantity": cart_item.quantity})
        # connection.execute(sqlalchemy.text(f"UPDATE cart SET num_of_green_potions = {cart_item.quantity} WHERE id = {cart_id}"))
        return "OK"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """
    # Make specfic logic for the cart
    logger.info(f"{cart_checkout.payment}")
    with db.engine.begin() as connection:
        # fetch the price of green potions
        # join with the potion table on id
        potions = connection.execute(sqlalchemy.text(f"SELECT bottle_id, quantity, num_price, cart_id FROM cart_item INNER JOIN potion_inventory ON cart_item.bottle_id = potion_inventory.id WHERE cart_id = {cart_id}")).fetchall()
        num_of_potions = 0
        total_cost = 0 
        for potion in potions:
            # compute amount ordered
            potion_id = potion[0]
            quantity = potion[1]
            num_price = potion[2]
            total_cost += num_price * quantity
            num_of_potions += quantity
            # transaction ledger 
            description = f"Checkout: {quantity} of Potion ID {potion_id} at {num_price} gold"
            transaction_id = connection.execute(sqlalchemy.text("INSERT INTO transactions (description) VALUES (:description) RETURNING id"), {"description": description}).scalar()
            # potion ledger
            values = {"transaction_id": transaction_id, "potion_id": potion_id, "change": -quantity}
            connection.execute(sqlalchemy.text("INSERT INTO potion_ledger_entries (transaction_id, potion_id, change) VALUES (:transaction_id, :potion_id, :change)"), values)
            # gold ledger 
            values = {"transaction_id": transaction_id, "change": num_price * quantity}
            sql_to_execute = "INSERT INTO gold_ledger_entries (transaction_id, change) VALUES (:transaction_id, :change)"
            connection.execute(sqlalchemy.text(sql_to_execute), values)
            # mark cart as checked out
        values = {"id": cart_id}
        sql_to_execute = "UPDATE cart SET is_checkout = 1 WHERE id = :id"
        connection.execute(sqlalchemy.text(sql_to_execute), values)
        
        # connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold = gold + {total_cost}"))
        logger.info(f"{cart_id}")
        logger.info(f"total_potions_bought: {num_of_potions}, total_gold_paid: {total_cost}")
        return {"total_potions_bought": num_of_potions, "total_gold_paid": total_cost}

        # get the quantity of the green potions this person wants to buy
        # quantity  = connection.execute(sqlalchemy.text(f"SELECT num_of_green_potions FROM cart WHERE id = {cart_id}")).scalar()
        # add the amount of gold recieved to my global inventory
        # connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_potions = num_green_potions - {quantity}"))
        # return {"total_potions_bought": quantity, "total_gold_paid": num_green_price * quantity}
     