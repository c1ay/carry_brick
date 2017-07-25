# coding: utf-8
from client.base.base_client import BaseClient
from client.okcoin.api.OkcoinSpotAPI import OKCoinSpot


API_KEY = ''
SECRET_KEY = ''
OKCOIN_URL = 'https://www.okcoin.cn'   #请求注意：国内账号需要 修改为 www.okcoin.cn


class Client(BaseClient):

    name = 'okcoin'

    def __init__(self):
        super().__init__()
        self.okcoin_client = OKCoinSpot(OKCOIN_URL, API_KEY, SECRET_KEY)

    def account(self):
        ret = self.okcoin_client.userinfo()
        account = {'free': {}, 'asset': {}, 'frozen': {}}
        # free: 账户资产
        # asset:账户现有资产，人民币单位
        # freezed: 冻结资产
        if ret['result']:
            account['free'].update(ret['info']['funds']['free'])
            account['asset'].update(ret['info']['funds']['asset'])
            account['frozen'].update(ret['info']['funds']['freezed'])
        return account

    def ltc_ticker(self):
        ret = self.okcoin_client.ticker('ltc_cny')
        return ret

    def ticker(self, coin='eth'):
        return self.okcoin_client.ticker('{}_cny'.format(coin))

    def ltc_depth(self):
        ret = self.okcoin_client.depth('ltc_cny')
        ret['asks'] = ret['asks'][::-1]
        return ret

    def depth(self, coin='eth'):
        ret = self.okcoin_client.depth('{}_cny'.format(coin))
        ret['asks'] = ret['asks'][::-1]
        return ret

    def sell_ltc(self, price, amount):
        price = int(price * 100) / 100
        amount = int(amount * 10000) / 10000
        ret = self.okcoin_client.trade('ltc_cny', 'sell', price, amount)
        if ret['result']:
            order_id = ret['order_id']
            return True, order_id
        msg = 'sell ltc failed: {}'.format(str(ret))
        return False, msg

    def sell(self, price, amount, coin='eth'):
        amount = int(amount * 10000) / 10000
        if price:
            price = int(price * 100) / 100
            ret = self.okcoin_client.trade('{}_cny'.format(coin), 'sell', price, amount)
        else:
            ret = self.okcoin_client.trade('{}_cny'.format(coin), 'sell_market', '', amount)
        if ret['result']:
            order_id = ret['order_id']
            return True, order_id
        msg = 'sell {} failed: {}'.format(coin, str(ret))
        return False, msg

    def sell_market(self, amount, coin, price=None):
        return self.sell(None, amount, coin)

    def buy_ltc(self, price, amount):
        price = int(price * 100) / 100
        amount = int(amount * 10000) / 10000
        ret = self.okcoin_client.trade('ltc_cny', 'buy', price, amount)
        if ret['result']:
            order_id = ret['order_id']
            return True, order_id
        msg = 'buy ltc failed'
        return False, msg

    def buy(self, price, amount, coin='eth'):
        amount = int(amount * 10000) / 10000
        price = int(price * 100) / 100
        ret = self.okcoin_client.trade('{}_cny'.format(coin), 'buy', price, amount)
        if ret['result']:
            order_id = ret['order_id']
            return True, order_id
        msg = 'buy {} failed: {}'.format(coin, str(ret))
        return False, msg

    def buy_market(self, amount, coin, price=None):
        amount = int(amount * 10000) / 10000
        price = int(price * 100) / 100
        ret = self.okcoin_client.trade('{}_cny'.format(coin), 'buy_market', price * amount)
        if ret['result']:
            order_id = ret['order_id']
            return True, order_id
        msg = 'buy {} failed: {}'.format(coin, str(ret))
        return False, msg

    def order_info(self, order_id, coin='ltc'):
        """
        get okcoin order info
        :param order_id: order_id
        :param coin: coin type
        :return: {"status": 0, "ret": {}, "complete_amount": 0.11}
                 status: order status, ret: okcoin origin ret
                 complete_volume: complete volume
        """
        okcoin_status_map = {
            self.trade_complete: self.trade_complete,
            self.trade_not_complete: self.trade_not_complete,
            self.trade_partly_complete: self.trade_partly_complete
        }
        order = {}
        ret = self.okcoin_client.orderinfo('{}_cny'.format(coin), order_id)
        order['success'] = True if ret['orders'][0]['status'] == 2 else False
        order['status'] = okcoin_status_map.get(ret['orders'][0]['status'], self.trade_not_complete)
        order['complete_volume'] = ret['orders'][0]['deal_amount']
        order['ret'] = ret
        return order

    def cancel_order(self, order_id, coin='ltc'):
        ret = self.okcoin_client.cancelOrder('{}_cny'.format(coin), order_id)
        return ret

