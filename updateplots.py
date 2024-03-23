from flask import Flask, render_template
import plotly
import json
import scripts.stock_plots as stock_plt
from scripts.stock_analysis import get_extrema_analysis
from datetime import datetime, timedelta
from plotly.offline import plot as plt
import plotly.express as px
import plotly.graph_objects as go

import yfinance as yf

app = Flask(__name__)


def download_data(stocks):
    stocks_str = " ".join(stocks)
    return yf.Tickers(stocks_str)


def analyse_data(stocks, stock_data, past_days):
    plots = {}
    small1 = {}
    small2 = {}
    analyses = {}
    all_plot = []
    for stock in stocks:
        # stock_price = yf.download(stock, ago, tdy, progress=False)
        stock_price = stock_data.tickers[stock].history(period=f"{past_days}d")

        plot = stock_plt.CandlestickPlot(stock_price)
        plot.add_ma_analysis()
        plot.add_min_max_analysis(order=4)
        plot.add_button()
        plot.add_psar()

        plot.fig.update_layout(title={"text": stock})
        plot.fig.update_yaxes(title_text="Candles", row=1, col=1)
        plot.fig.update_yaxes(title_text="Vol", row=2, col=1)
        plot.fig.update_yaxes(title_text="SAR", row=3, col=1)

        # plot.fig.update_layout(margin=dict(l=10, r=10, t=10, b=10))

        plotly_plot = json.dumps(plot.fig, cls=plotly.utils.PlotlyJSONEncoder)
        plots[stock] = plotly_plot

        max2min, min2max = get_extrema_analysis(
            plot.extrema_data["max_idx"], plot.extrema_data["min_idx"]
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

        # Update plot layout
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

        fig2 = px.scatter(x=[0, 1, 2, 3, 4], y=[0, 1, 4, 9, 16])
        fig2.update_layout(margin=dict(l=10, r=10, t=10, b=10))
        small1[stock] = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
        small2[stock] = json.dumps(fig2, cls=plotly.utils.PlotlyJSONEncoder)

        # plot.fig.update_layout(height=400)
        # fig.update_layout(height=200)

        # plot.fig.update_layout(margin=dict(l=10, r=10, t=10, b=10))
        # fig.update_layout(margin=dict(l=10, r=10, t=10, b=10))

        # all_plot.append(
        #     {
        #         "big_plot": json.dumps(plot.fig, cls=plotly.utils.PlotlyJSONEncoder),
        #         "small_plots": [
        #             json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder),
        #             json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder),
        #         ],
        #     }
        # )

    return plots, small1, small2


def generate_page(html_page, html_path, stocks, past_days):
    stock_data = download_data(stocks)

    plots, small1, small2 = analyse_data(stocks, stock_data, past_days)
    with app.app_context():
        greetings = f"Last update: {str(datetime.now())}"

        rendered_template = render_template(
            html_page, greetings=greetings, plots=plots, small1=small1, small2=small2
        )

        with open(html_path, "w") as static_file:
            static_file.write(rendered_template)

    return


if __name__ == "__main__":
    big = ["AAPL", "GOOG", "AMZN"]
    tech = ["NVDA", "TSLA", "SMCI"]
    generate_page("homeplots.html", "static_html/big.html", big, 400)
    generate_page("homeplots.html", "static_html/tech.html", tech, 400)
