from binance.client import Client
from binance.futures import Futures 
import datetime
import functools
from decimal import *
import pandas as pd
import time

client = Futures(key='', secret='', base_url='https://testnet.binancefuture.com/')

def mapCandleData(res):
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

i = 0
while True: 
    print(i)
    i += 1
    response = client.klines('ETHUSDT', '5m', limit=31)
    candle = list(map(mapCandleData, response))
    df = pd.DataFrame(candle)

    sma7 = ta.sma(df["close"], length=7)
    sma30 = ta.sma(df["close"], length=30)
    direction = ''
    if (sma7.iloc[-2] >= sma30.iloc[-2]) and (sma7.iloc[-1] <= sma30.iloc[-1]):
        direction = 'SELL'
    elif (sma7.iloc[-2] <= sma30.iloc[-2]) and (sma7.iloc[-1] >= sma30.iloc[-1]):
        direction = 'BUY'

    if direction != '':
        last_price = float(Decimal(df.iloc[-1]['close']))
        if direction == 'BUY':
            take_profit = round(last_price + last_price * 0.08 / 20, 2)
            stop_loss = round(last_price - last_price * 0.02 / 20, 2)
            reverse_direction = 'SELL'
        else: 
            stop_loss = round(last_price + last_price * 0.02 / 20, 2)
            take_profit = round(last_price - last_price * 0.08 / 20, 2)
            reverse_direction = 'BUY'
        params = {
            'batchOrders': [
                {
                    'symbol': 'ETHUSDT',
                    'side': direction,
                    'type': 'LIMIT',
                    'price': str(last_price),
                    'quantity': '1',
                    'timeInForce': 'GTC'
                },
                {
                    'symbol': 'ETHUSDT',
                    'side': reverse_direction,
                    'type': 'STOP_MARKET',
                    'stopPrice': str(stop_loss),
                    'quantity': '1',
                    'closePosition': 'true'
                },
                {
                    'symbol': 'ETHUSDT',
                    'side': reverse_direction,
                    'type': 'TAKE_PROFIT_MARKET',
                    'stopPrice': str(take_profit),
                    'quantity': '1',
                    'closePosition': 'true'
                }
            ]
        }

        response = client.new_batch_order(**params)
        account = client.account()
        print(response)
        print("Market Price: ", last_price)
        print("Take Profit: ", take_profit)
        print("Stop Loss: ", stop_loss)
        print("Balance: ", account['availableBalance'])
    
    time.sleep(5 * 60)
