# import asyncio
import pandas as pd
import numpy as np

from datetime import datetime
from v2.historical_data import HistoricalData
from v2.binance_client import BinanceClient

client = BinanceClient(futures=False)
history = HistoricalData(client)

symbol = "DOGEUSDT"
interval = "1m"
fromDate = int(datetime.strptime('2022-12-13 00:00:00', '%Y-%m-%d %H:%M:%S').timestamp() * 1000)
toDate = int(datetime.strptime('2022-12-14 23:00:00', '%Y-%m-%d %H:%M:%S').timestamp() * 1000)

file_dir = 'data/{}_{}_{}.csv'.format(symbol, fromDate, toDate)

# data = history.get_historical_data(interval, symbol, fromDate, toDate)
# df = history.get_data_frame(data)
# df.to_csv(file_dir)
def round_2(x):
    try:
        return round(x,6)
    except:
        return x

first_index_larger=lambda seq, m: [ii for ii in range(0, len(seq)) if seq[ii] > m][0] 
first_index_smaller=lambda seq, m: [ii for ii in range(0, len(seq)) if seq[ii] < m][0] 

def draw_sth():

    import matplotlib.pyplot as plt

    x= df.index.tolist()
    y1= df['Average']
    plt.plot(x,y1) 
    plt.xlabel('X-axis')
    plt.ylabel('Y-axis')
    plt.title("A simple line graph")
    plt.show()

def cal_time(date_time, hours_wating=5):
    from datetime import timedelta    
    given_time = datetime.strptime(date_time, '%Y-%m-%d %H:%M:%S')
    final_time = given_time - timedelta(hours=hours_wating)
    return final_time

def read_and_find_history(percentage=5, percentage_loss=2, hours_wating=5):
    global file_dir
    df = pd.read_csv(file_dir)
    df = df[df['Volume'] != 0]
    count = df['Volume'].count()
    print('=> Total:' + str(count))

    positive_name = '+{}%'.format(percentage)
    negative_name = '-{}%'.format(percentage)

    df['Average'] = df[['High','Close']].mean(axis=1).astype(float).apply(round_2)
    df[positive_name] = (df['Average'] * (1 + percentage/100)).astype(float).apply(round_2)
    df[negative_name] = (df['Average'] * (1 + (-1*percentage_loss/100))).astype(float).apply(round_2)
    # index = df.index.tolist()

    # Delete columns
    df.drop('Date', inplace=True, axis=1)
    df.drop('Open', inplace=True, axis=1)
    df.drop('High', inplace=True, axis=1)
    df.drop('Close', inplace=True, axis=1)
    df.drop('Low', inplace=True, axis=1)
    df.drop('Time', inplace=True, axis=1)

    # get data as arrays
    average = df['Average'].to_numpy()
    negative_percent = df[negative_name].to_numpy()  
    positive_percent = df[positive_name].to_numpy()  
    timestamp = df['Timestamp'].to_numpy()
    take_profit_time = (np.ones(count) * -1).astype(str)
    order_price_est = (np.ones(count) * -1).astype(float)
    order_price = (np.ones(count) * -1).astype(float)
    order_time = (np.ones(count) * -1).astype(str) 
 
    for i, v in enumerate(positive_percent.copy()):   
        """
            Get from current index to index has increased by x percentage
            In the middle of array, there's no value blew -x percentage (negative_percent)
        """
        if v <= average[i:].max() and v >= average[i:].min():
            j = np.where(average[i:] > v)[0][0] + i
            if negative_percent[i] < average[i:j].min():
 
                take_profit_time[i] = timestamp[j]

                # Find pre price and index (before it direct to +x percentage)
                price_pre_est = round_2(average[j] * (1 + (-1*percentage/100)))
                if average[i:j].min() < price_pre_est: 
                
                    price_est = average[:j].min() #interval_est.mean()
                    index_est = np.where(average[:j] <= price_est)[0][-1]  
                    if index_est != 0 and index_est > i:
                        # Find time of price (before it direct to +x percentage) 
                        order_price[i] = average[index_est]
                        order_time[i] = timestamp[index_est]

 
    # reindex to original indices
    df['TakeProfitPrice'] = df[positive_name] 
    df['TakeProfitTime'] = take_profit_time 
    # df['OrderPriceEst'] = order_price_est 
    df['OrderPrice'] = order_price 
    df['OrderTime'] = order_time 
    df['OrderPrice'] = df['OrderPrice'].astype(float).apply(round_2) 
    df = df[df['TakeProfitTime'] != '-1']
    df = df[df['OrderTime'] != '-1.0']

    df.drop(positive_name, inplace=True, axis=1)
    df.drop(negative_name, inplace=True, axis=1)

    df['WaitingTime'] = df['OrderTime'].map(cal_time)
    df = df[df['WaitingTime'] < df['Timestamp']]
    file_dir = 'data/edited_{}_{}_{}.csv'.format(symbol, fromDate, toDate) 
    df.to_csv(file_dir)
    print(df.head()) 
    print('=> After Total:' + str(df['Volume'].count()))
read_and_find_history()