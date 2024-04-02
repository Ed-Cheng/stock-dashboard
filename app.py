from flask import Flask, send_from_directory

app = Flask(__name__)


@app.route("/")
def home():
    return send_from_directory("static_html", "mag7.html")


@app.route("/mag7")
def mag7():
    return send_from_directory("static_html", "mag7.html")


@app.route("/ai")
def ai():
    return send_from_directory("static_html", "ai.html")


@app.route("/tech")
def tech():
    return send_from_directory("static_html", "tech.html")


@app.route("/meme")
def meme():
    return send_from_directory("static_html", "meme.html")


@app.route("/watch")
def watch():
    return send_from_directory("static_html", "watch.html")


if __name__ == "__main__":
    app.run(debug=True)
