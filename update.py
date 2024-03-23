from flask import Flask, render_template
import plotly
import json
import scripts.stock_plots as stock_plt
from scripts.stock_analysis import get_extrema_analysis
from datetime import datetime, timedelta
from plotly.offline import plot as offline_plot

import yfinance as yf

app = Flask(__name__)


def download_data(stocks):
    stocks_str = " ".join(stocks)
    return yf.Tickers(stocks_str)


def analyse_data(stocks, stock_data, past_days):
    plots = {}
    analyses = {}
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

        plotly_plot = json.dumps(plot.fig, cls=plotly.utils.PlotlyJSONEncoder)
        html_plot = offline_plot(plot.fig, output_type="div")
        plots[stock] = plotly_plot

        analysis = ""
        for ex_type, ex_data in plot.extrema_data.items():
            analysis += get_extrema_analysis(ex_data, ex_type, ex_type.split()[-1])
            analysis += "\n"
        analysis = analysis.replace("\n", "<br>")
        analysis = analysis.replace("±", "&plusmn;")

        analyses[stock] = analysis[:-2]

    return plots, analyses


def generate_page(html_page, html_path, stocks, past_days):
    stock_data = download_data(stocks)

    plots, analyses = analyse_data(stocks, stock_data, past_days)
    with app.app_context():
        greetings = f"Last update: {str(datetime.now())}"
        # analysis = (
        #     "This is the first line.\nThis is the second line.\nThis is the third line."
        # )

        rendered_template = render_template(
            html_page, greetings=greetings, plots=plots, analyses=analyses
        )

        with open(html_path, "w") as static_file:
            static_file.write(rendered_template)

    return


if __name__ == "__main__":
    big = ["AAPL", "GOOG", "AMZN"]
    tech = ["NVDA", "TSLA", "SMCI"]
    generate_page("home.html", "static_html/big.html", big, 400)
    generate_page("home.html", "static_html/tech.html", tech, 400)
