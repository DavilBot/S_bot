import requests
import hashlib
import hmac
import time
import datetime
import pandas as pd
from operator import itemgetter
from json import JSONDecodeError


class BaseApi:
    def __init__(self, token="None", secret="None", symbol="ETCBTC"):
        self.token = token
        # self.api_secret_b = bytes(secret, 'utf-8')
        self.api_secret = secret
        self.base_url = "https://api.binance.com"
        self.headers = {'X-MBX-APIKEY': self.token,
                        }
        self.symbol = symbol

    def __repr__(self):
        return "BaseApi(token={}, secret={}".format(self.token, self.secret)

    def _get_answer(self, url="", headers=None, payload=None, method='get', **kwargs):
        print("url={} payload={} headers={}".format(url, payload, headers))
        if method == 'get':
            answer = requests.get(url, headers=headers, params=payload)
        else:
            answer = requests.post(url, data=payload, headers=headers)
        if answer.status_code != 200:
            print("Status", answer.status_code)
            print(answer.json())
            time.sleep(10)
            return self._get_answer(url, payload=payload, headers=headers, method=method)
        return answer

    def sign_payload(self, payload={}):
        payload['timestamp'] = self.get_timestamp()
        payload['recvWindow'] = 5000

        payload_list = self._order_params(payload)
        payload_str = ""
        for i, v in payload_list:
            payload_str += "&" + i + "=" + str(v)
        payload_str = payload_str[1:]
        # s = base64.b64encode(payload_json.encode('utf-8'))
        m = hmac.new(self.api_secret.encode('utf-8'), payload_str.encode('utf-8'), hashlib.sha256)
        m = m.hexdigest()
        payload_list.append(('signature', m))
        # payload['signature'] = m
        return payload_list

    def _order_params(self, data):
        """
            Convert params to list with signature as last element
            :param data:
            :return:
        """
        has_signature = False
        params = []
        for key, value in data.items():
            if key == 'signature':
                has_signature = True
            else:
                params.append((key, value))
        # sort parameters by key
        params.sort(key=itemgetter(0))
        if has_signature:
            params.append(('signature', data['signature']))
        return params

    def _print_time(self, tm):
        print(
            datetime.datetime.fromtimestamp(
                int(tm / 1000)
            ).strftime('%Y-%m-%d %H:%M:%S')
        )

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

    def get_candle(self, interval='5m', limit=55):
        url = self.base_url + "/api/v1/klines"
        url += "?symbol=" + self.symbol + "&interval=" + interval + "&limit=" + str(limit)
        answer = requests.get(url).json()
        opens, lows, highs, tsmp, closes, = [], [], [], [], []
        # for binance candle
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
        return df

    def get_timestamp(self):
        return int(time.time() * 1000)

    def get_balance(self):
        self.arrs = []
        url = self.base_url + '/api/v3/account'
        payload = self.sign_payload()
        return self._get_answer(url, payload=payload, headers=self.headers)

    def place_order(self, **kwargs):
        url = self.base_url + "/api/v3/order"
        # print(kwargs)
        # self.client_order_id = "myorder" + str(int(time.time()))
        # kwargs['newClientOrderId'] = self.client_order_id
        payload = self.sign_payload(kwargs)
        print("order ", payload)
        self.log.write("my payload {} \n".format(payload))
        answer = self._get_answer(url, payload=payload, headers=self.headers, method='post')
        self.order_id = answer.json()['orderId']
        return answer

    def get_last_orders(self):
        args = {}
        url = self.base_url + '/api/v3/allOrders'
        args['symbol'] = self.symbol
        payload = self.sign_payload(args)
        return self._get_answer(url, payload=payload, headers=self.headers)

    def get_trades(self, order_id=None):
        args = {}
        url = self.base_url + '/api/v3/myTrades'
        args['symbol'] = self.symbol
        if order_id is not None:
            args['fromId'] = order_id
        payload = self.sign_payload(args)
        return self._get_answer(url, payload=payload, headers=self.headers)

    def get_new_balance(self):
        args = {}
        if not self.order_id:
            print("don't know order_id")
            exit(-2)
        trades = self.get_trades().json()
        amount = 0
        if self.isBTC:
            sell_quantity = 0
            for trade in trades:
                if trade['orderId'] == self.order_id:
                    sell_quantity += float(trade['qty'])
                    amount += float(trade['price']) * float(trade['qty'])
            return amount, sell_quantity
        else:
            sell_btc = 0
            for trade in trades:
                if trade['orderId'] == self.order_id:
                    amount += float(trade['qty'])# / float(trade['price'])
                    sell_btc += float(trade['price']) * float(trade['qty'])
            return sell_btc, amount