import pandas as pd
import plotly.graph_objects as go

from scripts.stock_analysis import get_extrema_idx_for_plot, get_extrema_eval_for_plot


def create_stock_plot(order: int, stock: pd.DataFrame) -> go.Figure:
    max_idx, min_idx = get_extrema_idx_for_plot(order, stock)
    max_eval, min_eval = get_extrema_eval_for_plot(max_idx, min_idx, stock)

    # Create candlestick plot
    candlestick = go.Candlestick(
        x=stock.index,
        open=stock["Open"],
        high=stock["High"],
        low=stock["Low"],
        close=stock["Close"],
        name="Candlestick",
    )

    # Create scatter plots for local minima and maxima
    scatter_minima = go.Scatter(
        x=stock.index[min_idx],
        y=stock["Low"].iloc[min_idx],
        mode="markers+text",
        marker=dict(color="red", size=8),
        name="Local Minima",
        text=min_eval,
        textposition="bottom center",
    )

    scatter_maxima = go.Scatter(
        x=stock.index[max_idx],
        y=stock["High"].iloc[max_idx],
        mode="markers+text",
        marker=dict(color="green", size=8),
        name="Local Maxima",
        text=max_eval,
        textposition="top center",
    )

    # Create figure and add traces
    fig = go.Figure(data=[candlestick, scatter_minima, scatter_maxima])
    fig.update_layout(autosize=True, xaxis_rangeslider_visible=False)

    return fig
