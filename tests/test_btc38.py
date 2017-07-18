# coding: utf-8
from client.btc38 import Client


def test_btc38():
    client = Client()
    ret = client.account()
    print('account')
    print(ret)
    ret = client.ticker('ltc')
    print(ret)
    ret = client.depth('ltc')
    print("bids", ret['bids'])
    print("asks", ret['asks'])
    ret = client.buy(1, 1, 'ltc')
    print(ret)
    order_id = ret[1]
    ret = client.order_info(order_id, 'ltc')
    print(ret)
    ret = client.cancel_order(order_id, 'ltc')
    print(ret)


if __name__ == '__main__':
    test_btc38()
