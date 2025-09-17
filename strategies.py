
import pandas as pd
import numpy as np

def sma_crossover(df, fast=20, slow=50):
    df = df.copy()
    df["ma_f"] = df["c"].rolling(fast).mean()
    df["ma_s"] = df["c"].rolling(slow).mean()
    df["signal"] = 0
    cross_up = (df["ma_f"].shift(1) <= df["ma_s"].shift(1)) & (df["ma_f"] > df["ma_s"])
    cross_dn = (df["ma_f"].shift(1) >= df["ma_s"].shift(1)) & (df["ma_f"] < df["ma_s"])
    df.loc[cross_up,"signal"] = 1
    df.loc[cross_dn,"signal"] = -1
    return df.dropna()

def rsi_strategy(df, period=14, low=30, high=70):
    df = df.copy()
    delta = df["c"].diff()
    gain = (delta.where(delta>0,0)).rolling(period).mean()
    loss = (-delta.where(delta<0,0)).rolling(period).mean()
    rs = gain/loss
    df["rsi"] = 100 - (100/(1+rs))
    df["signal"] = 0
    df.loc[df["rsi"]<low,"signal"] = 1
    df.loc[df["rsi"]>high,"signal"] = -1
    return df.dropna()

def bollinger_strategy(df, period=20, stds=2):
    df = df.copy()
    ma = df["c"].rolling(period).mean()
    std = df["c"].rolling(period).std()
    df["upper"] = ma + stds*std
    df["lower"] = ma - stds*std
    df["signal"] = 0
    df.loc[df["c"]<df["lower"],"signal"] = 1
    df.loc[df["c"]>df["upper"],"signal"] = -1
    return df.dropna()
