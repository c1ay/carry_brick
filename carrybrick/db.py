# coding: utf-8
from datetime import datetime

from pony.orm import Database, Required

db = Database()
db.bind('sqlite', 'carry_brick.db', create_db=True)


class TradeRecord(db.Entity):

    create_time = Required(datetime)
    before_cny = Required(str, 20)
    before_ltc = Required(str, 20)
    before_btc = Required(str, 20)
    current_cny = Required(str, 20)
    current_ltc = Required(str, 20)
    current_btc = Required(str, 20)
    profit = Required(str, 20)
    except_profit = Required(str, 20)
    sell_price = Required(str, 20)
    sell_count = Required(str, 20)
    sell_coin = Required(str, 20)
    sell_platform = Required(str, 20)
    buy_price = Required(str, 20)
    buy_count = Required(str, 20)
    buy_coin = Required(str, 20)
    buy_platform = Required(str, 20)


class Record(db.Entity):

    create_time = Required(datetime)
    before_cny = Required(str, 20)
    cny = Required(str, 20)
    coin = Required(str, 16)
    current_volume = Required(str, 20)
    sell_platform = Required(str, 10)
    sell_price = Required(str, 20)
    sell_amount = Required(str, 20)
    buy_platform = Required(str, 10)
    buy_price = Required(str, 20)
    buy_amount = Required(str, 20)


db.generate_mapping(create_tables=True)
