from flask import Flask, send_from_directory

app = Flask(__name__)


@app.route("/")
def big():
    return send_from_directory("static_html", "big.html")


@app.route("/tech")
def tech():
    return send_from_directory("static_html", "tech.html")


if __name__ == "__main__":
    app.run(debug=True)
