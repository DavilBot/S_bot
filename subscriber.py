import sys
import json
import requests
import time
import urllib
import os.path
import threading
import pandas as pd
TOKEN = "592999139:AAEpQFDBQ4s-pgjUNGEfsQVHGdiop4b0pi0"
URL = "https://api.telegram.org/bot{}/".format(TOKEN)

class TeleTradeBot():
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
            list_bots = []
            data = {}
            if(os.path.isfile('data.json')):
                with open('data.json', 'r') as fp:
                        data = json.load(fp)
                        list_bots = data[str(chat)]
            bots = [['cci', 'ppo', 'mfi'], ['macd', 'sma', 'aroon'], ['rsi', 'bollinger', 'b_indicator']]
            frequency = [['send me every 4 days', 'send me every day', 'send me every 12 hours', 'send me every hour']]
            if text in list_bots:
                self.send_message("You have already subscribed to this tradebot", chat)
                continue
            if text == "/start":
                self.send_message("Hello! Here you can subscribe on a single tradebot or all available and track the price.", chat)
            elif text == "/sub_all":
                data[str(chat)] = ['cci','macd','mfi']#list of all bots
                with open('data.json', 'w') as fp:
                    json.dump(data, fp)
                self.send_message("Your subscribed to all tradebots", chat)
            elif text == "/sub_par" or text =="/not_freq":
                new_l = []
                message = ""
                if text =="/sub_par":
                    new_l = bots
                    message = "Choose bot"
                else:
                    new_l = frequency
                    message = "Choose time interval to receive announcements from tradebots"
                keyboard = self.build_keyboard(new_l)
                self.send_message(message, chat, keyboard)
            elif text == "cci":
                list_bots.append('cci')
                data[str(chat)] = list_bots
                with open('data.json', 'w') as fp:
                    json.dump(data, fp)
                self.send_message("You have successfully subscribed", chat)
            elif text == "mfi":
                list_bots.append('mfi')
                data[str(chat)] = list_bots
                with open('data.json', 'w') as fp:
                    json.dump(data, fp)
                self.send_message("You have successfully subscribed", chat)
            elif text == "ppo":
                list_bots.append('ppo')
                data[str(chat)] = list_bots
                with open('data.json', 'w') as fp:
                    json.dump(data, fp)
                self.send_message("You have successfully subscribed", chat)
            elif text == "macd":
                list_bots.append('macd')
                data[str(chat)] = list_bots
                with open('data.json', 'w') as fp:
                    json.dump(data, fp)
                self.send_message("You have successfully subscribed", chat)
            else:
                self.send_message("Type '/' to view commands", chat)

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

    def build_keyboard(self, items):
        keyboard = items#[[item] for item in items]
        reply_markup = {"keyboard":keyboard, "one_time_keyboard": True}
        return json.dumps(reply_markup)

    def main(self):
        last_update_id = None
        self.__init__()
#        super().__init__()
        while True:
            updates = self.get_updates(last_update_id)
            print("OK")
            if len(updates["result"]) > 0:
                last_update_id = self.get_last_update_id(updates) + 1
                self.handle_updates(updates)
            time.sleep(0.5)


if __name__ == '__main__':
        obj = TeleTradeBot()
        obj.main()

