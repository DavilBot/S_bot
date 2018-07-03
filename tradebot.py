import sys
import json
import requests
import time
import urllib
import os.path
from binance_api import TradeBot
import threading
TOKEN = "601740536:AAEvvbFvz94qWhVbHjxRq0ZV6w1k__g7hJU"
URL = "https://api.telegram.org/bot{}/".format(TOKEN)

class TeleTradeBot(TradeBot):
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
    def new_handle(self, updates):
        for update in updates["result"]:
            self.chat = update["message"]["chat"]["id"]
            text = update["message"]["text"]
            if text == "/init" and self.ticker == "true":
                thread = threading.Thread(target=super().trade_on)
                thread.daemon = True
                thread.start()
                self.event.set()
                self.send_message("You initialized tradebot!",self.chat)
#                thread_two = threading.Thread(target=self.send_loop_message(chat))
#                thread_two.daemon = True
#                thread_two.start()
            elif text == "/stop" and self.ticker == "true":
                self.event.clear()
                self.send_message("You stopped a tradebot.", self.chat)
    def handle_updates(self, updates):
        for update in updates["result"]:
            text = update["message"]["text"]
            chat = update["message"]["chat"]["id"]
            list_names = []
            self.ticker = "false"
            data = {}
            data['users'] = []
            names = {}
            names['names'] = []
            curr_pass = ""
            name_prev = ""
            if(os.path.isfile('data.txt') and os.path.isfile('names.txt')):
                with open('names.txt') as json_file:
                    names = json.load(json_file)
                    for n in names['names']:
                        if n['chat'] == chat:
                            name_prev = n['name']
                with open('data.txt') as json_file:
                    data = json.load(json_file)
                    for p in data['users']:
                        list_names.append(p['name'])
                        if p['name'] == name_prev:
                            curr_pass = p['password']
                            self.ticker = p['ticker']
            if text == "/start" and self.ticker == "false":
                keyboard = self.build_keyboard(list_names)#items
                self.send_message("Select user", chat, keyboard)
            elif text == "/help":
                self.send_message("type '/start' if you want to login"+"\n"+
                             "remember, you can't log in from the same account to several users and to users that are active now from another account" + "\n"+
                         "type '/logout' if you want to logout and if your '/start' is not working" + "\n"+
                         "type '/balance' to get current balance(can be achieved only if you logged in)" + "\n"+
                         "type '/init' to start the tradebot(can be achieved only if you logged in)" + "\n" +
                         "type '/stop' to stop tradebot running (can be achieved only if you logged in)",chat)
            elif self.ticker == "true" and text == "/balance":
                self.send_message("Your balance is (btc_amount) {}, (coin_amount) {}.".format(self.btc_amount, self.coin_amount), chat)
            elif text == "/logout" and self.ticker == "true":
                with open('data.txt') as json_file:
                    data = json.load(json_file)
                    for p in data['users']:
                        if p['name'] == name_prev:
                            p['ticker'] = "false"
                with open('data.txt','w') as outfile:
                    json.dump(data, outfile)
                with open('names.txt') as json_file:
                    names = json.load(json_file)
                    for n in names['names']:
                        if n['name'] == name_prev:
                            n['chat'] = "000"
                with open('names.txt', 'w') as outfile:
                    json.dump(names, outfile)
                self.send_message("You have successfully logged out", chat)
            elif text in list_names:
                string = ''
                with open('data.txt') as json_file:
                    data = json.load(json_file)
                    for p in data['users']:
                        if p['name']==text and p['ticker']=="true":
                            string = "This username is busy now"
                            continue
                    if string == "":
                        with open('names.txt') as json_file:
                            names = json.load(json_file)
                            for n in names['names']:
                                if n['name']==text:
                                    n['chat'] = chat
                        with open('names.txt', 'w') as outfile:
                            json.dump(names, outfile)
                        string = "Now, please, type password"
                    self.send_message(string, chat)
            elif text == curr_pass:
                with open('data.txt') as json_file:
                    data = json.load(json_file)
                    for p in data['users']:
                        if p['name'] == name_prev:
                            p['ticker'] = "true"
                with open('data.txt','w') as outfile:
                    json.dump(data, outfile)
                self.send_message("Now you can trade with bot", chat)
            elif text == "/init" or text == "/stop":
                continue
            else:
                self.send_message("Type '/help' to see all available commands",chat)

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
        super().__init__()
        while True:
            updates = self.get_updates(last_update_id)
            if len(updates["result"]) > 0:
                last_update_id = self.get_last_update_id(updates) + 1
                self.handle_updates(updates)
                self.new_handle(updates)
            time.sleep(0.5)


if __name__ == '__main__':
        obj = TeleTradeBot()
        obj.main()

