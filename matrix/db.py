# coding: utf-8
from datetime import datetime

from pony.orm import Database, Required

db = Database()
db.bind('sqlite', 'matrix.db', create_db=True)


class Price(db.Entity):

    coin = Required(str, 20)
    buy_price = Required(str, 20)
    buy_amount = Required(str, 20)
    sell_price = Required(str, 20)
    sell_amount = Required(str, 20)
    create_time = Required(datetime)


class PriceDiff(db.Entity):

    coin = Required(str, 20)
    diff = Required(str, 20)
    create_time = Required(datetime)
    coin_diff = Required(str, 20)
    amount = Required(str, 20)

db.generate_mapping(create_tables=True)
