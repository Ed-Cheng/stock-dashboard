import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import timedelta

from scripts.indicators import calculate_psar

from scripts.stock_analysis import (
    eval_max_min,
    get_extrema_idx_for_plot,
    get_extrema_eval_for_plot,
)


class CandlestickPlot:
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.fig = self.add_basic_candles()
        self.cal_technical_indicators()

    def cal_technical_indicators(self):
        self.df["5ma"] = self.df["Close"].rolling(5).mean()
        self.df["10ma"] = self.df["Close"].rolling(10).mean()
        self.df["20ma"] = self.df["Close"].rolling(20).mean()
        self.df["20ema"] = self.df["Close"].ewm(span=20).mean()
        self.df["50ema"] = self.df["Close"].ewm(span=50).mean()
        self.df["std"] = self.df["Close"].rolling(20).std()
        self.df["upper_bb"] = self.df["20ma"] + 2 * self.df["std"]
        self.df["lower_bb"] = self.df["20ma"] - 2 * self.df["std"]

    def add_basic_candles(self) -> go.Figure:
        fig = make_subplots(
            rows=3,
            cols=1,
            shared_xaxes=True,
            # subplot_titles=("Candle Chart", "Volume", "PSAR"),
            vertical_spacing=0,
            row_width=[0.15, 0.15, 0.7],
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

        # Create a column to store the color flag
        self.df["vol_color"] = ""

        # Compare each number with the previous one and set the color flag accordingly
        green_mask = self.df["Volume"] > self.df["Volume"].shift()
        self.df.loc[green_mask, "vol_color"] = "green"
        self.df.loc[~green_mask, "vol_color"] = "red"

        fig.add_trace(
            go.Bar(
                x=self.df.index,
                y=self.df["Volume"],
                # marker_color="#689be3",
                marker_color=self.df["vol_color"],
                showlegend=False,
            ),
            row=2,
            col=1,
        )

        # build complete timepline from start date to end date
        dt_all = pd.date_range(start=self.df.index[0], end=self.df.index[-1])
        # retrieve the dates that ARE in the original datset
        dt_obs = [d.strftime("%Y-%m-%d") for d in pd.to_datetime(self.df.index)]
        # define dates with missing values
        dt_breaks = [d for d in dt_all.strftime("%Y-%m-%d").tolist() if not d in dt_obs]
        # hide dates with no values
        fig.update_xaxes(rangebreaks=[dict(values=dt_breaks)])

        fig.update_layout(autosize=True, xaxis_rangeslider_visible=False)
        return fig

    def add_ma_analysis(self):
        ma_analysis = []
        ma_pairs = [
            ("5ma", "black"),
            ("10ma", "orange"),
            ("20ema", "red"),
            ("50ema", "royalblue"),
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
                name="BB up",
            )
        )

        ma_analysis.append(
            go.Scatter(
                x=self.df.index,
                y=self.df["20ma"] - (self.df["std"] * 2),
                line=dict(color="#689be3", width=0.5),
                fill="tonexty",
                fillcolor="rgba(104, 155, 227, 0.3)",
                name="BB low",
            )
        )

        for sub_plot in ma_analysis:
            self.fig.add_trace(
                sub_plot,
                row=1,
                col=1,
            )

    def add_min_max_analysis(self, order):
        max_idx, min_idx = get_extrema_idx_for_plot(order, self.df)

        max_eval, min_eval = eval_max_min(max_idx, min_idx, self.df)
        max_eval_str, min_eval_str = get_extrema_eval_for_plot(max_eval, min_eval)

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

        self.fig.add_trace(
            scatter_minima,
            row=1,
            col=1,
        )

        self.fig.add_trace(
            scatter_maxima,
            row=1,
            col=1,
        )

    def add_psar(self, af_step=0.02, af_max=0.2):
        self.df = calculate_psar(self.df, af_step, af_max)

        # Compare each number with the previous one and set the color flag accordingly
        green_mask = self.df["psar_diff"] > self.df["psar_diff"].shift()
        self.df["psar_color"] = ""
        self.df.loc[green_mask, "psar_color"] = "green"
        self.df.loc[~green_mask, "psar_color"] = "red"

        self.fig.add_trace(
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

        self.fig.add_trace(
            go.Bar(
                x=self.df.index,
                y=self.df["psar_diff"],
                marker_color=self.df["psar_color"],
                showlegend=False,
            ),
            row=3,
            col=1,
        )

    def add_button(self):
        buttons = [
            dict(
                label="Reset",
                method="relayout",
                args=["xaxis.autorange", True],
                args2=["yaxis.autorange", True],
            )
        ]

        # Note that 1M is 20 trading days in stock market
        for label, days in [("1M", 20), ("3M", 60), ("6M", 120)]:
            buttons.append(
                dict(
                    label=label,
                    method="relayout",
                    args=[
                        "yaxis.range",
                        [
                            0.9 * min(self.df.iloc[-days:]["Low"]),
                            1.1 * max(self.df.iloc[-days:]["High"]),
                        ],
                    ],
                    args2=[
                        "xaxis.range",
                        [self.df.index[-days], self.df.index[-1] + timedelta(days=1)],
                    ],
                )
            )

        self.fig.update_layout(
            updatemenus=[
                dict(type="buttons", direction="right", x=0.5, y=1.2, buttons=buttons)
            ]
        )
