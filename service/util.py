import datetime
import functools
import time
import pandas as pd
import pandas_ta as ta

import os
import sys
file_dir = os.path.dirname(os.path.realpath(__file__))
root_dir = os.path.abspath(file_dir + '/..')
sys.path.append(os.path.normpath(root_dir)) 

from pprint import pprint
from decimal import *
from service.formula import FormulaService

class UtilService(object):

    def mapCandleData(self, res):
        open_time = datetime.datetime.fromtimestamp(res[0]/1000)
        return {
            'open_time': open_time,
            'open': float(Decimal(res[1])),
            'high': float(Decimal(res[2])),
            'low': float(Decimal(res[3])),
            'close': float(Decimal(res[4])),
        }

    def get_value(self, old_price, new_price, leverage, quantity): 
        quantity = quantity * leverage
        total_old_price = quantity * old_price 
        total_new_price = quantity * new_price 
        return abs(total_new_price - total_old_price)

    def get_candle(self, response, start, end):
        return response[start:end]

    def is_take_profit(self, high_price, low_price, take_profit_price):
        if take_profit_price and take_profit_price != 0 and high_price >= take_profit_price: return True
        return False

    def is_stop_loss(self, high_price, low_price, stop_loss_price):
        if stop_loss_price and stop_loss_price != 0 and low_price <= stop_loss_price: return True
        return False

    def get_fee(self, current_price, quantity, leverage, side="maker"):
        if side == "taker" : fee_rate=0.0002
        elif side == "maker" : fee_rate=0.0004
        return quantity * leverage * current_price * fee_rate

    def finish_order(self, high, low, last_price, balance, order):
        take_profit = order['take_profit']
        stop_loss = order['stop_loss']
        quantity = order['quantity']
        leverage = order['leverage'] 
        entry = order['entry']

        if(self.is_take_profit(high, low, take_profit)): 
            # print("=== Take profit")
            # pprint({
            #     "init":round(balance, 2), 
            #     "after":round(balance + self.get_value(entry, take_profit, leverage, quantity) + self.get_fee(last_price, quantity, leverage,side="taker"),2), 
            #     "entry":entry, 
            #     "take_profit":take_profit,
            #     "fee":self.get_fee(last_price, quantity, leverage,side="taker"),
            #     "value":round(self.get_value(entry, take_profit, leverage, quantity), 2)
            # }) 
            balance += self.get_value(entry, take_profit, leverage, quantity) - self.get_fee(last_price, quantity, leverage,side="taker")
            order['balance_finish'] = balance
            order['value'] = self.get_value(entry, take_profit, leverage, quantity) - self.get_fee(last_price, quantity, leverage,side="taker")
            order['is_finish'] = True
            order['type'] = 'TAKE_PROFIT'

        elif(self.is_stop_loss(high, low, stop_loss)): 
            # print("=== Stop loss")
            # pprint({
            #     "init":round(balance, 2), 
            #     "after":round(balance - self.get_value(entry, stop_loss, leverage, quantity) + self.get_fee(last_price, quantity, leverage,side="taker"), 2), 
            #     "entry":entry, 
            #     "stop_loss": stop_loss, 
            #     "fee": self.get_fee(last_price, quantity, leverage,side="taker"),
            #     "value": round(self.get_value(entry, stop_loss, leverage, quantity), 2)
            # })
            balance -= self.get_value(entry, stop_loss, leverage, quantity) + self.get_fee(last_price, quantity, leverage,side="taker")
            order['balance_finish'] = balance
            order['value'] = self.get_value(entry, stop_loss, leverage, quantity) + self.get_fee(last_price, quantity, leverage,side="taker")
            order['is_finish'] = True 
            order['type'] = 'STOP_LOSS'
               
        # if order['is_finish']: 
        #     pprint(order)
        #     print("\n========\n")
        
        return balance

    def run_report(self, mark_klines, balance, quantity, leverage, limit = 31):
        take_profit = 0
        stop_loss = 0
        end = 31
        book_order = {}
        count_win = 0
        count_lose = 0

        for i in range(0, limit - 30):
            candle = list(map(self.mapCandleData, self.get_candle(mark_klines, i, end + i)))
            direction = FormulaService.formula_1(candle)
            last_price = candle[-1]['close']
            if balance < quantity * leverage * last_price: 
                print('Balance is insufficient. Balance: {}'.format(balance))
                assert('Balance is insufficient. Balance: {}'.format(balance))
                return

            for book_time, order in book_order.items():
                if order['is_finish'] == False: 
                    balance = self.finish_order(candle[-1]['high'], candle[-1]['low'], candle[-1]['close'], balance, order)
                    if order['type'] == 'TAKE_PROFIT': count_win += 1
                    if order['type'] == 'STOP_LOSS': count_lose += 1
                
            if direction != 'NOT': 
                entry = last_price
                if direction == 'BUY':
                    take_profit = round(last_price + last_price * 0.08 / 20, 2)
                    stop_loss = round(last_price - last_price * 0.02 / 20, 2)
                else: 
                    stop_loss = round(last_price + last_price * 0.02 / 20, 2)
                    take_profit = round(last_price - last_price * 0.08 / 20, 2)
                balance -= self.get_fee(last_price, quantity, leverage,side="maker")
                # print("== Make order")
                # pprint({
                #     "balance": round(balance, 2),
                #     "entry": entry,
                #     "take_profit": take_profit,
                #     "stop_loss": stop_loss,
                #     "direction": direction,
                #     "fee": round(self.get_fee(last_price, quantity, leverage,side="maker"),2),
                # })

                book_order[candle[-1]['open_time']] = {
                    'balance': balance,
                    'balance_finish': balance,
                    'value': 0,
                    'direction': direction,
                    'entry': last_price,
                    'quantity': quantity,
                    'leverage': leverage,
                    'fee': round(self.get_fee(last_price, quantity, leverage,side="maker"),2),
                    'take_profit': take_profit,
                    'stop_loss': stop_loss,
                    'type': '',
                    'is_finish': False,
                }
                # print('Make order')
                # pprint(book_order[candle[-1]['open_time']])
        return book_order, balance, count_win, count_lose

    def export_csv_order(self, path, book_order):
        df = pd.DataFrame(book_order)
        df = df.transpose()
        df.to_csv(path)