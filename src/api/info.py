from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
from src import database as db
import sqlalchemy

# import logging
# logger = logging.getLogger("uvicorn")


router = APIRouter(
    prefix="/info",
    tags=["info"],
    dependencies=[Depends(auth.get_api_key)],
)

class Timestamp(BaseModel):
    day: str
    hour: int

@router.post("/current_time")
def post_time(timestamp: Timestamp):
    """
    Share current time.
    """
    with db.engine.begin() as connection:
        values = {"day": timestamp.day, "time": timestamp.hour}
        sql_to_execute = 'UPDATE global_inventory SET day = :day, time = :time'
        connection.execute(sqlalchemy.text(sql_to_execute), values)
    # logger.log(f"{timestamp.day} {timestamp.hour}")

    return "OK"

