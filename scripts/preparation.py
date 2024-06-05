import pandas as pd
import numpy as np
import yfinance as yf


def download_data(stocks):
    stocks_str = " ".join(stocks)
    return yf.Tickers(stocks_str)


def add_moving_average(df):
    df["interday_chg"] = (df["Close"] - df["Open"]) / df["Open"]
    df["day_change"] = df["Close"].pct_change()

    for i in [3, 5, 10, 20, 60]:
        df[f"ma{i}"] = df["Close"].rolling(i).mean()
        df[f"ema{i}"] = df["Close"].ewm(span=i).mean()

    return df


def add_volatility(df):
    if "day_change" not in df.columns:
        df["day_change"] = df["Close"].pct_change()

    for i in [5, 20, 60]:
        df[f"volatility{i}"] = df["day_change"].rolling(i).std()

    return df


def add_norm_volume(df):
    for i in [5, 10, 20]:
        df[f"vol{i}"] = df["Volume"].rolling(i).mean() / df["Volume"]

    return df


def add_bollinger_band(df):
    if "ma20" not in df.columns:
        df["ma20"] = df["Close"].rolling(20).mean()
    std = df["Close"].rolling(20).std()

    df["upper_bb"] = df["ma20"] + 2 * std
    df["lower_bb"] = df["ma20"] - 2 * std

    return df


def add_macd(df):
    ema12 = df["Close"].ewm(span=12).mean()
    ema26 = df["Close"].ewm(span=26).mean()
    macd = (ema12 - ema26) / ema26
    macd_signal = macd.ewm(span=9).mean()

    df["macd_hist"] = macd - macd_signal
    df["macd_ma3"] = df["macd_hist"].rolling(3).mean()
    df["macd_ma5"] = df["macd_hist"].rolling(5).mean()

    for i in [1, 2, 3]:
        df[f"macd_{i}d_diff"] = df["macd_hist"] - df["macd_hist"].shift(i)

    return df


def add_psar(df, af_step=0.02, af_max=0.2):
    # Initialize columns
    psar_array = np.zeros(len(df))
    af_array = np.full(len(df), af_step)

    # Initial values
    bull = True
    psar = df.iloc[0]["Low"]
    ep = df.iloc[0]["High"]

    for i in range(1, len(df)):
        if bull:
            psar = psar + af_array[i - 1] * (ep - psar)
            if df.iloc[i]["Low"] < psar:
                bull = False
                psar = ep
                ep = df.iloc[i]["Low"]
                af_array[i] = af_step
            else:
                if df.iloc[i]["High"] > ep:
                    ep = df.iloc[i]["High"]
                    af_array[i] = min(af_array[i - 1] + af_step, af_max)
                else:
                    af_array[i] = af_array[i - 1]
        else:
            psar = psar - af_array[i - 1] * (psar - ep)
            if df.iloc[i]["High"] > psar:
                bull = True
                psar = ep
                ep = df.iloc[i]["High"]
                af_array[i] = af_step
            else:
                if df.iloc[i]["Low"] < ep:
                    ep = df.iloc[i]["Low"]
                    af_array[i] = min(af_array[i - 1] + af_step, af_max)
                else:
                    af_array[i] = af_array[i - 1]

        psar_array[i] = psar

    psar_array[0] = df.iloc[0]["Close"]

    df["psar"] = psar_array

    return df


def add_stochastic_oscillator(df):
    for i in [7, 23]:
        low = df["Low"].rolling(window=i).min()
        high = df["High"].rolling(window=i).max()
        df[f"os_k{i}"] = (df["Close"] - low) / (high - low)
        df[f"os_d{i}"] = df[f"os_k{i}"].rolling(window=3).mean()

        df[f"os_kd{i}"] = df[f"os_k{i}"] - df[f"os_d{i}"]
        df[f"os_kd{i}_1d"] = df[f"os_kd{i}"] - df[f"os_kd{i}"].shift(1)
        df[f"os_kd{i}_2d"] = df[f"os_kd{i}"] - df[f"os_kd{i}"].shift(2)

    return df


def add_target(df):
    df["ema3"] = df["Close"].ewm(span=3).mean()

    df["short_target"] = (df["ema3"].shift(-2) - df["Close"]) / df["Close"]
    df["short_target"] = pd.cut(
        df["short_target"],
        bins=[-1, -0.03, 0.03, 1],
        labels=[0, 1, 2],
        right=False,
    )

    df["long_target"] = (df["ema3"].shift(-10) - df["Close"]) / df["Close"]
    df["long_target"] = pd.cut(
        df["long_target"],
        bins=[-1, -0.03, 0.03, 1],
        labels=[0, 1, 2],
        right=False,
    )

    target = ["short_target", "long_target"]

    return df, target


def preprocess(stock_data):
    stock_data, target = add_target(stock_data)
    old_columns = stock_data.columns

    # Un-normalized features
    stock_data = add_moving_average(stock_data)
    stock_data = add_bollinger_band(stock_data)
    stock_data = add_psar(stock_data, af_step=0.02, af_max=0.2)

    unnorm_features = list(set(stock_data.columns) - set(old_columns))
    stock_data[unnorm_features] = stock_data[unnorm_features].div(
        stock_data["Close"], axis=0
    )

    # Normalized features
    stock_data = add_macd(stock_data)
    stock_data = add_norm_volume(stock_data)
    stock_data = add_stochastic_oscillator(stock_data)
    stock_data = add_volatility(stock_data)

    train_features = list(set(stock_data.columns) - set(old_columns))
    stock_data = stock_data.dropna()

    return stock_data, train_features, target
