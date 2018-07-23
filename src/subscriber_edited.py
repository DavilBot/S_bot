import sys
import json
import requests
import time
import urllib
import os.path
import threading
import pandas as pid
import subprocess
import pika
TOKEN = "550693266:AAF7r6fsLpfhWRUyWH4te_IFY1IOFoQjRWs"
URL = "https://api.telegram.org/bot{}/".format(TOKEN)

class SubscriberBot():
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
            print(update["message"])
            if 'text' in update["message"]:
                text = update["message"]["text"]
            else:
                continue
            chat = update["message"]["chat"]["id"]
            list_bots = []
            data = {}
            tick = "False"
            if(os.path.isfile('data.json') and os.path.isfile('Ticker.txt')):
                with open('data.json', 'r') as fp:
                        data = json.load(fp)
                        if str(chat) in data:
                            list_bots = data[str(chat)]
                with open('Ticker.txt', 'r') as r:
                        tick = r.read()
            bots = [['cci', 'ppo', 'mfi'], ['macd', 'sma', 'aroon'], ['rsi', 'bollinger', 'b_indicator']]
            all_bots = ['cci', 'ppo', 'mfi', 'macd', 'sma', 'aroon', 'rsi', 'bollinger', 'b_indicator']
            if tick == "True" and text in list_bots and text in all_bots:
                self.send_message("You have already subscribed to this tradebot", chat)
                continue
            if tick == "False" and text not in list_bots and text in all_bots:
                self.send_message("You are not subscribed to this tradebot", chat)
                continue
            if text == "/start":
                self.send_message("Hello! Here you can subscribe on a single tradebot or all available and track the price.", chat)
            elif text == "/sub_all":
                data[str(chat)] = all_bots#list of all bots
                with open('data.json', 'w') as fp:
                    json.dump(data, fp)
                self.send_message("You subscribed to all tradebots", chat)
            elif text == "/unsub_all":
                data[str(chat)] = []
                with open('data.json', 'w') as fp:
                    json.dump(data, fp)
                self.send_message("You unsubscribed from all tradebots", chat)
            elif text == "/sub_par" or text == "/unsub_par":
                if text == "/sub_par":
                    tick = "True"
                else:
                    tick = "False"
                with open("Ticker.txt", "w") as tf:
                    tf.write(tick)
                keyboard = self.build_keyboard(bots)
                self.send_message("Choose bot", chat, keyboard)
            elif text in all_bots:
                self.add_del_bot(chat, text, tick, list_bots, data)
            else:
                self.send_message("Type '/' to view commands", chat)

    def add_del_bot(self, chat, text, tick, list_bots, data):
        message = ""
        if tick == "True":
            list_bots.append(text)
            message = "You have successfully subscribed"
        else:
            list_bots.remove(text)
            message = "You have successfully unsubscribed"
        data[str(chat)] = list_bots
        with open('data.json', 'w') as fp:
            json.dump(data, fp)
        self.send_message(message,chat)

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

    def bot_send_message(self, ch, method, properties, body):
        queue = json.loads(body)
        data = {}
        if os.path.isfile('data.json'):
             with open('data.json', 'r') as fp:
                 data = json.load(fp)
        for v in data:
            if queue["bot"] in data[v]:
                self.send_message(queue["bot"] + " " + queue["text"], int(v))
        print(body)
        ch.basic_ack(delivery_tag = method.delivery_tag)
    def channel(self):
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
        channel = connection.channel()
        channel.queue_declare(queue='hello')
        channel.basic_consume(self.bot_send_message, queue = 'hello')
        print('[*] Waiting for messages. To exit press CRTL + C')
        channel.start_consuming()

    def main(self):
        last_update_id = None
        self.__init__()
        threads = threading.Thread(target=self.channel, args=())
        threads.daemon = True
        threads.start()
        while True:
            updates = self.get_updates(last_update_id)
            print(updates)
            if "result" in updates:
                if len(updates["result"]) > 0:
                    last_update_id = self.get_last_update_id(updates) + 1
                    self.handle_updates(updates)
                time.sleep(0.5)


if __name__ == '__main__':
        obj = SubscriberBot()
        obj.main()

