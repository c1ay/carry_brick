# coding:utf-8
import time

from client.base.base_client import BaseClient
from client.huobi.HuobiService import (
    get_ticker, get_depth, sell, buy, cancelOrder, getAccountInfo,
    getOrderInfo,
    sellMarket, buyMarket, get_kline)
from client.huobi.huobi_eth_sdk import ApiClient, get_eth_ticker, get_eth_depth

ACCESS_KEY = ""
SECRET_KEY = ""


class Client(BaseClient):

    name = 'huobi'
    huobi_client = ApiClient(ACCESS_KEY, SECRET_KEY)
    accs = huobi_client.get('/v1/account/accounts')
    account_id = accs[0].id

    eth_status_map = {
        "filled": 2,
        "partial-filled": 1,
        "submitted": 0,
        "submitting": 0,
    }

    def old_account(self):
        ret = getAccountInfo()
        account = {'free': {}, 'asset': {}, 'frozen': {}}
        if isinstance(ret, dict):
            account['free']['cny'] = ret['available_cny_display']
            account['free']['ltc'] = ret['available_ltc_display']
            account['free']['btc'] = ret['available_btc_display']
            account['asset']['total'] = ret['total']
            account['frozen']['cny'] = ret['frozen_cny_display']
            account['frozen']['ltc'] = ret['frozen_ltc_display']
            account['frozen']['btc'] = ret['frozen_btc_display']
        return account

    def account(self):
        ret = getAccountInfo()
        account = {'free': {}, 'asset': {}, 'frozen': {}}
        if isinstance(ret, dict):
            account['free']['cny'] = float(ret['available_cny_display'])
            account['free']['ltc'] = ret['available_ltc_display']
            account['free']['btc'] = ret['available_btc_display']
            account['free']['eth'] = 0
            account['free']['etc'] = 0
            account['asset']['total'] = ret['total']
            account['frozen']['cny'] = float(ret['frozen_cny_display'])
            account['frozen']['ltc'] = ret['frozen_ltc_display']
            account['frozen']['btc'] = ret['frozen_btc_display']
            account['frozen']['eth'] = 0
            account['free']['etc'] = 0
        accounts = self.huobi_client.get('/v1/account/accounts')
        for acc in accounts:
            eth_account = self.huobi_client.get('/v1/account/accounts/%s/balance' % acc.id)
            for item in eth_account['list']:
                account_type = item['type'] if item['type'] == 'frozen' else 'free'
                account[account_type][item['currency']] += float(item['balance'])
        return account

    def eth_account(self):
        accounts = self.huobi_client.get('/v1/account/accounts')
        account = {}
        for acc in accounts:
            eth_account = self.huobi_client.get('/v1/account/accounts/%s/balance' % acc.id)
            for item in eth_account['list']:
                account_type = item['type'] if item['type'] == 'frozen' else 'free'
                account[account_type][item['currency']] = float(item['balance'])
        return account

    def get_kline(self, seconds, length, coin):
        return get_kline(seconds, length, coin)

    def ltc_ticker(self):
        ret = get_ticker()
        return ret

    def ticker(self, coin='eth'):
        if coin == 'ltc':
            return self.ltc_depth()
        elif coin == 'eth':
            return get_eth_ticker()
        elif coin == 'btc':
            raise NotImplementedError
        else:
            raise NotImplementedError

    def ltc_depth(self):
        ret = get_depth()
        return ret

    def depth(self, coin='eth'):
        if coin == 'ltc':
            return self.ltc_depth()
        elif coin == 'eth':
            return get_eth_depth()
        elif coin == 'btc':
            raise NotImplementedError
        else:
            raise NotImplementedError

    def sell_ltc(self, price, amount):
        amount = int(amount * 10000) / 10000
        if price:
            price = int(price * 100) / 100
            ret = sell(2, price, amount)
        else:
            ret = sellMarket(2, amount, '', '')
        if ret['result'] == 'success':
            return True, ret['id']
        msg = 'sell ltc failed msg:{}'.format(str(ret))
        return False, msg

    def sell(self, price, amount, coin):
        amount = int(amount * 10000) / 10000
        if price:
            price = int(price * 100) / 100
        if coin == 'eth':
            order_id = self.create_oder(price, amount, 'sell-limit')
            ret = self.place_order(order_id)
            print(ret)
            return True, order_id
        elif coin == 'ltc':
            return self.sell_ltc(price, amount)
        elif coin == 'btc':
            return False, ""
        else:
            return False, ""

    def sell_market(self, amount, coin):
        amount = int(amount * 10000) / 10000
        if coin == 'eth':
            order_id = self.create_oder(None, amount, 'sell-market')
            ret = self.place_order(order_id)
            print(ret)
            return True, order_id
        elif coin == 'ltc':
            return self.sell_ltc(None, amount)
        elif coin == 'btc':
            return False, ""
        else:
            return False, ""

    def buy(self, price, amount, coin='ltc'):
        price = int(price * 100) / 100
        amount = int(amount * 10000) / 10000
        if coin == 'ltc':
            return self.sell_ltc(price, amount)
        elif coin == 'eth':
            order_id = self.create_oder(price, amount, 'buy-limit')
            ret = self.place_order(order_id)
            print(ret)
            return True, order_id
        elif coin == 'btc':
            raise NotImplementedError
        else:
            raise NotImplementedError

    def buy_market(self, amount, coin, price=None):
        amount = int(amount * 10000) / 10000
        if coin == 'ltc':
            return self.buy_ltc(price, amount)
        elif coin == 'eth':
            order_id = self.create_oder(price, amount, 'buy-market')
            ret = self.place_order(order_id)
            print(ret)
            return True, order_id
        elif coin == 'btc':
            raise NotImplementedError
        else:
            raise NotImplementedError

    def buy_ltc(self, price, amount):
        amount = int(amount * 10000) / 10000
        if price:
            price = int(price * 100) / 100
            ret = buy(2, price, amount)
        else:
            ret = buyMarket(2, amount, '', '')
        if ret['result'] == 'success':
            return True, ret['id']
        msg = 'sell ltc failed'
        return False, msg

    def order_info(self, order_id, coin='ltc'):
        """
        :param order_id:  order_id
        :param coin:  coin_type
        :return: {"status": 1, "ret": {}, "complete_volume": 0.1}
                status: order status: 0, not complete, 1, partly complete
                complete_volume: complete volume
        """
        order = {}
        if coin == 'ltc':
            ret = getOrderInfo(2, order_id)
            order['success'] = True if ret['status'] == 2 else False
            order['ret'] = ret
            order['status'] = ret['status']
            order['complete_volume'] = ret['processed_amount']
        elif coin == 'eth':
            ret = self.huobi_client.get('/v1/order/orders/%s' % order_id)
            if ret['state'] == 'filled':
                order['success'] = True
                order['ret'] = ret
            order['complete_volume'] = ret['field-amount']
            order['status'] = self.eth_status_map.get(ret['state'], 0)
        elif coin == 'btc':
            raise NotImplementedError
        else:
            raise NotImplementedError
        return order

    def cancel_order(self, order_id, coin='ltc'):
        if coin == 'ltc':
            ret = cancelOrder(2, order_id)
        elif coin == 'eth':
            ret = self.huobi_client.post('/v1/order/orders/%s/submitcancel' % order_id)
        elif coin == 'btc':
            raise NotImplementedError
        else:
            raise NotImplementedError
        return ret

    def create_oder(self, price, amount, order_type='buy-limit'):
        """
        :param price:
        :param amount: 限价单表示下单数量，市价买单时表示买多少钱，市价卖单时表示卖多少币
        :param order_type:
        :return:
        """
        if order_type == 'buy-market':
            amount = round(amount * price, 2)
        params = {
            'account-id': self.account_id,
            'amount': str(amount),
            'symbol': 'ethcny',
            'type': order_type,
            'source': 'api'
        }
        if order_type not in ('buy-market', 'sell-market'):
            params.update({
                'price': str(price),
            })
            print(params)
        order_id = self.huobi_client.post('/v1/order/orders', params)
        return order_id

    def place_order(self, order_id):
        while True:
            try:
                self.huobi_client.post('/v1/order/orders/%s/place' % order_id)
                break
            except Exception as e:
                print("huobi place order error: ", e)
                time.sleep(0.1)
                continue
