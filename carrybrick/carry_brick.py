# coding: utf-8
import time
from datetime import datetime

from pony.orm import db_session, commit

from carrybrick.db import TradeRecord
from carrybrick.log import get_logger
from carrybrick.notify import profit_notify_everyday
from client import huobi, okcoin

fee = 0.0022
depth_limit = 0.3


class CarryBrick:
    listen_client = (
        huobi.Client(),          # huobi 客户端
        okcoin.Client(),         # okcoin 客户端
    )
    logger = get_logger('carry brick')

    def account(self):
        account = {
            'free': {'cny': 0.0, 'btc': 0.0, 'ltc': 0.0},
            'frozen': {'cny': 0.0, 'btc': 0.0, 'ltc': 0.0},
            'total_cny': 0.0,
            'platform': {}
        }
        for client in self.listen_client:
            ret = client.account()
            account['free']['cny'] += float(ret['free']['cny'])
            account['free']['btc'] += float(ret['free']['btc'])
            account['free']['ltc'] += float(ret['free']['ltc'])
            account['total_cny'] += float(ret['asset']['total'])
            account['frozen']['cny'] += float(ret['frozen']['cny'])
            account['frozen']['btc'] += float(ret['frozen']['btc'])
            account['frozen']['ltc'] += float(ret['frozen']['ltc'])
            account[client.name] = ret
            account['platform'][client.name] = {
                "cny": ret['free']['cny'],
                "ltc": ret['free']['ltc'],
                "btc": ret['free']['btc'],
                "origin": ret
            }
        return account

    def collect_depth(self):
        min_buy = None
        max_sell = None
        self.logger.info("开始计算价格深度")
        for client in self.listen_client:
            depth = client.ltc_depth()
            if not min_buy:
                min_buy = {
                    "depth": depth['asks'][0],
                    "client": client
                }
            else:
                if depth['asks'][0][0] < min_buy['depth'][0]:
                    min_buy = {
                        "depth": depth['asks'][0],
                        "client": client
                    }
            if not max_sell:
                max_sell = {
                    "depth": depth['bids'][0],
                    "client": client
                }
            else:
                if depth['bids'][0][0] > max_sell['depth'][0]:
                    max_sell = {
                        "depth": depth['bids'][0],
                        "client": client
                    }
        self.logger.info("最小买入价: %.2f, 深度: %.4f, 平台: %s, 最大卖出价: %.2f, 深度: %.4f, 平台: %s",
                         min_buy['depth'][0], min_buy['depth'][1], min_buy['client'].name,
                         max_sell['depth'][0], max_sell['depth'][1], max_sell['client'].name
                         )
        return min_buy, max_sell

    def calculate_trade_count(self, account, max_sell, min_buy):
        self.logger.info("开始计算: 最大卖出, 买入数量")
        max_sell_count = float(account[max_sell['client'].name]['free']['ltc'])
        max_buy_count = float(account[min_buy['client'].name]['free']['cny']) / min_buy['depth'][0] * (1 - fee)
        sell_count = min(max_sell_count, max_buy_count)
        buy_count = sell_count / (1 - fee)
        self.logger.info("最大卖出 %.4f, 买入数量: %.4f", sell_count, buy_count)
        return sell_count, buy_count

    def trade(self, sell_client, buy_client, sell_count, buy_count, sell_price, buy_price):
        self.logger.info("开始交易")
        # 先卖出
        self.logger.info("开始卖出")
        ret, sell_order_id = sell_client.sell_ltc(sell_price, sell_count)
        if not ret:
            raise RuntimeError('卖出失败: {} 价格 {}, 卖出 {}, msg:{}'.format(
                sell_client.name, sell_price, sell_count, sell_order_id))
        sell_ret = sell_client.order_info(sell_order_id)
        if not sell_ret['success']:
            self.logger.info("订单未立即完成, 等待: %.2f", 0.1)
            time.sleep(0.05)
            ret = sell_client.order_info(sell_order_id)
            self.logger.info("第二次查询卖出订单: %s", str(ret))
            # 卖出失败， 取消本次交易
            if not ret['success']:
                cancel_ret = sell_client.cancel_order(sell_order_id)
                self.logger.info("卖出失败 取消卖出: %s", str(cancel_ret))
                return False, "卖出失败"
        self.logger.info("卖出完成")
        # TODO 处理部分成交
        # TODO 卖出后，买入订单有时不能完成，是卖出和买入时间间隔太大
        # 买入
        ret, buy_order_id = buy_client.buy_ltc(buy_price, buy_count)
        if not ret:
            raise RuntimeError('买入失败: {} 价格 {}, 买出 {}'.format(buy_client.name, buy_price, buy_count))
        buy_ret = buy_client.order_info(buy_order_id)
        if not buy_ret['success']:
            query_times = 2
            while True:
                if query_times > 60:
                    self.logger.error("查询%s次订单未完成, %s平台, order_number: %s",
                                      str(query_times), buy_client.name, str(buy_order_id))
                    break
                self.logger.info("订单未立即完成, 等待: %.2f, 再次查询", 0.5)
                time.sleep(0.5)
                ret = buy_client.order_info(buy_order_id)
                if ret['success']:
                    self.logger.info("第%s次查询买入订单: %s 完成", str(query_times), str(ret))
                    break
                self.logger.info("第%s次查询买入订单: %s 未完成", str(query_times), str(ret))
                query_times += 1
            return True, '交易完成'
        return True, '交易完成'

    def carry_coin(self, send_client, receive_client, amount, coin_type='ltc'):
        """
        platform A send coin to platform B
        :param coin_type:
        :param send_client:
        :param receive_client:
        :param amount:
        :return: Boolean
        """
        pass

    def calculate_carry_coin(self):
        pass

    @db_session
    def go(self):
        need_update_account = True
        while True:
            time.sleep(1)
            profit_notify_everyday()
            try:
                if need_update_account:
                    self.logger.info("更新账户信息")
                    account = self.account()
                    need_update_account = False
            except Exception as e:
                self.logger.error("获取账户信息错误: %s, 暂停2s", str(e))
                time.sleep(2)
                continue
            self.logger.info(
                "本次循环前资产, cny: %.2f, btc: %.4f, ltc: %.4f, 总cny: %.2f",
                account['free']['cny'],
                account['free']['btc'],
                account['free']['ltc'],
                account['total_cny'],
            )
            self.logger.info(
                "本次循环前冻结资产, cny: %.2f, btc: %.4f, ltc: %.4f",
                account['frozen']['cny'],
                account['frozen']['btc'],
                account['frozen']['ltc'],
            )
            for k, v in account['platform'].items():
                self.logger.info(
                    "%s 平台 cny: %s, ltc: %s, btc: %s", k, str(v['cny']), str(v['ltc']), str(v['btc'])
                )
            try:
                min_buy, max_sell = self.collect_depth()
            except Exception as e:
                self.logger.error("获取深度信息错误: %s, 暂停2s", str(e))
                time.sleep(2)
                continue
            if min_buy['client'].name == max_sell['client'].name:
                self.logger.info("相同平台%s, 跳过", min_buy['client'].name)
                continue
            before_ltc = account['free']['ltc']
            before_cny = account['free']['cny']

            # 判断ltc 数量
            if float(account[min_buy['client'].name]['free']['cny']) < 1:
                self.logger.info("%s 平台cny不足: %s < 1", min_buy['client'].name,
                                 account[min_buy['client'].name]['free']['cny'])
                continue
            if float(account[max_sell['client'].name]['free']['ltc']) < 0.1:
                self.logger.info("%s 平台ltc不足: %s < 0.1", max_sell['client'].name,
                                 account[max_sell['client'].name]['free']['ltc'])
                continue
            sell_count, buy_count = self.calculate_trade_count(account, max_sell, min_buy)

            # 判断深度
            if buy_count > min_buy['depth'][1] * depth_limit or sell_count > max_sell['depth'][1] * depth_limit:
                # 用depth_limit来确保有足够多的单可以交易
                self.logger.info("深度不足: %.4f < %.4f * %s or %.4f < %.4f * %s",
                                 buy_count, min_buy['depth'][1], str(depth_limit),
                                 sell_count, max_sell['depth'][1], str(depth_limit)
                                 )
                continue

            # 判断盈利
            profit = sell_count * max_sell['depth'][0] * (1 - fee) - buy_count * min_buy['depth'][0]
            if profit < 0.1:
                self.logger.info("本次收益 %.2f < 0.1, 跳过", profit)
                continue

            self.logger.info("本次预计收益 %.2f", profit)
            # 先执行卖出， 再执行买入
            ret, msg = self.trade(sell_client=max_sell['client'], buy_client=min_buy['client'],
                                  sell_count=sell_count, buy_count=buy_count,
                                  sell_price=max_sell['depth'][0], buy_price=min_buy['depth'][0]
                                  )
            if not ret:
                self.logger.warn("本次交易失败: %s", str(msg))
                continue
            account = self.account()
            self.logger.info(
                "本次循环后资产, cny: %.2f, btc: %.4f, ltc: %.4f, 总cny: %.2f",
                account['free']['cny'],
                account['free']['btc'],
                account['free']['ltc'],
                account['total_cny'],
            )
            self.logger.info(
                "本次循环后冻结资产, cny: %.2f, btc: %.4f, ltc: %.4f",
                account['frozen']['cny'],
                account['frozen']['btc'],
                account['frozen']['ltc'],
            )
            self.logger.info(
                "实际收益, cny: %.2f - %.2f = %.2f, ltc: %.4f - %.4f = %.4f",
                account['free']['cny'], before_cny, account['free']['cny'] - before_cny,
                account['free']['ltc'], before_ltc, account['free']['ltc'] - before_ltc,
            )
            if 0 < account['free']['cny'] - before_cny < profit:
                self.logger.warn("实际收益 小于 预计收益")
            # 记录交易
            for k, v in account['platform'].items():
                self.logger.info(
                    "%s 平台 cny: %s, ltc: %s, btc: %s", k, str(v['cny']), str(v['ltc']), str(v['btc'])
                )
            TradeRecord(
                create_time=datetime.now(), before_cny=str(before_cny), before_ltc=str(before_ltc),
                before_btc=str(account['free']['btc']), current_cny=str(account['free']['cny']),
                current_ltc=str(account['free']['ltc']),
                current_btc=str(account['free']['btc']),
                profit=str(account['free']['cny'] - before_cny),
                except_profit=str(profit),
                sell_price=str(max_sell['depth'][0]),
                sell_count=str(sell_count),
                sell_coin='ltc',
                sell_platform=max_sell['client'].name,
                buy_price=str(min_buy['depth'][0]),
                buy_count=str(buy_count),
                buy_coin='ltc',
                buy_platform=min_buy['client'].name,
            )
            commit()
            if account['free']['cny'] - before_cny < 0:
                self.logger.warn("实际收益小于0")
                break
            need_update_account = True
