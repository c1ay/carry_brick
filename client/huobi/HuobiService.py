#coding=utf-8
import requests

from client.huobi.Util import send2api

ACCOUNT_INFO = "get_account_info"
GET_ORDERS = "get_orders"
ORDER_INFO = "order_info"
BUY = "buy"
BUY_MARKET = "buy_market"
CANCEL_ORDER = "cancel_order"
NEW_DEAL_ORDERS = "get_new_deal_orders"
ORDER_ID_BY_TRADE_ID = "get_order_id_by_trade_id"
SELL = "sell"
SELL_MARKET = "sell_market"


'''
获取账号详情
'''
def getAccountInfo():
    params = {"method":ACCOUNT_INFO}
    extra = {}
    res = send2api(params, extra)
    return res


'''
获取所有正在进行的委托
'''
def getOrders(coinType):
    params = {"method":GET_ORDERS}
    params['coin_type'] = coinType
    extra = {}
    res = send2api(params, extra)
    return res
'''
获取订单详情
@param coinType
@param id
'''
def getOrderInfo(coinType, id):
    params = {"method": ORDER_INFO}
    params['coin_type'] = coinType
    params['id'] = id
    extra = {}
    res = send2api(params, extra)
    return res

'''
限价买入
@param coinType
@param price
@param amount
@param tradePassword
@param tradeid
@param method
'''
def buy(coinType,price,amount,tradePassword='',tradeid=''):
    params = {"method": BUY}
    params['coin_type'] = coinType
    params['price'] = price
    params['amount'] = amount
    extra = {}
    extra['trade_password'] = tradePassword
    # extra['trade_id'] = tradeid
    res = send2api(params, extra)
    return res

'''
限价卖出
@param coinType
@param price
@param amount
@param tradePassword
@param tradeid
'''
def sell(coinType,price,amount,tradePassword='',tradeid=''):
    params = {"method": SELL}
    params['coin_type'] = coinType
    params['price'] = price
    params['amount'] = amount
    extra = {}
    extra['trade_password'] = tradePassword
    # extra['trade_id'] = tradeid
    res = send2api(params, extra)
    return res


'''
市价买
@param coinType
@param amount
@param tradePassword
@param tradeid
'''

def buyMarket(coinType,amount,tradePassword,tradeid):
    params = {"method": BUY_MARKET}
    params['coin_type'] = coinType
    params['amount'] = amount
    extra = {}
    extra['trade_password'] = tradePassword
    extra['trade_id'] = tradeid
    res = send2api(params, extra)
    return res

'''
市价卖出
@param coinType
@param amount
@param tradePassword
@param tradeid
'''
def sellMarket(coinType,amount,tradePassword,tradeid):
    params = {"method": SELL_MARKET}
    params['coin_type'] = coinType
    params['amount'] = amount
    extra = {}
    extra['trade_password'] = tradePassword
    extra['trade_id'] = tradeid
    res = send2api(params, extra)
    return res

'''
查询个人最新10条成交订单
@param coinType
'''
def getNewDealOrders(coinType):
    params = {"method": NEW_DEAL_ORDERS}
    params['coin_type'] = coinType
    extra = {}
    res = send2api(params, extra)
    return res
'''
根据trade_id查询oder_id
@param coinType
@param tradeid
'''
def getOrderIdByTradeId(coinType,tradeid):
    params = {"method": ORDER_ID_BY_TRADE_ID}
    params['coin_type'] = coinType
    params['trade_id'] = tradeid
    extra = {}
    res = send2api(params, extra)
    return res


'''
撤销订单
@param coinType
@param id
'''

def cancelOrder(coinType,id):
    params = {"method": CANCEL_ORDER}
    params['coin_type'] = coinType
    params['id'] = id
    extra = {}
    res = send2api(params, extra)
    return res


def get_ticker(symbol='ltc'):
    ret = requests.get('http://api.huobi.com/staticmarket/ticker_{}_json.js'.format(symbol), timeout=5)
    return ret.json()


def get_depth(symbol='ltc'):
    ret = requests.get('http://api.huobi.com/staticmarket/depth_{}_json.js'.format(symbol), timeout=5)
    return ret.json()


def get_kline(period=180, length=300, coin='eth'):
    """
    period 参数	说明
001	1分钟线
005	5分钟
015	15分钟
030	30分钟
060	60分钟
100	日线
200	周线
300	月线
400	年线
    :param period:
    :param length:
    :param coin:
    :return:
    """
    period = "{:0>3d}".format(int(period / 60))
    ret = requests.get("http://api.huobi.com/staticmarket/{}_kline_{}_json.js?length={}".format(coin, period, length))
    return ret.json()
