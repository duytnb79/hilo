import asyncio
import websockets
import json
import datetime
from decimal import *

def map_candle(res):  
    if 'k' in res:
        k = res['k']
        open_time = datetime.datetime.fromtimestamp(k['t']/1000)
        close_time = datetime.datetime.fromtimestamp(k['T']/1000)
        symbol = k['s']
        return {
            'open_time': open_time,
            'close_time': close_time,
            'symbol': symbol,
            'open': float(Decimal(k['o'])),
            'high': float(Decimal(k['h'])),
            'low': float(Decimal(k['l'])),
            'close': float(Decimal(k['c'])),
            'middle': (float(Decimal(k['o'])) + float(Decimal(k['c']))) / 2,
        }


async def candle_stick_data():
    url = "wss://stream.binance.com:9443/ws/" #steam address
    first_pair = 'bnbbtc@kline_1m' #first pair
    pair = 'xrpusdt'

    async with websockets.connect(url+first_pair) as sock:
        pairs = '{"method": "SUBSCRIBE", "params": ["' + pair + '@kline_1s"],  "id": 1}'#other pairs

        await sock.send(pairs)
        print(f"> {pairs}")
        while True:
            resp = await sock.recv() 
            resp = json.loads(resp) 
            if 's' in resp and resp['s'].lower() == pair:
                resp = map_candle(resp) 
                print(f"< {resp}")

asyncio.get_event_loop().run_until_complete(candle_stick_data())

