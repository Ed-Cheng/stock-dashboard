import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from scripts.stock_analysis import get_extrema_idx_for_plot, get_extrema_eval_for_plot


class CandlestickPlot:
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.fig = self.add_basic_candles()
        self.calc_technical_indicators()

    def calc_technical_indicators(self):
        self.df["5ma"] = self.df["Close"].rolling(5).mean()
        self.df["20ma"] = self.df["Close"].rolling(20).mean()
        self.df["20ema"] = self.df["Close"].ewm(span=20).mean()
        self.df["std"] = self.df["Close"].rolling(20).std()
        self.df["upper_bb"] = self.df["20ma"] + 2 * self.df["std"]
        self.df["lower_bb"] = self.df["20ma"] - 2 * self.df["std"]

    def add_basic_candles(self):
        fig = make_subplots(
            rows=2,
            cols=1,
            shared_xaxes=True,
            # subplot_titles=("Candle Chart", "Volume"),
            vertical_spacing=0,
            row_width=[0.2, 0.8],
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

        fig.add_trace(
            go.Bar(
                x=self.df.index,
                y=self.df["Volume"],
                marker_color="#689be3",
                showlegend=False,
            ),
            row=2,
            col=1,
        )

        fig.update_layout(autosize=True, xaxis_rangeslider_visible=False)
        return fig

    def add_ma_analysis(self):
        ma_analysis = []
        ma_analysis.append(
            go.Scatter(
                x=self.df.index,
                y=self.df["5ma"],
                line=dict(color="black", width=0.5),
                name="5ma",
            )
        )

        ma_analysis.append(
            go.Scatter(
                x=self.df.index,
                y=self.df["20ema"],
                line=dict(color="red", width=0.5),
                name="20ema",
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
        max_eval, min_eval = get_extrema_eval_for_plot(max_idx, min_idx, self.df)

        scatter_minima = go.Scatter(
            x=self.df.index[min_idx],
            y=self.df["Low"].iloc[min_idx],
            mode="markers+text",
            marker=dict(color="red", size=8),
            name="Min",
            text=min_eval,
            textposition="bottom center",
        )

        scatter_maxima = go.Scatter(
            x=self.df.index[max_idx],
            y=self.df["High"].iloc[max_idx],
            mode="markers+text",
            marker=dict(color="green", size=8),
            name="Max",
            text=max_eval,
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

    def add_button(self):
        self.fig.update_layout(
            updatemenus=[
                dict(
                    type="buttons",
                    direction="right",
                    x=0.5,
                    y=1.2,
                    buttons=[
                        dict(
                            label="reset",
                            method="relayout",
                            args=["xaxis.autorange", True],
                            args2=["yaxis.autorange", True],
                        ),
                        dict(
                            label="60 trading days",
                            method="relayout",
                            args=[
                                "yaxis.range",
                                [
                                    0.95 * min(self.df.iloc[-60:]["Low"]),
                                    1.05 * max(self.df.iloc[-60:]["High"]),
                                ],
                            ],
                            args2=[
                                "xaxis.range",
                                [self.df.index[-60], self.df.index[-1]],
                            ],
                        ),
                    ],
                )
            ]
        )
