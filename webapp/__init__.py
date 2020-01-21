from flask import Flask, render_template
from webapp.plotter import candle_chart


def create_app():
    app = Flask(__name__)
    app.config.from_pyfile('config.py')

    @app.route('/')
    def index():
        title = "CryptoCandle"
        chart = candle_chart("BTCUSD", 30, 50)
        return render_template('index.html', page_title=title, chart = chart)
    return app