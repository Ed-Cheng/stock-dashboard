from flask import Flask, render_template
import plotly
import json
import scripts.fundamentals as funds
import scripts.stock_plots as stock_plt
from datetime import datetime, timedelta

import yfinance as yf


app = Flask(__name__)


@app.route("/")
def index():
    greetings = "Hello World, new"

    tdy = datetime.now()
    past_days = 400
    ago = datetime.now() - timedelta(days=past_days)

    tickers = ["AAPL", "TSLA", "GOOG", "NFLX"]
    plots = {}
    for ticker in tickers:
        stock = yf.download(ticker, ago, tdy, progress=False)
        plot = stock_plt.CandlestickPlot(stock)
        plot.add_ma_analysis()
        plot.add_min_max_analysis(order=4)
        plot.add_button()
        plot.add_psar()

        plot.fig.update_layout(title={"text": ticker})
        plot.fig.update_yaxes(title_text="Candles", row=1, col=1)
        plot.fig.update_yaxes(title_text="Vol", row=2, col=1)
        plot.fig.update_yaxes(title_text="SAR", row=3, col=1)

        plotly_plot = json.dumps(plot.fig, cls=plotly.utils.PlotlyJSONEncoder)
        plots[ticker] = plotly_plot

    return render_template("home.html", greetings=greetings, plots=plots)


@app.route("/tech")
def tech_page():
    greetings = "tech"

    tdy = datetime.now()
    past_days = 400
    ago = datetime.now() - timedelta(days=past_days)

    tickers = ["SMCI", "NVDA"]
    plots = {}
    for ticker in tickers:
        stock = yf.download(ticker, ago, tdy, progress=False)
        plot = stock_plt.CandlestickPlot(stock)
        plot.add_ma_analysis()
        plot.add_min_max_analysis(order=4)
        plot.add_button()
        plot.add_psar()

        plot.fig.update_layout(title={"text": ticker})
        plot.fig.update_yaxes(title_text="Candles", row=1, col=1)
        plot.fig.update_yaxes(title_text="Vol", row=2, col=1)
        plot.fig.update_yaxes(title_text="SAR", row=3, col=1)

        plotly_plot = json.dumps(plot.fig, cls=plotly.utils.PlotlyJSONEncoder)
        plots[ticker] = plotly_plot

    return render_template("tech.html", greetings=greetings, plots=plots)


if __name__ == "__main__":
    # app.directory = "./"
    # app.run(host="127.0.0.1", port=5000)
    app.run(debug=True)
