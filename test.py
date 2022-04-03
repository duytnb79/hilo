
import datetime 
import os
import pandas as pd
from service.util import UtilService
from binance.futures import Futures 
from dotenv import load_dotenv

load_dotenv()
## get exchange 
util = UtilService() 
client = Futures(
    key=os.environ.get('KEY_TESTNET_BINANCE'),
    secret=os.environ.get('SECRET_TESTNET_BINANCE'))

def iso_to_timestamp(date_time_str):
    if date_time_str == None: return None
    return int(datetime.datetime.strptime(date_time_str, "%Y-%m-%dT%H:%M:%S.%fZ").timestamp() * 1000)

def timestamp_to_iso(timestamp):
    if timestamp == None: return None
    return datetime.datetime.fromtimestamp(timestamp/1000)

def test_case(symbol, time_frame, since, limit, params, balance, quantity, leverage, is_export=True):
    init_balance = balance
   
    ## Get Chart  
    mark_klines = client.klines(symbol, 
                                time_frame, 
                                endTime= iso_to_timestamp(since),
                                limit=1500)
    ## Order 
    try:
        book_order, balance, count_win, count_lose = util.run_report(mark_klines=mark_klines, 
                        balance=balance, 
                        quantity=quantity, 
                        leverage=leverage,
                        limit=limit,
                        risk=3)
    except:
        return
    if since == None: since = str(datetime.datetime.now().date())
    if is_export: util.export_csv_order(path='data_test/{}.csv'.format(since), book_order=book_order)
    print("Case {}: {}-{} # {}M-{}W-{}L # Rate: W-L:{}".format(since[0:10], init_balance, round(balance), len(book_order), count_win, count_lose, round(count_win/count_lose,2)))

def allsundays(year):
    _now = datetime.datetime.now()
    return pd.date_range(start=str(year), end=str(_now), 
                         freq='W-SUN').strftime('%Y-%m-%dT06:59:00.000Z').tolist()

if __name__ == '__main__':
    sundays = allsundays(2022) 
    start_times = sundays
    #  [
    #     None, # From Now
    #     '2022-04-03T00:00:00.000Z', # From 2022-04-03T00:00:00.000Z,
    #     '2022-03-02T00:00:00.000Z',
    #     '2022-03-16T00:00:00.000Z',
    #     '2022-03-28T00:00:00.000Z',
    #     '2022-03-24T00:00:00.000Z', 
    #     '2022-02-02T00:00:00.000Z',
    #     '2022-02-12T00:00:00.000Z',
    #     '2022-02-18T00:00:00.000Z',
    #     '2022-02-24T00:00:00.000Z',
    # ]

    for since in start_times:
        test_case(symbol='ADAUSDT', time_frame='1m', since=since, limit=1500, params={}, 
            balance=1000, quantity=10, leverage=20, is_export=False)
    