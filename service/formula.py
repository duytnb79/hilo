
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
        sma7 = ta.sma(df["close"], length=7)
        sma30 = ta.sma(df["close"], length=30)
        direction = ''
        if (sma7.iloc[-2] >= sma30.iloc[-2]) and (sma7.iloc[-1] <= sma30.iloc[-1]):
            direction = 'SELL'
        elif (sma7.iloc[-2] <= sma30.iloc[-2]) and (sma7.iloc[-1] >= sma30.iloc[-1]):
            direction = 'BUY'
        return direction