import os
import json
from datetime import datetime, timedelta


import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf

from scripts.indicators import calculate_psar
from scripts.stock_analysis import (
    eval_max_min,
    get_extrema_analysis,
    get_extrema_eval_for_plot,
    get_extrema_idx_for_plot,
)


class PlotInfo:
    def __init__(self, ticker_object: yf.Ticker, symbol: str, period: str):
        self.df = ticker_object.history(period=period)
        self.ticker_object = ticker_object
        self.symbol = symbol
        self.cal_technical_indicators()
        self.candle = self.add_basic_candles()
        self.extrema_data = {}
        self.forecast_folder = "past_forecast"

    def cal_technical_indicators(self):
        self.df["5ma"] = self.df["Close"].rolling(5).mean()
        self.df["10ma"] = self.df["Close"].rolling(10).mean()
        self.df["20ma"] = self.df["Close"].rolling(20).mean()
        self.df["12ema"] = self.df["Close"].ewm(span=12).mean()
        self.df["20ema"] = self.df["Close"].ewm(span=20).mean()
        self.df["26ema"] = self.df["Close"].ewm(span=26).mean()
        self.df["60ema"] = self.df["Close"].ewm(span=60).mean()
        self.df["std"] = self.df["Close"].rolling(20).std()
        self.df["upper_bb"] = self.df["20ma"] + 2 * self.df["std"]
        self.df["lower_bb"] = self.df["20ma"] - 2 * self.df["std"]
        return

    def add_basic_candles(self) -> go.Figure:
        fig = make_subplots(
            rows=4,
            cols=1,
            shared_xaxes=True,
            # subplot_titles=("Candle Chart", "Volume", "PSAR"),
            vertical_spacing=0.02,
            row_width=[0.1, 0.1, 0.1, 0.7],
        )

        # Create candlestick plot
        candlestick = go.Candlestick(
            x=self.df.index,
            open=self.df["Open"],
            high=self.df["High"],
            low=self.df["Low"],
            close=self.df["Close"],
            name="Candles",
        )

        fig.add_trace(
            candlestick,
            row=1,
            col=1,
        )

        # Create volume
        self.df["vol_color"] = ""
        green_vol = self.df["Volume"] > self.df["Volume"].shift()
        self.df.loc[green_vol, "vol_color"] = "green"
        self.df.loc[~green_vol, "vol_color"] = "red"

        fig.add_trace(
            go.Bar(
                x=self.df.index,
                y=self.df["Volume"],
                marker_color=self.df["vol_color"],
                showlegend=False,
            ),
            row=2,
            col=1,
        )

        # Create macd
        self.df["macd"] = (self.df["12ema"] - self.df["26ema"]) / self.df["26ema"]
        self.df["macd_signal"] = self.df["macd"].ewm(span=9).mean()
        self.df["macd_hist"] = self.df["macd"] - self.df["macd_signal"]

        self.df["macd_color"] = ""
        green_macd = self.df["macd_hist"] > self.df["macd_hist"].shift()
        self.df.loc[green_macd, "macd_color"] = "green"
        self.df.loc[~green_macd, "macd_color"] = "red"

        fig.add_trace(
            go.Bar(
                x=self.df.index,
                y=self.df["macd_hist"],
                marker_color=self.df["macd_color"],
                showlegend=False,
            ),
            row=4,
            col=1,
        )

        fig.update_yaxes(type="log", title_text="Candles(log)", row=1, col=1)
        fig.update_yaxes(title_text="Vol", row=2, col=1)
        fig.update_yaxes(title_text="SAR", row=3, col=1)
        fig.update_yaxes(title_text="MACD", row=4, col=1)

        fig.update_layout(
            autosize=True,
            title={"text": self.symbol},
            xaxis_rangeslider_visible=False,
            height=600,
        )

        return fig

    def update_forecast_data(self):
        if os.path.exists(f"{self.forecast_folder}/{self.symbol}.json"):
            with open(f"{self.forecast_folder}/{self.symbol}.json", "r") as f:
                forecast_data = json.load(f)
        else:
            forecast_data = {}

        if self.df.index[-1] in forecast_data:
            return

        op_dates = self.ticker_object.options

        upper = []
        lower = []
        date = []
        last_date = pd.Timestamp(self.df.index[-1]).strftime("%Y-%m-%d")
        # last_date = last_date.strftime("%Y-%m-%d")
        last_date = datetime.strptime(last_date, "%Y-%m-%d")

        # Option contracts in 5 weeks (35 days)
        for i in [0, 1, 2, 3, 4]:
            call_chain = self.ticker_object.option_chain(op_dates[i]).calls
            call_idx = sum(call_chain["inTheMoney"]) - 1
            call_strike = call_chain.iloc[call_idx]["strike"]
            call_iv = call_chain.iloc[call_idx]["impliedVolatility"]

            put_chain = self.ticker_object.option_chain(op_dates[i]).puts
            put_idx = -sum(put_chain["inTheMoney"])
            put_strike = put_chain.iloc[put_idx]["strike"]
            put_iv = put_chain.iloc[put_idx]["impliedVolatility"]

            days = (datetime.strptime(op_dates[i], "%Y-%m-%d") - last_date).days
            strike = (call_strike + put_strike) / 2
            iv = (call_iv + put_iv) / 2
            forecast_std = iv * strike * np.sqrt(days / 365)

            if not upper:
                date.append(last_date.strftime("%Y-%m-%d"))
                upper.append(strike)
                lower.append(strike)

            date.append(op_dates[i])
            upper.append(strike + forecast_std)
            lower.append(strike - forecast_std)

        if len(forecast_data) >= 5:
            oldest_date = min(forecast_data.keys())
            del forecast_data[oldest_date]

        forecast_data[last_date.strftime("%Y-%m-%d")] = {
            "date": date,
            "upper": upper,
            "lower": lower,
        }

        with open(f"{self.forecast_folder}/{self.symbol}.json", "w") as f:
            json.dump(forecast_data, f)

        return

    def add_forecast(self, fig) -> go.Figure:
        self.update_forecast_data()

        if os.path.exists(f"{self.forecast_folder}/{self.symbol}.json"):
            with open(f"{self.forecast_folder}/{self.symbol}.json", "r") as f:
                forecast_data = json.load(f)
        else:
            return fig

        colour_set = {
            "grey": "rgba(150, 150, 150, ",
            "blue": "rgba(173, 216, 230, ",
            "green": "rgba(144, 238, 144, ",
            "pink": "rgba(255, 182, 193, ",
            "purple": "rgba(218, 112, 214, ",
        }
        opacity_solid = "1.0)"
        opacity_clear = "0.5)"

        for data, colour in zip(forecast_data.values(), colour_set.values()):
            pred_date = data["date"][0][-5:]
            fig.add_trace(
                go.Scatter(
                    x=data["date"],
                    y=data["upper"],
                    line=dict(color=colour + opacity_solid, width=0.5),
                    mode="lines+markers",
                    name=f"{pred_date} forecast",
                    showlegend=False,
                ),
                row=1,
                col=1,
            )

            fig.add_trace(
                go.Scatter(
                    x=data["date"],
                    y=data["lower"],
                    line=dict(color=colour + opacity_solid, width=0.5),
                    mode="lines+markers",
                    fill="tonexty",
                    fillcolor=colour + opacity_clear,
                    name=f"{pred_date} forecast",
                ),
                row=1,
                col=1,
            )

        return fig

    def add_ma_analysis(self, fig) -> go.Figure:
        ma_analysis = []
        ma_pairs = [
            ("5ma", "black"),
            ("10ma", "orange"),
            ("20ema", "red"),
            ("60ema", "royalblue"),
        ]

        for ma, color in ma_pairs:
            ma_analysis.append(
                go.Scatter(
                    x=self.df.index,
                    y=self.df[ma],
                    line=dict(color=color, width=0.8),
                    name=ma,
                )
            )

        ma_analysis.append(
            go.Scatter(
                x=self.df.index,
                y=self.df["20ma"] + (self.df["std"] * 2),
                # line=dict(color="#a9e5fc", width=0.5),
                line=dict(color="#689be3", width=0.5),
                showlegend=False,
            )
        )

        ma_analysis.append(
            go.Scatter(
                x=self.df.index,
                y=self.df["20ma"] - (self.df["std"] * 2),
                line=dict(color="#689be3", width=0.5),
                fill="tonexty",
                fillcolor="rgba(104, 155, 227, 0.3)",
                name="Bollinger",
            )
        )

        for sub_plot in ma_analysis:
            fig.add_trace(
                sub_plot,
                row=1,
                col=1,
            )

        return fig

    def add_min_max_analysis(self, fig, order) -> go.Figure:
        max_idx, min_idx = get_extrema_idx_for_plot(order, self.df)

        max_eval, min_eval = eval_max_min(max_idx, min_idx, self.df)
        max_eval_str, min_eval_str = get_extrema_eval_for_plot(max_eval, min_eval)

        self.extrema_data = {
            "max_idx": max_idx,
            "min_idx": min_idx,
            "max_eval": max_eval,
            "min_eval": min_eval,
        }

        scatter_minima = go.Scatter(
            x=self.df.index[min_idx],
            y=self.df["Low"].iloc[min_idx],
            mode="markers+text",
            marker=dict(color="red", size=8),
            name="Min",
            text=min_eval_str,
            textposition="bottom center",
        )

        scatter_maxima = go.Scatter(
            x=self.df.index[max_idx],
            y=self.df["High"].iloc[max_idx],
            mode="markers+text",
            marker=dict(color="green", size=8),
            name="Max",
            text=max_eval_str,
            textposition="top center",
        )

        fig.add_trace(
            scatter_minima,
            row=1,
            col=1,
        )

        fig.add_trace(
            scatter_maxima,
            row=1,
            col=1,
        )

        return fig

    def add_psar(self, fig, af_step=0.02, af_max=0.2) -> go.Figure:
        self.df = calculate_psar(self.df, af_step, af_max)

        # Compare each number with the previous one and set the color flag accordingly
        green_mask = self.df["psar_diff"] > self.df["psar_diff"].shift()
        self.df["psar_color"] = ""
        self.df.loc[green_mask, "psar_color"] = "green"
        self.df.loc[~green_mask, "psar_color"] = "red"

        fig.add_trace(
            go.Scatter(
                x=self.df.index,
                y=self.df["psar"],
                mode="markers",
                marker=dict(color="black", size=1),
                name="PSAR",
            ),
            row=1,
            col=1,
        )

        fig.add_trace(
            go.Bar(
                x=self.df.index,
                y=self.df["psar_diff"],
                marker_color=self.df["psar_color"],
                showlegend=False,
            ),
            row=3,
            col=1,
        )

        return fig

    def add_button(self, fig) -> go.Figure:
        buttons = [
            dict(
                label="Reset",
                method="relayout",
                args=[
                    {
                        "xaxis.autorange": True,
                        "yaxis.autorange": True,
                        "yaxis2.autorange": True,
                        "yaxis3.autorange": True,
                    }
                ],
            )
        ]

        # Note that 1M is 20 trading days in stock market
        for label, days in [("1M", 20), ("3M", 60), ("6M", 120)]:
            buttons.append(
                dict(
                    label=label,
                    method="relayout",
                    args=[
                        {
                            "xaxis.range": [
                                self.df.index[-days],
                                # add space for forecasts
                                self.df.index[-1] + timedelta(4 * np.sqrt(days)),
                            ],
                            "yaxis.range": [
                                np.log10(0.9 * min(self.df.iloc[-days:]["Low"])),
                                np.log10(1.1 * max(self.df.iloc[-days:]["High"])),
                            ],
                            "yaxis2.range": [
                                (0.95 * min(self.df.iloc[-days:]["Volume"])),
                                (1.05 * max(self.df.iloc[-days:]["Volume"])),
                            ],
                            "yaxis3.range": [
                                (0.95 * min(self.df.iloc[-days:]["psar_diff"])),
                                (1.05 * max(self.df.iloc[-days:]["psar_diff"])),
                            ],
                        },
                    ],
                )
            )

        fig.update_layout(
            updatemenus=[
                dict(type="buttons", direction="right", x=0.5, y=1.2, buttons=buttons)
            ]
        )

        return fig

    def generate_candle_plot(self, p2p_order=4) -> go.Figure:
        fig = self.add_basic_candles()
        # fig = self.update_forecast_data(fig)
        fig = self.add_forecast(fig)
        fig = self.add_ma_analysis(fig)
        fig = self.add_min_max_analysis(fig, order=p2p_order)
        fig = self.add_psar(fig)
        fig = self.add_button(fig)
        fig.update_layout(xaxis=dict(rangebreaks=[dict(bounds=["sat", "mon"])]))

        return fig

    def generate_candle_plot_no_op(self, p2p_order=4) -> go.Figure:
        fig = self.add_basic_candles()
        # fig = self.update_forecast_data(fig)
        fig = self.add_ma_analysis(fig)
        fig = self.add_min_max_analysis(fig, order=p2p_order)
        fig = self.add_psar(fig)
        fig = self.add_button(fig)
        fig.update_layout(xaxis=dict(rangebreaks=[dict(bounds=["sat", "mon"])]))

        return fig

    def generate_peak2peak_plot(self) -> go.Figure:
        max2min, min2max = get_extrema_analysis(
            self.extrema_data["max_idx"], self.extrema_data["min_idx"]
        )

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                y=max2min, mode="lines+markers", line_color="red", name="max2min"
            )
        )
        fig.add_trace(
            go.Scatter(
                y=min2max, mode="lines+markers", line_color="green", name="min2max"
            )
        )

        fig.update_layout(
            title=dict(text="Peak to peak analysis", font=dict(size=10)),
            yaxis_title="days",
            margin=dict(l=10, r=10, t=40, b=10),
            legend=dict(
                font=dict(size=10),
                orientation="h",
                yanchor="bottom",
                y=1,
                xanchor="right",
                x=1,
            ),
        )

        return fig
