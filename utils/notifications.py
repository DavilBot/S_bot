import sys
import time
import telepot
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
from time import gmtime, strftime, sleep
from pprint import pprint

class Notifications:

    def __init__(self):
        self.userDict = self.initDict()
        print(self.userDict)
        # isLogging = 1
        TOKEN = "569637100:AAGxA9yB0Ep4iHEuW1nm50pZBwa0rQn68fo"
        self.bot = telepot.Bot(TOKEN)
        MessageLoop(self.bot, {'chat': self.onChatMessage,
                          'callback_query': self.onCallbackQuery
                          }).run_as_thread()
        print("LogBot initialized")
        # while 1:
        #     sendLogMsg("log")
        #     sleep(1)



    def onChatMessage(self, msg):
        # global userDict
        contentType, chatType, chatID = telepot.glance(msg)
        if contentType == "text":
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Start Logging", callback_data="start")],
                [InlineKeyboardButton(text="Stop Logging", callback_data="stop")],
            ])
            if msg["text"] == "/options":
                self.bot.sendMessage(chatID, "Options:", reply_markup=keyboard)
            elif msg["text"] == "/start":
                if str(msg["from"]["id"]) in self.userDict:
                    self.bot.sendMessage(chatID, "You are already registered")
                    self.bot.sendMessage(chatID, "Options:", reply_markup=keyboard)
                else:
                    self.userDict[str(msg["from"]["id"])] = '0'
                    self.bot.sendMessage(chatID, "Options:", reply_markup=keyboard)
                    file = open("users.txt", "a")
                    file.write(str('\n' + str(msg["from"]["id"]) + ' ' + '0'))
            else:
                self.bot.sendMessage(chatID, "/options")


    def onCallbackQuery(self, msg):
        # global userDict
        queryID, fromID, queryData = telepot.glance(msg, flavor="callback_query")
        print("Callback query:", queryID, fromID, msg["from"]["first_name"] + ' ' + queryData)
        if str(msg["from"]["id"]) in self.userDict:
            if queryData == "start":
                self.bot.answerCallbackQuery(queryID, text="Logging is active")
                self.userDict[msg["from"]["id"]] = '1'
            elif queryData == "stop":
                self.bot.answerCallbackQuery(queryID, text="Logging is inactive")
                self.userDict[msg["from"]["id"]] = '0'
        else:
            self.bot.answerCallbackQuery(queryID, text="use /start")


    def sendLogMsg(self, message):
        # global userDict
        for key, value in self.userDict.items():
            if value == '1':
                self.bot.sendMessage(key, str(message))


    def initDict(self):
        users = dict()
        file = open("users.txt", "r")
        tempList = file.read().split('\n')
        for el in tempList:
            if el:
                tt = el.split(' ')
                users[tt[0]] = tt[1]
        print(users)
        file.close()
        return users





