from datetime import datetime
import pandas as pd
import requests
from typing import *
import time 

def ms_to_dt_utc(ms: int) -> datetime:
    return datetime.utcfromtimestamp(ms / 1000)

def ms_to_dt_local(ms: int) -> datetime:
    return datetime.fromtimestamp(ms / 1000)
    
class HistoricalData(object):

    def __init__(self, client):
        self.client = client

    def ms_to_dt_utc(ms: int) -> datetime:
        return datetime.utcfromtimestamp(ms / 1000)

    def ms_to_dt_local(ms: int) -> datetime:
        return datetime.fromtimestamp(ms / 1000)

    def get_data_frame(self, data):
        df = pd.DataFrame(data, columns=['Timestamp', "Open", "High", "Low", "Close", "Volume"])
        df["Timestamp"] = df["Timestamp"].apply(lambda x: ms_to_dt_local(x))
        df['Date'] = df["Timestamp"].dt.strftime("%d/%m/%Y")
        df['Time'] = df["Timestamp"].dt.strftime("%H:%M:%S")
        column_names = ["Date", "Time", "Open", "High", "Low", "Close", "Volume"]
        df = df.set_index('Timestamp')
        df = df.reindex(columns=column_names)

        return df

    def get_historical_data(self, interval, symbol, start_time, end_time, limit=1500):
        collection = []
        while start_time < end_time:
            data = self.client.get_historical_data(symbol,interval=interval, start_time=start_time, end_time=end_time, limit=limit)
            print(self.client.exchange + " " + symbol + " : Collected " + str(len(data)) + " initial data from "+ str(ms_to_dt_local(data[0][0])) +" to " + str(ms_to_dt_local(data[-1][0])))
            start_time = int(data[-1][0] + 1000)
            collection +=data
            time.sleep(1.1)

        return collection
    