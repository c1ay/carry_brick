# coding:utf-8
from client import btc38
from client import huobi
from client import okcoin
from matrix.crawl_price import CrawlPrice


def test_matrix():
    listen_client = (
        huobi.Client(),  # huobi 客户端
        okcoin.Client(),  # okcoin 客户端
        # btc38.Client(),  # btc38 客户端
    )
    c = CrawlPrice(listen_client, 'eth', 'huobi-okcoin')
    ret = c.crawl()
    print(ret)
    c.save(ret)


if __name__ == '__main__':
    test_matrix()
