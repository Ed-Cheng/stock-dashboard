from flask import Flask, render_template
import plotly
import json
import scripts.stock_plots as stock_plt
from datetime import datetime, timedelta

import yfinance as yf

app = Flask(__name__)


def json_plots(tickers, past_days):
    tdy = datetime.now()
    ago = datetime.now() - timedelta(days=past_days)

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

    return plots


def generate_page(html_page, html_path, tickers, past_days):
    plots = json_plots(tickers, past_days)
    with app.app_context():
        greetings = str(datetime.now())
        rendered_template = render_template(html_page, greetings=greetings, plots=plots)

        with open(html_path, "w") as static_file:
            static_file.write(rendered_template)

    return


if __name__ == "__main__":
    big = ["AAPL", "GOOG", "AMZN"]
    tech = ["NVDA", "TSLA", "SMCI"]
    generate_page("home.html", "static_html/big.html", big, 400)
    generate_page("home.html", "static_html/tech.html", tech, 400)
