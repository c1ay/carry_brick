# coding: utf-8
from datetime import datetime, date, timedelta

from pony.orm import db_session

from carrybrick.db import TradeRecord
from carrybrick.log import email_logger, send_email

notify_clock = 22
start_date = date.today()


@db_session
def profit_notify_everyday():
    global start_date
    # return
    if datetime.now().hour != notify_clock:
        return
    if start_date != date.today():
        return
    now = datetime.now()
    start = datetime(now.year, now.month, now.day - 1, notify_clock)
    end = start + timedelta(days=1)
    subject = "数字货币搬砖{} - {}收益".format(start.strftime("%Y-%m-%d %H:%M:%S"), end.strftime("%Y-%m-%d %H:%M:%S"))
    trades = list(TradeRecord.select(
        lambda t: start <= t.create_time and t.create_time< end).order_by(TradeRecord.create_time))
    trades_count = len(trades)
    profit = float(trades[-1].current_cny) - float(trades[0].current_cny)
    msg = '{}次交易， cny: {} -> {}, ltc: {} -> {}, 收益: {}'.format(
        trades_count, round(float(trades[0].current_cny), 2), round(float(trades[-1].current_cny), 2),
        round(float(trades[0].current_ltc), 4), round(float(trades[-1].current_ltc), 4), round(profit, 2)
    )
    send_email(subject, msg)
    start_date += timedelta(days=1)
