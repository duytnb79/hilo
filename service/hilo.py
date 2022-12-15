import datetime
import functools
import time
import pandas as pd
import pandas_ta as ta
import time
import asyncio
import os
import sys

file_dir = os.path.dirname(os.path.realpath(__file__))
root_dir = os.path.abspath(file_dir + '/..')
sys.path.append(os.path.normpath(root_dir)) 

from playsound import playsound
from dotenv import load_dotenv
from decimal import *
from pprint import pprint
from binance.futures import Futures  
from service.formula import FormulaService 
from binance.enums import KLINE_INTERVAL_1MINUTE

load_dotenv()

class HiLoService(object):

    def __init__(self, is_test=True,**kwargs):
        self.LEVERAGE = 10
        self.ALLOW_MONEY = 5
        self.SYMBOL_COIN = 'DOGEUSDT'
        self.RISK = 5
        self.REWARD = 6
        self.TIME_UNIT = 1
        self.TIME_SYMBOL = 'm'
        self.book_orders = [] 
        self.base_url='https://testnet.binancefuture.com/' 
        self.is_test = is_test
        self.is_has_order_long = False
        self.is_has_order_short = False
        if self.is_test:
            self.client = Futures(
                key= os.environ.get('KEY_TESTNET_BINANCE'),
                secret= os.environ.get('SECRET_TESTNET_BINANCE'),
                base_url=self.base_url)
        else: 
            self.client = Futures(
                key=os.environ.get('KEY_BINANCE'),
                secret=os.environ.get('SECRET_BINANCE'))
        self.info = self.client.exchange_info()
        self.change_margin_type()
        self.change_margin_leverage()

    def change_margin_leverage(self):
        self.client.change_leverage(symbol=self.SYMBOL_COIN,leverage= self.LEVERAGE, recvWindow=6000)

    def check_has_open_orders(self):
        orders =self.client.get_orders()
        if len(orders) != 0: return True
        return False

    def change_margin_type(self, _type='ISOLATED'):
        try:
            self.client.change_margin_type(self.SYMBOL_COIN,_type)
        except:
            assert('It has already been {}.'.format(_type))
            print('{} has already been {}.'.format(self.SYMBOL_COIN,_type))

    def is_can_next_order(self):
        left_orders = list(filter(lambda order: (order['type'] == 'STOP_MARKET' or order['type'] == 'TAKE_PROFIT_MARKET') and order['status'] == 'NEW' , self.client.get_all_orders(self.SYMBOL_COIN)))
        if len(left_orders) > 0:  
            return False
        else: return True
    
    def stop_order_error(self, orders):
        for order in orders:
            if 'orderId' in order.keys() and order['type'] != 'MARKET':
                print('cancel', order['orderId']) 
                try: 
                    self.client.cancel_order(self.SYMBOL_COIN, order['orderId'])
                except:
                    print('err cancel', order)

    def handle_stop_market_order(self, reverse_direction, quantity):
        print('handle_stop_market_order', reverse_direction, quantity)
        order = self.client.new_order(**{
            'symbol': self.SYMBOL_COIN,
            'side': reverse_direction,
            'type': 'MARKET',
            'quantity': str(quantity), 
        })

    def is_correct_condition(self, direction, order_type, last_price, stop_price):
        if order_type == 'STOP' or order_type == 'STOP_MARKET':
            if direction == 'BUY': return last_price >= stop_price
            if direction == 'SELL': return last_price <= stop_price
        if order_type == 'TAKE_PROFIT' or order_type == 'TAKE_PROFIT_MARKET':
            if direction == 'BUY': return last_price <= stop_price
            if direction == 'SELL': return last_price >= stop_price
        print('aa', direction, order_type, last_price, stop_price)
        return False

    def diff_minute(self, date_time_1, date_time_2):
        return (datetime.datetime.strptime(date_time_2, "%Y-%m-%d %H:%M:%S.%f") - datetime.datetime.strptime(date_time_1, "%Y-%m-%d %H:%M:%S.%f")).seconds / 60 / 1000

    async def run_hilo(self):   
        i = 0 
        current_order_price = 0
        current_order_direction = ''
        order_time = []
        is_first = True
        while True: 
            i += 1 
            candle = list(map(self.handle_candle_data, self.client.klines(self.SYMBOL_COIN, '{}{}'.format(self.TIME_UNIT, self.TIME_SYMBOL), limit=41)))
            direction = FormulaService.formula(candle)
            # last_price = float(Decimal(candle[-1]['close'])) 
            print('last_price',candle[-1])
            
            # if self.is_test: 
            #     last_price *= ratio_last_price[i]
            #     if is_first: 
            #         direction = 'BUY'
            #         is_first = False 

            # range_time_in_order = 2 # minutes
           
            # is_not_dupplicate_order_in_time = len(order_time) == 0 or (len(order_time) != 0 and self.diff_minute(order_time[-1], str(candle[-1]['close_time'])) >= range_time_in_order)
            # # print('is_not_dupplicate_order_in_time',is_not_dupplicate_order_in_time)
            # # print('self.is_can_next_order()',self.is_can_next_order())
            # print("Time {} {} - {} direction {} - {}:{}".format(candle[-1]['close_time'], self.SYMBOL_COIN, last_price, direction,  current_order_direction, current_order_price))
            # # print('is_not_dupplicate_order_in_time',is_not_dupplicate_order_in_time, )
            # if not self.is_can_next_order() and is_not_dupplicate_order_in_time:
            #     # đã vào lệnh, nhưng sideway đổi hướng
            #     # thì hủy lệnh đang có
            #     # nếu đang long mà giá thấp hơn sẽ chuyển thành short
            #     # nếu đang short mà giá cao hơn sẽ chuyển thành long
                
            #     if self.is_has_order_long and ((current_order_price != 0 and current_order_price > last_price * 0.02) or direction == 'SELL'):
            #         print('CHANGE DIRECTION (SIDE WAY). LONG -> SHORT')
            #         if self.market_order:
            #             reverse_direction = self.get_reverse_direction(self.market_order['side'])
            #             self.handle_stop_market_order(reverse_direction, self.market_order['origQty'])
            #         self.is_has_order_long = False
            #         direction = reverse_direction
            #         time.sleep(2)

            #     if self.is_has_order_short and ((current_order_price != 0 and current_order_price < last_price * 0.02) or direction == 'BUY'):
            #         print('CHANGE DIRECTION (SIDE WAY). SHORT -> LONG')
            #         if self.market_order:
            #             reverse_direction = self.get_reverse_direction(self.market_order['side'])
            #             self.handle_stop_market_order(reverse_direction, self.market_order['origQty'])
            #         self.is_has_order_short = False 
            #         direction = reverse_direction
            #         time.sleep(2) 
                
            # if direction != '' and is_not_dupplicate_order_in_time and self.is_can_next_order(): 
            #     # chưa vào lệnh
            #     take_profit_price, stop_loss_price, reverse_direction = self.get_metric_to_order(direction, last_price)

            #     is_correct_take_profit_order = self.is_correct_condition(direction, 'TAKE_PROFIT_MARKET', last_price, take_profit_price)
            #     is_correct_stop_loss_order = self.is_correct_condition(direction, 'STOP_MARKET', last_price, stop_loss_price)
            #     pprint({
            #         'take_profit_price':take_profit_price, 
            #         'stop_loss_price':stop_loss_price, 
            #         'last_price':last_price, 
            #         'is_correct_take_profit_order':is_correct_take_profit_order,
            #         'is_correct_stop_loss_order': is_correct_stop_loss_order
            #     })
            #     if take_profit_price == None or not is_correct_stop_loss_order or not is_correct_stop_loss_order: continue
            #     quantity = self.get_quantity_allow(last_price)
            #     orders = self.book_order(direction, reverse_direction, quantity, take_profit_price, stop_loss_price)
            #     self.book_orders.extend(orders)  
            #     print('orders',orders)
            #     order_time.append(str(candle[-1]['close_time']))
            #     market_order = None
            #     try:
            #         _temp = list(filter(lambda x: 'origType' in x and x['origType'] == 'MARKET', orders))
            #         market_order = _temp[0] if len(_temp) != 0 else None 
            #         _temp = list(filter(lambda x: 'origType' in x and x['origType'] == 'STOP_MARKET', orders))
            #         stop_market_order = _temp[0] if len(_temp) != 0 else None
            #         _temp = list(filter(lambda x: 'origType' in x and x['origType'] == 'TAKE_PROFIT_MARKET', orders))
            #         take_profit_order = _temp[0] if len(_temp) != 0 else None

                    
            #         if market_order == None or stop_market_order == None or take_profit_order == None:
            #             if market_order != None: self.handle_stop_market_order(reverse_direction, quantity)
            #             # self.stop_order_error(orders)
            #             # assert('Error order')
            #             # print('Error order')
            #             # return
            #         else: 
            #             self.market_order = self.client.query_order(symbol=self.SYMBOL_COIN, orderId=market_order['orderId'])
            #             if self.market_order['side'] == 'BUY': self.is_has_order_long = True
            #             if self.market_order['side'] == 'SELL': self.is_has_order_short = True

            #             current_order_price = round(float(Decimal(self.market_order['avgPrice'])), self.get_precision(self.SYMBOL_COIN, 'pricePrecision'))
            #             current_order_direction = direction
            #             print('current_order_price',current_order_price)
            #     except:
            #         if market_order != None: self.handle_stop_market_order(reverse_direction, quantity)
            #         self.stop_order_error(orders)
            #         assert('Error order')
            #         print('Error order')
            #         return
            #     save_order = { 
            #         "market_order_id": market_order['orderId'],
            #         "stop_market_order_id": stop_market_order['orderId'],
            #         "take_profit_order_id": take_profit_order['orderId'],
            #         "symbol": self.SYMBOL_COIN,
            #         "entry":last_price,
            #         "quantity":quantity, 
            #         "take_profit_price": take_profit_price,
            #         "stop_loss_price": stop_loss_price,
            #         "direction":direction,
            #         "balance": self.client.account()['availableBalance']
            #     }
            #     self.save_new_order(save_order, str(candle[-1]['close_time']))
            # await asyncio.sleep(5)

    
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
                    'reduceOnly': 'True',
                    'workingType':"MARK_PRICE"
                },
                {
                    'symbol': self.SYMBOL_COIN,
                    'side': reverse_direction,
                    'type': 'TAKE_PROFIT_MARKET',
                    'stopPrice': str(take_profit_price),
                    'quantity': str(quantity), 
                    'timeInForce': 'GTE_GTC',
                    'reduceOnly': 'True',
                    'workingType':"MARK_PRICE"
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

    def get_reverse_direction(self, direction):
        if direction == 'BUY': return 'SELL'
        return 'BUY'

    def get_quantity_allow(self, current_price):
        return round(self.ALLOW_MONEY / current_price * self.LEVERAGE, self.get_precision(self.SYMBOL_COIN, 'quantityPrecision'))

    def get_metric_to_order(self, direction, last_price):
        if (self.is_has_order_long and direction == 'SELL') or (self.is_has_order_short and direction == 'BUY'): 
            if self.check_has_open_orders():
                if self.is_has_order_long and direction == 'SELL':
                    print('There\'s order long so end long position to short')
                    if self.market_order:
                        reverse_direction = self.get_reverse_direction(self.market_order['side'])
                        self.handle_stop_market_order(reverse_direction, self.market_order['origQty'])
                    self.is_has_order_long = False
                    time.sleep(2)

                if self.is_has_order_short and direction == 'BUY':
                    print('There\'s order short so end short position to long')
                    if self.market_order:
                        reverse_direction = self.get_reverse_direction(self.market_order['side'])
                        self.handle_stop_market_order(reverse_direction, self.market_order['origQty'])
                    self.is_has_order_short = False 
                    time.sleep(2)

        if direction == 'BUY' and self.is_has_order_long == False:
            take_profit = round(last_price + last_price * (self.REWARD / 100) / self.LEVERAGE, self.get_precision(self.SYMBOL_COIN, 'pricePrecision'))
            stop_loss = round(last_price - last_price * (self.RISK / 100) / self.LEVERAGE, self.get_precision(self.SYMBOL_COIN, 'pricePrecision'))
            reverse_direction = 'SELL'
            
        elif direction == 'SELL' and self.is_has_order_short == False:
            stop_loss = round(last_price + last_price * (self.RISK / 100) / self.LEVERAGE, self.get_precision(self.SYMBOL_COIN, 'pricePrecision'))
            take_profit = round(last_price - last_price * (self.REWARD / 100) / self.LEVERAGE, self.get_precision(self.SYMBOL_COIN, 'pricePrecision'))
            reverse_direction = 'BUY' 
        else:
            return None, None, None
        return take_profit, stop_loss, reverse_direction

    def save_new_order(self, save_order, created_time):
        playsound('assets/direct-545.mp3')
        path = 'data/{}.csv'.format(str(datetime.datetime.now().date()))
        book_order = {}
        if os.path.isfile(path): 
            for i in self.read_csv_order(path):
                create_date = i['Unnamed: 0']
                del i['Unnamed: 0']
                book_order[create_date] = i
        book_order[created_time] = save_order 
        self.export_csv_order(path, book_order)

    def read_csv_order(self, path):
        df = pd.read_csv(path)
        return df.to_dict('records')

    def export_csv_order(self, path, book_order):
        df = pd.DataFrame(book_order)
        df = df.transpose()
        df.to_csv(path)