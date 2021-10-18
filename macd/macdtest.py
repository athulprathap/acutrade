import pandas as pd
import sqlalchemy
from binance.client import Client
from binance.websockets import BinanceSocketManager
import ta
import numpy as np
from time import sleep

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
    )  # Stochastic Oscillator in a 14 day period
    df["D"] = (
        df["K"].rolling(3).mean()
    )  # Stochastic slope line is a 3 period simple moving average
    df["RSI"] = ta.momentum.rsi(df["Close"], window=14)
    df["MACD"] = ta.trend.macd_diff(df.Close)
    df.dropna(inplace=True)


#!/usr/bin/python
# -*- coding: utf-8 -*-


class Signals:
    def __init__(self, df, lags):

        # lags is how back wwe want to look if the lines create a signal or not

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
        )  # if we get a trigger we getting 1 otherwise 0
        self.df["Buy"] = np.where(
            self.df.trigger
            & self.df["K"].between(20, 80)
            & self.df["D"].between(20, 80)
            & (self.df.RSI > 50)
            & (self.df.MACD > 0),
            1,
            0,
        )  # if with trigger all the other conditions are also fulfilled
        # if all these conditions are met we can then conclude to put either 1 or 0 at that position


def strategy(pair, qty, open_position=False):
    df = getminutedata(pair, "1m", "100")
    applytechnicals(df)
    inst = Signals(df, 5)
    inst.decide()
    #comment for pull

    print(
        f"current close is " + str(df.Close.iloc[-1])
    )  # to show us that the steps above have been fulfilled
    print(f"current buy state is " + str(df.Buy.iloc[-1]))
    if df.Buy.iloc[-1]:
        # if we have a buy signal in our most recent row then we buy
        # order = client.create_order(symbol=pair,
        #                           side='BUY',
        #                            type='MARKET',
        #                            quantity=qty)

        # print(order)

        buyprice = df.Close.iloc[-1]
        buy_time = df.Time.iloc[-1]

        data = ["BUY",str(buyprice),str(buy_time)]
        with open('trades.csv', 'a') as f_object:
            
            writer_object = writer(f_object)
            writer_object.writerow(data)
            f_object.close()
            
        open_position = True  # this will be used for our selling condition
    

        # buyprice = float(order['fills'][0]['price']) #extracting buying price from the order, type cast to float because it's a string value
        
        while open_position:
            sleep(0.5)  # to avoid acessive requests to the binance platform
            df = getminutedata(
                pair, "1m", "2"
            )  # we can also just go 1 min back but we want to avoide an empty dataframe so we will look at 2 min back data

            # some feedback data
            print("current Close is " + str(df.Close.iloc[-1]))
            print(
                f"current Target is " + str(buyprice * 1.005)
            )  # this is for 0.5% profit
            print(f"current Stop is " + str(buyprice * 0.995))  # 0.5% loss

            # target se current price bada hona chiya jitne pe humne kharida tha or agr stop loss se chota hua toh bech do
            if df.Close.iloc[-1] <= buyprice * 0.995 or df.Close.iloc[-1] >= 1.005 * buyprice:
                
                # order = client.create_order(symbol=pair,
                #                          side='SELL',
                #                          type='MARKET',
                #                          quantity=qty)
                sp = df.Close.iloc[-1]
                sell_time = df.Time.iloc[-1]


                data = ["SELL",str(sp),str(sell_time)]
                
                with open('trades.csv', 'a') as f_object:
                    writer_object = writer(f_object)
                    writer_object.writerow(data)
                    f_object.close()
                # print(order)
                # added comment
                break


if __name__ == "__main__":

    while True:
        strategy("BTCUSDT", 10)  # 10 tokens
        sleep(0.5)


if __name__ == "__main__":

    while True:
        strategy("BTCUSDT", 10)  # 10 tokens
        sleep(0.5)

