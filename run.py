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
    past_days = 360
    ago = datetime.now() - timedelta(days=past_days)

    tickers = ["AAPL", "TSLA", "GOOG", "NFLX"]
    plots = {}
    for ticker in tickers:
        stock = yf.download(ticker, ago, tdy, progress=False)
        plot = stock_plt.create_stock_plot(order=4, stock=stock)
        plotly_plot = json.dumps(plot, cls=plotly.utils.PlotlyJSONEncoder)
        plots[ticker] = plotly_plot

    return render_template("home.html", greetings=greetings, plots=plots)


if __name__ == "__main__":
    # app.directory = "./"
    # app.run(host="127.0.0.1", port=5000)
    app.run(debug=True)
