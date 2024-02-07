import numpy as np
import pandas as pd
from scipy.signal import argrelmin, argrelmax


def merge_extrema_idx_with_val(
    max_idx: list, min_idx: list, stock_data: pd.DataFrame
) -> np.ndarray:
    """Merge and sort indices of max and min values from stock data along with their corresponding values."""
    max_values = stock_data["High"].iloc[max_idx]
    min_values = stock_data["Low"].iloc[min_idx]

    merged_idx = np.concatenate((max_idx, min_idx))
    merged_val = np.concatenate((max_values.values, min_values.values))
    # Representing min as 0 and max as 1
    merged_type = np.concatenate(([1] * len(max_idx), [0] * len(min_idx)))

    stacked_array = np.vstack((merged_idx, merged_val, merged_type))
    sorted_extrema = stacked_array[:, stacked_array[0].argsort()]

    return sorted_extrema


def clean_extrema_idx(
    max_idx: list, min_idx: list, stock_data: pd.DataFrame
) -> tuple[list, list]:
    """Confirm that there are no consecutive minimums or maximums."""
    sorted_extrema = merge_extrema_idx_with_val(max_idx, min_idx, stock_data)

    prev = sorted_extrema[:, 0]
    clean_max_idx = []
    clean_min_idx = []

    for i in range(1, len(sorted_extrema[0])):
        curr = sorted_extrema[:, i]
        if curr[2] != prev[2]:
            idx = int(prev[0])
            clean_max_idx.append(idx) if prev[2] == 1 else clean_min_idx.append(idx)
            prev = curr
        # multi max
        elif curr[2] == 1:
            prev = prev if prev[1] > curr[1] else curr
        # multi min
        elif curr[2] == 0:
            prev = prev if prev[1] < curr[1] else curr

    # Add the final "prev" as it must be valid
    idx = int(prev[0])
    clean_max_idx.append(idx) if prev[2] == 1 else clean_min_idx.append(idx)

    return clean_max_idx, clean_min_idx


def eval_max_min(
    max_idx: list, min_idx: list, stock_data: pd.DataFrame
) -> tuple[list, list]:
    """Evaluate the percentages of min/max difference from previous extremes"""
    sorted_extrema = merge_extrema_idx_with_val(max_idx, min_idx, stock_data)

    prev = sorted_extrema[:, 0]
    max_eval = []
    min_eval = []
    # Initialize the first local max or min
    max_eval.append(0) if prev[2] == 1 else min_eval.append(0)

    for i in range(1, len(sorted_extrema[0])):
        curr = sorted_extrema[:, i]
        eval = round((((curr[1] - prev[1]) / prev[1])) * 100, 1)
        (
            max_eval.append(f"{str(eval)}%")
            if eval > 0
            else min_eval.append(f"{str(eval)}%")
        )
        prev = curr

    return max_eval, min_eval


def get_extrema_idx_for_plot(order: int, stock: pd.DataFrame) -> tuple[list, list]:
    max_idx = argrelmax(stock["High"].values, order=order)[0]
    min_idx = argrelmin(stock["Low"].values, order=order)[0]

    max_idx, min_idx = clean_extrema_idx(max_idx, min_idx, stock)

    return max_idx, min_idx


def get_extrema_eval_for_plot(
    max_idx: list, min_idx: list, stock: pd.DataFrame
) -> tuple[list, list]:
    max_eval, min_eval = eval_max_min(max_idx, min_idx, stock)

    return max_eval, min_eval
