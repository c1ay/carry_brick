# coding: utf-8
import time

from client.huobi import Client as hb_client
from client.okcoin import Client as ok_client

huobi_high = 0
okcoin_high = 0


def test_eth():
    hb = hb_client()
    ok = ok_client()
    global huobi_high
    global okcoin_high
    change = {"high": 'huobi', 'change': 0}
    while True:
        time.sleep(1)
        hb_ret = hb.depth('eth')
        ok_ret = ok.depth('eth')
        if float(hb_ret['asks'][0][0]) > float(ok_ret['bids'][0][0]):
            diff = float(hb_ret['asks'][0][0]) - float(ok_ret['bids'][0][0])
            if change['high'] != 'huobi':
                print("huobi: ", hb_ret['bids'][0][0], 'ok_ret: ', ok_ret['bids'][0][0])
                print("火币卖价比okcoin买价高", diff)
                change['high'] = 'huobi'
                change['change'] += 1
        elif float(hb_ret['bids'][0][0]) < float(ok_ret['asks'][0][0]):
            okcoin_high += 1
            diff = - float(hb_ret['asks'][0][0]) + float(ok_ret['bids'][0][0])
            if change['high'] != 'okcoin':
                print("huobi: ", hb_ret['bids'][0][0], 'ok_ret: ', ok_ret['bids'][0][0])
                print("火币买价比okcoin卖家价低", diff)
                change['high'] = 'okcoin'
                change['change'] += 1
        else:
            continue
        print(change)


if __name__ == '__main__':
    test_eth()
