
import pandas_ta as ta
import pandas as pd

class FormulaService(object):

    @staticmethod 
    def formula_1(candle):
        df = pd.DataFrame(candle)
        sma7 = ta.sma(df["close"], length=7)
        sma30 = ta.sma(df["close"], length=30)
        direction = 'NOT'
        if (sma7.iloc[-2] >= sma30.iloc[-2]) and (sma7.iloc[-1] <= sma30.iloc[-1]):
            direction = 'SELL'
        elif (sma7.iloc[-2] <= sma30.iloc[-2]) and (sma7.iloc[-1] >= sma30.iloc[-1]):
            direction = 'BUY'
        return direction

    @staticmethod
    def formula(candle):
        df = pd.DataFrame(candle)
        ma3 = ta.sma(df["close"], length=3)
        ma40 = ta.sma(df["close"], length=40)
        direction = ''
        if (ma3.iloc[-2] >= ma40.iloc[-2]) and (ma3.iloc[-1] <= ma40.iloc[-1]):
            direction = 'SELL'
        elif (ma3.iloc[-2] <= ma40.iloc[-2]) and (ma3.iloc[-1] >= ma40.iloc[-1]):
            direction = 'BUY'
        return direction