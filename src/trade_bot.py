from json import JSONDecodeError
import time
import requests

from utils.sql_connector import SQLConnector
from base_api import BaseApi
import pandas as pd


class TradeBot(BaseApi):
    def __init__(self,
                 token='kj36RD6y6BoSWXb8MOscQnZJWJriISwS6t9cWbM6COgeK8ugY2CluF2i4HTE0BVS',
                 secret=b'mDvFxW0I902jadoz3aAsq9msf1ILZLAusFldIaTEbsyjqZGoOKVVyC5ocSNk5KeE',
                 cci='{"tp_sma":140, "interval":20}',
                 macd='{"macd":5}',
                 isBTC=True, amount=5, symbol='ETCBTC'):
        super().__init__(token, secret, symbol)
        self.cci = cci
        self.macd = macd
        self.bought_price = None
        self.order_id = None
        self.isBTC = isBTC
        self.amount = amount
        self.symbol = symbol
        self.base_url = "https://api.binance.com"
        self.bought_price = None
        self.order_id = None
        if isBTC:
            self.btc_amount = amount
            self.coin_amount = 0.
        else:
            self.btc_amount = 0.
            self.coin_amount = amount

    def get_trade_balance(self):
        if self.init:
            return
        if self.isBTC:
            buy_btc, sell_coin = self.get_new_balance()

            self.btc_amount = self.btc_amount + buy_btc
            self.coin_amount = self.coin_amount - sell_coin
        else:
            sell_btc, buy_coin = self.get_new_balance()

            self.coin_amount = self.coin_amount + buy_coin
            self.btc_amount = self.btc_amount - sell_btc

    def check_trade_condition(self):
        return True
        # i = len(self.df) - 1
        # if not self.bought_price:
        #     self.bought_price = self.df['Close'][i]
#        if self.isBTC:
#            if (self.check_buy_condition(self.df['Grade'][i])):
#                coin_amount = self.amount / self.df['Close'][i] * 0.9995
#                print ("Buy coin_quantity {} price {}".format(coin_amount,
#                                                    self.df['Close'][i]))
                # print ("K {} D {}".format(
                # self.df['STOCH_RSI_K_' + str(self.stoch_rsi)][i],
                # self.df['STOCH_RSI_D_' + str(self.stoch_rsi)][i]))
                # self._print_time(self.data['TimeStamp'][i].astype('int'))
                # self.bought_price = self.df['Close'][i]
#                self.notifier.sendLogMsg("Buy Condition %f\n" % (self.df['Grade'][i]))
#                self.order_coin_btc()
#                return True
#        else:
#            if self.check_sell_condition(self.df['Grade'][i]):
#                self.notifier.sendLogMsg("Sell Condition %f\n" % (self.df['Grade'][i]))
#                self.order_coin_btc()
#                return True
#        return False

    def get_prices(self, from_binance = False):
        if from_binance:
            df = self.get_valid_candle(limit=161)
            return df
        else:
            host = '188.40.108.37'
            con = SQLConnector(host=host, pwd='Behappysm_161',
                               user='crypto', db='db_crypto2')
            sql_str = '''SELECT `close`, `mts`,`high`, `low` FROM `prices5m`
                         WHERE platform = 'binance' and ticker='t{}'
                        ORDER BY `prices5m`.`mts` ASC'''
            sql_str = sql_str.format(self.symbol)
            print ("SQL", sql_str)
            answer = con.exec_sql(sql_str)
            df = pd.DataFrame(answer)
            df = pd.DataFrame(answer).rename(index=int, columns={'close': 'Close', 'mts': 'TimeStamp',
                                                                 'high': 'High', 'low': 'Low'})
            # df.TimeStamp = pd.to_datetime(df.TimeStamp, unit='ms')
            return df

    def get_backtest(self, limit=500):
        return "Not implemented for this Bot"

    def get_valid_candle(self, *args, **kwargs):
        repeat = True
        while repeat:
            try:
                answer = self.get_candle(*args, **kwargs)
                repeat = False
            except JSONDecodeError:
                time.sleep(1)
                pass
        return answer

    def get_candle(self, interval='1h', limit=161):
        url = self.base_url + "/api/v1/klines"
        url += "?symbol=" + self.symbol + "&interval=" + interval + "&limit=" + str(limit)
        try:
            answer = requests.get(url).json()
            opens, lows, highs, tsmp, closes, = [], [], [], [], []
            self.log.write("Answer {}".format(answer))
            #for binance candle
            for i in answer:
                opens.append(i[1])
                closes.append(i[4])
                lows.append(i[3])
                highs.append(i[2])
                tsmp.append(i[0])
            opens = pd.Series(opens, name='Open')
            closes = pd.Series(closes, name='Close')
            highs = pd.Series(highs, name='High')
            lows = pd.Series(lows, name='Low')
            tsmp = pd.Series(tsmp, name='TimeStamp')
            df = pd.DataFrame()
            df = df.join(opens, how='right')
            df = df.join(closes)
            df = df.join(lows)
            df = df.join(highs)
            df = df.join(tsmp)
            df = df.astype('float')
        except Exception as e:
            self.log.write("Failed: {}\n".str(e))
        return df

    def get_candle_based_on_time(self, interval='5m', start_time=time.time()):
        url = self.base_url + "/api/v1/klines"
        url += "?symbol=" + self.symbol + "&interval=" + interval + "&startTime=" + str(start_time)
        print(url)
        try:
            answer = requests.get(url).json()
            opens, lows, highs, tsmp, closes = [], [], [], [], []
            # for binance candle
            for i in answer:
                opens.append(i[1])
                closes.append(i[4])
                lows.append(i[3])
                highs.append(i[2])
                tsmp.append(i[0]/1000)
            opens = pd.Series(opens, name='Open')
            closes = pd.Series(closes, name='Close')
            highs = pd.Series(highs, name='High')
            lows = pd.Series(lows, name='Low')
            tsmp = pd.Series(tsmp, name='TimeStamp')
            df = pd.DataFrame()
            df = df.join(opens, how='right')
            df = df.join(closes)
            df = df.join(lows)
            df = df.join(highs)
            df = df.join(tsmp)
            df = df.astype('float')
        except Exception as e:
            self.log.write("Failed: {}\n".str(e))
        return df

    def order_coin_btc(self):
        last_index = 159
        data = self.get_valid_candle()
        if self.isBTC:
            side = "BUY"
            # price = data['Close'][len(data) - 1]
            price = data['Close'][last_index]
            amount = self.btc_amount / price * .95 // 0.01 / 100
        else:
            side = "SELL"
            amount = self.coin_amount // 0.01 / 100
        self.isBTC = not self.isBTC
        self.init = False
        # Order Type = MARKET
        return self.place_order(side=side, type="MARKET", quantity=amount,
                                symbol=self.symbol)
        # Order Type = LIMIT
        # return self.place_order(side=side, type="LIMIT", timeInForce="GTC", quantity=amount, price=data['Close'][last_index], symbol=self.symbol)

