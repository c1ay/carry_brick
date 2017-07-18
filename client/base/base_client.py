# coding: utf-8


class BaseClient:
    timeout = 0.3
    trade_not_complete = 0
    trade_partly_complete = 1
    trade_complete = 2

    def ticker(self, coin):
        raise NotImplementedError

    def depth(self, coin):
        raise NotImplementedError

    def trades(self):
        raise NotImplementedError

    def account(self):
        raise NotImplementedError

    def sell(self, price, amount, coin):
        raise NotImplementedError

    def buy(self, price, amount, coin):
        raise NotImplementedError

    def order_info(self, order_id, coin):
        raise NotImplementedError

    def cancel_order(self, order_id, coin):
        raise NotImplementedError
