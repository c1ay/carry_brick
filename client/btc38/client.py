# coding: utf-8
from client.base.base_client import BaseClient
from client.btc38.util import Client as BtcCli


access_key = ''
secret_key = ''
uid = ''


class Client(BaseClient):

    name = 'btc38'
    btc38_cli = BtcCli(access_key, secret_key, uid)

    def account(self):
        account = {'free': {'btc': 0, 'eth': 0}, 'asset': {'total': 0}, 'frozen': {'btc': 0, 'eth': 0}, 'imma': {}}
        ret = self.btc38_cli.getMyBalance()
        for k, v in ret.items():
            if 'lock' in k:
                account['frozen'][k[:3]] = v
            elif 'imma' in k:
                account['imma'][k[:3]] = v
            else:
                account['free'][k[:3]] = v
        return account

    def ticker(self, coin):
        if coin == 'ltc':
            ret = self.btc38_cli.getTickers('cny', coin)
        else:
            raise NotImplementedError
        return ret

    def depth(self, coin):
        if coin == 'ltc':
            ret = self.btc38_cli.getDepth(c=coin)
        else:
            raise NotImplemented
        return ret

    def buy(self, price, amount, coin):
        if coin == 'ltc':
            ret = self.btc38_cli.submitOrder(1, 'cny', price, amount, coin)
            order_ret = ret[0].decode()
            if 'succ' in order_ret:
                order_info = order_ret.split("|")
                # 成交成功不会有order_id
                order_id = None
                if len(order_info) == 2:
                    order_id = order_info[1]
                return True, order_id
            else:
                return False, order_ret
        else:
            raise NotImplementedError

    def sell(self, price, amount, coin):
        if coin == 'ltc':
            ret = self.btc38_cli.submitOrder(2, 'cny', price, amount, coin)
            order_ret = ret[0].decode()
            if 'succ' in order_ret:
                order_info = order_ret.split("|")
                # 成交成功不会有order_id
                order_id = None
                if len(order_info) == 2:
                    order_id = order_info[1]
                return True, order_id
            else:
                return False, order_ret
        else:
            raise NotImplementedError

    def order_info(self, order_id, coin):
        info = {}
        if coin == 'ltc':
            # get order info
            ret = self.btc38_cli.getOrderList(coin)
            for item in ret:
                if item['id'] == order_id:
                    info['status'] = self.trade_not_complete
                    break
            else:
                info['status'] = self.trade_complete
        else:
            raise NotImplementedError
        return info

    def cancel_order(self, order_id, coin):
        if coin == 'ltc':
            ret = self.btc38_cli.cancelOrder('cny', order_id, coin)
            order_info = ret[0].decode()
            if 'succ' in order_info:
                return True
            else:
                return False
        else:
            raise NotImplemented
