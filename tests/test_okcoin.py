# coding: utf-8
import time
import sys
sys.path.append('..')
from client.okcoin import client as okcoin_client


def test_ltc():
    client = okcoin_client.Client()
    # print(client.account())
    print(client.ltc_ticker())
    depth = client.ltc_depth()
    print('卖方')
    print(depth['asks'][:10])
    print('买方')
    print(depth['bids'][:10])
    print("卖")
    # _, order_id = client.sell_ltc(999.0, 0.1)
    # print(order_id)
    # info = client.order_info(order_id)
    # print('info:', info)
    # # time.sleep(5)
    # print(client.cancel_order(order_id))
    # _, order_id = client.buy_ltc(1, 0.1)
    # # time.sleep(5)
    # print(order_id)
    # print(client.cancel_order(order_id))


def test_eth():
    client = okcoin_client.Client()
    print(client.ticker('eth'))
    ret = client.depth('eth')
    print(ret['asks'][:10])
    print(ret['bids'][:10])

if __name__ == '__main__':
    test_eth()
