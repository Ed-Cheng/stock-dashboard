import numpy as np


def calculate_psar(stock_data, af_step=0.02, af_max=0.2):
    data = stock_data.copy()

    # Initialize columns
    psar_array = np.zeros(len(data))
    af_array = np.full(len(data), af_step)

    # Initial values
    bull = True
    psar = data.iloc[0]["Low"]
    ep = data.iloc[0]["High"]

    for i in range(1, len(data)):
        if bull:
            psar = psar + af_array[i - 1] * (ep - psar)
            if data.iloc[i]["Low"] < psar:
                bull = False
                psar = ep
                ep = data.iloc[i]["Low"]
                af_array[i] = af_step
            else:
                if data.iloc[i]["High"] > ep:
                    ep = data.iloc[i]["High"]
                    af_array[i] = min(af_array[i - 1] + af_step, af_max)
                else:
                    af_array[i] = af_array[i - 1]
        else:
            psar = psar - af_array[i - 1] * (psar - ep)
            if data.iloc[i]["High"] > psar:
                bull = True
                psar = ep
                ep = data.iloc[i]["High"]
                af_array[i] = af_step
            else:
                if data.iloc[i]["Low"] < ep:
                    ep = data.iloc[i]["Low"]
                    af_array[i] = min(af_array[i - 1] + af_step, af_max)
                else:
                    af_array[i] = af_array[i - 1]

        psar_array[i] = psar

    psar_array[0] = data.iloc[0]["Close"]

    data["psar"] = psar_array
    data["psar_diff"] = data["Close"] - psar_array

    return data
