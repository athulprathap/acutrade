import pandas as pd
from binance.client import Client
from binance.websockets import BinanceSocketManager
import ta
import numpy as np
from time import sleep
from csv import writer
api_key = "UOVRq8pnF00jk4gbgMshASlPV4rCECjfcykkc8WYT3Z0ETefal3248ZwWsLnRAf4"
api_secret = "zA3fnlCjEaNpYDCEOW21iLWPdG2QeiyKuOoLm5dANraUTh5tErYkBJ5MyQ8UaWX6"

client = Client(api_key, api_secret)
bsm = BinanceSocketManager(client)

def getminutedata(symbol, interval, lookback):
    frame = pd.DataFrame(
        client.get_historical_klines(symbol, interval, lookback + " min ago UTC")
    )
    frame = frame.iloc[:, :6]
    frame.columns = ["Time", "Open", "High", "Low", "Close", "Volume"]
    frame = frame.set_index("Time")
    frame.index = (
        pd.to_datetime(frame.index, unit="ms")
        .tz_localize("UTC")
        .tz_convert("Asia/Kolkata")
    )
    frame = frame.astype(float)
    frame = frame.reset_index()
    return frame


def applytechnicals(df):
    df["K"] = ta.momentum.stoch(
        df.High, df.Low, df.Close, window=14, smooth_window=3
    ) 
    df["D"] = (
        df["K"].rolling(3).mean()
    ) 
    df["RSI"] = ta.momentum.rsi(df["Close"], window=14)
    df["MACD"] = ta.trend.macd_diff(df.Close)
    df.dropna(inplace=True)

class Signals:
    def __init__(self, df, lags):

        

        self.df = df
        self.lags = lags

    def gettrigger(self):

        dfx = pd.DataFrame()
        for i in range(self.lags + 1):

            mask = (self.df["K"].shift(i) < 20) & (self.df["D"].shift(i) < 20)
            dfx = dfx.append(mask, ignore_index=True)

        return dfx.sum(axis=0)

    def decide(self):

        self.df["trigger"] = np.where(
            self.gettrigger(), 1, 0
        ) 
        self.df["Buy"] = np.where(
            self.df.trigger
            & self.df["K"].between(20, 80)
            & self.df["D"].between(20, 80)
            & (self.df.RSI > 50)
            & (self.df.MACD > 0),
            1,
            0,
        ) 


def strategy(pair, qty, open_position=False):
    df = getminutedata(pair, "1m", "100")
    applytechnicals(df)
    inst = Signals(df, 13) #changed the lag value
    inst.decide()
    

    print(
        f"current close is " + str(df.Close.iloc[-1])
    ) 
    print(f"current buy state is " + str(df.Buy.iloc[-1]))
    if df.Buy.iloc[-1]:
       

        buyprice = df.Close.iloc[-1]
        buy_time = df.Time.iloc[-1]

        data = ["BUY",str(buyprice),str(buy_time)]
        with open('/home/aryan/acutrade/macd/trades10a.csv', 'a') as f_object: #changed the path to the csv file
            
            writer_object = writer(f_object)
            writer_object.writerow(data)
            f_object.close()
            
        open_position = True 
    

       
        
        while open_position:
            sleep(0.5)
            df = getminutedata(
                pair, "1m", "2"
            ) 

           
            print("current Close is " + str(df.Close.iloc[-1]))
            print(
                f"current Target is " + str(buyprice * 1.005) 
            )  
            print(f"current Stop is " + str(buyprice * 0.995)) 
            
            if df.Close.iloc[-1] <= buyprice * 0.995 or df.Close.iloc[-1] >= 1.005 * buyprice:
                
               
                sp = df.Close.iloc[-1]
                sell_time = df.Time.iloc[-1]


                data = ["SELL",str(sp),str(sell_time)]
                
                with open('/home/aryan/acutrade/macd/trades10a.csv', 'a') as f_object: #changed the path to the csv file
                    writer_object = writer(f_object)
                    writer_object.writerow(data)
                    f_object.close()
                
                break


if __name__ == "__main__":

    while True:
        strategy("BTCUSDT", 10)
        sleep(0.5)
