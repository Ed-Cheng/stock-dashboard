from flask import Flask, render_template
import plotly
import json
import scripts.stock_plots as stock_plots
from scripts.stock_analysis import get_extrema_analysis
from datetime import datetime, timedelta
from plotly.offline import plot as plt
import plotly.express as px
import plotly.graph_objects as go

import yfinance as yf

import warnings

warnings.simplefilter(action="ignore", category=FutureWarning)

app = Flask(__name__)


def download_data(stocks):
    stocks_str = " ".join(stocks)
    return yf.Tickers(stocks_str)


def analyse_data(stocks, stock_data, past_days):
    candle_plots = {}
    p2p_plots = {}
    ai_plots = {}
    for stock in stocks:
        stock_price = stock_data.tickers[stock].history(period=f"{past_days}d")

        stock_plot = stock_plots.PlotInfo(stock_price)
        # Main candle plots
        candle = stock_plot.generate_candle_plot(p2p_order=4)
        candle.update_layout(title={"text": stock})
        candle_plots[stock] = json.dumps(candle, cls=plotly.utils.PlotlyJSONEncoder)

        # Small plot 1: peak to peak
        p2p = stock_plot.generate_peak2peak_plot()

        # Small plot 2: AI recommendation
        fig2 = px.scatter(x=[0, 1, 2, 3, 4], y=[0, 1, 4, 9, 16])
        fig2.update_layout(
            title=dict(text="AI Grading system Maintaining", font=dict(size=20)),
            margin=dict(l=10, r=10, t=100, b=10),
        )

        candle_plots[stock] = json.dumps(candle, cls=plotly.utils.PlotlyJSONEncoder)
        p2p_plots[stock] = json.dumps(p2p, cls=plotly.utils.PlotlyJSONEncoder)
        ai_plots[stock] = json.dumps(fig2, cls=plotly.utils.PlotlyJSONEncoder)

    return candle_plots, p2p_plots, ai_plots


def generate_page(html_page, html_path, stocks, past_days):
    stock_data = download_data(stocks)

    candle_plots, p2p_plots, ai_plots = analyse_data(stocks, stock_data, past_days)
    with app.app_context():
        greetings = f"Last update: {str(datetime.now())[:-10]} (GMT)"

        rendered_template = render_template(
            html_page,
            greetings=greetings,
            plots=candle_plots,
            small1=p2p_plots,
            small2=ai_plots,
        )

        with open(html_path, "w") as static_file:
            static_file.write(rendered_template)

    return


if __name__ == "__main__":
    ticker_lists = {
        "mag7": ["NVDA", "META", "MSFT", "AMZN", "TSLA", "GOOG", "AAPL", "NFLX"],
        "ai": ["AMD", "SMCI", "AVGO", "MRVL", "QCOM", "INTC", "TSM", "ASML"],
        "tech": ["ARM", "MU", "TXN", "ADBE", "ORCL", "ON", "ISRG", "PI"],
        "meme": ["PLTR", "AI", "CRM", "ROKU", "SNOW", "PTON", "FUBO", "AFRM", "SOFI"],
        "watch": ["COIN", "U", "UPST", "WOLF"],
    }

    for tag, tickers in ticker_lists.items():
        generate_page("homeplots.html", f"static_html/{tag}.html", tickers, 400)
        print(f"Finished generating {tag}")
