from flask import Flask, render_template, request
from webapp.plotter import candle_chart


def create_app():
    app = Flask(__name__)
    app.config.from_pyfile('config.py')

    @app.route('/')
    def index():
        title = "CryptoCandle"
        return render_template('index.html', page_title=title)


    @app.route('/api', methods=["GET"])
    def api():
        pair  = request.args.get("pair", "BTCUSD")
        interval  = int(request.args.get("interval", 1))
        depth = int(request.args.get("depth", 40))
        chart = candle_chart(pair, interval, depth)
        title = "API"
        return render_template('api.html', page_title=title, chart = chart)

    
    @app.route('/chart', methods=["GET"])
    def chart():
        title = "Chart"
        return render_template('chart.html', page_title=title, chart = chart)

    @app.route('/demo')
    def demo():
        title = "Demo"
        chart = candle_chart("BTCUSD", 30, 50)
        return render_template('demo.html', page_title=title, chart = chart)



    return app
