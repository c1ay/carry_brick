# coding: utf-8
import time
from datetime import datetime

from pony.orm import commit, db_session

from matrix.db import Price, PriceDiff


class CrawlPrice:

    def __init__(self, listen_client, listen_coin, coin_diff):
        """
        :param listen_client: except list of client.Client object
        :param listen_coin: listen coin
        """
        self.listen_client = listen_client
        self.listen_coin = listen_coin
        self.coin_a, self.coin_b = coin_diff.split('-')

    def crawl(self):
        rets = []
        for client in self.listen_client:
            ret = client.depth(self.listen_coin)
            ret['name'] = client.name
            rets.append(ret)
        return rets

    @db_session
    def save(self, rets):
        coin_a_price, coin_b_price = None, None
        for item in rets:
            if item['name'] == self.coin_a:
                coin_a_price = item
            elif item['name'] == self.coin_b:
                coin_b_price = item
            Price(
                coin=self.listen_coin, sell_price=str(item['asks'][0][0]), sell_amount=str(item['asks'][0][1]),
                buy_price=str(item['bids'][0][0]), buy_amount=str(item['bids'][0][1]), create_time=datetime.now()
                  )
        if coin_a_price and coin_b_price:
            if coin_a_price['asks'][0][0] > coin_b_price['bids'][0][0]:
                diff = coin_a_price['asks'][0][0] - coin_b_price['bids'][0][0]
                amount = min(coin_a_price['asks'][0][1], coin_b_price['bids'][0][1])
            elif coin_a_price['bids'][0][0] < coin_b_price['asks'][0][0]:
                diff = coin_a_price['bids'][0][0] - coin_b_price['asks'][0][0]
                amount = min(coin_a_price['bids'][0][1], coin_b_price['asks'][0][1])
            PriceDiff(
                create_time=datetime.now(), diff=str(diff), coin_diff="{}-{}".format(self.coin_a, self.coin_b),
                amount=str(amount), coin=self.listen_coin,
            )

    def go(self):
        while True:
            time.sleep(1)
            try:
                ret = self.crawl()
            except Exception as e:
                print(e)
                continue
            self.save(ret)
