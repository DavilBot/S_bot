from trade_bot import TradeBot
from utils.treeset import TreeSet
from utils.notifications import Notifications
import json
import math
import time
import pandas as pd
import os.path

class CciBot(TradeBot):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        j = json.loads(self.cci)
        self.tp_sma = j['tp_sma']
        self.interval = j['interval']
        print("balance btc  {} coin {} status {}".format(self.btc_amount, self.coin_amount, self.isBTC))

        self.log = open("log.txt", "a")
       # self.notifier = Notifications()


    def calc_grades(self, from_binance = False):
        self.df = self.get_prices(from_binance)
        self.set_tp_prices()
        self.set_values()
        self.set_ranges()
        self.set_grades()
        print(self.df['Close'][159])
        self.log.write("my close {} \n".format(self.df['Close'][159]))

    def set_tp_prices(self):
        tp_list = []
        for index, row in self.df.iterrows():
            tp_list.append((row['Close']+row['Low']+row['High'])/3)
        tp_list = pd.Series(tp_list, name='Tp')
        self.df = self.df.join(tp_list)

    def set_values(self):
        tp_range_prices = self.df[:self.tp_sma-1]
        tp_list = []
        value_list = []
        for index, row in tp_range_prices.iterrows():
            tp_list.append(row['Tp'])
            value_list.append(None)
        tp_sum = sum(tp_list)
        other_prices = self.df[self.tp_sma-1:]
        for index, row in other_prices.iterrows():
            tp_list.append(row['Tp'])
            tp_sum = tp_sum + row['Tp']
            sma = tp_sum/self.tp_sma
            mean_dev = self.mean_deviation(tp_list, sma)
            value = 0
            if mean_dev != 0:
                value = (row['Tp']-sma)/(0.015*mean_dev)

            value_list.append(value)

            tp_sum = tp_sum - tp_list[0]
            tp_list.pop(0)
        value_list = pd.Series(value_list, name='Cci')
        self.df = self.df.join(value_list)

    def mean_deviation(self, tp_list, sma):
        mean_dev = 0
        for val in tp_list:
            diff = sma - val
            mean_dev = mean_dev + diff
        return mean_dev/self.tp_sma

    def set_ranges(self):
        values = TreeSet([])
        values_cnt = dict({})
        value_idx = []

        min_list = []
        max_list = []

        #delete nan values
        self.df = self.df.dropna(axis=0, subset=['Cci'])

        df_values = self.df['Cci'].values.astype('float')
        df_mts = self.df['TimeStamp'].values.astype('int64')
        range_flist = df_values[:self.interval-1]
        for cci in range_flist:
            value = cci
            if value not in values_cnt:
                values.add(value)
                values_cnt[value] =1
            else:
                values_cnt[value] = values_cnt[value]+1
            value_idx.append(value)

            min_list.append(values[0])
            max_list.append(values[-1])

        range_llist = df_values[self.interval-1:]
        for cci in range_llist:
            #insertion
            value = cci
            if value not in values_cnt:
                values.add(value)
                values_cnt[value] = 1
            else:
                values_cnt[value] = values_cnt[value] + 1
            value_idx.append(value)
            #end

            min_list.append(values[0])
            max_list.append(values[-1])

            #remove
            remove_value = value_idx[0]
            values_cnt[remove_value] = values_cnt[remove_value]-1
            if values_cnt[remove_value] == 0:
                values.remove(remove_value)
                values_cnt.pop(remove_value)
            value_idx.pop(0)
            #end

        min_list = pd.Series(min_list, name='Min')
        max_list = pd.Series(max_list, name='Max')
        df_mts = pd.Series(df_mts, name="TimeStamp")
        df_ranges = pd.concat([min_list, max_list, df_mts], axis=1)
        self.df = self.df.join(df_ranges.set_index('TimeStamp'), on='TimeStamp')

    def set_grades(self):
        grade_list = []
        df_mts = self.df['TimeStamp'].values.astype('int64')
        for index, row in self.df.iterrows():
            grade = -1
            if row['Cci'] == 0:
                grade = 5
            elif row['Cci'] >= -100 and row['Cci'] < 0:
                grade = 4+(row['Cci']+100)/100
            elif row['Cci'] <= 100 and row['Cci'] > 0:
                grade = 5+(row['Cci']/100)
            elif row['Cci'] < -100:
                step = math.fabs((row['Min']+100)/4)
                grade = (row['Cci']-row['Min'])/step
            elif row['Cci'] > 100:
                step = (row['Max']-100)/4
                grade = 6+(row['Cci']-100)/step
            grade_list.append(10-grade)

        df_mts = pd.Series(df_mts, name="TimeStamp")
        grade_list = pd.Series(grade_list, name="Grade")
        grade_list = pd.concat([grade_list, df_mts], axis=1)
        self.df = self.df.join(grade_list.set_index('TimeStamp'), on='TimeStamp')

    def get_backtest(self):
        transactions_buy = 0
        transactions_sell = 0
        for index, row in self.df.iterrows():
            if self.isBTC and self.check_buy_condition(row['Grade']):
                self.isBTC = False
                self.amount = self.amount / row['Close'] * 0.9995
                transactions_buy = transactions_buy+1
            elif not self.isBTC and self.check_sell_condition(row['Grade']):
                self.isBTC = True
                self.amount = self.amount * row['Close'] * 0.9995
                transactions_sell = transactions_sell+1
        print("%d %d",transactions_buy,transactions_sell)

    def check_buy_condition(self, grade=-1):
        print("Buy Condition ", grade)
        self.log.write("Buy Condition %f\n"%(grade))
        self.log.flush()
        return grade > 8.0

    def check_sell_condition(self, grade=-1):
        print("Sell Condition ", grade)
        self.log.write("Sell Condition %f\n"%(grade))
        self.log.flush()
        return grade < 2.0

    def print_amount(self):
        print(self.amount)

    def trade_on_cci(self):
        self.init = True
        while True:
            self.calc_grades(from_binance = True)
            # print(self.df)
            # self.get_etc_btc_balance()
            if self.check_trade_condition():
                self.get_trade_balance()
                self.bot_send_message("my balance btc {} {} {}".format(self.btc_amount, self.symbol, self.coin_amount), "cci")
               # self.notifier.sendLogMsg("my balance btc {} {} {}".format(
                   # self.btc_amount, self.symbol, self.coin_amount))

            print ("my balance btc {} {} {}".format(
                    self.btc_amount, self.symbol, self.coin_amount))
            self.log.write("my balance btc {} {} {}\n".format(
                self.btc_amount, self.symbol, self.coin_amount))
            self.log.flush()
            time.sleep(120)

if __name__ == '__main__':
    DOS_PUB = "z6fQcrTPseYt0vQeCyIoINlOZybA6yMs8mUe41vRdgLukEq8z43zhoCTCLi1RQoI"
    DOS_SECRET = 's6Cb9JJsmmMcEn0VQ8aLdAfap8LUeWvJaBKHeoNtAb2qnfZOpVA8We3xdoa9mJmD'

    bot = CciBot(token=DOS_PUB,
                 secret=DOS_SECRET,
                 isBTC=True, amount=0.012, symbol="ETCBTC")
    # bot.calc_grades()
    bot.trade_on_cci()
    # print(bot.get_balance().json())
    # print(bot.get_last_orders().json())
    # bot.get_backtest()
    # bot.print_amount()
