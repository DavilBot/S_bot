from trade_bot import TradeBot
import json
import pandas as pd
from utils.notifications import Notifications
from pyti.moving_average_convergence_divergence import moving_average_convergence_divergence
import time


class MacdBot(TradeBot):
    def __init__(self,
                 **kwargs):
        super().__init__(**kwargs)
        j = json.loads(self.macd)
        # self.ema_days = j['ema']
        self.macd_days = j['macd']
        self.log = open("log_macd.txt", "a")
        # self.notifier = Notifications()
        # print ("balance btc  {} coin {} status {}".format(self.btc_amount, self.coin_amount, self.isBTC))

    def calc_grades(self, from_binance=False):
        self.df = self.get_prices(from_binance)
        self.EMA(ema_days=5)
        self.EMA(ema_days=35)
        self.MACD()
        self.macd_signal()

    def EMA(self, ema_days=5, data=None):
        smoothing_constant = 2/(ema_days+1)
        ema_list = []
        if data is None:
            first_ema = self.df[:ema_days]
            sum_close = 0
            for index, row in first_ema.iterrows():
                sum_close += row['Close']
                ema_list.append(None)
            ema = sum_close/ema_days

            other_ema = self.df[ema_days:]
            for index, row in other_ema.iterrows():
                ema = smoothing_constant*(row['Close']-ema) + ema
                ema_list.append(ema)
            ema_list = pd.Series(ema_list, name='Ema_'+str(ema_days))
            self.df = self.df.join(ema_list)
        else:
            row = self.df.iloc[-1]
            ema = row['Ema_'+str(ema_days)]
            for idnex, row in data.iterrows():
                ema = smoothing_constant * (row['Close'] - ema) + ema
                ema_list.append(ema)
            ema_list = pd.Series(ema_list, name='Ema_' + str(ema_days))
            data = data.join(ema_list)
            return data

    def MACD(self, data=None):
        if data is None:
            self.df = self.df.shift(-35)[:-35]
            macd_values = []
            for index, row in self.df.iterrows():
                macd_values.append(row['Ema_5']-row['Ema_35'])
            macd_values = pd.Series(macd_values, name="Macd")
            self.df = self.df.join(macd_values)
        else:
            macd_values = []
            for index, row in data.iterrows():
                macd_values.append(row['Ema_5'] - row['Ema_35'])
            macd_values = pd.Series(macd_values, name="Macd")
            data = data.join(macd_values)
            return data

    def macd_signal(self, data=None):
        smoothing_constant = 2 / (self.macd_days + 1)
        macd_list = []
        if data is None:
            first_ema = self.df[:self.macd_days]
            sum_close = 0
            for index, macd in first_ema.iterrows():
                sum_close += macd['Macd']
                macd_list.append(None)
            ema = sum_close / self.macd_days

            other_ema = self.df[self.macd_days:]
            for idnex, macd in other_ema.iterrows():
                ema = smoothing_constant * (macd['Macd'] - ema) + ema
                macd_list.append(ema)
            macd_list = pd.Series(macd_list, name='Macd_line')
            self.df = self.df.join(macd_list)
            #shift index
            self.df = self.df.shift(-self.macd_days)[:-self.macd_days]
        else:
            row = self.df.iloc[-1]
            ema = row['Macd_line']
            for idnex, macd in data.iterrows():
                ema = smoothing_constant * (macd['Macd'] - ema) + ema
                macd_list.append(ema)
            macd_list = pd.Series(macd_list, name='Macd_line')
            data = data.join(macd_list)
            return data


    def get_backtest(self, limit=500):
        self.calc_grades()
        count = 0
        success_count = 0
        self.prev_price = self.df['Close'][0]
        self.bought_price = self.prev_price
        print ("backtest is here len of data is ", len(self.df))
        for i in range(1, len(self.df)-1):
            if self.isBTC:
                if (self.check_buy_condition(i)):
                    self.isBTC = False
                    self.amount = self.amount / self.df['Close'][i+1] * 0.9995
                    print ("Buy", self.amount, self.df['Close'][i+1])
                    print("buy time", self.df['TimeStamp'][i])
                    print ("index ", i)
                    self.bought_price = self.df['Close'][i+1]
                    count +=1
            else:
                if self.check_sell_condition(i):
                    self.isBTC = True
                    if self.df['Close'][i+1] > self.bought_price:
                        success_count +=1
                    self.amount = self.amount * self.df['Close'][i+1] * 0.9995
                    print("sell time", self.df['TimeStamp'][i+1])
                    print ("index ", i)
                    print ("Sell", self.amount, self.df['Close'][i+1])
            self.prev_price = self.df['Close'][i+1]
        if not self.isBTC:
            self.amount = self.amount*self.df['Close'][len(self.df) -1]*0.9995
        print ('finally', self.amount)
        print ( "accuracy {} / {}".format(success_count, count))

    def check_buy_condition(self, index=-1):
        i = index
        if (self.margin_macd_down(i) and
            self.df['Macd'][i] > self.df['Macd'][i-2] and
            self.df['Macd_line'][i] > self.df['Macd_line'][i-2]):
            print ("buy index ", i)
            return True
        else:
            return False

    def check_sell_condition(self, index=-1):
        i = index
        condition_1 = self.margin_macd_up(i)
        condition_2 = False
        condition_3 = False
        condition_4 = self.get_profit_stop(self.df['Close'][i], self.prev_price, 0.020)
        if condition_4 or condition_1 or condition_2 or condition_3:
            print ("sell index ", i)
            print ("Sell coin_quantity {} price {}", self.coin_amount, self.df['Close'][i])
            print ("condition_1 {}, condition_2 {} condition_3 {} condition_4 {}".format(condition_1,
                                                            condition_2, condition_3,
                                                            condition_4))
            return True
        else:
            return False

    def margin_macd_down(self, index=-1, margin=0.25):
        down_line = - 0.00003
        if (self.df['Macd'][index] > down_line * (1 + margin) and
            self.df['Macd'][index] < down_line * (1 - margin) and
            self.df['Macd_line'][index] > down_line * (1 + margin) and
            self.df['Macd_line'][index] < down_line * (1 - margin)):
            return True
        else:
            return False

    def margin_macd_up(self, index=-1, margin=0.25):
        up_line = 0.00003
        if (self.df['Macd'][index] < up_line * (1 + margin) and
            self.df['Macd'][index] > up_line * (1 - margin) and
            self.df['Macd_line'][index] < up_line * (1 + margin) and
            self.df['Macd_line'][index] > up_line * (1 - margin)):
            return True
        else:
            return False

    def get_profit_stop(self, price_cur, price_prev, margin=0.01):
        return (price_cur - price_prev)/ price_prev > margin

    def trade_on_macd(self):
        self.calc_grades()
        self.init = True
        while True:
            # row = self.df.iloc[-1]
            # data = self.get_candle_based_on_time(start_time=int(row['TimeStamp']*1000+1000))
            # print(len(data))
            # if len(data) > 1:
            #     #calc grades
            #     data = self.EMA(ema_days=5, data=data)
            #     data = self.EMA(ema_days=35, data=data)
            #     data = self.MACD(data=data)
            #     data = self.macd_signal(data=data)
            #     length = len(self.df)
            #     for index, row in data.iterrows():
            #         self.df.loc[index+length] = row
            #     self.df.drop(self.df.tail(1).index, inplace=True)
            #     self.df = self.df.shift(-len(self.df)+5)[:-len(self.df)+5]
            #     #end
            #     if self.check_trade_condition():
            #         self.get_trade_balance()
            #         self.bot_send_message(
            #             "my balance btc {} {} {}".format(self.btc_amount, self.symbol, self.coin_amount))
            #         # self.notifier.sendLogMsg("my balance btc {} {} {}".format(
            #         #     self.btc_amount, self.symbol, self.coin_amount))
            #
            #     print("my balance btc {} {} {}".format(
            #         self.btc_amount, self.symbol, self.coin_amount))
            #     self.log.write("my balance btc {} {} {}\n".format(
            #         self.btc_amount, self.symbol, self.coin_amount))
            #     self.log.flush()
            self.bot_send_message("my balance btc 0.3231","macd")
            time.sleep(15)

    def check_trade_condition(self):
        return True
        i = len(self.df) - 1
        # if not self.bought_price:
        #     self.bought_price = self.df['Close'][i]
        if self.isBTC:
            if (self.check_buy_condition(i)):
                coin_amount = self.amount / self.df['Close'][i] * 0.9995
                print ("Buy coin_quantity {} price {}".format(coin_amount,
                                                    self.df['Close'][i]))
                self.notifier.sendLogMsg("Buy Condition")
                # self.log.write("Buy Condition")
                self.order_coin_btc(i)
                return True
        else:
            if self.check_sell_condition(i):
                self.notifier.sendLogMsg("Sell Condition")
                # self.log.write("Sell Condition")
                self.order_coin_btc(i)
                return True
        return False

    def order_coin_btc(self, last_index=-1):
        row = self.df.iloc[-1]
        data = self.get_candle_based_on_time(start_time=int(row['TimeStamp'] * 1000 + 1000))
        if self.isBTC:
            side = "BUY"
            price = data['Close'][len(data) - 1]
            # price = data['Close'][last_index]
            amount = self.btc_amount / price * .95 // 0.01 / 100
        else:
            side = "SELL"
            amount = self.coin_amount // 0.01 / 100
        self.isBTC = not self.isBTC
        self.init = False
        # Order Type = MARKET
        return self.place_order(side=side, type="MARKET", quantity=amount,
                                symbol=self.symbol)

if __name__== '__main__':
    DOS_PUB = "z6fQcrTPseYt0vQeCyIoINlOZybA6yMs8mUe41vRdgLukEq8z43zhoCTCLi1RQoI"
    DOS_SECRET = 's6Cb9JJsmmMcEn0VQ8aLdAfap8LUeWvJaBKHeoNtAb2qnfZOpVA8We3xdoa9mJmD'
    bot = MacdBot(token=DOS_PUB, secret=DOS_SECRET, isBTC=True, amount=0.012, symbol="ETCBTC")
    # bot.get_backtest(limit=1000)
    bot.trade_on_macd()
