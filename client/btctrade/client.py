import hashlib
import hmac
import urllib.parse

import requests
import time

from client.base.base_client import BaseClient


btc_trade_url = 'https://api.btctrade.com/api/'

access_key = ''
secret_key = ''


def get_depth(coin='ltc'):
    params = {'coin': coin}
    ret = requests.get(btc_trade_url + 'depth', params=params, timeout=10)
    return ret.json()


def get_ticker(coin='ltc'):
    params = {'coin': coin}
    ret = requests.get(btc_trade_url + 'ticker', params=params, timeout=10)
    return ret.json()


def params_sign(params):
    params['key'] = access_key
    params['nonce'] = int(time.time())
    params['version'] = 2
    _md5key = hashlib.md5(secret_key.encode('utf-8')).hexdigest()
    params = sorted(params.items(), key=lambda d: d[0], reverse=False)
    message = urllib.parse.urlencode(params)
    _hmac = hmac.new(_md5key.encode('utf-8'), message.encode('utf-8'), digestmod='sha256')
    params['signature'] = _hmac.hexdigest()
    return params


class Client(BaseClient):

    def account(self):
        params = params_sign({})
        ret = requests.post(btc_trade_url + 'balance/', json=params)
        ret = ret.json()
        account = {'free': {}, 'asset': {}, 'frozen': {}}
        account['free']['cny'] = ret['cny_balance']
        account['free']['ltc'] = ret['ltc_balance']
        account['free']['btc'] = ret['btc_balance']
        account['asset']['total'] = ret['asset']
        account['frozen']['cny'] = ret['cny_reserved']
        account['frozen']['ltc'] = ret['ltc_reserved']
        account['frozen']['btc'] = ret['btc_reserved']
        return account

    def ltc_depth(self):
        ret = get_depth('ltc')
        ret['asks'] = ret['asks'][::-1]
        return ret

    def ltc_ticker(self):
        ret = get_depth('ltc')
        return ret

    def buy_ltc(self, price, amount):
        """
        :param price: buy price
        :param amount: buy amount
        :return: (True or False, msg)
        """
        pass

    def buy(self, price, amount, coin):
        if coin == 'ltc':
            self.buy_ltc(price, amount)
        elif coin == 'eth':
            # buy eth
            pass

    def sell(self, price, amount, coin):
        if coin == 'ltc':
            self.sell_ltc(price, amount)
        elif coin == 'eth':
            pass

    def sell_ltc(self, price, amount):
        """
        :param price: float, sell price
        :param amount: float, sell amount
        :return: (True or False, msg)
        """
        pass

    def order_info(self, order_id, coin='ltc'):
        pass

    def cancel_order(self, order_id, coin='ltc'):
        pass
