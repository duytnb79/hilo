
import pandas_ta as ta


class FormulaService(object):

    @staticmethod 
    def formula_1(df):
        sma7 = ta.sma(df["close"], length=7)
        sma30 = ta.sma(df["close"], length=30)
        direction = 'NOT'
        if (sma7.iloc[-2] >= sma30.iloc[-2]) and (sma7.iloc[-1] <= sma30.iloc[-1]):
            direction = 'SHORT'
        elif (sma7.iloc[-2] <= sma30.iloc[-2]) and (sma7.iloc[-1] >= sma30.iloc[-1]):
            direction = 'LONG'
        return direction