#coding=utf-8
import sys

import time

sys.path.append('..')

from client.huobi import client as huobi_client


def test_ltc():
    client = huobi_client.Client()
    # print(client.account())
    print(client.ltc_ticker())
    depth = client.ltc_depth()
    print('卖方')
    print(depth['asks'][:10])
    print('买方')
    print(depth['bids'][:10])
    # print('卖')
    # _, order_id = client.sell_ltc(999.0, 0.1)
    # print(order_id)
    # # time.sleep(5)
    # print(client.order_info(order_id))
    # print(client.cancel_order(order_id))
    # _, order_id = client.buy_ltc(1, 0.1)
    # print(client.order_info(order_id))
    # print(client.cancel_order(order_id))


def test_eth():
    client = huobi_client.Client()

    print(client.account())
    print(client.ticker(coin='eth'))
    ret = client.depth(coin='eth')
    print(ret['asks'])
    print(ret['bids'])
    # ret = client.buy(1, 0.01, 'eth')
    # print(ret)


def test_eth_market():
    client = huobi_client.Client()
    client.buy_market(0.01, 'eth')
    client.sell_market(0.01, 'eth')

if __name__ == '__main__':
    # test_ltc()
    # test_eth()
    test_eth_market()
