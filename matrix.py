# coding: utf-8
from client import huobi
from client import okcoin
from matrix.crawl_price import CrawlPrice

if __name__ == '__main__':
    listen_client = (
        huobi.Client(),  # huobi 客户端
        okcoin.Client(),  # okcoin 客户端
        # btc38.Client(),  # btc38 客户端
    )
    c = CrawlPrice(listen_client, 'eth', 'huobi-okcoin')
    c.go()
