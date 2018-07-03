import sys
import json
import requests
import time
import urllib
import os.path
#from binance_api import TradeBot
import threading
import pandas as pd
TOKEN = "592999139:AAEpQFDBQ4s-pgjUNGEfsQVHGdiop4b0pi0"
URL = "https://api.telegram.org/bot{}/".format(TOKEN)

class TeleTradeBot():
#    thread = threading.Thread(target=super().trade_on)
#    thread.daemon = True
    def get_url(self, url):
        response = requests.get(url)
        content = response.content.decode("utf8")
        return content

    def get_json_from_url(self, url):
        content = self.get_url(url)
        js = json.loads(content)
        return js

    def get_updates(self,offset=None):
        url = URL + "getUpdates?timeout=100"
        if offset:
            url += "&offset={}".format(offset)
        js = self.get_json_from_url(url)
        return js

    def get_last_update_id(self, updates):
        update_ids = []
        for update in updates["result"]:
            update_ids.append(int(update["update_id"]))
        return max(update_ids)

    def handle_updates(self, updates):
        for update in updates["result"]:
            text = update["message"]["text"]
            chat = update["message"]["chat"]["id"]
            df = pd.read_csv("subscribers.csv")
            list_bots = df[str(chat)].tolist()
            #df = df.drop([str(chat)], 1)
            print(df)
            tick = False
            if text == "/start":
                #keyboard = self.build_keyboard(list_names)#items
                #self.send_message("",chat,keyboard)
                self.send_message("Hello! Here you can subscribe on a single tradebot or all available and track the price.", chat)
            elif text == "/subscribe_all":
                self.send_message("Your subscribed to all tradebots", chat)
            elif text == "/subscribe_cci":
                for l in list_bots:
                    if l == 'cci':
                        tick = True
                        continue
                if tick == True:
                    self.send_message("You already have subscribed on this bot", chat)
                    continue
                else:
                    list_bots.append("cci")
                    df[str(chat)] = list_bots
                    with open('subscribers.csv', 'w') as f:
                        df.to_csv(f)
                    self.send_message("You have successfully subscribed", chat)
            elif text == "/subscribe_macd":
                for l in list_bots:
                    if l == 'macd':
                        tick = True
                        continue
                if tick == True:
                    self.send_message("You already have subscribed on this bot", chat)
                    continue
                else:
                    list_bots.append("macd")
                    df[str(chat)] = list_bots
                    with open('subscribers.csv', 'w') as f:
                        df.to_csv(f)
                    self.send_message("You have successfully subscribed", chat)

    def get_last_chat_id_and_text(self, updates):
        num_updates = len(updates["result"])
        last_update = num_updates - 1
        text = updates["result"][last_update]["message"]["text"]
        chat_id = updates["result"][last_update]["message"]["chat"]["id"]
        return (text, chat_id)

    def send_message(self, text, chat_id, reply_markup=None):
        text = urllib.parse.quote_plus(text)
        url = URL + "sendMessage?text={}&chat_id={}&parse_mode=Markdown".format(text, chat_id)
        if reply_markup:
            url += "&reply_markup={}".format(reply_markup)
        self.get_url(url)

    def send_loop_message(self, chat_id, reply_markup = None):
                text = "Your balance is (btc_amount) {},(coin_amount) {}.".format(self.btc_amount, self.coin_amount)
                text = urllib.parse.quote_plus(text)
                url = URL + "sendMessage?text={}&chat_id={}&parse_mode=Markdown".format(text, chat_id)
                if reply_markup:
                    url += "&reply_markup={}".format(reply_markup)
                self.get_url(url)

    def build_keyboard(self, items):
        keyboard = [[item] for item in items]
        reply_markup = {"keyboard":keyboard, "one_time_keyboard": True}
        return json.dumps(reply_markup)

    def main(self):
        last_update_id = None
        self.__init__()
#        super().__init__()
        while True:
            updates = self.get_updates(last_update_id)
            if len(updates["result"]) > 0:
                last_update_id = self.get_last_update_id(updates) + 1
                self.handle_updates(updates)
            time.sleep(0.5)


if __name__ == '__main__':
        obj = TeleTradeBot()
        obj.main()

