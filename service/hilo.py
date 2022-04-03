import datetime
import functools
import time
import pandas as pd
import pandas_ta as ta
import time

import os
import sys
file_dir = os.path.dirname(os.path.realpath(__file__))
root_dir = os.path.abspath(file_dir + '/..')
sys.path.append(os.path.normpath(root_dir)) 

from dotenv import load_dotenv
from decimal import *
from pprint import pprint
from binance.futures import Futures  
from service.formula import FormulaService 

load_dotenv()

class HiLoService(object):

    def __init__(self, **kwargs):
        self.LEVERAGE = 10
        self.ALLOW_MONEY = 1500
        self.SYMBOL_COIN = 'ETHUSDT'
        self.RISK = 3
        self.REWARD = 7
        self.TIME_UNIT = 1
        self.TIME_SYMBOL = 'm'
        self.symbol = 'ETHUSDT' 
        self.book_orders = [] 
        self.base_url='https://testnet.binancefuture.com/' 
        self.client = Futures(
            key=os.environ.get('KEY_TESTNET_BINANCE'),
            secret=os.environ.get('SECRET_TESTNET_BINANCE'), 
            base_url=self.base_url)
        self.info = self.client.exchange_info() 
        self.change_margin_type()
        self.change_margin_leverage()

    def change_margin_leverage(self):
        self.client.change_leverage(symbol=self.SYMBOL_COIN,leverage= self.LEVERAGE, recvWindow=6000)

    def change_margin_type(self, _type='ISOLATED'):
        try:
            self.client.change_margin_type(self.SYMBOL_COIN,_type)
        except:
            assert('It has already been {}.'.format(_type))
            print('{} has already been {}.'.format(self.SYMBOL_COIN,_type))

    def is_can_next_order(self):
        left_orders = list(filter(lambda order: (order['type'] == 'STOP_MARKET' or order['type'] == 'TAKE_PROFIT_MARKET') and order['status'] == 'NEW' , self.client.get_all_orders(self.SYMBOL_COIN)))
        if len(left_orders) != 2:  
            if len(left_orders) == 0: return True 
            return True 
        else: return False
    
    
    def run_hilo(self, is_test=False): 
        i = 0 
        order_time = []
        while True: 
            i += 1 
            candle = list(map(self.handle_candle_data, self.client.klines(self.SYMBOL_COIN, '{}{}'.format(self.TIME_UNIT, self.TIME_SYMBOL), limit=31)))
            direction = FormulaService.formula(candle)
            if is_test: direction = 'BUY'
            last_price = float(Decimal(candle[-1]['close']))
            print("Time {} price {} direction {}".format(candle[-1]['close_time'], candle[-1]['close'], direction))
            
            if direction != '' and str(candle[-1]['close_time'])[:10] not in order_time: #and self.is_can_next_order(): 
                take_profit_price, stop_loss_price, reverse_direction = self.get_metric_to_order(direction, last_price)
                quantity = self.get_quantity_allow(last_price)
                orders = self.book_order(direction, reverse_direction, quantity, take_profit_price, stop_loss_price)
                self.book_orders.extend(orders)  
                print('orders',orders)
                order_time.append(str(datetime.datetime.fromtimestamp(orders[0]['updateTime']/1000))[:10])
                pprint({
                    "market_price":last_price,
                    "quantity":quantity, 
                    "take_profit_price": take_profit_price,
                    "stop_loss_price": stop_loss_price,
                    "direction":direction,
                    "balance": self.client.account()['availableBalance']
                }) 
            time.sleep(5)

    def book_order(self, direction, reverse_direction, quantity, take_profit_price, stop_loss_price):
        params = {
            'batchOrders': [
                {
                    'symbol': self.SYMBOL_COIN,
                    'side': direction,
                    'type': 'MARKET',
                    'quantity': str(quantity),
                },
                {
                    'symbol': self.SYMBOL_COIN,
                    'side': reverse_direction,
                    'type': 'STOP_MARKET',
                    'stopPrice': str(stop_loss_price),
                    'quantity': str(quantity), 
                    'timeInForce': 'GTE_GTC',
                    'reduceOnly': 'True'
                },
                {
                    'symbol': self.SYMBOL_COIN,
                    'side': reverse_direction,
                    'type': 'TAKE_PROFIT_MARKET',
                    'stopPrice': str(take_profit_price),
                    'quantity': str(quantity), 
                    'timeInForce': 'GTE_GTC',
                    'reduceOnly': 'True'
                }
            ]
        }

        orders = self.client.new_batch_order(**params) 
        return orders

    
    def get_precision(self, symbol, precision):
        if self.info == None: self.info = self.client.exchange_info()
        for x in self.info['symbols']:
            if x['symbol'] == symbol:
                return x[precision]


    def handle_candle_data(self, res):
        open_time = datetime.datetime.fromtimestamp(res[0]/1000)
        close_time = datetime.datetime.fromtimestamp(res[6]/1000)
        return {
            'open_time': open_time,
            'open': res[1],
            'high': res[2],
            'low': res[3],
            'close': res[4],
            'close_time': close_time
        }

    def get_quantity_allow(self, current_price):
        return round(self.ALLOW_MONEY / current_price, self.get_precision(self.SYMBOL_COIN, 'quantityPrecision'))

    def get_metric_to_order(self, direction, last_price):
        if direction == 'BUY':
            take_profit = round(last_price + last_price * (self.REWARD / 100) / self.LEVERAGE, self.get_precision(self.SYMBOL_COIN, 'pricePrecision'))
            stop_loss = round(last_price - last_price * (self.RISK / 100) / self.LEVERAGE, self.get_precision(self.SYMBOL_COIN, 'pricePrecision'))
            reverse_direction = 'SELL'
        else: 
            stop_loss = round(last_price + last_price * (self.RISK / 100) / self.LEVERAGE, self.get_precision(self.SYMBOL_COIN, 'pricePrecision'))
            take_profit = round(last_price - last_price * (self.REWARD / 100) / self.LEVERAGE, self.get_precision(self.SYMBOL_COIN, 'pricePrecision'))
            reverse_direction = 'BUY'
        return take_profit, stop_loss, reverse_direction

    