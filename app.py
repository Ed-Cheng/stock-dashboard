from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def index():
    greetings = "Hello World, this is my first plotly plot"

    ls = ["aa", "ss", "ff"]


    return render_template("newhome.html", ls=ls)


if __name__ == "__main__":
    app.directory='./'
    app.run(host='127.0.0.1', port=5000)