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

from binance.futures import Futures 
from pprint import pprint
from decimal import *
from service.formula import FormulaService

class UtilService(object):

    def __init__(self):
        self.client = Futures(
            key=os.environ.get('KEY_TESTNET_BINANCE'),
            secret=os.environ.get('SECRET_TESTNET_BINANCE'))
        self.info = None

    def compare_time(self, date_time_1, date_time_2): 
        return (date_time_1-date_time_2).total_seconds() / 60

    def mapCandleData(self, res):
        open_time = datetime.datetime.fromtimestamp(res[0]/1000)
        return {
            'open_time': open_time,
            'open': float(Decimal(res[1])),
            'high': float(Decimal(res[2])),
            'low': float(Decimal(res[3])),
            'close': float(Decimal(res[4])),
        }

    def get_value(self, old_price, new_price, quantity):  
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

    def get_fee(self, current_price, quantity, fee_rate=0.0004):
        return quantity * current_price * fee_rate

    def finish_order(self, open_time, current_time, high, low, last_price, balance, order):
        take_profit = order['take_profit']
        stop_loss = order['stop_loss']
        quantity = order['quantity']
        leverage = order['leverage'] 
        entry = order['entry']

        if(self.is_take_profit(high, low, take_profit)):
            balance += self.get_value(entry, take_profit, quantity) - 2*self.get_fee(last_price, quantity)
            order['balance_finish'] = balance
            order['value (+fee)'] = self.get_value(entry, take_profit, quantity) - 2*self.get_fee(last_price, quantity)
            order['is_finish'] = True
            order['close_time'] = str(current_time)
            order['keep (min)'] =  self.compare_time(current_time, open_time)
            order['type'] = 'TAKE_PROFIT'

        elif(self.is_stop_loss(high, low, stop_loss)): 
            balance -= (self.get_value(entry, stop_loss, quantity) + 2*self.get_fee(last_price, quantity))
            order['balance_finish'] = balance
            order['value (+fee)'] = -1 * (self.get_value(entry, stop_loss, quantity) + 2*self.get_fee(last_price, quantity))
            order['is_finish'] = True 
            order['close_time'] = str(current_time)
            order['keep (min)'] =  self.compare_time(current_time, open_time)
            order['type'] = 'STOP_LOSS'
                
        return balance

    def get_precision(self, symbol, precision):
        if self.info == None: 
            self.info = self.client.exchange_info()
        for x in self.info['symbols']:
            if x['symbol'] == symbol:
                return x[precision]

    def get_quantity_allow(self, allow_money, current_price, leverage, symbol):
        return round(allow_money * leverage / current_price, self.get_precision(symbol, 'quantityPrecision'))
    
    def get_reverse_direction(self, direction):
        if direction == 'BUY': return 'SELL'
        return 'BUY'

    def run_report(self, symbol, mark_klines, balance, allow_money, leverage, limit = 31, risk=2, reward=8):
        take_profit = 0
        stop_loss = 0
        end = 41
        book_order = {}
        count_win = 0
        count_lose = 0
        count_draw = 0

        for i in range(0, limit - end):
            is_can_next_order = True
            candle = list(map(self.mapCandleData, self.get_candle(mark_klines, i, end + i)))
            direction = FormulaService.formula(candle)
            last_price = candle[-1]['close']
            # if balance < leverage * last_price: 
            #     print('Balance is insufficient. Balance: {}'.format(balance))
            #     assert('Balance is insufficient. Balance: {}'.format(balance))
            #     return None, None, None
            current_order = None
            current_book_time = None
            for book_time, order in book_order.items():
                if order['is_finish'] == False: 
                    balance = self.finish_order(book_time, candle[-1]['open_time'], candle[-1]['high'], candle[-1]['low'], candle[-1]['close'], balance, order)
                    if order['type'] == 'TAKE_PROFIT': count_win += 1
                    if order['type'] == 'STOP_LOSS': count_lose += 1
                    if order['is_finish'] == False: 
                        current_order = order
                        current_book_time = book_time
                        is_can_next_order = False                    
            if current_book_time != None and current_order != None and is_can_next_order == False and self.get_reverse_direction(current_order['direction']) == direction:
                book_order[current_book_time]['is_finish'] = 'NONE' 
                book_order[current_book_time]['type'] = 'CHANGE_DIRECTION' 
                book_order[current_book_time]['value (+fee)'] = round(book_order[current_book_time]['fee'], self.get_precision(symbol, 'pricePrecision'))
                book_order[current_book_time]['balance_finish'] -= round(book_order[current_book_time]['fee'], self.get_precision(symbol, 'pricePrecision'))
                balance -= book_order[current_book_time]['fee']
                count_draw += 1
                is_can_next_order = True

            if direction != '' and is_can_next_order: 
                entry = last_price
                if direction == 'BUY':
                    take_profit = round(last_price + last_price * (reward / 100) / leverage, self.get_precision(symbol, 'pricePrecision'))
                    stop_loss = round(last_price - last_price * (risk / 100) / leverage, self.get_precision(symbol, 'pricePrecision'))
                else: 
                    stop_loss = round(last_price + last_price * (risk / 100) / leverage, self.get_precision(symbol, 'pricePrecision'))
                    take_profit = round(last_price - last_price * (reward / 100) / leverage, self.get_precision(symbol, 'pricePrecision'))

                quantity = self.get_quantity_allow(allow_money, last_price, leverage, symbol)
                quantity_not_leverage = round(quantity / leverage, self.get_precision(symbol, 'quantityPrecision'))
                if balance <= allow_money: 
                    balance += allow_money
                    return book_order, balance, count_win, count_lose
                book_order[candle[-1]['open_time']] = {
                    # 'close_time': '',
                    'keep (min)': '',
                    # 'open': candle[-1]['open'],
                    # 'close': candle[-1]['close'],
                    # 'high': candle[-1]['high'],
                    # 'low': candle[-1]['low'],
                    'balance': balance,
                    'type': '',
                    'balance_finish': balance,
                    'value (+fee)': 0,
                    'allow_money': allow_money,
                    'direction': direction,
                    'entry': last_price,
                    'quantity': quantity,
                    'quantity_real': quantity_not_leverage,
                    'leverage': leverage,
                    'fee': self.get_fee(last_price, quantity),
                    'take_profit': take_profit,
                    'stop_loss': stop_loss,
                    'is_finish': False,
                } 
        return book_order, balance, count_win, count_lose, count_draw

    def export_csv_order(self, path, book_order):
        df = pd.DataFrame(book_order)
        df = df.transpose()
        df.to_csv(path)