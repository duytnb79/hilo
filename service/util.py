import datetime
import functools
import pandas as pd
import time
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
        return {
            'open_time': datetime.datetime.fromtimestamp(res[0]/1000),
            'open': res[1],
            'high': res[2],
            'low': res[3],
            'close': res[4],
        }

    def get_value(self, old_price, new_price, multiple, volume): 
        total_volume = volume * multiple
        total_old_price = total_volume * old_price 
        total_new_price = total_volume * new_price 
        return abs(total_new_price - total_old_price)

    def get_candle(self, response, start, end):
        return response[start:end]

    def is_take_profit(self, current_price, take_profit_price):
        if take_profit_price and take_profit_price != 0 and current_price >= take_profit_price: return True
        return False

    def is_stop_loss(self, current_price, stop_loss_price):
        if stop_loss_price and stop_loss_price != 0 and current_price <= stop_loss_price: return True
        return False

    def get_fee(self, current_price, volume, multiple, side="maker"):
        if side == "taker" : fee_rate=0.0002
        elif side == "maker" : fee_rate=0.0004
        return volume * multiple * current_price * fee_rate

    def run_report(self, mark_klines, balance, volume, multiple, limit = 54):
        take_profit = 0
        stop_loss = 0
        end = 31
        from pprint import pprint
        for i in range(0, limit - 31 - 1):
            candle = list(map(self.mapCandleData, self.get_candle(mark_klines, i, end + i)))
            df = pd.DataFrame(candle)
            direction = FormulaService.formula_1(df)
            last_price = float(Decimal(df.iloc[-1]['close']))
            if balance < volume * multiple * last_price: 
                print('Balance is insufficient. Balance: {}'.format(balance))
                assert('Balance is insufficient. Balance: {}'.format(balance))
                return

            if(self.is_take_profit(last_price, take_profit)): 
                print("=== Take profit")
                pprint({
                    "init":round(balance, 2), 
                    "after":round(balance + self.get_value(entry, take_profit, multiple, volume) + self.get_fee(last_price, volume, multiple,side="taker"),2), 
                    "entry":entry, 
                    "take_profit":take_profit,
                    "fee":self.get_fee(last_price, volume, multiple,side="taker"),
                    "value":round(self.get_value(entry, take_profit, multiple, volume), 2)
                })
                print("\n========\n")
                balance += self.get_value(entry, take_profit, multiple, volume) - self.get_fee(last_price, volume, multiple,side="taker")
                take_profit = 0
                stop_loss = 0
            if(self.is_stop_loss(last_price, stop_loss)): 
                print("=== Stop loss")
                pprint({
                    "init":round(balance, 2), 
                    "after":round(balance - self.get_value(entry, stop_loss, multiple, volume) + self.get_fee(last_price, volume, multiple,side="taker"), 2), 
                    "entry":entry, 
                    "stop_loss": stop_loss, 
                    "fee": self.get_fee(last_price, volume, multiple,side="taker"),
                    "value": round(self.get_value(entry, stop_loss, multiple, volume), 2)
                })
                print("\n========\n")
                balance -= self.get_value(entry, stop_loss, multiple, volume) + self.get_fee(last_price, volume, multiple,side="taker")
                stop_loss = 0
                take_profit = 0

            if direction != 'NOT': 
                entry = last_price
                if direction == 'LONG':
                    take_profit = round(last_price + last_price * 0.08 / 20, 2)
                    stop_loss = round(last_price - last_price * 0.02 / 20, 2)
                else: 
                    stop_loss = round(last_price + last_price * 0.02 / 20, 2)
                    take_profit = round(last_price - last_price * 0.08 / 20, 2)
                balance -= self.get_fee(last_price, volume, multiple,side="maker")
                print("== Make order")
                pprint({
                    "balance": round(balance, 2),
                    "entry": entry,
                    "take_profit": take_profit,
                    "stop_loss": stop_loss,
                    "direction": direction,
                    "fee": round(self.get_fee(last_price, volume, multiple,side="maker"),2),
                })
