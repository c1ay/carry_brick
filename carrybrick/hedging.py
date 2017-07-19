# coding: utf-8
import time
import random
from datetime import datetime

from pony.orm import db_session, commit

from carrybrick.db import Record
from carrybrick.log import get_logger
from carrybrick.notify import profit_notify_everyday
from client import huobi, okcoin, btc38
from client.huobi.huobi_eth_sdk import ApiError

fee = 0.0015                   # 交易费率
depth_limit = 0.35             # 深度百分比限制
profit_limit = 0.26            # 最小利润
trade_percent = 0.618          # 交易额占当前仓位百分比
trade_count_limit = 0.035      # 最小交易额
limit_diff = 8.5               # 价格差


class CarryBrick:
    listen_client = (
        huobi.Client(),          # huobi 客户端
        okcoin.Client(),         # okcoin 客户端
        # btc38.Client(),          # btc38 客户端
    )
    logger = get_logger('carry brick')
    coin = 'ltc'
    coin_diff = None

    def __init__(self, trade_coin):
        self.coin = trade_coin

    def account(self):
        account = {
            'free': {'cny': .0, 'btc': .0, 'ltc': .0, 'eth': .0},
            'frozen': {'cny': .0, 'btc': .0, 'ltc': .0, 'eth': .0},
            'total_cny': .0,
            'platform': {}
        }
        for client in self.listen_client:
            ret = client.account()
            account['free']['cny'] += float(ret['free']['cny'])
            account['free']['btc'] += float(ret['free']['btc'])
            account['free']['ltc'] += float(ret['free']['ltc'])
            account['free']['eth'] += float(ret['free']['eth'])
            account['total_cny'] += float(ret['asset']['total'])
            account['frozen']['cny'] += float(ret['frozen']['cny'])
            account['frozen']['btc'] += float(ret['frozen']['btc'])
            account['frozen']['ltc'] += float(ret['frozen']['ltc'])
            account[client.name] = ret
            account['platform'][client.name] = {
                "cny": ret['free']['cny'],
                "ltc": ret['free']['ltc'],
                "btc": ret['free']['btc'],
                "eth": ret['free']['eth'],
                "origin": ret
            }
        return account

    def collect_depth(self, account):
        # 过滤平台不能买入和卖出的
        min_buy = None
        max_sell = None
        self.logger.info("开始计算价格深度")
        for client in self.listen_client:
            depth = client.depth(coin=self.coin)
            # min_buy 过滤cny小于10
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
            # max_sell 过滤ltc 小于 0.1
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
        # 保留三位小数
        self.logger.info("开始计算: 最大卖出, 买入数量")
        max_sell_count = float(account[max_sell['client'].name]['free'][self.coin]) * trade_percent
        max_buy_count = float(account[min_buy['client'].name]['free']['cny']) * 0.7 / min_buy['depth'][0] * (1 - fee)
        sell_count = min(max_sell_count, max_buy_count)
        buy_count = sell_count / (1 - fee)
        sell_count = round(sell_count, 4)
        buy_count = round(buy_count, 4)
        # if sell_count == buy_count:
        #     if random.random() > 0.3:
        #         if sell_count > 0.1:
        #             buy_count += 0.0003
        #         elif sell_count > 0.0005:
        #             buy_count += 0.0002
        #         else:
        #             buy_count += 0.0001
        # buy_count += 0.0003
        if self.coin_diff:
            buy_count += float(self.coin_diff)
        if buy_count * min_buy['depth'][0] > float(account[min_buy['client'].name]['free']['cny']):
            buy_count = sell_count
        self.logger.info("最大卖出 %.4f, 买入数量: %.4f", sell_count, buy_count)
        return sell_count, buy_count

    def trade(self, sell_client, buy_client, sell_count, buy_count, sell_price, buy_price):
        self.logger.info("开始交易")
        # 先卖出
        self.logger.info("开始卖出")
        try:
            ret, sell_order_id = sell_client.sell_market(sell_count, coin=self.coin)
        except Exception as e:
            self.logger.error("卖出错误: %s", str(e))
        if not ret:
            raise RuntimeError('卖出失败: {} 价格 {}, 卖出 {}, msg:{}'.format(
                sell_client.name, sell_price, sell_count, sell_order_id))
        time.sleep(0.05)
        sell_ret = sell_client.order_info(sell_order_id, coin=self.coin)
        if sell_ret['status'] == sell_client.trade_not_complete:
            self.logger.info("订单未立即完成, 等待: %.2f", 0.1)
            ret = sell_client.order_info(sell_order_id, coin=self.coin)
            self.logger.info("第二次查询卖出订单: %s", str(ret))
            # 卖出失败， 取消本次交易
            if ret['status'] == sell_client.trade_not_complete:
                try:
                    cancel_ret = sell_client.cancel_order(sell_order_id, coin=self.coin)
                    self.logger.info("卖出失败 取消卖出: %s", str(cancel_ret))
                    return False, "卖出失败"
                except ApiError as e:
                    self.logger.error("取消失败，可能已卖出, %s, 再次查询", str(e))
                    ret = sell_client.order_info(sell_order_id, coin=self.coin)
                    if ret['status'] == sell_client.trade_not_complete:
                        cancel_ret = sell_client.cancel_order(sell_order_id, coin=self.coin)
                        self.logger.info("卖出失败 取消卖出: %s", str(cancel_ret))
                        return False, "卖出失败"
                    elif ret['status'] == sell_client.trade_partly_complete:
                        # 部分成功， 改变买入数量
                        cancel_ret = sell_client.cancel_order(sell_order_id, coin=self.coin)
                        self.logger.info("部分卖出，取消订单: %s", str(cancel_ret))
                        real_sell_count = float(ret['complete_volume'])
                        self.logger.info("部分卖出成功, 卖出: %.4f", real_sell_count)
                        buy_count = real_sell_count / (1 - fee)
            elif ret['status'] == sell_client.trade_partly_complete:
                # 部分成功， 改变买入数量
                cancel_ret = sell_client.cancel_order(sell_order_id, coin=self.coin)
                self.logger.info("部分卖出，取消订单: %s", str(cancel_ret))
                real_sell_count = float(ret['complete_volume'])
                self.logger.info("部分卖出成功, 卖出: %.4f", real_sell_count)
                buy_count = real_sell_count / (1 - fee)
        elif sell_ret['status'] == sell_client.trade_partly_complete:
            # 部分成功， 改变买入数量
            cancel_ret = sell_client.cancel_order(sell_order_id, coin=self.coin)
            self.logger.info("部分卖出，取消订单: %s", str(cancel_ret))
            real_sell_count = float(ret['complete_volume'])

            self.logger.info("部分卖出成功, 卖出: %.4f", real_sell_count)
            buy_count = real_sell_count / (1 - fee)
        else:
            self.logger.info("第一次卖出成功")
        self.logger.info("卖出完成")
        # TODO 卖出后，买入订单有时不能完成，是卖出和买入时间间隔太大
        # 买入
        self.logger.info("开始买入")
        ret, buy_order_id = buy_client.buy_market(buy_count, coin=self.coin, price=buy_price)
        if not ret:
            raise RuntimeError('买入失败: {} 价格 {}, 买出 {} error:{}'.format(
                buy_client.name, buy_price, buy_count, buy_order_id))
        buy_ret = buy_client.order_info(buy_order_id, coin=self.coin)
        if buy_ret['status'] != buy_client.trade_complete:
            query_times = 2
            while True:
                if query_times > 60:
                    self.logger.error("查询%s次订单未完成, %s平台, order_number: %s",
                                      str(query_times), buy_client.name, str(buy_order_id))
                    break
                self.logger.info("订单未立即完成, 等待: %.2f, 再次查询", 0.5)
                time.sleep(0.5)
                ret = buy_client.order_info(buy_order_id, coin=self.coin)
                if ret['status'] == buy_client.trade_complete:
                    self.logger.info("第%s次查询买入订单: %s 完成", str(query_times), str(ret))
                    break
                self.logger.info("第%s次查询买入订单: %s 未完成", str(query_times), str(ret))
                query_times += 1
            return True, '交易完成'
        return True, '交易完成'

    @db_session
    def go(self):
        need_update_account = True
        while True:
            time.sleep(0.5)
            # profit_notify_everyday()
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
                "本次循环前资产, cny: %.2f, btc: %.4f, ltc: %.4f, eth: %.4f, 总cny: %.2f",
                account['free']['cny'],
                account['free']['btc'],
                account['free']['ltc'],
                account['free']['eth'],
                account['total_cny'],
            )
            self.logger.info(
                "本次循环前冻结资产, cny: %.2f, btc: %.4f, ltc: %.4f, eth: %.4f",
                account['frozen']['cny'],
                account['frozen']['btc'],
                account['frozen']['ltc'],
                account['frozen']['eth'],
            )
            for k, v in account['platform'].items():
                self.logger.info(
                    "%s 平台 cny: %s, eth: %s, ltc: %s, btc: %s", k, str(v['cny']), str(v['eth']), str(v['ltc']), str(v['btc'])
                )
            try:
                min_buy, max_sell = self.collect_depth(account)
            except Exception as e:
                self.logger.error("获取深度信息错误: %s, 暂停2s", str(e))
                time.sleep(2)
                continue
            if min_buy['client'].name == max_sell['client'].name:
                self.logger.info("相同平台%s, 跳过", min_buy['client'].name)
                continue
            before_coin = account['free'][self.coin]
            before_cny = account['free']['cny']

            # 判断coin 数量
            if float(account[min_buy['client'].name]['free']['cny']) < 1:
                self.logger.info("%s 平台cny不足: %s < 1", min_buy['client'].name,
                                 account[min_buy['client'].name]['free']['cny'])
                continue
            if float(account[max_sell['client'].name]['free'][self.coin]) < 0.03:
                self.logger.info("%s 平台%s: %s < 0.03", max_sell['client'].name, self.coin,
                                 account[max_sell['client'].name]['free'][self.coin])
                continue
            sell_count, buy_count = self.calculate_trade_count(account, max_sell, min_buy)
            if sell_count < trade_count_limit:
                self.logger.info("sell_count %.4f < %.4f 跳过", sell_count, trade_count_limit)
                continue

            # 判断深度
            if buy_count > min_buy['depth'][1] * depth_limit or sell_count > max_sell['depth'][1] * depth_limit:
                # 用depth_limit来确保有足够多的单可以交易
                self.logger.info("深度不足: %.3f < %.4f * %s or %.3f < %.4f * %s",
                                 buy_count, min_buy['depth'][1], str(depth_limit),
                                 sell_count, max_sell['depth'][1], str(depth_limit)
                                 )
                continue

            # 判断盈利
            # 这里的计算利润和交易所的计算会有精度问题
            sell_count = round(sell_count, 4)
            buy_count = round(buy_count, 4)
            sell_money = sell_count * max_sell['depth'][0] * (1 - fee)
            buy_money = buy_count * min_buy['depth'][0]
            profit = sell_money - buy_money
            self.logger.info(
                "%s price: %s, %s price: %s", max_sell['client'].name, max_sell['depth'][0],
                min_buy['client'].name, min_buy['depth'][0]
            )
            if max_sell['depth'][0] - min_buy['depth'][0] < limit_diff:
                self.logger.info("差价小于 %s", str(limit_diff))
                continue
            # if profit < profit_limit:
            #     self.logger.info("本次收益 %.2f < %.2f, 跳过", profit, profit_limit)
            #     continue

            self.logger.info("本次预计收益 %.2f - %.2f = %.2f", sell_money, buy_money, profit)
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
                "本次循环后资产, cny: %.2f, btc: %.4f, ltc: %.4f, eth: %.4f,总cny: %.2f",
                account['free']['cny'],
                account['free']['btc'],
                account['free']['ltc'],
                account['free']['eth'],
                account['total_cny'],
            )
            self.logger.info(
                "本次循环后冻结资产, cny: %.2f, btc: %.4f, ltc: %.4f, eth: %.4f",
                account['frozen']['cny'],
                account['frozen']['btc'],
                account['frozen']['ltc'],
                account['frozen']['eth'],
            )
            self.logger.info(
                "实际收益, cny: %.2f - %.2f = %.2f, %s: %.4f - %.4f = %.4f",
                account['free']['cny'], before_cny, account['free']['cny'] - before_cny, self.coin,
                account['free'][self.coin], before_coin, account['free'][self.coin] - before_coin,
            )
            if 0 < account['free']['cny'] - before_cny < profit:
                self.logger.warn("实际收益 小于 预计收益")
            # 记录交易
            for k, v in account['platform'].items():
                self.logger.info(
                    "%s 平台 cny: %s, ltc: %s, btc: %s", k, str(v['cny']), str(v['ltc']), str(v['btc'])
                )
            Record(
                create_time=datetime.now(),
                before_cny=str(before_cny),
                coin=self.coin,
                current_volume=str(account['free'][self.coin]),
                cny=str(account['free']['cny']),
                sell_price=str(max_sell['depth'][0]),
                sell_amount=str(sell_count),
                sell_platform=max_sell['client'].name,
                buy_price=str(min_buy['depth'][0]),
                buy_amount=str(buy_count),
                buy_platform=min_buy['client'].name,
            )
            commit()
            price = min_buy['depth'][0]
            coin_diff = (account['free'][self.coin] - before_coin)
            real_profit = account['free']['cny'] - before_cny + coin_diff * price
            if coin_diff < -0.005:
                # 补偿差值
                self.coin_diff = abs(coin_diff)
            self.logger.info("实际利润(币值变化 + cny变化) %.2f", real_profit)
            if real_profit < 0:
                self.logger.warn("实际收益小于0")
                break
            need_update_account = True
